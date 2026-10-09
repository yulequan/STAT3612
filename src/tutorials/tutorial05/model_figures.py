"""Small classifier examples and plots shared with the hands-on notebook."""
import json
import math
from pathlib import Path

import numpy as np

EXAMPLES = json.loads(Path(__file__).with_name('model_examples.json').read_text())


def sigmoid(score):
    return 1 / (1 + math.exp(-score)) if score >= 0 else math.exp(score) / (1 + math.exp(score))


def nb_example(counts=None, alpha=1):
    """Use counts from the lesson's four labelled messages and nine-word vocabulary."""
    if alpha <= 0:
        raise ValueError('Smoothing alpha must be positive.')
    source = EXAMPLES['nb']
    counts = counts if counts is not None else {w['name']: w['initial'] for w in source['words']}
    terms = []
    for word in source['words']:
        feature = float(counts.get(word['name'], 0))
        if feature < 0:
            raise ValueError('Word counts must be nonnegative.')
        if not feature:
            continue
        ham, spam = [(word['counts'][c] + alpha) / (source['totals'][c] + alpha * source['vocabulary']) for c in [0, 1]]
        weight = math.log(spam / ham)
        terms.append(dict(name=word['name'], feature=feature, weight=weight, value=feature * weight, ham=ham, spam=spam))
    bias = math.log(source['priors'][1] / source['priors'][0])
    score = bias + sum(t['value'] for t in terms)
    return dict(bias=bias, score=score, probability=sigmoid(score), priors=source['priors'], contributions=terms)


def lr_example(counts=None):
    """Weights fitted to the six labelled training messages in model_examples.json."""
    source = EXAMPLES['logistic']
    counts = counts if counts is not None else {w['name']: w['initial'] for w in source['words']}
    terms = [dict(name=w['name'], feature=float(counts.get(w['name'], 0)), weight=w['weight'],
                  value=float(counts.get(w['name'], 0)) * w['weight']) for w in source['words'] if counts.get(w['name'], 0)]
    score = source['bias'] + sum(t['value'] for t in terms)
    return dict(bias=source['bias'], score=score, probability=sigmoid(score), contributions=terms)


def knn_example(counts=(1, 0), k=3):
    """Normalize two-word count vectors and rank by their actual cosine distances."""
    source = EXAMPLES['knn']
    if not 1 <= k <= len(source['points']):
        raise ValueError('k must be between 1 and the number of examples.')
    values = np.asarray([p['counts'] for p in source['points']], dtype=float)
    values /= np.linalg.norm(values, axis=1, keepdims=True)
    query = np.asarray(counts, dtype=float)
    if query.shape != (2,) or np.any(query < 0):
        raise ValueError('Supply two nonnegative counts: prize and class.')
    norm = np.linalg.norm(query)
    query = query / norm if norm else query
    # A zero direction supplies no meaningful comparison in the toy illustration.
    distances = 1 - values @ query
    order = sorted(range(len(values)), key=lambda i: (float(distances[i]), i))[:k] if norm else []
    neighbors = [dict(index=i, text=source['points'][i]['text'], label=source['points'][i]['label'],
                      distance=max(0., float(distances[i]))) for i in order]
    return dict(neighbors=neighbors, probability=float(np.mean([n['label'] for n in neighbors])) if neighbors else None,
                points=[dict(x=float(v[0]), y=float(v[1]), **p) for v, p in zip(values, source['points'])],
                query=dict(x=float(query[0]), y=float(query[1])), metric='cosine', zero_vector=not bool(norm))


def lr_flow_values(counts=None, text='Claim your free prize now!'):
    source = EXAMPLES['logistic']
    counts = counts if counts is not None else {w['name']: w['initial'] for w in source['words']}
    state = lr_example(counts)
    return dict(text=text, weights=str([round(w['weight'], 3) for w in source['words']]),
                bias=f'{state["bias"]:.3f}', vector=str([counts.get(w['name'], 0) for w in source['words']]),
                calculation=f'{state["bias"]:.3f}' + ''.join(f' + ({t["feature"]:g} × {t["weight"]:.3f})' for t in state['contributions']),
                score=f'{state["score"]:.3f}', probability=f'{100 * state["probability"]:.1f}',
                hamProbability=f'{100 * (1 - state["probability"]):.1f}',
                prediction='Spam' if state['probability'] > .5 else 'Ham')


def knn_flow_values(counts=(1, 0), k=3, text='Claim your prize now!'):
    source = EXAMPLES['knn']
    all_rows = knn_example(counts, len(source['points']))
    selected = all_rows['neighbors'][:k]
    spam = sum(n['label'] for n in selected)
    return dict(text=text, vector=str(list(counts)),
                direction=str([round(all_rows['query'][axis], 3) for axis in ('x', 'y')]),
                ranking='\n'.join(f'{"✓ " if i < k else "  "}#{i + 1} · {n["distance"]:.3f} · {"Spam" if n["label"] else "Ham"} · {n["text"]}' for i, n in enumerate(all_rows['neighbors'])),
                labels=', '.join('Spam' if n['label'] else 'Ham' for n in selected),
                spam=str(spam), k=str(len(selected)),
                probability=f'{100 * spam / len(selected):.1f}' if selected else '—',
                prediction=('Spam' if spam > len(selected) / 2 else 'Ham') if selected else 'Add a known word first')


def prediction_flow(explanation, kind):
    """Put the fitted result in feature → learned model → prediction order."""
    terms = evidence_terms(explanation) if kind != 'knn' else []
    features = ', '.join(f'{t["name"]}: {t.get("feature", t["value"]):.3f}' for t in terms[:6])
    neighbors = explanation.get('neighbors', [])
    votes = ', '.join('Spam' if n['label'] else 'Ham' for n in neighbors)
    p = explanation['probability']
    mechanism = {'nb': 'Class priors × word likelihoods, then normalize',
                 'logistic': 'Learned weights → score → sigmoid', 'knn': 'Uniform neighbour vote'}[kind]
    return dict(title='Predict a new message with the trained model', layout='vertical', stages=[
        dict(title='1 · Reuse the fitted feature transformation', nodes=[dict(label='Message → same feature columns',
             code=explanation['text'], text=features + (', …' if len(terms) > 6 else '') if kind != 'knn' else 'Use the fitted training vocabulary and IDF.')]),
        dict(title='2 · Apply what the model learned from training', nodes=[dict(label=mechanism,
             code=f'Labels: {votes}\nSpam votes / k = {sum(n["label"] for n in neighbors)} / {len(neighbors)}' if kind == 'knn' else 'model.predict_proba([message])', text='')]),
        dict(title='3 · Choose the class with the larger probability', nodes=[dict(label='Model prediction: ' + ('Spam' if explanation['prediction'] else 'Ham'),
             code=f'Ham: {100 * (1 - p):.1f}%\nSpam: {100 * p:.1f}%', text='This is the model’s default decision.')])], caption='')


def evidence_terms(explanation):
    if 'evidence' in explanation:
        return [dict(name=t['word'], value=t['contribution'], feature=t['value'],
                     weight=math.log(t['spam'] / t['ham'])) for t in explanation['evidence']]
    return explanation['contributions']


def plot_evidence(explanation, kind='nb', title=None):
    """A waterfall preserves the sum of every feature, even when the tail is grouped."""
    import matplotlib.pyplot as plt
    terms = evidence_terms(explanation)
    if len(terms) > 9:
        terms = terms[:8] + [dict(name=f'Other {len(terms) - 8} features', value=sum(t['value'] for t in terms[8:]))]
    names = ['Class prior' if kind == 'nb' else 'Intercept'] + [t['name'] for t in terms]
    values = [explanation['bias']] + [t['value'] for t in terms]
    ends = np.cumsum(values)
    starts = np.r_[0., ends[:-1]]
    fig, axes = plt.subplots(1, 2, figsize=(11, max(3.5, len(names) * .42)), gridspec_kw={'width_ratios': [3, 1]})
    ax = axes[0]
    for i, (start, end, value) in enumerate(zip(starts, ends, values)):
        color = '#84929c' if i == 0 else '#aa613d' if value > 0 else '#45657e'
        ax.barh(i, abs(value), left=min(start, end), height=.6, color=color)
        ax.plot([end, end], [i - .32, i + .32], color='#202e3a', lw=1.5)
        ax.annotate(f'{value:+.3f}', (end, i), xytext=(5 if value >= 0 else -5, 0),
                    textcoords='offset points', ha='left' if value >= 0 else 'right', va='center', fontsize=9)
        if i:
            ax.plot([start, start], [i - 1 + .32, i - .32], color='#aebfc9', ls=':', lw=1)
    ax.axvline(0, color='#87949d', ls='--', lw=.8)
    ax.set_yticks(range(len(names)), names, fontfamily='monospace')
    ax.invert_yaxis()
    low, high = min(0., float(ends.min())), max(0., float(ends.max()))
    pad = max(.7, (high - low) * .2)
    ax.set_xlim(low - pad, high + pad)
    ax.set(xlabel='← evidence for ham     cumulative score     evidence for spam →', title='Start, then add each contribution')
    p = explanation['probability']
    axes[1].barh(['Ham', 'Spam'], [1 - p, p], color=['#45657e', '#aa613d'])
    axes[1].set(xlim=(0, 1), xlabel='Model estimate', title=f'Final score: {explanation["score"]:.3f}')
    axes[1].axvline(.5, color='#87949d', ls='--', lw=.8)
    for i, value in enumerate([1 - p, p]):
        axes[1].text(.02, i, f'{value:.1%}', va='center', color='white' if value > .25 else '#202e3a')
    fig.suptitle(title or EXAMPLES['nb' if kind == 'nb' else 'logistic']['title'])
    fig.tight_layout()
    plt.show()


def plot_neighbors(explanation, title=None):
    import matplotlib.pyplot as plt
    neighbors = explanation['neighbors']
    toy = 'points' in explanation
    height = 4 if toy else max(4, len(neighbors) * .32)
    fig, axes = plt.subplots(1, 2, figsize=(9 if toy else 10, height), gridspec_kw={'width_ratios': [2 if toy else 3, 1]})
    ax = axes[0]
    if 'points' in explanation:
        selected = {n['index'] for n in neighbors}
        labelled = set()
        for i, p in enumerate(explanation['points']):
            ax.scatter(p['x'], p['y'], s=80, c='#aa613d' if p['label'] else '#45657e',
                       alpha=1 if i in selected else .25, edgecolors='#202e3a' if i in selected else 'none',
                       label=('Spam' if p['label'] else 'Ham') if p['label'] not in labelled else None)
            labelled.add(p['label'])
        query = explanation['query']
        ax.scatter(query['x'], query['y'], marker='^', c='#202e3a', s=120, label='New message')
        ax.set(xlabel='prize weight', ylabel='class weight', xlim=(-.05, 1.05), ylim=(-.05, 1.05),
               title='Toy directions: circled points vote')
        ax.set_aspect('equal', adjustable='box')
        ax.legend(loc='upper right', fontsize=8)
    else:
        for i, n in enumerate(neighbors):
            ax.plot([0, n['distance']], [i, i], c='#e1e7eb')
            ax.scatter(n['distance'], i, s=70, c='#aa613d' if n['label'] else '#45657e')
        ax.set_yticks(range(len(neighbors)), [f'#{i + 1}' for i in range(len(neighbors))])
        ax.invert_yaxis()
        ax.set(xlabel=explanation.get('metric', 'cosine') + ' distance (smaller = nearer)', title='Fitted neighbour distances')
        if explanation.get('zero_vector'):
            ax.set_title('No known words: tied distances give little evidence')
    if neighbors:
        spam = sum(n['label'] for n in neighbors)
        axes[1].bar(['Ham', 'Spam'], [len(neighbors) - spam, spam], color=['#45657e', '#aa613d'])
        axes[1].set(ylabel='Votes', title=f'{spam} / {len(neighbors)} = {explanation["probability"]:.1%} spam')
    else:
        axes[1].text(.5, .5, 'Add a known word\nto compare directions.', ha='center', va='center')
        axes[1].axis('off')
    fig.suptitle(title or EXAMPLES['knn']['title'])
    fig.tight_layout()
    plt.show()
