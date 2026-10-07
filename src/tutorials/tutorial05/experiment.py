"""Scientific source shared by Tutorial05's browser and student notebook."""
import contextlib
import csv
import io
import json
import re
import traceback

import numpy as np
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (average_precision_score, confusion_matrix, log_loss,
                             precision_recall_curve, roc_auc_score, roc_curve)
from sklearn.model_selection import StratifiedKFold, train_test_split
from sklearn.neighbors import KNeighborsClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import FunctionTransformer, SplineTransformer, StandardScaler

SEED = 3612
FEATURES = ['Characters', 'Words', 'Links', 'Digits', 'Exclamation marks']
TOKEN_PATTERN = r'(?u)\b[a-z0-9]+\b'


def tokens(text):
    """Simple, explicit tokenizer; the vectorizers use the same pattern."""
    return re.findall(TOKEN_PATTERN, text.lower())


def numerical_features(messages):
    """Hand-designed observations; no labels or fitted statistics are used."""
    return np.asarray([[len(s), len(tokens(s)),
                        len(re.findall(r'https?://|www\.', s, flags=re.I)),
                        sum(c.isdigit() for c in s), s.count('!')]
                       for s in messages], dtype=float)


def load_data(path):
    """Deduplicate message identities BEFORE splitting; reject label conflicts."""
    with open(path, encoding='utf-8-sig', newline='') as handle:
        rows = list(csv.DictReader(handle, fieldnames=['Category', 'Message'],
                                   delimiter='\t', quoting=csv.QUOTE_NONE))
    unique = {}
    excluded = 0
    for row in rows:
        text, category = row['Message'], row['Category']
        if category not in ('ham', 'spam'):
            raise ValueError('Expected ham/spam Category.')
        if not text.strip() or text.strip() == '#ERROR!':
            excluded += 1
            continue
        # Identical after whitespace/case normalization must not cross splits.
        identity = ' '.join(text.lower().split())
        label = int(category == 'spam')
        if identity in unique and unique[identity][1] != label:
            raise ValueError('Conflicting labels for the same message.')
        unique.setdefault(identity, (text, label))
    messages = np.asarray([r[0] for r in unique.values()])
    labels = np.asarray([r[1] for r in unique.values()], dtype=int)
    train_val, test = train_test_split(np.arange(len(labels)), test_size=.2,
                                      stratify=labels, random_state=SEED)
    train, validation = train_test_split(train_val, test_size=.25,
                                       stratify=labels[train_val], random_state=SEED)
    return messages, labels, {'train': train, 'validation': validation, 'test': test}, {'raw': len(rows), 'excluded': excluded}


def rule_predict(messages, keywords=('free', 'win', 'prize')):
    """A transparent rule: flag when any selected whole-word token appears."""
    selected = set(keywords)
    return np.asarray([int(bool(selected.intersection(tokens(s)))) for s in messages])


def decision_metrics(y, probability, threshold=.5):
    """Threshold-dependent decisions, computed once in the scientific layer."""
    p = np.asarray(probability, dtype=float)
    prediction = (p >= threshold).astype(int)
    tn, fp, fn, tp = confusion_matrix(y, prediction, labels=[0, 1]).ravel()
    precision = tp / (tp + fp) if tp + fp else 0.
    recall = tp / (tp + fn) if tp + fn else 0.
    return {'accuracy': float((prediction == y).mean()), 'precision': float(precision),
            'recall': float(recall), 'f1': float(2 * precision * recall / (precision + recall))
            if precision + recall else 0., 'confusion': [[int(tn), int(fp)], [int(fn), int(tp)]],
            'false_positive_rate': float(fp / (tn + fp)) if tn + fp else 0.}


def metrics(y, probability, threshold=.5):
    """Positive class is spam. Undefined precision is reported as zero."""
    p = np.asarray(probability, dtype=float)
    return {**decision_metrics(y, p, threshold),
            'log_loss': float(log_loss(y, np.clip(p, 1e-12, 1 - 1e-12), labels=[0, 1])),
            'average_precision': float(average_precision_score(y, p)),
            'roc_auc': float(roc_auc_score(y, p))}


def build_model(kind='logistic', representation='count', C=1., k=5):
    """Keep every learned transformation inside the pipeline."""
    if representation == 'numeric' or kind in ('lda', 'gam'):
        steps = [('features', FunctionTransformer(numerical_features)),
                 ('log', FunctionTransformer(np.log1p))]
        if kind == 'gam':
            # Separate spline bases for each input; no feature interactions.
            steps += [('splines', SplineTransformer(n_knots=4, degree=3,
                                                    include_bias=False))]
        steps += [('scale', StandardScaler())]
    else:
        vectorizer = CountVectorizer if representation == 'count' else TfidfVectorizer
        steps = [('vectorizer', vectorizer(token_pattern=TOKEN_PATTERN, min_df=2,
                                          max_features=2500))]
    if kind == 'lda':
        classifier = LinearDiscriminantAnalysis(solver='lsqr', shrinkage='auto')
    elif kind == 'knn':
        classifier = KNeighborsClassifier(n_neighbors=int(k), algorithm='brute',
                                           metric='euclidean' if representation == 'numeric' else 'cosine')
    else:
        classifier = LogisticRegression(C=float(C), solver='liblinear', max_iter=1000,
                                         random_state=SEED)
    return Pipeline(steps + [('classifier', classifier)])


def cross_validate(messages, labels, representation='count', values=(.01, .1, 1., 10.)):
    """Fit vocabulary, IDF and model afresh inside EACH training fold."""
    folds = list(StratifiedKFold(5, shuffle=True, random_state=SEED).split(messages, labels))
    rows = []
    for C in values:
        scores, training, vocabulary_sizes = [], [], []
        for train, heldout in folds:
            model = build_model(C=C, representation=representation)
            model.fit(messages[train], labels[train])
            scores.append(average_precision_score(labels[heldout], model.predict_proba(messages[heldout])[:, 1]))
            training.append(average_precision_score(labels[train], model.predict_proba(messages[train])[:, 1]))
            vocabulary_sizes.append(len(model.named_steps['vectorizer'].vocabulary_))
        rows.append({'C': C, 'folds': list(map(float, scores)), 'train': float(np.mean(training)),
                     'mean': float(np.mean(scores)), 'std': float(np.std(scores, ddof=1)),
                     'vocabulary_sizes': vocabulary_sizes})
    return rows


class Experiment:
    def __init__(self, path):
        self.messages, self.labels, self.splits, self.audit = load_data(path)
        with open(path, encoding='utf-8-sig') as handle:
            # The first lines exactly as stored: label, tab, message.
            self.preview = [handle.readline().rstrip('\n') for _ in range(6)]
        self.X_train = self.messages[self.splits['train']]
        self.y_train = self.labels[self.splits['train']]
        self.X_val = self.messages[self.splits['validation']]
        self.y_val = self.labels[self.splits['validation']]
        self.runs = {}
        self.final = None

    def initialize(self):
        counts = {s: {'total': len(ix), 'ham': int((self.labels[ix] == 0).sum()),
                      'spam': int((self.labels[ix] == 1).sum())} for s, ix in self.splits.items()}
        examples = []
        for label in (0, 1):
            for i in np.flatnonzero(self.y_train == label)[:6]:
                examples.append({'text': str(self.X_train[i]), 'label': label})
        numeric = numerical_features(self.X_train)
        distributions = []
        for j, name in enumerate(FEATURES):
            edges = np.linspace(0, float(np.percentile(numeric[:, j], 99)) + 1, 13)
            groups = []
            for label in (0, 1):
                values = numeric[self.y_train == label, j]
                # Final bin contains the long tail; normalize by class size.
                counts_j = np.histogram(np.minimum(values, edges[-1] - 1e-9), edges)[0]
                groups.append((counts_j / len(values)).tolist())
            distributions.append({'name': name, 'edges': edges.tolist(), 'groups': groups})
        # Train and validation rows for the in-page data table; test stays hidden.
        table = []
        for split in ('train', 'validation'):
            ix = self.splits[split]
            for i, values in zip(ix, numerical_features(self.messages[ix])):
                table.append({'split': split, 'label': int(self.labels[i]),
                              'text': str(self.messages[i]), 'features': values.tolist()})
        return {'raw': self.audit['raw'], 'preview': self.preview, 'table': table, 'excluded': self.audit['excluded'], 'unique': len(self.messages),
                'duplicates': self.audit['raw'] - self.audit['excluded'] - len(self.messages), 'counts': counts,
                'examples': examples, 'distributions': distributions,
                'baseline': metrics(self.y_val, np.zeros(len(self.y_val))),
                'points': [{'x': float(r[0]), 'y': float(r[3]), 'label': int(y)}
                           for r, y in zip(numeric[:350], self.y_train[:350])]}

    def rules(self, params):
        keywords = tokens(params.get('keywords', 'free win prize'))
        predictions = rule_predict(self.X_val, keywords)
        errors = np.flatnonzero(predictions != self.y_val)
        return {'metrics': metrics(self.y_val, predictions), 'errors': [
            {'text': str(self.X_val[i]), 'label': int(self.y_val[i]), 'prediction': int(predictions[i])}
            for i in errors[:10]], 'custom': int(rule_predict([params.get('text', '')], keywords)[0])}

    def vectorize(self, params):
        documents = params.get('documents', ['Free prize now', 'Are you free after class', 'Win a prize prize'])
        use_tfidf = params.get('representation', 'count') == 'tfidf'
        vectorizer = (TfidfVectorizer if use_tfidf else CountVectorizer)(token_pattern=TOKEN_PATTERN)
        matrix = vectorizer.fit_transform(documents)
        text = params.get('text', 'free meeting tomorrow')
        test = vectorizer.transform([text])
        idf = vectorizer.idf_.tolist() if use_tfidf else [1.] * matrix.shape[1]
        return {'documents': documents, 'text': text, 'representation': params.get('representation', 'count'),
                'vocabulary': vectorizer.get_feature_names_out().tolist(),
                'matrix': matrix.toarray().tolist(), 'transformed': test.toarray()[0].tolist(),
                'idf': idf, 'tokens': tokens(text),
                'unknown': sorted(set(tokens(text)) - set(vectorizer.vocabulary_)),
                'numeric': numerical_features([text])[0].tolist()}

    def fit(self, config, progress_callback=None):
        if self.final:
            raise ValueError('Final test already evaluated. Restart Python for a new experiment.')
        kind = config.get('kind', 'logistic')
        representation = 'numeric' if kind in ('lda', 'gam') else config.get('representation', 'count')
        C, k = float(config.get('C', 1.)), int(config.get('k', 5))
        if C <= 0 or not 1 <= k <= len(self.y_train):
            raise ValueError('C must be positive and k must fit the training set.')
        if kind not in ('logistic', 'lda', 'gam', 'knn') or representation not in ('count', 'tfidf', 'numeric'):
            raise ValueError('Unknown model or representation.')
        model = build_model(kind, representation, C, k)
        model.fit(self.X_train, self.y_train)
        probability = model.predict_proba(self.X_val)[:, 1]
        run_id = f'run{len(self.runs) + 1}'
        row = {'id': run_id, 'kind': kind, 'representation': representation, 'C': C, 'k': k,
               'train': metrics(self.y_train, model.predict_proba(self.X_train)[:, 1]),
               'validation': metrics(self.y_val, probability),
               'parameters': int(model.named_steps['classifier'].coef_.size)
               if hasattr(model.named_steps['classifier'], 'coef_') else len(self.X_train),
               'thresholds': [decision_metrics(self.y_val, probability, i / 100) for i in range(101)],
               # Validation score counts per class in 20 equal bins on [0, 1].
               'histogram': [np.histogram(probability[self.y_val == c], 20, (0, 1))[0].tolist()
                             for c in (0, 1)]}
        self.runs[run_id] = {'model': model, 'row': row, 'probability': probability}
        return row

    def regularization(self, params):
        rows = [self.fit({'C': C, 'representation': params.get('representation', 'count')})
                for C in (.001, .01, .1, 1., 10.)]
        models = [self.runs[row['id']]['model'] for row in rows]
        coefficients = np.vstack([m.named_steps['classifier'].coef_[0] for m in models])
        # Follow the eight words with the largest weights at the weakest penalty.
        words = models[-1].named_steps['vectorizer'].get_feature_names_out()
        top = np.argsort(-np.abs(coefficients[-1]))[:8]
        return {'rows': rows, 'weights': np.linalg.norm(coefficients, axis=1).tolist(),
                'paths': [{'word': str(words[j]), 'weights': coefficients[:, j].tolist()} for j in top]}

    def cv(self, params):
        if self.final:
            raise ValueError('The final test decision is frozen. Restart to begin again.')
        representation = params.get('representation', 'count')
        rows = cross_validate(self.X_train, self.y_train, representation)
        best = max(rows, key=lambda row: row['mean'])
        train, heldout = next(StratifiedKFold(5, shuffle=True, random_state=SEED).split(self.X_train, self.y_train))
        vectorizer = CountVectorizer(token_pattern=TOKEN_PATTERN, min_df=2, max_features=2500)
        vectorizer.fit(self.X_train[train])
        unknown = sorted(set(t for s in self.X_train[heldout] for t in tokens(s)) - set(vectorizer.vocabulary_))
        return {'rows': rows, 'best': best['C'], 'fold_sizes': [len(train), len(heldout)],
                'fold_unknown': unknown[:16], 'run': self.fit({'C': best['C'], 'representation': representation})}

    def explain(self, params):
        run = self.runs[params['id']]
        model = run['model']
        text = params.get('text', 'Congratulations! Claim your free prize now!')
        vector = model[:-1].transform([text])
        classifier = model.named_steps['classifier']
        if not hasattr(classifier, 'coef_'):
            distances, indices = classifier.kneighbors(vector)
            return {'text': text, 'neighbors': [{'text': str(self.X_train[i]), 'label': int(self.y_train[i]),
                                   'distance': float(d)} for d, i in zip(distances[0], indices[0])],
                    'probability': float(model.predict_proba([text])[0, 1])}
        values = vector.toarray()[0] if hasattr(vector, 'toarray') else vector[0]
        contributions = values * classifier.coef_[0]
        if 'vectorizer' in model.named_steps:
            names = model.named_steps['vectorizer'].get_feature_names_out()
        elif run['row']['kind'] == 'gam':
            n = len(values) // len(FEATURES)
            contributions = contributions.reshape(len(FEATURES), n).sum(axis=1)
            names = FEATURES
        else:
            names = FEATURES
        active = np.flatnonzero(contributions)
        order = active[np.argsort(-np.abs(contributions[active]))]
        bias = float(classifier.intercept_[0])
        return {'contributions': [{'name': str(names[i]), 'value': float(contributions[i])} for i in order],
                'bias': bias, 'score': float(bias + contributions.sum()),
                'probability': float(model.predict_proba([text])[0, 1]),
                'text': text, 'numeric': numerical_features([text])[0].tolist()}

    def lda(self, params):
        row = self.fit({'kind': 'lda'})
        model = self.runs[row['id']]['model']
        transformed = model[:-1].transform(self.X_train)
        classifier = model.named_steps['classifier']
        means, covariance = classifier.means_, classifier.covariance_
        ix = [0, 3]  # log length and log digit count, in standardized coordinates
        centers = means[:, ix]
        cov = covariance[np.ix_(ix, ix)]
        w = np.linalg.solve(cov, centers[1] - centers[0])
        b = -.5 * (centers[1] @ np.linalg.solve(cov, centers[1]) - centers[0] @ np.linalg.solve(cov, centers[0]))
        b += np.log(classifier.priors_[1] / classifier.priors_[0])
        eigenvalues, eigenvectors = np.linalg.eigh(cov)
        angles = np.linspace(0, 2 * np.pi, 80)
        ring = np.column_stack([np.cos(angles), np.sin(angles)]) @ (eigenvectors @ np.diag(np.sqrt(eigenvalues))).T
        return {'run': row, 'means': centers.tolist(), 'ellipses': [(ring + m).tolist() for m in centers],
                'points': [{'x': float(r[0]), 'y': float(r[3]), 'label': int(y)}
                           for r, y in zip(transformed[:350], self.y_train[:350])],
                'boundary': {'w': w.tolist(), 'b': float(b)},
                'priors': classifier.priors_.tolist()}

    def gam(self, params):
        row = self.fit({'kind': 'gam', 'C': params.get('C', 1.)})
        model = self.runs[row['id']]['model']
        raw = numerical_features(self.X_train)
        reference = np.median(raw, axis=0)
        curves = []
        for j, name in enumerate(FEATURES):
            grid = np.linspace(float(raw[:, j].min()), max(1., np.percentile(raw[:, j], 99)), 60)
            matrix = np.tile(reference, (len(grid), 1))
            matrix[:, j] = grid
            # Start after the raw-text feature step; manually supplied observations.
            values = model[1:-1].transform(matrix)
            base = model[1:-1].transform(reference.reshape(1, -1))
            effect = (values - base) @ model.named_steps['classifier'].coef_[0]
            curves.append({'name': name, 'x': grid.tolist(), 'effect': effect.tolist()})
        return {'run': row, 'reference': reference.tolist(), 'curves': curves}

    def evaluate(self, params):
        run = self.runs[params['id']]
        threshold = float(params.get('threshold', .5))
        if not 0 <= threshold <= 1:
            raise ValueError('Threshold must be between 0 and 1.')
        p, y = run['probability'], self.y_val
        predicted = (p >= threshold).astype(int)
        errors = np.flatnonzero(predicted != y)
        ordered = sorted(errors, key=lambda i: -abs(p[i] - .5))
        precision, recall, _ = precision_recall_curve(y, p)
        fpr, tpr, _ = roc_curve(y, p)
        # Thin only the displayed curves; metrics use all observations.
        def sample(a, b):
            ix = np.unique(np.linspace(0, len(a) - 1, min(160, len(a))).astype(int))
            return np.column_stack([a[ix], b[ix]]).tolist()
        return {'threshold': threshold, 'metrics': metrics(y, p, threshold), 'pr': sample(recall, precision),
                'roc': sample(fpr, tpr), 'prevalence': float(y.mean()),
                'errors': [{'text': str(self.X_val[i]), 'label': int(y[i]),
                            'probability': float(p[i]), 'prediction': int(predicted[i])}
                           for i in ordered[:12]]}

    def final_test(self, params):
        identity = params['id']
        threshold = float(params.get('threshold', .5))
        reason = str(params.get('reason', '')).strip()
        if not reason:
            raise ValueError('Record why you chose this model and threshold before testing.')
        if not 0 <= threshold <= 1:
            raise ValueError('Threshold must be between 0 and 1.')
        if self.final:
            if self.final['id'] != identity or self.final['threshold'] != threshold:
                raise ValueError('The test set has already been used; the decision is frozen.')
            return self.final
        run = self.runs[identity]
        ix = self.splits['test']
        probability = run['model'].predict_proba(self.messages[ix])[:, 1]
        self.final = {'id': identity, 'threshold': threshold, 'reason': reason,
                      'configuration': {k: run['row'][k] for k in ('kind', 'representation', 'C', 'k')},
                      'validation': metrics(self.y_val, run['probability'], threshold),
                      'test': metrics(self.labels[ix], probability, threshold)}
        return self.final

    def execute(self, params):
        # A fresh namespace for each snippet; intentionally omit held-out test arrays.
        namespace = {name: globals()[name] for name in ('np', 'tokens', 'numerical_features',
                     'rule_predict', 'metrics', 'build_model', 'cross_validate',
                     'CountVectorizer', 'TfidfVectorizer')}
        namespace.update(X_train=self.X_train.copy(), y_train=self.y_train.copy(),
                         X_val=self.X_val.copy(), y_val=self.y_val.copy())
        output, error = io.StringIO(), None
        try:
            with contextlib.redirect_stdout(output):
                exec(params['code'], namespace)
        except Exception:
            error = traceback.format_exc()
        return {'stdout': output.getvalue(), 'error': error}

    def dispatch(self, action, params):
        handlers = {'initialize': lambda p: self.initialize(), 'rules': self.rules,
                    'vectorize': self.vectorize, 'regularization': self.regularization,
                    'cv': self.cv, 'explain': self.explain, 'lda': self.lda, 'gam': self.gam,
                    'evaluate': self.evaluate, 'final_test': self.final_test, 'execute': self.execute}
        if action not in handlers:
            raise ValueError(f'Unknown action: {action}')
        return json.dumps(handlers[action](params), allow_nan=False)
