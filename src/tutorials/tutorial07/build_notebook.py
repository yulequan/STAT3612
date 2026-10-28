#!/usr/bin/env python3
"""Build the editable student notebook from the shared experiment and curriculum."""
import argparse
import ast
import json
from pathlib import Path

import nbformat
from nbclient import NotebookClient

HERE = Path(__file__).resolve().parent
CONTENT = json.loads((HERE / 'curriculum.json').read_text())
SOURCE = (HERE / 'experiment.py').read_text()
FUNCTIONS = {node.name: ast.get_source_segment(SOURCE, node)
             for node in ast.parse(SOURCE).body if isinstance(node, ast.FunctionDef)}


def build(execute=False):
    cells = []

    def md(text):
        cells.append(nbformat.v4.new_markdown_cell(text.strip()))

    def code(text):
        cells.append(nbformat.v4.new_code_cell(text.strip()))

    md(f'''# Tutorial 07 · {CONTENT['title']}

**STAT / SDST 3612 · {CONTENT['subtitle']}**

Tutor: Yinghao Zhu · yhzhu99@connect.hku.hk

{CONTENT['task']}

{CONTENT['motivation']}

## Learning route

{chr(10).join(f"{i + 1}. **{c['title']}** — {c['question']}" for i, c in enumerate(CONTENT['chapters']))}

Follow the chapters in order. Each one connects the idea, a decision-boundary plot,
the Python operation and a small editable experiment. Model settings are chosen on
validation data; the shared test split is evaluated once at the end.

## Learning objectives

{chr(10).join('- ' + item for item in CONTENT['objectives'])}

**Prerequisites:** {CONTENT['prerequisites']}

**Outcome:** {CONTENT['outcome']}

All data are generated locally with scikit-learn and NumPy: two moons, iris petals and
XOR quadrants. Nothing is downloaded. The test rows are deliberately absent from the
setup namespace used by the editable snippets and from all plots below.
''')

    md('''## Setup

Keep `experiment.py` and `curriculum.json` beside this notebook, or extract the
complete student ZIP. Install `requirements.txt` first. The next cell imports the
shared scientific functions and creates the fixed train / validation / test split.
''')
    code('''import json
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
from experiment import (Experiment, metrics, make_teaching_data, build_tree, build_forest,
                        build_boosting, build_svm)

lab = Experiment()
X_train, y_train = lab.moons["X_train"].copy(), lab.moons["y_train"].copy()
X_val, y_val = lab.moons["X_val"].copy(), lab.moons["y_val"].copy()
X_iris_train, y_iris_train = lab.iris["X_train"].copy(), lab.iris["y_train"].copy()
X_iris_val, y_iris_val = lab.iris["X_val"].copy(), lab.iris["y_val"].copy()
X_xor_train, y_xor_train = lab.xor["X_train"].copy(), lab.xor["y_train"].copy()
X_xor_val, y_xor_val = lab.xor["X_val"].copy(), lab.xor["y_val"].copy()
initial = lab.initialize()
compare_models = lab.compare
plt.rcParams.update({"figure.figsize": (7, 4.8), "axes.spines.top": False,
                     "axes.spines.right": False})
BLUE, ORANGE = "#45657e", "#aa613d"

def draw(plot, data, title):
    """Plot a decision surface, train/validation rows and optional support vectors."""
    bounds = plot["bounds"]
    fig, ax = plt.subplots()
    grid = plot.get("grid")
    if grid:
        z = np.asarray(grid["z"])
        ax.contourf(grid["x"], grid["y"], z, levels=np.linspace(-1, 1, 21),
                    cmap="RdBu_r", alpha=.35)
        ax.contour(grid["x"], grid["y"], z, levels=[0], colors="#202e3a", linewidths=1)
    for split, marker, size, alpha in (("train", "o", 18, .55), ("validation", "^", 32, .9)):
        rows = [point for point in plot["points"] if point["split"] == split]
        if rows:
            ax.scatter([p["x"] for p in rows], [p["y"] for p in rows],
                       c=[ORANGE if p["label"] else BLUE for p in rows],
                       marker=marker, s=size, alpha=alpha,
                       edgecolors="white" if split == "validation" else "none",
                       linewidths=.5, label=split)
    for point in plot.get("support", []):
        ax.scatter(point["x"], point["y"], s=95, facecolors="none",
                   edgecolors="#202e3a", linewidths=1.4)
    for line in plot.get("lines", []):
        ax.plot([line["x1"], line["x2"]], [line["y1"], line["y2"]], color="#202e3a",
                linestyle="--" if line.get("dashed") else "-", linewidth=1.4)
    ax.set_xlim(bounds[0], bounds[1])
    ax.set_ylim(bounds[2], bounds[3])
    ax.set_xlabel(data["feature_names"][0])
    ax.set_ylabel(data["feature_names"][1])
    ax.set_title(title)
    ax.set_aspect("equal", adjustable="box")
    ax.legend(loc="best", fontsize=8)
    plt.tight_layout()
    plt.show()
''')

    for i, section in enumerate(CONTENT['chapters']):
        md(f'''## {i + 1}. {section['title']}

### {section['conceptTitle']}

{section['idea']}

{chr(10).join('- ' + point for point in section['points'])}
''')
        if section['equation']:
            md('### Formula and notation\n\n$$' + section['equation'] + '$$\n\n' +
               '\n'.join(f'- ${symbol}$: {meaning}' for symbol, meaning in section['notation']))

        identity = section['id']
        if identity == 'data':
            code('''for name in ("moons", "iris"):
    data = lab.datasets[name]
    draw(lab.data_plot(name), data, data["name"] + " · train + validation")
    print(name, initial["counts"][name])
''')
        elif identity == 'tree':
            code('''tree = build_tree(depth=4).fit(X_train, y_train)
draw(lab.plot_for(tree, lab.moons), lab.moons, "Decision tree · depth 4")
print("train", metrics(y_train, tree.predict(X_train)))
print("validation", metrics(y_val, tree.predict(X_val)))
print("leaves", tree.get_n_leaves(), "actual depth", tree.get_depth())
''')
        elif identity == 'forest':
            code('''row = lab.fit_forest({"mode": "forest", "n_estimators": 100})
draw(row["plot"], lab.moons, "Random forest · 100 trees")
curve = row["curve"]
plt.plot(curve["n"], curve["train"], color=BLUE, label="train")
plt.plot(curve["n"], curve["validation"], color=ORANGE, label="validation")
plt.xlabel("number of trees")
plt.ylabel("accuracy")
plt.title("Random forest: accuracy as trees are added")
plt.legend()
plt.tight_layout()
plt.show()
print("OOB", row["oob"], "validation", row["validation"])
''')
        elif identity == 'boosting':
            code('''for mode, lr in (("adaboost", .5), ("gradient", .1)):
    row = lab.fit_boosting({"mode": mode, "n_estimators": 100, "learning_rate": lr})
    draw(row["plot"], lab.moons, row["name"] + " · 100 trees")
    curve = row["curve"]
    plt.plot(curve["n"], curve["train"], color=BLUE, label="train")
    plt.plot(curve["n"], curve["validation"], color=ORANGE, label="validation")
    plt.xlabel("number of trees")
    plt.ylabel("accuracy")
    plt.title(row["name"] + ": staged validation curve")
    plt.legend()
    plt.tight_layout()
    plt.show()
    print(mode, "best staged tree", row["best_n"], "validation", row["validation"])
''')
        elif identity == 'margins':
            code('''row = lab.fit_margin({"C": 1})
draw(row["plot"], lab.iris, "Linear SVM · C = 1")
print("support vectors", row["support_count"])
print("train", row["train"])
print("validation", row["validation"])
''')
        elif identity == 'kernels':
            code('''for dataset, kernel, gamma in (("moons", "rbf", 1), ("xor", "linear", 1),
                                ("xor", "rbf", 1)):
    row = lab.fit_kernel({"dataset": dataset, "kernel": kernel, "C": 1,
                          "gamma": gamma, "degree": 3})
    draw(row["plot"], lab.datasets[dataset],
         f"{dataset} · {kernel} kernel · validation {row['validation']['accuracy']:.3f}")
    print(dataset, kernel, "support vectors", row["support_count"],
          "validation", row["validation"])
''')
        elif identity == 'compare':
            code('''comparison = lab.compare()
rows = comparison["rows"]
for row in rows:
    print(f"{row['name']:<30} train {row['train']['accuracy']:.3f}  "
          f"validation {row['validation']['accuracy']:.3f}  f1 {row['validation']['f1']:.3f}")
selected = rows[0]
selected_key = selected["params"]["key"]
detail = lab.inspect_candidate({"key": selected_key})
print("Selected on validation:", detail["row"]["name"])
print(detail["metrics"])
draw(detail["plot"], lab.moons, detail["row"]["name"] + " · validation")
''')

        md(f'''### {section['activityTitle']}

{section['experiment']}

### {section['pythonTitle']}

Run the example, change one input or choice, then explain the output.
''')
        code(section['starter'])
        if section['links']:
            md(' · '.join(f'[{title}]({url})' for title, url in section['links']))

    md('''## Freeze a choice and evaluate the test set

Write a model-selection reason using validation evidence: performance, a confusion
matrix or an error pattern, and one limitation. The final test cell remains inactive
while the reason is empty. After it runs, the decision is frozen; restart the notebook
to begin a genuinely new experiment.
''')
    code('''reason = ''  # Write your model and threshold rationale before testing.
if reason.strip():
    final = lab.final_test({"key": selected_key, "reason": reason})
    print(json.dumps(final, indent=2))
else:
    print("Record a rationale above, then run the final test once.")
''')

    md('''## Your experiment record

Report the data split, one decision-boundary plot, validation comparisons for the
tree, forest, boosting and SVM families, one inspected error case, and the final
validation/test result. Explain why the selected model is appropriate and what the
result does not establish.
''')
    code('''record = {"seed": initial["seed"], "counts": initial["counts"],
          "comparison": comparison["rows"], "final": lab.final}
Path("tutorial07-results.json").write_text(json.dumps(record, indent=2))
print("Recorded candidates:", len(record["comparison"]))
''')

    md('''## Appendix: supporting scientific functions

The lesson above uses the public helpers directly. These functions are copied from
`experiment.py` for readers who want to inspect or modify data generation, metrics,
model builders and plotting payloads. They are not prerequisites for following the
lesson.
''')
    code('''import numpy as np
from sklearn.datasets import load_iris, make_moons
from sklearn.ensemble import (AdaBoostClassifier, BaggingClassifier,
                              GradientBoostingClassifier, RandomForestClassifier)
from sklearn.metrics import confusion_matrix
from sklearn.model_selection import train_test_split
from sklearn.svm import SVC
from sklearn.tree import DecisionTreeClassifier, export_text
from experiment import SEED
''')
    for name, function in FUNCTIONS.items():
        md(f'### `{name}`')
        code(function)

    notebook = nbformat.v4.new_notebook(cells=cells, metadata={
        'kernelspec': {'display_name': 'Python 3', 'language': 'python', 'name': 'python3'},
        'language_info': {'name': 'python'},
    })
    for index, cell in enumerate(notebook.cells):
        cell.id = f'tutorial07-{index:03d}'
    if execute:
        NotebookClient(notebook, timeout=600,
                       resources={'metadata': {'path': str(HERE)}}).execute()
        # The final record cell is meant for students' extracted folder, not the source tree.
        (HERE / 'tutorial07-results.json').unlink(missing_ok=True)
    nbformat.write(notebook, HERE / 'tutorial07.ipynb')
    print(f'Built {len(cells)} cells' + (' with executed outputs.' if execute else '.'))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--execute', action='store_true')
    build(parser.parse_args().execute)
