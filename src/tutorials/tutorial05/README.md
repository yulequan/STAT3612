# Tutorial05 · Spam Email Classification

Follow the complete workflow: inbox consequences → keyword baseline → original data and
fair splits → numerical features → word counts and TF–IDF → logistic contributions →
regularization → training-only CV → LDA → a binomial additive spline model → KNN →
validation threshold and errors → frozen test decision.

The website and notebook cover every chapter. There are no timed routes or optional
classroom-only discussion sections. Each chapter connects an explanation, mathematical
notation, an interactive or plotted mechanism, the scientific Python and an editable
experiment. All numerical computations use `experiment.py`; lesson content is shared
through `curriculum.json`.

## Original data and scope

Use the **original UCI SMS Spam Collection**, compiled by Almeida and Gómez Hidalgo
and described by Almeida, Gómez Hidalgo and Yamakami (2011). It contains 5,574 English
SMS messages from several research/volunteer sources, not full email messages.
See [data/README.md](data/README.md) for the original links, research citation,
compilation background, attribution, checksum and limitations. The source bytes are
unchanged; this tutorial does not use a Kaggle CSV mirror.

Case/whitespace-normalized message identity removes 415 repeats before splitting.
The retained message text is unchanged. There are 5,159 unique identities; the fixed
stratified split is **3,095 train / 1,032 validation / 1,032 test**, seed 3612.
CV fits every pipeline stage separately on four training folds and scores the fifth.
Test messages are excluded from the browser’s editable experiment namespace.

Numerical models use log(1+x) and training-fitted scaling on five counts. LDA uses a
shared covariance with shrinkage. The additive model uses separate cubic spline bases
and regularized binomial logistic fitting; it is not a dedicated GAM package and its
L2 coefficient penalty is not a derivative-based spline roughness penalty. Text models
use a consistent alphanumeric tokenizer, min_df=2 and at most 2,500 sparse features.
KNN uses Euclidean distance for standardized numerical inputs and cosine for text.

## Student package

Extract the complete zip. Keep the notebook beside `experiment.py`, `curriculum.json`
and the `data/` folder. Use Python 3.11+ in a virtual environment:

```sh
python -m pip install -r requirements.txt
python -m jupyter lab
```

Open `tutorial05.ipynb`, run the sections in order, modify the provided experiments and
explain the observations. All baseline cells execute as supplied. The last test cell
requires a nonempty model/threshold rationale. After testing, the lab freezes that decision.
Submit your executed notebook and experiment record. Avoid repeatedly checking test
performance while choosing a model; restarting Python does not undo test exposure.

The browser uses Pyodide 0.27.7 with scikit-learn 1.6.1. Native notebook dependencies
are declared in `requirements.txt`; small numerical differences across versions are possible.
The website serves its runtime, dataset and wheels locally without runtime CDN downloads.

## Course maintenance

```sh
uv run python src/tutorials/tutorial05/build_notebook.py --execute
uv run python scripts/verify.py
```

Regeneration replaces the course notebook. Students edit downloaded copies. The generator
extracts scientific functions from `experiment.py`, reuses the web curriculum and produces
executed baseline figures. Keep production source, notebook and dataset together here.
