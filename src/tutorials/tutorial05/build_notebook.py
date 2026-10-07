#!/usr/bin/env python3
"""Build the complete notebook from the web curriculum and shared Python source."""
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
        cells.append(nbformat.v4.new_code_cell(text))
    md('# Tutorial05 · Spam Email Classification\n\n' + CONTENT['subtitle'] +
       '\n\n**Tutor:** Yinghao Zhu · yhzhu99@connect.hku.hk\n\n' + CONTENT['task'] + '\n\n' + CONTENT['motivation'])
    md('## Learning route\n\n' + '\n'.join(f'{i + 1}. **{c["title"]}** — {c["question"]}' for i, c in enumerate(CONTENT['chapters'])) +
       '\n\n## Learning objectives\n\n' + '\n'.join('- ' + s for s in CONTENT['objectives']) +
       '\n\n**Prerequisites:** ' + CONTENT['prerequisites'] + '\n\n**Outcome:** ' + CONTENT['outcome'] +
       """

Each section explains the mechanism, plots or inspects an actual computation, then runs an editable experiment. All sections form the classroom lesson.""")
    md('## Data source and setup\n\n' + (HERE / 'data/README.md').read_text() +
       """

Extract the complete student package. Keep `experiment.py` beside this notebook and retain `data/`. Install `requirements.txt`, then run cells in order. The original file is bundled locally; no dataset download or NLTK resources are required.""")
    code("""import json
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import experiment as science
from experiment import (Experiment, SEED, FEATURES, TOKEN_PATTERN, tokens, numerical_features,
                        load_data, rule_predict, decision_metrics, metrics, build_model, cross_validate,
                        CountVectorizer, TfidfVectorizer, Pipeline, FunctionTransformer,
                        StandardScaler, SplineTransformer, LogisticRegression,
                        LinearDiscriminantAnalysis, KNeighborsClassifier,
                        StratifiedKFold, train_test_split, average_precision_score,
                        confusion_matrix, log_loss, roc_auc_score)
import csv
import re

lab = Experiment("data/SMSSpamCollection.txt")
X_train, y_train = lab.X_train.copy(), lab.y_train.copy()
X_val, y_val = lab.X_val.copy(), lab.y_val.copy()
initial = lab.initialize()
print("Original / excluded / duplicate / retained:", initial["raw"], initial["excluded"], initial["duplicates"], initial["unique"])
print("Splits:", initial["counts"])
print("First lines of the raw file:")
for line in initial["preview"][:4]:
    print("  ", line.replace("\\t", " ⇥ "))
plt.rcParams.update({"figure.figsize": (9, 4), "axes.spines.top": False, "axes.spines.right": False})
HAM, SPAM = "#45657e", "#aa613d\"""")
    seen = set()
    for i, section in enumerate(CONTENT['chapters']):
        identity = section['id']
        md(f'## {i + 1}. {section["title"]}\n\n**{section["question"]}**\n\n' +
           f'**Key idea:** {section["idea"]}\n\n' +
           '\n'.join('- ' + point for point in section['points']) + '\n\n$$' + section['equation'] + '$$\n\n' +
           '\n'.join(f'- ${symbol}$: {meaning}' for symbol, meaning in section['notation']) +
           '\n\n**Try it**\n\n' + '\n'.join(f'{j + 1}. {s}' for j, s in enumerate(section['steps'])))
        for function in section['functions']:
            if function not in seen:
                md(f'### Inspect the implementation: `{function}`\n\nThis cell is copied from `experiment.py`. Subsequent direct experiments use this editable function. The assignment also updates the shared lab implementation for later fits.')
                code(FUNCTIONS[function] + f'\n\nscience.{function} = {function}')
                seen.add(function)
        if identity == 'inbox':
            code("""rule_result = lab.rules({"keywords": "free win prize", "text": "Are you free after class?"})
print("Constructed normal message →", "spam" if rule_result["custom"] else "ham")
print("Validation metrics:", rule_result["metrics"])
for item in rule_result["errors"][:6]:
    print("True", item["label"], "predicted", item["prediction"], item["text"])""")
        elif identity == 'data':
            code("""names = list(initial["counts"])
ham = [initial["counts"][name]["ham"] for name in names]
spam = [initial["counts"][name]["spam"] for name in names]
plt.bar(names, ham, label="Ham", color=HAM)
plt.bar(names, spam, bottom=ham, label="Spam", color=SPAM)
plt.ylabel("Messages")
plt.title("Stratified splits after deduplication")
plt.legend()
plt.show()
for item in initial["examples"][:4]:
    print(item["label"], item["text"])""")
        elif identity == 'features':
            code("""fig, axes = plt.subplots(1, 2, figsize=(12, 4))
for j, ax in enumerate(axes):
    d = initial["distributions"][j]
    width = np.diff(d["edges"])[0]
    centers = np.asarray(d["edges"][:-1])
    for label, color in [(0, HAM), (1, SPAM)]:
        ax.bar(centers + label * width * .4, d["groups"][label], width=width * .4, color=color, label="Ham" if label == 0 else "Spam")
    ax.set(xlabel=d["name"] + " (last bin includes tail)", ylabel="Within-class proportion")
    ax.legend()
plt.tight_layout()
plt.show()
numeric_run = lab.fit({"representation": "numeric"})
print("Numerical logistic validation:", numeric_run["validation"])""")
        elif identity == 'text':
            code("""toy = ["free prize now", "are you free after class", "win a prize prize"]
for representation in ["count", "tfidf"]:
    result = lab.vectorize({"documents": toy, "text": "free meeting tomorrow", "representation": representation})
    fig, ax = plt.subplots()
    matrix = np.vstack([result["matrix"], result["transformed"]])
    image = ax.imshow(matrix, cmap="Blues", aspect="auto")
    ax.set_xticks(range(len(result["vocabulary"])), result["vocabulary"], rotation=45, ha="right")
    ax.set_yticks(range(4), ["Train 1", "Train 2", "Train 3", "New message"])
    for (row, col), value in np.ndenumerate(matrix):
        ax.text(col, row, f"{value:.2f}", ha="center", va="center", color="white" if value > matrix.max() / 2 else "black")
    ax.set_title(representation + " · same vocabulary for new messages")
    fig.colorbar(image, ax=ax)
    plt.tight_layout()
    plt.show()
    print("Ignored words:", result["unknown"])""")
        elif identity == 'logistic':
            code("""count_run = lab.fit({"representation": "count", "C": 1})
tfidf_run = lab.fit({"representation": "tfidf", "C": 1})
explanation = lab.explain({"id": count_run["id"], "text": "Congratulations! Claim your free prize now!"})
items = explanation["contributions"][:14]
plt.barh([item["name"] for item in items], [item["value"] for item in items], color=[SPAM if item["value"] > 0 else HAM for item in items])
plt.axvline(0, color="grey", linewidth=1)
plt.xlabel("Message-specific contribution to linear score")
plt.title("Largest contributions; total uses all features and intercept")
plt.tight_layout()
plt.show()
print("Intercept / score / probability:", explanation["bias"], explanation["score"], explanation["probability"])""")
        elif identity == 'regularization':
            code("""sweep = lab.regularization({"representation": "count"})
Cs = [row["C"] for row in sweep["rows"]]
fig, axes = plt.subplots(1, 3, figsize=(15, 4))
for split, color in [("train", HAM), ("validation", SPAM)]:
    axes[0].semilogx(Cs, [row[split]["average_precision"] for row in sweep["rows"]], "o-", label=split, color=color)
axes[0].set(xlabel="C (smaller = stronger penalty)", ylabel="Average precision", ylim=(0, 1))
axes[0].legend()
axes[1].semilogx(Cs, sweep["weights"], "o-", color=HAM)
axes[1].set(xlabel="C", ylabel="L2 coefficient norm")
for path in sweep["paths"]:
    axes[2].semilogx(Cs, path["weights"], "o-", label=path["word"])
axes[2].set(xlabel="C", ylabel="Word weight", title="Largest weights at C = 10")
axes[2].legend(fontsize=8)
plt.tight_layout()
plt.show()""")
        elif identity == 'validation':
            code("""cv_result = lab.cv({"representation": "count"})
for row in cv_result["rows"]:
    print("C:", row["C"], "fold AP:", np.round(row["folds"], 3), "mean ± SD:", round(row["mean"], 3), round(row["std"], 3))
means = [row["mean"] for row in cv_result["rows"]]
std = [row["std"] for row in cv_result["rows"]]
plt.errorbar([row["C"] for row in cv_result["rows"]], means, yerr=std, fmt="o-", color=HAM)
plt.xscale("log")
plt.xlabel("C")
plt.ylabel("Held-out fold AP (mean ± SD, not a confidence interval)")
plt.title("Training-only CV; transformations refitted in each fold")
plt.show()
print("Selected C:", cv_result["best"])
print("Fold vocabulary sizes:", cv_result["rows"][0]["vocabulary_sizes"])
print("Held-out words absent from retained fold vocabulary:", cv_result["fold_unknown"])""")
        elif identity == 'lda':
            code("""lda_result = lab.lda({})
fig, ax = plt.subplots()
for label, color in [(0, HAM), (1, SPAM)]:
    points = np.asarray([[p["x"], p["y"]] for p in lda_result["points"] if p["label"] == label])
    ax.scatter(points[:, 0], points[:, 1], s=12, alpha=.35, color=color, label="Ham" if label == 0 else "Spam")
    ellipse = np.asarray(lda_result["ellipses"][label])
    ax.plot(ellipse[:, 0], ellipse[:, 1], color=color)
wx, wy = lda_result["boundary"]["w"]
b = lda_result["boundary"]["b"]
x = np.linspace(-3, 6, 50)
if abs(wy) > 1e-9:
    ax.plot(x, -(wx * x + b) / wy, "--", color="grey", label="Two-feature marginal rule")
ax.set(xlabel="Standardized log(1 + characters)", ylabel="Standardized log(1 + digits)", xlim=(-3, 6), ylim=(-2, 6), title="LDA: marginal distributions; metrics use all five features")
ax.legend()
plt.show()
print("LDA validation:", lda_result["run"]["validation"])
print("Numerical logistic comparison:", numeric_run["validation"])""")
        elif identity == 'gam':
            code("""gam_result = lab.gam({"C": 1})
fig, axes = plt.subplots(2, 3, figsize=(13, 7))
for curve, ax in zip(gam_result["curves"], axes.flat):
    ax.plot(curve["x"], curve["effect"], color=HAM)
    ax.axhline(0, color="grey", linewidth=.7)
    ax.set(xlabel=curve["name"], ylabel="Log-odds change from median")
axes.flat[-1].axis("off")
fig.suptitle("Additive model effects; other features at training medians")
plt.tight_layout()
plt.show()
print("Reference values:", gam_result["reference"])
print("Additive model validation:", gam_result["run"]["validation"])""")
        elif identity == 'neighbors':
            code("""knn_run = lab.fit({"kind": "knn", "representation": "tfidf", "k": 5})
neighbours = lab.explain({"id": knn_run["id"], "text": "Claim your free prize now"})
for item in neighbours["neighbors"]:
    print("Distance:", round(item["distance"], 3), "label:", item["label"], "text:", item["text"])
print("Spam vote:", neighbours["probability"])
print("KNN validation:", knn_run["validation"])""")
        elif identity == 'decision':
            code("""print("Candidate comparisons on validation; threshold metrics here use 0.5")
for item in lab.runs.values():
    row = item["row"]
    print(row["id"], row["kind"], row["representation"], "C", row["C"], "k", row["k"], "AP", round(row["validation"]["average_precision"], 3), "precision", round(row["validation"]["precision"], 3), "recall", round(row["validation"]["recall"], 3))

# Edit using validation evidence before executing the final test cell.
selected_id = cv_result["run"]["id"]
threshold = .5
validation_result = lab.evaluate({"id": selected_id, "threshold": threshold})
print("Selected validation metrics:", validation_result["metrics"])
fig, axes = plt.subplots(1, 3, figsize=(14, 4))
cm = np.asarray(validation_result["metrics"]["confusion"])
axes[0].imshow(cm, cmap="Blues")
for (r, c), value in np.ndenumerate(cm):
    axes[0].text(c, r, str(value), ha="center", va="center", color="white" if value > cm.max()/2 else "black")
axes[0].set(xticks=[0, 1], yticks=[0, 1], xticklabels=["Ham", "Spam"], yticklabels=["Ham", "Spam"], xlabel="Predicted", ylabel="Actual", title="Validation confusion matrix")
pr, roc = np.asarray(validation_result["pr"]), np.asarray(validation_result["roc"])
axes[1].plot(pr[:, 0], pr[:, 1], color=HAM)
axes[1].axhline(validation_result["prevalence"], ls="--", color="grey", label="Constant-score reference")
axes[1].scatter(validation_result["metrics"]["recall"], validation_result["metrics"]["precision"], color=SPAM)
axes[1].set(xlabel="Recall", ylabel="Precision", title="PR curve", xlim=(0,1), ylim=(0,1))
axes[1].legend()
axes[2].plot(roc[:, 0], roc[:, 1], color=HAM)
axes[2].plot([0,1], [0,1], "--", color="grey")
axes[2].set(xlabel="False positive rate", ylabel="Recall", title="ROC curve", xlim=(0,1), ylim=(0,1))
plt.tight_layout()
plt.show()
for item in validation_result["errors"][:8]:
    print("True", item["label"], "predicted", item["prediction"], "p", round(item["probability"], 3), item["text"])""")
        md('### Run and explain\n\n' + section['experiment'])
        code(section['starter'])
        md('**Takeaway:** ' + section['takeaway'])
    md("""## Freeze the decision and evaluate the test set

Write your own rationale using validation evidence, the inbox error tradeoff and a data limitation. This cell runs only when the rationale is nonempty. The lab freezes the selected model and threshold after testing. Restarting a kernel does not make a repeatedly inspected test set unseen again.""")
    code("""reason = ''  # Write your model and threshold rationale before testing.
if reason.strip():
    final_result = lab.final_test({'id': selected_id, 'threshold': threshold, 'reason': reason})
    print(json.dumps(final_result, indent=2))
else:
    print('Record a rationale above, then run the final test once.')""")
    md("""## Experiment record

Report the baseline, representation/model comparisons, CV result, threshold decision, representative errors and limits of generalizing from historical English SMS to modern email. A higher score alone is not an explanation.""")
    code("""record = {'dataset': 'Original UCI SMS Spam Collection', 'seed': SEED, 'splits': initial['counts'],
          'runs': [{k: v for k, v in item['row'].items() if k not in ('thresholds',)} for item in lab.runs.values()],
          'cv': cv_result['rows'], 'final': lab.final}
Path('tutorial05-results.json').write_text(json.dumps(record, indent=2))
print('Saved tutorial05-results.json')""")
    nb = nbformat.v4.new_notebook(cells=cells, metadata={'kernelspec': {'display_name': 'Python 3', 'language': 'python', 'name': 'python3'}, 'language_info': {'name': 'python'}})
    if execute:
        NotebookClient(nb, timeout=600, resources={'metadata': {'path': str(HERE)}}).execute()
    nbformat.write(nb, HERE / 'tutorial05.ipynb')
    # The result file belongs to students, not to the source tree.
    (HERE / 'tutorial05-results.json').unlink(missing_ok=True)
    print(f'Built {len(cells)} cells' + (' with executed outputs.' if execute else '.'))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--execute', action='store_true')
    build(parser.parse_args().execute)
