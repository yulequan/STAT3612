# STAT3612 · Fall 2026 · Tutorial 08

**Ensemble Learning and Support Vector Machines**

Tutor: Yinghao Zhu · yhzhu99@connect.hku.hk

A 17-slide English Beamer walkthrough designed for a concise 30-minute classroom session, paired with an executable Jupyter notebook (`ensemble_svm_tutorial.ipynb`) containing 25 code cells and 13 decision-boundary figures.

## Learning route

1. **Ensemble Learning (`make_moons`, 500 samples, noise 0.3)**
   - **Single Decision Tree (Baseline):** Unrestricted `DecisionTreeClassifier` overfitting noisy points (`0.8533` test accuracy).
   - **Bagging (`BaggingClassifier`):** 500 bootstrap trees averaging out variance (`0.8933` test accuracy).
   - **Random Forest (`RandomForestClassifier`):** Bootstrap samples plus random feature subsets per split to decorrelate trees (`0.9000` test accuracy).
   - **Boosting (`AdaBoostClassifier`, `GradientBoostingClassifier`, `XGBClassifier`):** Sequential weak learners focusing on misclassified samples or residual errors (`0.8800`–`0.8867` test accuracy).
   - **Assignment 3 (Q1–Q2) Code Pattern:** Visualizing entropy trees with `plot_tree` and sweeping `max_depth = 2..12` for a single tree vs. a random forest.
2. **Support Vector Machines (`load_iris` 2D & synthetic `XOR`)**
   - **Margins & Support Vectors:** Visualizing the decision boundary ($f(\mathbf{x})=0$), margin gutters ($f(\mathbf{x})=\pm 1$) and `clf.support_vectors_` with `DecisionBoundaryDisplay`.
   - **Kernel Comparison (`linear`, `poly`, `rbf`, `sigmoid`):** Comparing accuracy and boundary geometry on Iris petal length/width (`RBF` achieves `0.92`) and 4-quadrant `XOR`.
   - **Assignment 3 (Q4) Code Pattern:** Feature scaling with `StandardScaler`, fitting `SVC(C=1.5, kernel="rbf")`, counting support vectors, and computing the test confusion matrix.

## Run the companion notebook

Extract `student.zip` and run from its folder with Python 3.10+:

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m jupyterlab ensemble_svm_tutorial.ipynb
```

Choose **Restart Kernel and Run All Cells**. All datasets are generated locally with scikit-learn and NumPy; no external files or network downloads are required after installing the packages.
