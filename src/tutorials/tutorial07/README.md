# Tutorial 07 · Trees, Ensembles and Support Vector Machines

**From axis-aligned splits and bagging to maximum-margin classifiers**

Tutor: Yinghao Zhu (yhzhu99@connect.hku.hk)

Start with two teaching datasets: 600 interleaving **two moons** points and 100
**iris petals** from two species. Each has two features and a binary label, so every
decision boundary can be drawn in the plane. The kernel chapter adds a third dataset,
**XOR quadrants**, to contrast linear and RBF boundaries.

## Learning route

1. **Data** — inspect the two moons and iris petals, then reserve train / validation /
   test rows.
2. **A single decision tree** — change depth and minimum leaf size; compare training and
   validation accuracy.
3. **Bagging and random forests** — average bootstrap trees, add feature randomness, and
   read validation and out-of-bag scores.
4. **Boosting** — compare AdaBoost and gradient boosting; tune the learning rate and the
   number of trees with staged validation curves.
5. **Margins** — read support vectors and the soft-margin C parameter on iris petals.
6. **Kernels** — compare linear, polynomial and RBF kernels on two moons and XOR.
7. **Compare, choose, test** — put every candidate on one validation table, inspect
   errors, write a reason, and evaluate one frozen choice on the test split.

The website chapters combine the idea, a decision-boundary experiment, highlighted
Python and an editable snippet. The companion notebook follows the same route with
saved outputs, so it can be read before running.

## Student package

Extract the complete ZIP and keep `experiment.py`, `curriculum.json` and
`tutorial07.ipynb` together. Use Python 3.11+ in a virtual environment:

```sh
python -m pip install -r requirements.txt
python -m jupyter lab
```

Open `tutorial07.ipynb` and choose **Restart Kernel and Run All Cells**. All data are
generated locally with scikit-learn and NumPy; there are no downloads, external files,
GPUs or project files. The notebook uses NumPy, scikit-learn and Matplotlib only.

The notebook's final cell is opt-in. Write a model-selection reason before running it;
the test split is not provided to the browser's editable snippets.

## Data and conventions

- **Two moons:** 600 points, noise 0.30, seed 3612. Stratified split: 360 train /
  120 validation / 120 test.
- **Iris petals:** classes 1 and 2 (versicolor and virginica), features petal length and
  petal width. Stratified split: 60 train / 20 validation / 20 test. Measurements are
  rounded to 0.1 cm, so identical two-feature rows can occur in different splits; these
  are distinct flowers rather than duplicated records.
- **XOR:** 400 standard-normal points split by quadrant. Stratified split: 240 train /
  80 validation / 80 test. It is used only in the kernel chapter.
- Class 1 is the positive class. Accuracy, precision, recall, F1 and the confusion
  matrix use the usual convention. The balanced moon and iris validation sets have a
  50% majority-class baseline.
- Model selection uses validation data. The test split is evaluated once after the
  choice is recorded.

## Course maintenance

`experiment.py` is the numerical source for both the website and the notebook.
`curriculum.json` holds the shared text, formulas, chapter order and starter snippets.
`Tutorial07.vue` renders the web scenes; `build_notebook.py` generates the complete
notebook and copies the public functions into its appendix. Regeneration replaces the
course notebook; students edit their downloaded copies.

From the repository root:

```sh
uv run python src/tutorials/tutorial07/build_notebook.py --execute
npm run build
uv run python scripts/verify.py tutorial07
```

The website uses Pyodide 0.27.7 with scikit-learn 1.6.1. Native requirements are in
`requirements.txt`; minor floating-point or version differences are possible.
