# Tutorial 06: Machine Learning for Time Series Data

**From Data Structures to Learned Representations**

Tutor: Yinghao Zhu (yhzhu99@connect.hku.hk)

Read `time_series_slides.pdf` (34 slides, about 60 minutes with discussion).
Open `time_series_tutorial.ipynb` for its executable Jupyter companion. Saved outputs
include 14 figures, so the notebook can also be read without running it.

## Run locally

Extract the complete ZIP and, from that folder with Python 3.10+, run:

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m jupyterlab time_series_tutorial.ipynb
```

On Windows, activate with `.venv\Scripts\activate` instead. In VS Code, select
the `.venv` interpreter as the notebook kernel. In Jupyter, choose **Restart
Kernel and Run All Cells**. No GPU, PyTorch, external datasets or course project
files are needed. All data are generated locally.

Allow 60-90 minutes to read and experiment; execution takes only a few seconds
on a typical CPU. Start with sections 1-5, the trained encoder in section 6, and
sections 8-9. Study architecture mechanics and ARIMA separately after running
the setup cells.

## What the examples mean

- A synthetic cohort of 400 patients connects data shapes, gaps, features,
  classifiers and evaluation. Its future heart-rate event is artificial, not
  a clinical definition of sepsis.
- A small dense network actually learns eight hidden features; a forecast head
  reuses them. RNN/GRU and attention examples use untrained illustrative weights
  to teach mechanics, not trained sequence-model performance.
- ARIMA and a seasonal model are fitted to separate longer synthetic series
  using statsmodels. There is no model leaderboard or order-search exercise.
- Development splits precede fitting. Final test evaluation follows model
  selection and refitting on train plus validation.
- The closing project slides introduce the task, file readers and open design
  questions, not a worked solution or submission. Moodle/Kaggle instructions
  and later course announcements remain authoritative. Actual Parquet loading
  is a reference snippet; install `pyarrow` separately for the course files.

## Publication source

Published from `stat3612-26fall-tutorial` on 2026-10-23. The notebook is an
unchanged copy from `notebooks/` in that authoring repository; the PDF is
compiled from `main.tex` with XeLaTeX. The companion requirements additionally
bound NumPy below 2.4 to avoid timedelta deprecation warnings in pandas 2.x.
These are
intentional tracked teaching assets, not temporary build outputs.

For maintainers: edit and validate the authoring repository first, then replace
these publication copies. Website builds need neither that checkout nor LaTeX.
