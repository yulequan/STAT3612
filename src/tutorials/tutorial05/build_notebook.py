#!/usr/bin/env python3
"""Build the complete dataset-first lesson from the shared web curriculum."""
import argparse
import ast
import json
from pathlib import Path

import nbformat
from nbclient import NotebookClient

HERE = Path(__file__).resolve().parent
CONTENT = json.loads((HERE / 'curriculum.json').read_text())
SOURCE = (HERE / 'experiment.py').read_text()
FUNCTIONS = {node.name: ast.get_source_segment(SOURCE, node) for node in ast.parse(SOURCE).body
             if isinstance(node, ast.FunctionDef)}


def build(execute=False):
    cells = []

    def md(text):
        cells.append(nbformat.v4.new_markdown_cell(text))

    def code(text):
        cells.append(nbformat.v4.new_code_cell(text.strip()))

    def focus(section):
        if section['focus']:
            lines = section['starter'].splitlines()
            excerpt = '\n'.join(line for start, end in section['focus']['ranges'] for line in lines[start:end])
            md('### ' + section['focus']['title'] + '\n\n```python\n' + excerpt + '\n```')

    md('# Tutorial05 · ' + CONTENT['title'] + '\n\n' + CONTENT['subtitle'] +
       '\n\n**Tutor:** Yinghao Zhu · yhzhu99@connect.hku.hk\n\n' + CONTENT['task'] + '\n\n' + CONTENT['motivation'])
    dataset = CONTENT['dataset']
    md('## ' + dataset['title'] + '\n\nSource: [UCI SMS Spam Collection](' + dataset['source'] + ') · [Download original ZIP](' + dataset['archive'] + ') · Local file: `data/SMSSpamCollection.txt`\n\n' + dataset['description'] + '\n\nRaw data: 5,574 SMS; 4,827 ham and 747 spam. No header.\n\n```text\n' + '\n'.join(row['label'] + '\t' + row['text'] for row in dataset['preview']) + '\n```\n\n' + dataset['limitations'])
    md('## Learning route\n\n' + '\n'.join(
        f'{i + 1}. **{c["title"]}**' + ' — ' + c['question']
        for i, c in enumerate(CONTENT['chapters'])) +
       '\n\nFollow every chapter in order. Each model has training, validation selection and a shared final test stage. '
       'Each chapter explains its inputs and uses the setup below.\n\n' +
       '## Learning objectives\n\n' + '\n'.join('- ' + s for s in CONTENT['objectives']) +
       '\n\n**Prerequisites:** ' + CONTENT['prerequisites'] + '\n\n**Outcome:** ' + CONTENT['outcome'])
    md('## Setup\n\nExtract the complete student package and keep all supporting files beside the notebook, including `experiment.py`, `model_figures.py`, `model_examples.json` and `data/`. '
       'Install `requirements.txt`. NLTK’s Treebank tokenizer needs no resource downloads.\n\n'
       'Setup supplies training and validation arrays. Test messages remain reserved for the final cell. '
       'Data provenance is in `data/README.md`; the next section shows the data split. '
       'The examples import NLTK and sklearn tools explicitly.')
    code('''import json
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
from experiment import Experiment, tokens, numerical_features, metrics, explain_model
from diagrams import draw_flow
from model_figures import nb_example, lr_example, knn_example, plot_evidence, plot_neighbors, lr_flow_values, knn_flow_values, prediction_flow

dataset_path = "data/SMSSpamCollection.txt"
lab = Experiment(dataset_path)
X_train, y_train = lab.X_train.copy(), lab.y_train.copy()
X_val, y_val = lab.X_val.copy(), lab.y_val.copy()
initial = lab.initialize()
curriculum = json.loads(Path("curriculum.json").read_text())
model_examples = json.loads(Path("model_examples.json").read_text())
plt.rcParams.update({"figure.figsize": (9, 4), "axes.spines.top": False, "axes.spines.right": False})
HAM, SPAM = "#45657e", "#aa613d"
''')
    for i, section in enumerate(CONTENT['chapters']):
        identity = section['id']
        md(f'## {i + 1}. {section["title"]}\n\n' +
           '### ' + section['conceptTitle'] + '\n\n' + section['idea'] + '\n\n' +
           '\n'.join('- ' + point for point in section['points']))
        if section['equation']:
            md('### Formula and notation\n\n$$' + section['equation'] + '$$\n\n' + '\n'.join(f'- ${symbol}$: {meaning}' for symbol, meaning in section['notation']))
        if 'workflow' in section:
            code(f'draw_flow(curriculum["chapters"][{i}]["workflow"], initial)')
        if identity == 'tokenize':
            focus(section)
        if section['flow'] and identity not in ('tfidf', 'naive'):
            code(f'draw_flow(curriculum["chapters"][{i}]["flow"], initial)')
        for item in section['worked']:
            text = '### ' + item['title'] + '\n\n' + '\n\n'.join(item['text'])
            if item['columns']:
                text += '\n\n| ' + ' | '.join(column.replace('|', r'\|') for column in item['columns']) + ' |\n| ' + ' | '.join('---' for _ in item['columns']) + ' |\n'
                text += '\n'.join('| ' + ' | '.join(str(v).replace('|', r'\|') for v in row) + ' |' for row in item['rows'])
            md(text)
        if section['flow'] and identity in ('tfidf', 'naive'):
            code(f'draw_flow(curriculum["chapters"][{i}]["flow"], initial)')
        if identity != 'tokenize':
            focus(section)
        if identity in ('naive', 'logistic', 'neighbors'):
            kind = {'naive': 'nb', 'logistic': 'logistic', 'neighbors': 'knn'}[identity]
            examples = json.loads((HERE / 'model_examples.json').read_text())
            if kind != 'nb':
                rows = examples[kind]['training' if kind == 'logistic' else 'points']
                words = [w['name'] for w in examples[kind]['words']] if kind == 'logistic' else examples[kind]['words']
                md('### Training messages → word-count vectors\n\nColumn order: `' + str(words) + '`\n\n'
                   '| Row | Label | Message | Vector |\n| --- | --- | --- | --- |\n' + '\n'.join(
                       f'| {index + 1} | {"Spam" if r["label"] else "Ham"} | `{r["text"]}` | `{r["counts"]}` |' for index, r in enumerate(rows)))
                md('### ' + examples[kind]['title'] + '\n\n' + examples[kind]['caption'] + '\n\n' + examples[kind]['challenge'])
                code('draw_flow(model_examples["logistic"]["flow"], lr_flow_values(**model_examples["logistic"]["queries"][0]))' if kind == 'logistic' else
                     'draw_flow(model_examples["knn"]["flow"], knn_flow_values(k=3, **model_examples["knn"]["queries"][0]))')
            md('### Inspect contribution or distance details\n\n' +
               (examples[kind]['caption'] + '\n\n' if kind == 'nb' else '') +
               '\n\n' + examples[kind]['challenge'] + ' Change the values in this cell and rerun to redraw the figure.')
            if kind == 'nb':
                code('plot_evidence(nb_example(alpha=1), kind="nb")')
            elif kind == 'logistic':
                code('plot_evidence(lr_example(model_examples["logistic"]["queries"][0]["counts"]), kind="logistic")')
            else:
                code('plot_neighbors(knn_example(counts=(1, 0), k=3))  # Counts: prize, call')
        if section['links']:
            md(' · '.join(f'[{title}]({url})' for title, url in section['links']))
        md('### ' + section['activityTitle'] + '\n\n' + section['experiment'] +
           '\n\n### ' + section['pythonTitle'] + '\n\nRun the example, change one input or choice, then explain the output.')
        code(section['starter'])
        if identity in ('naive', 'logistic', 'neighbors'):
            kind = 'nb' if identity == 'naive' else 'logistic' if identity == 'logistic' else 'knn'
            md('### Inspect the trained model on one message\n\nThe same visual explanation now uses the fitted pipeline above. Change the message and rerun; the model stays fixed.')
            code('explanation = explain_model(model, X_val[482], X_train, y_train)\n' +
                 f'draw_flow(prediction_flow(explanation, "{kind}"))')
            md('### Inspect the fitted contributions or distances')
            code(
                 ('plot_neighbors(explanation, title="KNN: neighbours for this message")' if kind == 'knn' else
                  f'plot_evidence(explanation, kind="{kind}", title="{examples[kind]["title"].split(":")[0]}: evidence for this message")'))
        if identity == 'text':
            code('''fig, ax = plt.subplots()
matrix = X.toarray()
ax.imshow(matrix, cmap="Blues", aspect="auto")
ax.set_xticks(range(matrix.shape[1]), vectorizer.get_feature_names_out())
ax.set_yticks([0, 1], ["Real SMS A", "Real SMS B"])
for (row, col), value in np.ndenumerate(matrix):
    ax.text(col, row, str(value), ha="center", va="center", color="white" if value == 2 else "black")
ax.set_title("Bag of Words: one row per message, one column per word")
plt.tight_layout()
plt.show()''')
        elif identity == 'tfidf':
            code('''fig, axes = plt.subplots(1, 2, figsize=(12, 4))
names = raw.get_feature_names_out()
axes[0].bar(names, weighted[0], color=HAM)
axes[0].set(title="Document 1: TF × IDF", ylabel="Unnormalized weight")
axes[1].bar(names, normalized[0], color=SPAM)
axes[1].set(title="Document 1: after L2 normalization", ylabel="Normalized value")
for ax in axes:
    ax.tick_params(axis="x", rotation=45)
plt.tight_layout()
plt.show()''')
        elif identity == 'regularization':
            code('''path_result = lab.regularization({"representation": "tfidf"})
Cs = [row["C"] for row in path_result["rows"]]
fig, axes = plt.subplots(1, 2, figsize=(12, 4))
for split, color in [("train", HAM), ("validation", SPAM)]:
    axes[0].semilogx(Cs, [row[split]["average_precision"] for row in path_result["rows"]], "o-", label=split, color=color)
axes[0].set(xlabel="C (smaller = stronger penalty)", ylabel="Average precision")
axes[0].legend()
for item in path_result["paths"]:
    axes[1].semilogx(Cs, item["weights"], label=item["word"])
axes[1].set(xlabel="C", ylabel="Word weight")
axes[1].legend(fontsize=8)
plt.tight_layout()
plt.show()''')
        elif identity == 'validation':
            code('''means = search.cv_results_["mean_test_score"]
std = search.cv_results_["std_test_score"]
Cs = [p["classifier__C"] for p in search.cv_results_["params"]]
plt.errorbar(Cs, means, yerr=std, fmt="o-", color=HAM)
plt.xscale("log")
plt.xlabel("C")
plt.ylabel("Held-out fold AP (mean ± SD, not a confidence interval)")
plt.title("The full pipeline is refitted in every training fold")
plt.show()''')
        elif identity == 'features':
            code('''values = numerical_features(X_train)
fig, axes = plt.subplots(1, 2, figsize=(12, 4))
for j, ax in enumerate(axes):
    for label, color in [(0, HAM), (1, SPAM)]:
        ax.hist(values[y_train == label, j], bins=25, density=True, alpha=.5, color=color, label="Ham" if label == 0 else "Spam")
    ax.set(xlabel=["Characters", "Tokens"][j], ylabel="Within-class density")
    ax.legend()
plt.tight_layout()
plt.show()''')
        elif identity == 'lda':
            code('''lda_result = lab.lda({})
fig, ax = plt.subplots()
for label, color in [(0, HAM), (1, SPAM)]:
    points = np.asarray([[p["x"], p["y"]] for p in lda_result["points"] if p["label"] == label])
    ax.scatter(points[:, 0], points[:, 1], s=12, alpha=.35, color=color, label="Ham" if label == 0 else "Spam")
    ellipse = np.asarray(lda_result["ellipses"][label])
    ax.plot(ellipse[:, 0], ellipse[:, 1], color=color)
ax.set(xlabel="Standardized log(1 + characters)", ylabel="Standardized log(1 + digits)", title="LDA: two-feature marginal; classifier uses all five features")
ax.legend()
plt.show()''')
        elif identity == 'gam':
            code('''gam_result = lab.gam({"C": 1})
fig, axes = plt.subplots(2, 3, figsize=(13, 7))
for item, ax in zip(gam_result["curves"], axes.flat):
    ax.plot(item["x"], item["effect"], color=HAM)
    ax.axhline(0, color="grey", linewidth=.7)
    ax.set(xlabel=item["name"], ylabel="Log-odds change from median")
axes.flat[-1].axis("off")
fig.suptitle("Additive effects; other features at training medians")
plt.tight_layout()
plt.show()''')
    md('### Select a candidate and inspect validation errors\n\n'
       'The lab helper keeps candidates for the error plots and final test cell, using the same pipelines shown above. '
       'The same setting grids from the model chapters are registered below, including numerical models and CV-selected LR. '
       'Use one shared validation comparison and do not evaluate every candidate on test. '
       'Choose using validation evidence, then write a reason before testing.')
    code('''# These finite setting grids match the complete training/validation experiments.
configs = ([{"kind": "nb", "representation": r, "alpha": a} for r in ["count", "tfidf"] for a in [.1, 1, 5]]
           + [{"kind": "logistic", "representation": "tfidf", "C": C} for C in [.001, .01, .1, 1, 10]]
           + [{"kind": "knn", "representation": "tfidf", "k": k} for k in [3, 5, 15]]
           + [{"kind": "logistic", "representation": "numeric", "C": C} for C in [.1, 1, 10]]
           + [{"kind": "lda", "representation": "numeric", "shrinkage": a} for a in ["auto", .1, .5]]
           + [{"kind": "gam", "representation": "numeric", "C": C} for C in [.1, 1, 10]]
           + [{"kind": "logistic", "representation": "tfidf", "C": search.best_params_["classifier__C"]}])
core_candidates = [lab.fit(config) for config in configs]
for row in core_candidates:
    print(row["id"], row["kind"], row["representation"], "validation AP:", round(row["validation"]["average_precision"], 3))
selected_id = max(core_candidates, key=lambda row: row["validation"]["average_precision"])["id"]
threshold = .5  # Change only using validation evidence.
validation_result = lab.evaluate({"id": selected_id, "threshold": threshold})
print("Selected validation metrics:", validation_result["metrics"])
for item in validation_result["errors"][:8]:
    print("True", item["label"], "predicted", item["prediction"], "p", round(item["probability"], 3), "|", item["text"])
fig, axes = plt.subplots(1, 2, figsize=(11, 4))
cm = np.asarray(validation_result["metrics"]["confusion"])
axes[0].imshow(cm, cmap="Blues")
for (r, c), value in np.ndenumerate(cm):
    axes[0].text(c, r, str(value), ha="center", va="center", color="white" if value > cm.max() / 2 else "black")
axes[0].set(xticks=[0, 1], yticks=[0, 1], xticklabels=["Ham", "Spam"], yticklabels=["Ham", "Spam"], xlabel="Predicted", ylabel="Actual", title="Validation errors")
pr = np.asarray(validation_result["pr"])
axes[1].plot(pr[:, 0], pr[:, 1], color=HAM)
axes[1].axhline(validation_result["prevalence"], ls="--", color="grey")
axes[1].scatter(validation_result["metrics"]["recall"], validation_result["metrics"]["precision"], color=SPAM)
axes[1].set(xlabel="Recall", ylabel="Precision", xlim=(0, 1), ylim=(0, 1), title="Validation precision–recall curve")
plt.tight_layout()
plt.show()''')
    md('### Freeze the decision and evaluate the test set\n\n'
       'Explain your representation, classifier and threshold using validation evidence. Include the error tradeoff '
       'and a data limitation. This cell runs only when the rationale is nonempty. '
       'After testing, the lab freezes the decision. Restarting Python does not make an inspected test set unseen again.')
    code('''reason = ''  # Write your model and threshold rationale before testing.
if reason.strip():
    final_result = lab.final_test({'id': selected_id, 'threshold': threshold, 'reason': reason})
    print(json.dumps(final_result, indent=2))
else:
    print('Record a rationale above, then run the final test once.')''')
    md('## Your experiment record\n\n'
       'Report the raw-file audit, one preprocessing choice, the representation comparison, the classifier comparison, '
       'training/validation selection for every model, a false positive, a false negative and your final rationale/test result.')
    code('''record = {'dataset': 'Original UCI SMS Spam Collection', 'seed': 3612, 'splits': initial['counts'],
          'runs': [{k: v for k, v in item['row'].items() if k != 'thresholds'} for item in lab.runs.values()],
          'final': lab.final}
print('Recorded candidates:', len(record['runs']))
Path('tutorial05-results.json').write_text(json.dumps(record, indent=2))''')
    md('## Appendix: supporting scientific functions\n\n'
       'The lesson examples above show the NLTK and sklearn calls directly. '
       'These functions are copied from `experiment.py` for readers who want to inspect or modify '
       'data loading, measurements and experiment bookkeeping. They are not prerequisites for following the lesson.')
    code('''import csv
import re
from nltk.tokenize import TreebankWordTokenizer
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (average_precision_score, confusion_matrix, log_loss,
                             precision_recall_curve, roc_auc_score, roc_curve)
from sklearn.model_selection import StratifiedKFold, train_test_split
from sklearn.naive_bayes import MultinomialNB
from sklearn.neighbors import KNeighborsClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import FunctionTransformer, SplineTransformer, StandardScaler
from experiment import SEED, FEATURES
''')
    for name, function in FUNCTIONS.items():
        md(f'### `{name}`')
        code(function)
    nb = nbformat.v4.new_notebook(cells=cells, metadata={
        'kernelspec': {'display_name': 'Python 3', 'language': 'python', 'name': 'python3'},
        'language_info': {'name': 'python'}})
    # Stable cell IDs keep regenerated notebooks reviewable.
    for index, cell in enumerate(nb.cells):
        cell.id = f'tutorial05-{index:03d}'
    if execute:
        NotebookClient(nb, timeout=600, resources={'metadata': {'path': str(HERE)}}).execute()
    nbformat.write(nb, HERE / 'tutorial05.ipynb')
    print(f'Built {len(cells)} cells' + (' with executed outputs.' if execute else '.'))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--execute', action='store_true')
    build(parser.parse_args().execute)
