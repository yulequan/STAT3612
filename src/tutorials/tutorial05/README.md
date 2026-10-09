# Tutorial05 · Spam Message Classification

Start with the **original UCI SMS Spam Collection**, then complete every chapter:
open the data → define the task → split train / validation / test → tokenize →
word counts → TF–IDF → NB / LR / KNN → regularization and CV → numerical LR /
LDA / GAM → validation comparison and error analysis → one final test.

## Download and open the data

- [UCI dataset page](https://archive.ics.uci.edu/dataset/228/sms+spam+collection)
- [Original ZIP download](https://archive.ics.uci.edu/static/public/228/sms+spam+collection.zip)
- The identical original bytes are bundled as `data/SMSSpamCollection.txt`.

Extract the UCI ZIP and open `SMSSpamCollection` in a text editor. There is no
header. Each line is `ham<TAB>message` or `spam<TAB>message`. These are English SMS,
not email. The 5,574 raw messages contain 4,827 ham and 747 spam. Read actual
messages before discussing their features. Provenance, citation, license, checksum
and dataset limitations are in [data/README.md](data/README.md).

The first chapter explicitly opens the file, audits repeated identities and
shows both steps of the stratified split. Ignoring case and excess whitespace
for identity removes 415 repeats; retained text stays unchanged. Seed 3612 gives
3,095 train / 1,032 validation / 1,032 test. The lesson distinguishes raw and
post-deduplication class proportions, with an always-ham validation baseline.

## Complete learning workflow

There is one required route. Each modeling chapter spells out training,
validation selection and the shared test stage. NB compares representation and
smoothing; LR compares C; KNN compares k; numerical LR and GAM compare C; LDA
compares covariance shrinkage. The browser's **Compare validation settings**
button fits the grid and displays training/validation metrics. Candidates stay
available in Evaluation. CV refits the full pipeline inside each training fold,
then evaluates the selected pipeline on the separate validation split.

Choose all model settings and the decision threshold using validation evidence.
Carry candidates to the shared comparison, record the final rationale, and test
one frozen train-fitted pipeline once. This tutorial keeps the selected fitted
pipeline unchanged rather than refitting it on validation. Test messages are
omitted from the browser snippet namespace. Restarting Python does not undo test
exposure.

All worked SMS text comes from the actual training or validation split. The NB
arithmetic uses priors and word counts fitted on all training SMS, and an
unchanged validation message. Formulas and symbol definitions precede tables,
substitutions, scores, normalization and the decision. Log-space evidence is
visible. LR and KNN arithmetic views use six real training SMS with reduced word
columns to expose every operation; they are clearly distinguished from the full
models and never supply reported evaluation metrics. KNN explains cosine,
Euclidean and Manhattan distances, works through their calculations, and shows
selected neighbors and individual votes without requiring Python.

Count and TF–IDF examples use real SMS and connect small inspectable matrices to
training-fitted full-data matrices. Text models use NLTK `TreebankWordTokenizer`,
lowercase and retain alphanumeric tokens, with no downloaded NLTK resources.
This preprocessing can discard punctuation, currency, URLs or contractions;
the lesson inspects what is lost. The real pipelines keep sparse matrices,
`min_df=2`, and at most 2,500 vocabulary words. TF–IDF uses smoothed natural-log
IDF and L2 normalization. Using TF–IDF with NB is an empirical nonnegative-weight
extension rather than literal multinomial counts.

Numerical models use log(1+x) and training-fitted scaling of characters, retained
tokens, links, digits and exclamation marks. Compare numerical LR, LDA and GAM
on the same features. LDA assumes Gaussian classes with shared covariance. The
GAM implementation has separate cubic spline bases and a regularized binomial
logistic fit, without interactions; its L2 coefficient penalty is not a
spline-derivative roughness penalty.

## Student package

Extract the complete zip. Keep the notebook beside `experiment.py`,
`curriculum.json`, `diagrams.py`, `model_figures.py`, `model_examples.json` and
`data/`. Use Python 3.11+ in a virtual environment:

```sh
python -m pip install -r requirements.txt
python -m jupyter lab
```

Run setup and every chapter in order. Predict the effect of an edit, run it,
then explain the output. Submit the executed notebook with the dataset audit,
all training/validation comparisons, false positives and false negatives,
the final model/threshold rationale, test metrics and dataset limitations.

The browser uses Pyodide 0.27.7, scikit-learn 1.6.1 and NLTK 3.8.1; native
requirements are in `requirements.txt`. Small numerical differences between
versions are possible. Runtime assets, wheels and data are bundled locally.

## Course maintenance

```sh
uv run python src/tutorials/tutorial05/build_notebook.py --execute
uv run python scripts/verify.py tutorial05
```

Maintain shared teaching content and flows in `curriculum.json`. The web and
notebook use the same formulas, text, SMS examples and workflow definitions.
`model_examples.json` stores the fitted NB training quantities and the six-row
LR/KNN arithmetic views; scientific regression tests check them against the
actual split and sklearn. `model_figures.py` supplies notebook plots.
Maintain scientific behavior in `experiment.py`; its functions are copied to
the notebook appendix. Regeneration replaces the course notebook; students edit
downloaded copies.
