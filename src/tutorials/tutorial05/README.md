# Tutorial05 · Spam Message Classification

Learn one continuous workflow: **message → NLTK tokens → word counts / TF–IDF →
classifier → prediction and errors**. No previous NLP course is assumed.

## Choose your learning route

The core route covers Text Classification, Our Messages and Labels, Tokenization,
Bag of Words, TF–IDF, Naive Bayes, Logistic Regression, KNN, then Evaluation and
Error Analysis. Rules appear only as a brief motivating counterexample.

Complete extensions cover regularization, cross-validation, numerical features,
LDA and a binomial additive spline model (GAM). Instructors can choose which to
teach. Each extension explains its inputs and uses the common setup; the core
comparison and final evaluation work without running any extensions.

The website and notebook share the explanations, worked tables, explicit NLTK /
sklearn imports and editable experiments in `curriculum.json`. Count matrices,
TF–IDF intermediate values and a hand-calculated NB prediction precede the real
classifiers. Supporting scientific functions are available in collapsed web
panels and a notebook appendix, keeping implementation details out of the main route.

Compare representations with NB fixed; compare NB, LR and KNN with TF–IDF fixed.
LDA and GAM use five numerical measurements and should be compared with numerical
LR on the same inputs. SVM, decision trees and random forests are outside this lesson.

## Original data and preprocessing

Use the **original UCI SMS Spam Collection**, compiled by Almeida and Gómez Hidalgo
and described by Almeida, Gómez Hidalgo and Yamakami (2011). The unchanged local
file contains 5,574 English SMS messages, not full emails. See
[data/README.md](data/README.md) for provenance, citation, license, checksum and limitations.

Case/whitespace-normalized identity removes 415 repeats before splitting. The
retained text is unchanged: **3,095 train / 1,032 validation / 1,032 test**, stratified,
seed 3612. Vocabulary and IDF are fitted on training data only; CV refits every
pipeline stage inside each training fold. Test messages are omitted from the
browser experiment namespace and final evaluation freezes the chosen decision.

All text vectorizers use NLTK `TreebankWordTokenizer`, lowercase and retain
alphanumeric tokens. It requires no downloaded NLTK corpora or models. Removing
punctuation, currency expressions or contractions can lose evidence; stopword
removal and stemming are discussed as choices rather than required cleaning.
Real text models keep sparse matrices, `min_df=2`, at most 2,500 vocabulary words.
Toy examples retain every token to make their columns inspectable.

TF–IDF uses sklearn's smoothed natural-log IDF and default L2 row normalization;
the worked example also inspects weights with `norm=None`. NB starts with counts
and additive smoothing. Using TF–IDF with NB is an empirical extension: weights
are nonnegative but are not literal multinomial counts. KNN uses uniform votes
and cosine distance for text.

Numerical extensions use log(1+x) and training-fitted scaling of characters,
retained tokens, links, digits and exclamation marks. LDA uses shared covariance
with shrinkage. The GAM-style implementation uses separate cubic spline bases
and regularized binomial logistic fitting, without interactions; its L2 penalty
is not a derivative-based spline roughness penalty.

## Student package

Extract the complete zip. Keep the notebook beside `experiment.py`,
`curriculum.json` and `data/`. Use Python 3.11+ in a virtual environment:

```sh
python -m pip install -r requirements.txt
python -m jupyter lab
```

Run setup, then the sections you are studying. In the core route, skip sections
9–13 and continue at section 14. Each browser snippet is self-contained after
setup and shows its own package imports. Notebook examples run in a shared kernel.
Predict what an edit will do, run it, then explain the observed output.

Submit the executed notebook and your comparisons, representative errors and
rationale. Run the final test cell only after writing a model/threshold reason.
Restarting Python does not undo test exposure.

The browser uses Pyodide 0.27.7, scikit-learn 1.6.1 and NLTK 3.8.1; native
notebook dependencies are in `requirements.txt`. Small version-dependent
numerical differences are possible. All browser runtime assets, wheels and data
are bundled locally; there are no runtime CDN or NLTK resource downloads.

## Course maintenance

```sh
uv run python src/tutorials/tutorial05/build_notebook.py --execute
uv run python scripts/verify.py tutorial05
```

Regeneration replaces the course notebook; students edit downloaded copies.
Maintain teaching content in `curriculum.json` and scientific behavior in
`experiment.py`. The generator places matching scientific functions in the
appendix and supplies stable cell IDs for reviewable updates.
