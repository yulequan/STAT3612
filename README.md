# STAT / SDST 3612 · Interactive tutorials

A Vue 3 + TypeScript website with real Python experiments and a companion Jupyter notebook.
Tutorial04 teaches one practical workflow: **data → preparation → prediction → loss →
one update → training → evaluation and improvement → beyond linear models**.
The minimal course homepage lists published tutorials. Each opens with an Overview of the
task, learning route, objectives, prerequisites and expected work; chapters are freely navigable.

Each chapter connects a mathematical explanation, an interactive demonstration, highlighted
Python source and a small editable experiment. LaTeX is rendered locally with KaTeX. The SGD
chapter replays intermediate values captured from the actual Python function, line by line.
The final chapter uses XOR and a movable convolution window to motivate nonlinear features,
MLPs and CNNs. These constructed examples illustrate mechanisms, not trained neural-network results.

## Start

```sh
npm ci
npm run dev
```

Open the URL printed by Vite, normally **http://localhost:5173**. The first run downloads
and caches the Python wheels, checking their SHA-256 hashes against the pinned Pyodide
lockfile. Later runs reuse the cache. The web toolchain needs Node.js 22.12+ (or 24+),
Python 3.10+ and `curl`; host scientific Python packages are not required to run the website.

## Deploy

```sh
npm ci
npm run build
```

**Publish `dist/`.** It contains the complete static website, Python runtime, scientific
packages, data and downloadable student packages. There is no backend, runtime CDN dependency,
or server-side Python. Hash-based chapter URLs need no special routing rules, and assets
use relative paths so the site can also be hosted under a subdirectory.

For a hosting provider, set the build command to `npm run build` and the publish/output
directory to `dist`. Ensure the build image has Python 3 and curl as noted above.

### GitHub Pages (GitHub Actions)

This repository publishes to **https://yulequan.github.io/STAT3612/** using
[`.github/workflows/deploy-pages.yml`](.github/workflows/deploy-pages.yml).

1. In the GitHub repository, open **Settings → Pages → Build and deployment**
   and set **Source** to **GitHub Actions** (requires repository administrator access).
2. Push to `main`, or run **Deploy GitHub Pages** from the **Actions** tab.
3. The workflow installs Node.js 22 and Python 3.13, runs `npm ci` and `npm run build`,
   checks the built site in Chromium under a subdirectory, and publishes only `dist/`.

Pull requests run the same build and deployment checks without publishing. Deployments
use the built-in `GITHUB_TOKEN`; no personal token, API keys or repository secrets are needed.
The `github-pages` environment must allow deployments from `main`.
The workflow's Python is only used to prepare static assets; it does not install the optional
notebook-authoring dependencies. Pyodide wheels are cached and SHA-256 checked on every build.

Vite's relative base (`./`) and hash navigation keep scripts, Python workers, datasets,
notebook downloads and demo links inside `/STAT3612/`. No custom 404 routing is needed.
The original standalone demo URLs remain valid:

- [Gradient Descent Step by Step](https://yulequan.github.io/STAT3612/gradient-descent-step-by-step.html)
- [GD vs SGD: Logistic Regression](https://yulequan.github.io/STAT3612/gd-vs-sgd-logistic-regression.html)

The course outline and header include **Demo**, alongside the imported tutorials.
The previous demo overview is preserved at [`demo/`](https://yulequan.github.io/STAT3612/demo/).
The original demos live in `public/`; asset preparation copies them unchanged into the
build alongside a locally bundled Three.js 0.160.1 and its license. Their calculations,
controls and visualizations are preserved, with links back to the course's Demo section.

After deployment, open Tutorial04, enter a practical chapter, wait for **Python ready**,
run an example and download **Notebook + data**. Also open both demos through **Demo**.

Preview the production build with `npm run preview`. For an offline class, copy `dist/`
and serve it locally:

```sh
python3 -m http.server 8000 --directory dist
```

Open **http://localhost:8000**. The complete build is about 38 MB, mostly Python and numerical
libraries. It works without internet access once built. Serve it over HTTP(S), not `file://`.

## A single source tree

```text
src/
  App.vue                      course navigation and chapter shell
  components/                  homepage, tutorial overview, math, code editor, images and charts
  runtime/                     Python worker and request lifecycle
  tutorials/
    index.ts                   automatically discovers lessons
    tutorial04/
      lesson.ts                title, overview, chapters, Vue component
      learning.ts              concepts, equations and editable Python starters
      Tutorial04.vue           interactive teaching scenes
      experiment.py            scientific implementation
      build_notebook.py        notebook content and function extraction
      tutorial04.ipynb         editable student notebook with baseline outputs
      data/mnist_3v8.npz        frozen MNIST subset
      tutorial.json            packages, assets and student-package manifest
      requirements.txt         student notebook dependencies
      README.md                student instructions
public/                        original standalone demos and demo overview
.github/workflows/             GitHub Pages build, browser checks and deployment
scripts/                       prepare assets, package, scaffold, verify
tests/                         numerical and real-browser checks
index.html, vite.config.ts     ordinary Vue/Vite entry and configuration
package.json, package-lock.json
pyproject.toml, uv.lock         local notebook/verification environment
```

There is no separate `web/`, `shared/`, or second tutorial tree. Components are shared within
`src/components`; each tutorial keeps its Vue, Python, notebook and data together.
`scripts/` contains actual build/verification commands, not course content.

Generated files live only in `.cache/`, `dist/` and `test-results/`, all ignored by Git.
Old session HTML, duplicate JavaScript computations, teaching guides/PDF, AI prompt cards,
prediction ledgers, screenshots, notebook HTML export and the old template have been removed.
The original standalone course demos are retained separately in `public/`.

## Python in the browser

[Pyodide](https://pyodide.org/) is a mature CPython-on-WebAssembly runtime. This site pins
**Pyodide 0.27.7 / Python 3.12.7, NumPy 2.0.2 and SciPy 1.14.1** as a compatible browser stack.
The notebook environment is pinned separately. Not every desktop Python package works in
WASM; declare and verify packages per lesson.

Each tutorial runs in its own Web Worker. Vue handles controls and visualisation; Python
handles the scientific operations. Training reports progress each epoch without blocking
navigation. The homepage and tutorial Overview do not start Python; entering a practical chapter loads its runtime.
The code editor runs student Python in the same worker with fresh copies of training and
validation arrays on each invocation. It captures printed output and errors. Stopping a run
restarts the worker and clears session models, including when a snippet loops indefinitely.
Returning to the homepage retains the tutorial session; reloading the page does not.
Export results to preserve comparisons. Snippets are local user-authored Python, not a
restricted security sandbox; the provided namespace omits held-out test arrays.

## Notebook

The website's **Notebook + data** link downloads a complete student zip. Tutorial04 has
one 35-cell notebook, including editable numerical functions, baseline outputs, a practical
investigation and a bridge to alternative classifiers and convolution. Each web chapter links
to its corresponding notebook section. File loading and image operations use its adjacent
`experiment.py`.

For local authoring:

```sh
uv sync
uv run jupyter lab
```

Open `src/tutorials/tutorial04/tutorial04.ipynb`. Maintain the teaching content in
`build_notebook.py` and the numerical functions in `experiment.py`, then regenerate:

```sh
uv run python src/tutorials/tutorial04/build_notebook.py --execute
npm run build
```

Regeneration overwrites edits to the course notebook; students edit their downloaded copies.
The generator copies the visible algorithm cells from `experiment.py`, preventing two
separately maintained implementations. The final test evaluation asks the student to first
write a reason for their model choice.

## Verify

```sh
uv run python scripts/verify.py
```

Verification checks scientific behavior and data separation, executes the extracted student
package (including its opt-in final test cell), checks notebook/source consistency, typechecks
and builds the site, then runs real-browser tests. WASM and native Python are compared at
every training epoch. Browser tests cover homepage navigation, all chapter starters, execution
traces, code editing and recovery, XOR/convolution, downloads, mobile layout, loading
failure/retry, cancellation, static subdirectory deployment and absence of external requests.

Tests use `/usr/bin/google-chrome` when available; set `CHROME_BIN` or run
`npx playwright install chromium` for another environment. Missing dependencies fail the
checks rather than silently skipping them. Screenshots/traces remain disposable test output.
If the default test ports (4173 and 4174) are occupied, set `TEST_PREVIEW_PORT` and
`TEST_STATIC_PORT` to available ports when running the verification or browser tests.

## Add the next tutorial

```sh
python3 scripts/new_tutorial.py 5 --title "Your next practical topic"
```

This creates one folder, `src/tutorials/tutorial05/`, with a runnable Vue/Python scaffold.
The registry discovers it automatically. Add its actual content, dataset and notebook before
sharing it; the scaffold is not a completed lesson. No future topic is assumed.

The small authoring contract:

- `lesson.ts` exports id, number, title, subtitle, overview, ordered chapters and a Vue component.
  The required `overview` defines the task, motivation, learning stages (with chapter ids),
  objectives, prerequisites and expected work. The shared shell renders it before loading the
  practical lesson, and passes the selected `chapter` to the lesson component. The scaffold
  includes this structure for every new tutorial.
- `tutorial.json` declares the Python `experiment`, optional `dataset`, `python_packages`,
  `web_assets` and `student_files`. The build packages every discovered tutorial.
- The Python module exports `Experiment(path)` with `dispatch(action, params)` returning a
  JSON string. `initialize` supplies starting data; other actions are lesson-specific.
- Training lessons may implement `fit(config, progress_callback)`. Progress is a JSON record,
  and the return value must be JSON-serializable. Plotting belongs in Vue or the notebook.

Reuse the worker and components when useful; each lesson remains free to use its own
teaching structure. Add subject-specific numerical and browser checks when adding a topic.
