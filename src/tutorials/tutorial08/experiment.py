"""Scientific source shared by Tutorial08's browser and student notebook.

The lesson keeps three small teaching datasets in memory:

* ``moons``: two interleaving crescents, used for trees, ensembles and kernels.
* ``iris``: two iris species described by petal length and width, used for margins.
* ``xor``: four noisy quadrants, used to contrast linear and RBF kernels.

Nothing outside scikit-learn's bundled data is downloaded. Test rows are held only
inside this object and are never exposed to browser snippets before the final test.
"""
import contextlib
import io
import json
import traceback

import numpy as np
from sklearn.datasets import load_iris, make_moons
from sklearn.ensemble import (AdaBoostClassifier, BaggingClassifier,
                              GradientBoostingClassifier, RandomForestClassifier)
from sklearn.metrics import confusion_matrix
from sklearn.model_selection import train_test_split
from sklearn.svm import SVC
from sklearn.tree import DecisionTreeClassifier, export_text

SEED = 3612


def split_dataset(X, y):
    """Return deterministic, stratified 60 / 20 / 20 train / validation / test rows."""
    X = np.asarray(X, dtype=float)
    y = np.asarray(y, dtype=int)
    X_dev, X_test, y_dev, y_test = train_test_split(
        X, y, test_size=.2, stratify=y, random_state=SEED)
    X_train, X_val, y_train, y_val = train_test_split(
        X_dev, y_dev, test_size=.25, stratify=y_dev, random_state=SEED)
    return {'X_train': X_train, 'y_train': y_train, 'X_val': X_val, 'y_val': y_val,
            'X_test': X_test, 'y_test': y_test}


def make_teaching_data():
    """Create the three fixed datasets used by both the lesson and the notebook."""
    X, y = make_moons(n_samples=600, noise=.30, random_state=SEED)
    moons = split_dataset(X, y)
    moons['name'] = 'Two moons'
    moons['feature_names'] = ['x1', 'x2']

    iris = load_iris()
    keep = np.isin(iris.target, [1, 2])
    # 0 = versicolor, 1 = virginica. Raw petal measurements keep the margin readable.
    X_iris = iris.data[keep][:, [2, 3]]
    y_iris = (iris.target[keep] == 2).astype(int)
    iris_data = split_dataset(X_iris, y_iris)
    iris_data['name'] = 'Iris petals'
    iris_data['feature_names'] = ['petal length (cm)', 'petal width (cm)']

    rng = np.random.default_rng(SEED)
    X_xor = rng.normal(size=(400, 2))
    y_xor = np.logical_xor(X_xor[:, 0] > 0, X_xor[:, 1] > 0).astype(int)
    xor = split_dataset(X_xor, y_xor)
    xor['name'] = 'XOR quadrants'
    xor['feature_names'] = ['x1', 'x2']
    return {'moons': moons, 'iris': iris_data, 'xor': xor}


def metrics(y_true, y_pred):
    """Decision metrics for a binary task; class 1 is the positive class."""
    y_true = np.asarray(y_true, dtype=int)
    y_pred = np.asarray(y_pred, dtype=int)
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred, labels=[0, 1]).ravel()
    precision = tp / (tp + fp) if tp + fp else 0.
    recall = tp / (tp + fn) if tp + fn else 0.
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.
    return {'accuracy': float((y_true == y_pred).mean()),
            'precision': float(precision), 'recall': float(recall), 'f1': float(f1),
            'confusion': [[int(tn), int(fp)], [int(fn), int(tp)]]}


def build_tree(depth=4, min_leaf=1):
    """A single axis-aligned classification tree."""
    depth = None if depth in (None, 'None', 0, '0') else int(depth)
    return DecisionTreeClassifier(max_depth=depth, min_samples_leaf=max(1, int(min_leaf)),
                                  random_state=SEED)


def build_forest(mode='forest', n_estimators=100, max_features='sqrt', max_depth=6):
    """Bagged trees (``mode='bagging'``) or a random forest (``mode='forest'``)."""
    n_estimators = max(1, int(n_estimators))
    max_depth = None if max_depth in (None, 'None', 0) else int(max_depth)
    if mode == 'bagging':
        return BaggingClassifier(
            estimator=DecisionTreeClassifier(max_depth=max_depth, random_state=SEED),
            n_estimators=n_estimators, max_samples=1.0, bootstrap=True,
            oob_score=True, n_jobs=1, random_state=SEED)
    if mode != 'forest':
        raise ValueError('mode must be forest or bagging')
    features = 1.0 if max_features in ('all', 1.0, '1.0') else max_features
    return RandomForestClassifier(
        n_estimators=n_estimators, max_depth=max_depth, max_features=features,
        bootstrap=True, oob_score=True, n_jobs=1, random_state=SEED)


def build_boosting(mode='gradient', n_estimators=100, learning_rate=.1):
    """AdaBoost with stumps or gradient-boosted shallow trees."""
    n_estimators = max(1, int(n_estimators))
    learning_rate = float(learning_rate)
    if mode == 'adaboost':
        return AdaBoostClassifier(
            estimator=DecisionTreeClassifier(max_depth=1, random_state=SEED),
            n_estimators=n_estimators, learning_rate=learning_rate, random_state=SEED)
    if mode != 'gradient':
        raise ValueError('mode must be adaboost or gradient')
    return GradientBoostingClassifier(
        n_estimators=n_estimators, learning_rate=learning_rate, max_depth=2,
        random_state=SEED)


def build_svm(kernel='rbf', C=1., gamma=1., degree=3):
    """Soft-margin support vector classifier with one of three teaching kernels."""
    C = float(C)
    if C <= 0:
        raise ValueError('C must be positive.')
    if kernel == 'linear':
        return SVC(kernel='linear', C=C)
    if kernel not in ('poly', 'rbf', 'sigmoid'):
        raise ValueError('kernel must be linear, poly, rbf or sigmoid')
    return SVC(kernel=kernel, C=C, gamma=float(gamma), degree=int(degree))


def _tree_probability(estimator, X):
    """Read class-1 probability even when a bootstrap tree sees only one class."""
    probabilities = estimator.predict_proba(X)
    positive = np.zeros(len(X), dtype=float)
    for column, label in enumerate(estimator.classes_):
        if int(label) == 1:
            positive = probabilities[:, column]
    return positive


def _bounds(X):
    X = np.asarray(X, dtype=float)
    low, high = X.min(axis=0), X.max(axis=0)
    span = np.maximum(high - low, 1e-6)
    return [float(low[0] - .08 * span[0]), float(high[0] + .08 * span[0]),
            float(low[1] - .08 * span[1]), float(high[1] + .08 * span[1])]


def _data_bounds(data):
    return _bounds(np.vstack([data['X_train'], data['X_val']]))


def _points(X, y, split):
    return [{'x': float(x), 'y': float(z), 'label': int(label), 'split': split}
            for (x, z), label in zip(X, y)]


def _importance(model):
    if hasattr(model, 'feature_importances_'):
        values = model.feature_importances_
    elif hasattr(model, 'estimators_'):
        values = np.mean([tree.feature_importances_ for tree in model.estimators_], axis=0)
    else:
        return []
    return [float(v) for v in values]


def _grid(model, bounds, resolution=55):
    x = np.linspace(bounds[0], bounds[1], resolution)
    y = np.linspace(bounds[2], bounds[3], resolution)
    xx, yy = np.meshgrid(x, y)
    flat = np.column_stack([xx.ravel(), yy.ravel()])
    if hasattr(model, 'predict_proba'):
        z = 2 * model.predict_proba(flat)[:, 1] - 1
    else:
        z = model.decision_function(flat)
        scale = float(np.max(np.abs(z))) or 1.
        z = z / scale
    return {'x': x.tolist(), 'y': y.tolist(),
            'z': np.asarray(z).reshape(resolution, resolution).tolist()}


def _support(model, data):
    if not hasattr(model, 'support_'):
        return []
    return [{'x': float(x[0]), 'y': float(x[1]), 'label': int(data['y_train'][i])}
            for i, x in zip(model.support_, model.support_vectors_)]


def _margin_lines(model, bounds):
    """Return f=0 and f=±1 lines for a linear SVC, clipped to the plot bounds."""
    if not hasattr(model, 'coef_'):
        return []
    w, b = model.coef_[0], float(model.intercept_[0])
    lines = []
    for level, name, dashed in ((0., 'boundary f=0', False),
                                (1., 'margin f=+1', True),
                                (-1., 'margin f=-1', True)):
        if abs(w[1]) > 1e-9:
            x1, x2 = bounds[0], bounds[1]
            y1 = (level - b - w[0] * x1) / w[1]
            y2 = (level - b - w[0] * x2) / w[1]
        elif abs(w[0]) > 1e-9:
            x1 = x2 = (level - b) / w[0]
            y1, y2 = bounds[2], bounds[3]
        else:
            continue
        lines.append({'name': name, 'x1': float(x1), 'y1': float(y1),
                      'x2': float(x2), 'y2': float(y2), 'dashed': dashed})
    return lines


class Experiment:
    def __init__(self, path=None):
        # ``path`` is accepted for the shared worker interface; all data are generated.
        self.path = path
        self.datasets = make_teaching_data()
        self.moons = self.datasets['moons']
        self.iris = self.datasets['iris']
        self.xor = self.datasets['xor']
        self.runs = {}
        self.counter = 0
        self.comparison = {}
        self.final = None

    def data_plot(self, name):
        data = self.datasets[name]
        return {'bounds': _data_bounds(data),
                'grid': None,
                'points': (_points(data['X_train'], data['y_train'], 'train')
                           + _points(data['X_val'], data['y_val'], 'validation')),
                'support': [], 'lines': []}

    def plot_for(self, model, data, support=False, lines=None):
        return {'bounds': _data_bounds(data),
                'grid': _grid(model, _data_bounds(data)),
                'points': (_points(data['X_train'], data['y_train'], 'train')
                           + _points(data['X_val'], data['y_val'], 'validation')),
                'support': _support(model, data) if support else [],
                'lines': lines or []}

    def _score(self, model, data):
        return {'train': metrics(data['y_train'], model.predict(data['X_train'])),
                'validation': metrics(data['y_val'], model.predict(data['X_val']))}

    def _store(self, kind, name, params, model, data, **extra):
        self.counter += 1
        row = {'id': f'run{self.counter}', 'kind': kind, 'name': name, 'params': params,
               'dataset': data['name'], 'feature_names': data['feature_names'],
               **self._score(model, data), **extra}
        self.runs[row['id']] = {'model': model, 'data': data, 'row': row}
        return row

    def _check_open(self):
        if self.final:
            raise ValueError('The final test is frozen. Restart Python to run another experiment.')

    def _forest_curve(self, model, data):
        total_train = np.zeros(len(data['y_train']))
        total_val = np.zeros(len(data['y_val']))
        n, train, validation = [], [], []
        for i, tree in enumerate(model.estimators_, start=1):
            total_train += _tree_probability(tree, data['X_train'])
            total_val += _tree_probability(tree, data['X_val'])
            n.append(i)
            train.append(float((((total_train / i) >= .5).astype(int) == data['y_train']).mean()))
            validation.append(float((((total_val / i) >= .5).astype(int) == data['y_val']).mean()))
        return {'n': n, 'train': train, 'validation': validation}

    def _staged_curve(self, model, data):
        train, validation = [], []
        for pred_train, pred_val in zip(model.staged_predict(data['X_train']),
                                        model.staged_predict(data['X_val'])):
            train.append(float((pred_train == data['y_train']).mean()))
            validation.append(float((pred_val == data['y_val']).mean()))
        return {'n': list(range(1, len(train) + 1)), 'train': train, 'validation': validation}

    def initialize(self):
        counts = {}
        for name, data in self.datasets.items():
            counts[name] = {}
            for split in ('train', 'val', 'test'):
                y = data[f'y_{split}']
                counts[name][split] = {'total': int(len(y)),
                                       'class0': int((y == 0).sum()),
                                       'class1': int((y == 1).sum())}
        baseline = {}
        for name, data in self.datasets.items():
            majority = int(np.bincount(data['y_train']).argmax())
            baseline[name] = metrics(data['y_val'], np.full(len(data['y_val']), majority))
        return {'counts': counts, 'baseline': baseline,
                'plots': {name: self.data_plot(name) for name in self.datasets},
                'seed': SEED}

    def fit_tree(self, params):
        self._check_open()
        depth = params.get('depth', 4)
        min_leaf = params.get('min_leaf', 1)
        model = build_tree(depth=depth, min_leaf=min_leaf)
        model.fit(self.moons['X_train'], self.moons['y_train'])
        rules = export_text(model, feature_names=self.moons['feature_names'],
                            max_depth=3, decimals=2).splitlines()[:20]
        return self._store(
            'tree', 'Decision tree', {'depth': depth, 'min_leaf': min_leaf}, model,
            self.moons, nodes=int(model.tree_.node_count),
            leaves=int(model.get_n_leaves()), actual_depth=int(model.get_depth()),
            rules=rules, importance=_importance(model),
            plot=self.plot_for(model, self.moons))

    def fit_forest(self, params):
        self._check_open()
        mode = params.get('mode', 'forest')
        n = int(params.get('n_estimators', 100))
        features = params.get('max_features', 'sqrt')
        model = build_forest(mode=mode, n_estimators=n, max_features=features)
        model.fit(self.moons['X_train'], self.moons['y_train'])
        return self._store(
            mode, 'Random forest' if mode == 'forest' else 'Bagged trees',
            {'mode': mode, 'n_estimators': n, 'max_features': features}, model,
            self.moons,
            oob=(None if not np.isfinite(getattr(model, 'oob_score_', np.nan))
                 else float(model.oob_score_)),
            importance=_importance(model), curve=self._forest_curve(model, self.moons),
            plot=self.plot_for(model, self.moons))

    def fit_boosting(self, params):
        self._check_open()
        mode = params.get('mode', 'gradient')
        n = int(params.get('n_estimators', 100))
        learning_rate = float(params.get('learning_rate', .1))
        model = build_boosting(mode=mode, n_estimators=n, learning_rate=learning_rate)
        model.fit(self.moons['X_train'], self.moons['y_train'])
        curve = self._staged_curve(model, self.moons)
        best = int(np.argmax(curve['validation'])) + 1
        return self._store(
            mode, 'AdaBoost' if mode == 'adaboost' else 'Gradient boosting',
            {'mode': mode, 'n_estimators': n, 'learning_rate': learning_rate}, model,
            self.moons, best_n=best, importance=_importance(model), curve=curve,
            plot=self.plot_for(model, self.moons))

    def fit_margin(self, params):
        self._check_open()
        C = float(params.get('C', 1.))
        model = build_svm(kernel='linear', C=C)
        model.fit(self.iris['X_train'], self.iris['y_train'])
        bounds = _data_bounds(self.iris)
        return self._store(
            'svm-linear', 'Linear SVM', {'C': C}, model, self.iris,
            support_count=int(len(model.support_)),
            plot=self.plot_for(model, self.iris, support=True,
                               lines=_margin_lines(model, bounds)))

    def fit_kernel(self, params):
        self._check_open()
        dataset = params.get('dataset', 'moons')
        data = self.datasets[dataset]
        kernel = params.get('kernel', 'rbf')
        C = float(params.get('C', 1.))
        gamma = float(params.get('gamma', 1.))
        degree = int(params.get('degree', 3))
        model = build_svm(kernel=kernel, C=C, gamma=gamma, degree=degree)
        model.fit(data['X_train'], data['y_train'])
        return self._store(
            f'svm-{kernel}', f'SVM · {kernel}', {'dataset': dataset, 'kernel': kernel,
                                                  'C': C, 'gamma': gamma, 'degree': degree},
            model, data, support_count=int(len(model.support_)),
            plot=self.plot_for(model, data, support=True))

    def compare(self, params=None):
        self._check_open()
        candidates = [
            ('tree', 'Decision tree · depth 4', 'tree', {'depth': 4, 'min_leaf': 1},
             lambda: build_tree(4).fit(self.moons['X_train'], self.moons['y_train'])),
            ('forest', 'Random forest · 160 trees', 'forest',
             {'mode': 'forest', 'n_estimators': 160, 'max_features': 'sqrt'},
             lambda: build_forest('forest', 160).fit(self.moons['X_train'], self.moons['y_train'])),
            ('bagging', 'Bagged trees · 160 trees', 'bagging',
             {'mode': 'bagging', 'n_estimators': 160},
             lambda: build_forest('bagging', 160).fit(self.moons['X_train'], self.moons['y_train'])),
            ('adaboost', 'AdaBoost · 120 stumps', 'adaboost',
             {'mode': 'adaboost', 'n_estimators': 120, 'learning_rate': .5},
             lambda: build_boosting('adaboost', 120, .5).fit(self.moons['X_train'], self.moons['y_train'])),
            ('gradient', 'Gradient boosting · 120 trees', 'gradient',
             {'mode': 'gradient', 'n_estimators': 120, 'learning_rate': .1},
             lambda: build_boosting('gradient', 120, .1).fit(self.moons['X_train'], self.moons['y_train'])),
            ('svm-linear', 'Linear SVM · C = 1', 'svm-linear', {'kernel': 'linear', 'C': 1},
             lambda: build_svm('linear', 1).fit(self.moons['X_train'], self.moons['y_train'])),
            ('svm-rbf', 'RBF SVM · C = 1, γ = 1', 'svm-rbf',
             {'kernel': 'rbf', 'C': 1, 'gamma': 1},
             lambda: build_svm('rbf', 1, 1).fit(self.moons['X_train'], self.moons['y_train'])),
        ]
        rows = []
        self.comparison = {}
        for key, name, kind, config, fit in candidates:
            model = fit()
            row = self._store(kind, name, {**config, 'key': key}, model, self.moons)
            self.comparison[key] = row['id']
            rows.append(row)
        rows.sort(key=lambda row: row['validation']['accuracy'], reverse=True)
        return {'rows': rows, 'best': rows[0]['params']['key'] if rows else None}

    def inspect_candidate(self, params):
        key = params.get('key')
        if key not in self.comparison:
            raise ValueError('Run the validation comparison first.')
        run = self.runs[self.comparison[key]]
        model, data, row = run['model'], run['data'], run['row']
        predicted = model.predict(data['X_val'])
        errors = []
        for (x, y), label, prediction in zip(data['X_val'], data['y_val'], predicted):
            if label != prediction:
                errors.append({'x': float(x), 'y': float(y),
                               'label': int(label), 'prediction': int(prediction)})
        return {'row': row, 'plot': run['plot'] if 'plot' in run else self.plot_for(model, data),
                'errors': errors[:12], 'metrics': row['validation']}

    def final_test(self, params):
        key = params.get('key')
        reason = str(params.get('reason', '')).strip()
        if key not in self.comparison:
            raise ValueError('Run the validation comparison before the final test.')
        if not reason:
            raise ValueError('Record why you chose this model before testing.')
        if self.final:
            if self.final['key'] != key:
                raise ValueError('The test set has already been used; the decision is frozen.')
            return self.final
        run = self.runs[self.comparison[key]]
        model, data, row = run['model'], run['data'], run['row']
        test = metrics(data['y_test'], model.predict(data['X_test']))
        self.final = {'key': key, 'name': row['name'], 'reason': reason,
                      'configuration': row['params'], 'validation': row['validation'],
                      'test': test}
        return self.final

    def execute(self, params):
        """Run one editable snippet with fresh train / validation arrays and no test data."""
        namespace = {'np': np, 'metrics': metrics, 'build_tree': build_tree,
                     'build_forest': build_forest, 'build_boosting': build_boosting,
                     'build_svm': build_svm, 'DecisionTreeClassifier': DecisionTreeClassifier,
                     'RandomForestClassifier': RandomForestClassifier,
                     'BaggingClassifier': BaggingClassifier,
                     'AdaBoostClassifier': AdaBoostClassifier,
                     'GradientBoostingClassifier': GradientBoostingClassifier, 'SVC': SVC,
                     'compare_models': lambda: self.compare()}
        for prefix, data in (('', self.moons), ('iris_', self.iris), ('xor_', self.xor)):
            for split in ('train', 'val'):
                namespace[f'X_{prefix}{split}'] = data[f'X_{split}'].copy()
                namespace[f'y_{prefix}{split}'] = data[f'y_{split}'].copy()
        output, error = io.StringIO(), None
        try:
            with contextlib.redirect_stdout(output):
                exec(params['code'], namespace)
        except Exception:
            error = traceback.format_exc()
        return {'stdout': output.getvalue(), 'error': error}

    def dispatch(self, action, params):
        handlers = {'initialize': lambda p: self.initialize(),
                    'fit_tree': self.fit_tree, 'fit_forest': self.fit_forest,
                    'fit_boosting': self.fit_boosting, 'fit_margin': self.fit_margin,
                    'fit_kernel': self.fit_kernel, 'compare': self.compare,
                    'inspect_candidate': self.inspect_candidate,
                    'final_test': self.final_test, 'execute': self.execute}
        if action not in handlers:
            raise ValueError(f'Unknown action: {action}')
        return json.dumps(handlers[action](params), allow_nan=False)
