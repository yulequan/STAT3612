# Tutorial04 · From pixels to a classifier

Build a logistic classifier for MNIST digits **3 (label 0)** and **8 (label 1)** using
minibatch SGD. The practice workflow is: inspect data, prepare inputs, compute predictions,
define loss, take one update, train, evaluate, and investigate an improvement.

## Use the student package

Extract the whole zip; keep `experiment.py` beside the notebook and retain the `data/` folder.
Use Python 3.11 or newer in a virtual environment:

```sh
python -m pip install -r requirements.txt
python -m jupyter lab
```

Open `tutorial04.ipynb` (in `src/tutorials/tutorial04/` in the course repository).
Run the baseline, make predictions before your comparisons, then try one motivated change.
The provided baseline cells execute without filling in exercises. The last test cell asks
you to write a model-selection reason before accessing the test set.

## What you will practise

1. Connect image positions, array shapes and labels.
2. Distinguish scaling, feature transformations and augmentation.
3. Explain a logistic score, probability and cross-entropy loss.
4. Reason about the direction of one gradient update.
5. Train with shuffled minibatches; compare learning rates, batch sizes and epochs.
6. Inspect validation errors and compare one proposed improvement.
7. Select a model using validation evidence, then evaluate on held-out test data.
8. Try a classifier that needs no SGD, explain XOR with nonlinear features, and connect a
   local convolution calculation to the assumptions behind CNNs.

Start with the website’s Overview for the task, learning route, objectives and expected
work. Each practical chapter then follows the same path: understand the idea, explore its
mechanism, read the corresponding Python, then edit and run a small experiment. The
one-update chapter lets you select executed lines and inspect their actual intermediate
values. Browser snippets start with fresh training/validation arrays; use `print(...)` to
inspect results. Stop and reset Python if a run takes too long. Resetting clears trained
models; download the notebook or export results to keep your work beyond this browser session.

The 35-cell notebook develops the same workflow through eight sections. Its final section
includes a nearest-centroid baseline, constructed XOR rules and a convolution experiment.
The CNN demonstration uses fixed filters to explain the operation; learning an MLP or CNN
is a suggested next investigation, with links to further material.

Submit your executed notebook with a baseline, one experiment, your reasoning and a
limitation. You may use AI for implementation and debugging; be able to explain the choices
and interpret the result. Higher accuracy is not the sole measure of a good experiment.

## Data and comparisons

The frozen file contains 2,000 real 28×28 MNIST digits, originally 1,200 train / 800 test.
A deterministic, stratified split (seed 3612) makes **960 train / 240 validation / 800 test**.
Each split is balanced. The original test set is unchanged. Pixel intensities are divided
by 255 in the loader; unscaled experiments multiply the features back by 255.

MNIST source: LeCun, Cortes and Burges, *The MNIST Database of Handwritten Digits*.

Training starts from zero weights/bias and reshuffles each epoch with seed 3612. The
baseline uses learning rate 0.1, 25 epochs and batch size 32. Browser and notebook use the
same experiment definitions, but minor floating-point differences across Python/BLAS
versions are possible. Do not compare these new results with old 1,200-training-image
figures: the split and training procedure have deliberately changed.

Translation is a horizontal shift with zero padding, not wraparound. The augmentation
example adds copies shifted one pixel right and doubles training examples; equal epochs
therefore also mean more parameter updates. A benefit on that shift does not establish
invariance to every translation. Feature processing is applied identically at evaluation.

## Course maintenance

`experiment.py` is the numerical source for both browser and notebook. `build_notebook.py`
extracts the key functions into editable cells and adds practice prompts. Regenerating the
notebook overwrites manual edits to the course copy; students work in their own copies.

From the repository root:

```sh
uv run python src/tutorials/tutorial04/build_notebook.py --execute
npm run build
uv run python scripts/verify.py
```

The Vue scenes, Python source, notebook and data live together in `src/tutorials/tutorial04/`.
Chapters can be visited in any order.
There are no short/long routes, teacher notes, prediction gates or numerical-audit chapters.
