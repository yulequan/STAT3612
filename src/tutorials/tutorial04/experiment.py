"""Image classification experiments shared by the browser and the notebook.

Only NumPy and SciPy are required. No plotting, browser API, or hidden network I/O.
The original 800 test images are held out; split the other 1200 into 960/240.
"""
import json
import contextlib
import io
import sys

import numpy as np
from scipy.ndimage import gaussian_filter, sobel


def load_data(path):
    with np.load(path) as source:
        images = source['X'].reshape(-1, 28, 28).astype(np.float64) / 255.0
        labels = source['y'].astype(np.float64)
        cutoff = int(source['n_train'])
    rng = np.random.default_rng(3612)
    train, validation = [], []
    for label in (0, 1):
        indices = np.flatnonzero(labels[:cutoff] == label)
        rng.shuffle(indices)
        n = len(indices) // 5
        validation.extend(indices[:n])
        train.extend(indices[n:])
    return {
        'images': images, 'labels': labels,
        'train': np.sort(train), 'validation': np.sort(validation),
        'test': np.arange(cutoff, len(labels)),
    }


def transform(images, kind='raw', amount=1.0):
    """Accept one image or a batch, always preserving its shape and value units."""
    x = np.asarray(images, dtype=np.float64)
    if kind == 'raw':
        return x.copy()
    if kind == 'blur':
        sigma = (0.0,) * (x.ndim - 2) + (float(amount), float(amount))
        return gaussian_filter(x, sigma=sigma, mode='reflect')
    if kind == 'edges':
        # Fixed scaling; never independently rescale each image for the model.
        return np.hypot(sobel(x, axis=-1, mode='reflect'),
                        sobel(x, axis=-2, mode='reflect')) / 4.0
    if kind == 'brightness':
        return np.clip(x + float(amount), 0, 1)
    if kind == 'shift':
        # Integer horizontal translation with zero padding, never wraparound.
        dx = int(amount)
        out = np.zeros_like(x)
        if dx == 0:
            return x.copy()
        if abs(dx) >= x.shape[-1]:
            return out
        if dx > 0:
            out[..., dx:] = x[..., :-dx]
        else:
            out[..., :dx] = x[..., -dx:]
        return out
    raise ValueError(f'Unknown transform: {kind}')


def features(images, representation='raw', normalize=True):
    x = transform(images, representation).reshape(len(images), -1)
    return x if normalize else x * 255.0


def sigmoid(z):
    z = np.asarray(z, dtype=np.float64)
    e = np.exp(-np.abs(z))
    return np.where(z >= 0, 1 / (1 + e), e / (1 + e))


def loss(w, b, X, y):
    z = X @ w + b
    return float(np.mean(np.logaddexp(0.0, z) - y * z))


def gradient(w, b, X, y):
    residual = sigmoid(X @ w + b) - y
    return X.T @ residual / len(y), float(residual.mean())


def step(w, b, X, y, lr):
    z = X @ w + b
    p = sigmoid(z)
    residual = p - y
    dw = X.T @ residual / len(y)
    db = float(residual.mean())
    w_new = w - lr * dw
    b_new = b - lr * db
    return w_new, b_new


def trace_step(w, b, X, y, lr):
    """Record locals after each executed line of the *actual* training step.

    This is a replayable trace, not a paused debugger. Only this small call is traced;
    the regular training loop runs without tracing overhead.
    """
    snapshots, previous = [], [None]
    names = ('z', 'p', 'residual', 'dw', 'db', 'w_new', 'b_new')

    def record(frame):
        if previous[0] is not None:
            values = {name: np.asarray(frame.f_locals[name]).tolist()
                      for name in names if name in frame.f_locals}
            snapshots.append({'line': previous[0] - step.__code__.co_firstlineno + 1,
                              'values': values})

    def tracer(frame, event, arg):
        if frame.f_code is step.__code__:
            if event in ('line', 'return'):
                record(frame)
                previous[0] = frame.f_lineno if event == 'line' else None
            return tracer
        return None

    original_trace = sys.gettrace()
    try:
        sys.settrace(tracer)
        result = step(w, b, X, y, lr)
    finally:
        sys.settrace(original_trace)
    return result, snapshots


def convolution_map(image, kernel):
    """Valid, stride-one cross-correlation: the operation called convolution in CNNs."""
    image, kernel = np.asarray(image), np.asarray(kernel)
    patches = np.lib.stride_tricks.sliding_window_view(image, kernel.shape)
    return np.einsum('ijab,ab->ij', patches, kernel)


def metrics(w, b, X, y):
    p = sigmoid(X @ w + b)
    pred = p >= .5
    confusion = [[int(np.sum((y == actual) & (pred == guess)))
                  for guess in (0, 1)] for actual in (0, 1)]
    return {'loss': loss(w, b, X, y), 'accuracy': float(np.mean(pred == y)),
            'confusion': confusion}


def train_epochs(X, y, X_validation, y_validation, *, lr=.1, epochs=25,
                 batch=32, seed=3612):
    """Yield one checkpoint per epoch, including the untrained starting point.

    Each epoch uses a seeded random permutation. Validation never changes weights.
    Equal epochs mean equal passes through data, not equal numbers of updates.
    """
    w, b = np.zeros(X.shape[1]), 0.0
    rng = np.random.default_rng(seed)
    for epoch in range(epochs + 1):
        yield {'epoch': epoch, 'train': metrics(w, b, X, y),
               'validation': metrics(w, b, X_validation, y_validation),
               'w': w.copy(), 'b': float(b)}
        if epoch == epochs:
            break
        order = rng.permutation(len(y))
        for start in range(0, len(y), batch):
            indices = order[start:start + batch]
            w, b = step(w, b, X[indices], y[indices], lr)


def train(X, y, X_validation, y_validation, **settings):
    history, final = [], None
    for checkpoint in train_epochs(X, y, X_validation, y_validation, **settings):
        final = checkpoint
        history.append({k: checkpoint[k] for k in ('epoch', 'train', 'validation')})
    return {'w': final['w'], 'b': final['b'], 'history': history}


class Experiment:
    """Small JSON boundary for classroom controls; the functions above are the lab API."""
    def __init__(self, path):
        self.data = load_data(path)
        self.models = {}
        self.serial = 0

    def initialize(self):
        d = self.data
        gallery = []
        for label in (0, 1):
            ids = d['train'][d['labels'][d['train']] == label][:6]
            gallery.extend({'id': int(i), 'label': int(label),
                            'pixels': d['images'][i].ravel().tolist()} for i in ids)
        return {'counts': {s: len(d[s]) for s in ('train', 'validation', 'test')},
                'gallery': gallery, 'shape': [28, 28]}

    def preview(self, sample=0, kind='raw', amount=1, **_):
        d = self.data
        sample = int(sample)
        x = d['images'][sample]
        out = transform(x, kind, amount)
        return {'pixels': out.ravel().tolist(), 'original': x.ravel().tolist(),
                'label': int(d['labels'][sample]), 'minimum': float(out.min()),
                'maximum': float(out.max()), 'mean': float(out.mean())}

    def score(self, sample=0, weight=1.0, bias=0.0, **_):
        d = self.data
        x = d['images'][int(sample)].ravel()
        train_ids = d['train']
        images = d['images'][train_ids]
        labels = d['labels'][train_ids]
        w = (images[labels == 1].mean(0) - images[labels == 0].mean(0)).ravel()
        w *= float(weight)
        contribution = w * x
        z = float(contribution.sum() + float(bias))
        return {'pixels': x.tolist(), 'weights': w.tolist(),
                'contributions': contribution.tolist(), 'score': z,
                'probability': float(sigmoid(z)), 'label': int(d['labels'][int(sample)])}

    def update(self, sample=0, lr=.1, **_):
        d = self.data
        X = d['images'][int(sample)].reshape(1, -1)
        y = d['labels'][[int(sample)]]
        w, b = np.zeros(X.shape[1]), 0.0
        dw, db = gradient(w, b, X, y)
        (w1, b1), trace = trace_step(w, b, X, y, float(lr))
        return {'label': int(y[0]), 'before': .5,
                'after': float(sigmoid(X @ w1 + b1)[0]),
                'lossBefore': loss(w, b, X, y), 'lossAfter': loss(w1, b1, X, y),
                'residual': .5 - float(y[0]), 'gradient': dw.tolist(),
                'weights': w1.tolist(), 'bias': b1, 'biasGradient': db,
                'pixels': X[0].tolist(), 'trace': trace}

    def convolution(self, sample=0, kind='vertical', row=10, col=10):
        kernels = {
            'vertical': [[-1, 0, 1], [-1, 0, 1], [-1, 0, 1]],
            'horizontal': [[-1, -1, -1], [0, 0, 0], [1, 1, 1]],
            'average': np.ones((3, 3)) / 9,
        }
        kernel = np.asarray(kernels[kind], dtype=float)
        row, col = int(row), int(col)
        if not 0 <= row <= 25 or not 0 <= col <= 25:
            raise ValueError('The top-left corner must be between 0 and 25.')
        image = self.data['images'][int(sample)]
        output = convolution_map(image, kernel)
        patch = image[row:row+3, col:col+3]
        return {'image': image.ravel().tolist(), 'kernel': kernel.tolist(),
                'patch': patch.tolist(), 'products': (patch * kernel).tolist(),
                'output': output.ravel().tolist(), 'value': float(output[row, col])}

    def execute(self, code):
        """Run the student's own snippet locally with fresh data copies on each call."""
        d = self.data
        namespace = {
            'np': np, 'sigmoid': sigmoid, 'loss': loss, 'gradient': gradient,
            'step': step, 'train': train, 'metrics': metrics,
            'transform': transform, 'features': features, 'convolution_map': convolution_map,
            'images': d['images'][d['train']].copy(),
            'X_train': features(d['images'][d['train']]),
            'y_train': d['labels'][d['train']].copy(),
            'X_val': features(d['images'][d['validation']]),
            'y_val': d['labels'][d['validation']].copy(),
        }
        output = io.StringIO()
        try:
            with contextlib.redirect_stdout(output):
                exec(compile(code, '<student experiment>', 'exec'), namespace)
            return {'stdout': output.getvalue(), 'error': None}
        except Exception as error:
            return {'stdout': output.getvalue(), 'error': f'{type(error).__name__}: {error}'}

    def fit(self, config, progress=None):
        lr = float(config.get('lr', .1))
        epochs, batch = int(config.get('epochs', 25)), int(config.get('batch', 32))
        if not 0 < lr <= 10 or not 1 <= epochs <= 100 or not 1 <= batch <= 1920:
            raise ValueError('Training settings are outside the classroom range.')
        config = {**config, 'lr': lr, 'epochs': epochs, 'batch': batch,
                  'representation': config.get('representation', 'raw'),
                  'normalize': bool(config.get('normalize', True)),
                  'augment': bool(config.get('augment', False))}
        d = self.data
        images, y = d['images'][d['train']], d['labels'][d['train']]
        if config['augment']:
            images = np.concatenate([images, transform(images, 'shift', 1)])
            y = np.concatenate([y, y])
        X = features(images, config['representation'], config['normalize'])
        Xv = features(d['images'][d['validation']], config['representation'], config['normalize'])
        yv = d['labels'][d['validation']]
        history = []
        for checkpoint in train_epochs(X, y, Xv, yv, lr=lr, epochs=epochs, batch=batch):
            row = {k: checkpoint[k] for k in ('epoch', 'train', 'validation')}
            history.append(row)
            if progress:
                progress(json.dumps(row))
        model = {'w': checkpoint['w'], 'b': checkpoint['b'], 'config': config}
        self.serial += 1
        model_id = str(self.serial)
        self.models[model_id] = model
        if len(self.models) > 8:
            del self.models[next(iter(self.models))]
        p = sigmoid(Xv @ model['w'] + model['b'])
        wrong = np.flatnonzero((p >= .5) != yv)
        wrong = sorted(wrong, key=lambda i: -abs(p[i] - .5))[:8]
        errors = [{'pixels': d['images'][d['validation'][i]].ravel().tolist(),
                   'label': int(yv[i]), 'probability': float(p[i])} for i in wrong]
        return {'id': model_id, 'config': config, 'history': history,
                'weights': model['w'].tolist(), 'bias': model['b'], 'errors': errors,
                'updates': epochs * int(np.ceil(len(y) / batch)), 'trainingSize': len(y)}

    def evaluate(self, model_id, split='validation', shift=0):
        if split not in ('validation', 'test'):
            raise ValueError('Evaluate on validation or test only.')
        model = self.models[str(model_id)]
        d, cfg = self.data, model['config']
        images = transform(d['images'][d[split]], 'shift', int(shift))
        X = features(images, cfg['representation'], cfg['normalize'])
        return {'split': split, 'shift': int(shift),
                **metrics(model['w'], model['b'], X, d['labels'][d[split]])}

    def dispatch(self, action, params):
        if action not in ('initialize', 'preview', 'score', 'update', 'evaluate', 'convolution', 'execute'):
            raise ValueError(f'Unknown action: {action}')
        return json.dumps(getattr(self, action)(**params))
