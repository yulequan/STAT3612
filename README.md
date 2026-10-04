# STAT / SDST 3612 · Course site

A Vue 3 + TypeScript + Tailwind CSS 4 website with real Python experiments and a companion Jupyter notebook.
Tutorial04 teaches one practical workflow: **data → preparation → prediction → loss →
one update → training → evaluation and improvement → beyond linear models**.
The course homepage opens at `/` and offers three sections: **Lectures**, **Tutorials** and
**Demos**. The homepage shows two levels: sections and their materials. The sidebar
starts at the same depth, with each tutorial's Overview and chapters collapsed. Entering
a tutorial (including a direct chapter URL) reveals its full chapter list. Separate caret
buttons collapse each branch independently; navigation leaves other branches as they were.
Search reveals matching chapters without changing the saved expansion state. Use the sidebar,
overview links or previous/next links to switch chapters. On phones, open **Menu**
to access the same hierarchy.

The Swiss-inspired interface uses a neutral palette, a restrained red accent, sans-serif
typography and a numbered resource grid. A geometric sigma mark identifies the course in
the header and favicon. Tailwind runs through its Vite plugin; colors and typography live
in the CSS theme. Fonts and assets stay local for offline use. The top bar carries only
course branding and the mobile menu; course navigation lives in the sidebar. On phones,
the menu focuses search, closes with Escape or a tap outside, and keeps the page behind
it inactive. Search filters materials only when a query is entered. Lecture materials
have not been published yet.
The homepage identifies Prof. Lequan Yu as the instructor. Tutorial04's overview begins
with the tutor's name and contact email.
Tutorials open with an Overview of the task, learning route, objectives, prerequisites and
expected work; chapters are freely navigable.

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
lockfile. Later runs reuse the cache. Asset preparation stages complete files, then updates
`.cache/public` in place; running `npm run build` or `npm run prepare:assets` while Vite is
open keeps its watched directories intact. If an older running server reports HTML instead
of tutorial JSON, restart `npm run dev` once, then reload the page. The web toolchain needs
Node.js 22.12+ (or 24+), Python 3.10+ and `curl`; host scientific Python packages are not required to run the website.

## Deploy

```sh
npm ci
npm run build
```

**Publish `dist/`.** It contains the complete static website, Python runtime, scientific
packages, data and downloadable student packages. There is no backend, runtime CDN dependency,
or server-side Python. The build generates an `index.html` for every course route, so
clean chapter URLs support direct visits and refreshes on ordinary static hosting. Each
entry roots its assets at the site directory, including when hosted under a subdirectory.

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

The build reads the course catalog and automatically emits entry pages for all sections,
demos, tutorial overviews and chapters. For example,
**https://yulequan.github.io/STAT3612/tutorials/tutorial04/prepare** opens the preparation
chapter without a hash. Navigation uses browser history and keeps the Python session alive.
Each entry fixes its asset base before normalizing a trailing slash, keeping scripts, Python
workers, datasets, notebook downloads and demo links inside `/STAT3612/`. No custom 404
routing or server rewrites are needed. New lessons are included automatically.
The original standalone demo URLs remain valid:

- [Gradient Descent Step by Step](https://yulequan.github.io/STAT3612/gradient-descent-step-by-step.html)
- [GD vs SGD: Logistic Regression](https://yulequan.github.io/STAT3612/gd-vs-sgd-logistic-regression.html)

Course routes follow the material hierarchy:

- `/lectures` — lecture catalog (ready for future materials).
- `/tutorials` → `/tutorials/tutorial04/overview` → individual chapters.
- `/demos` → `/demos/gradient-descent` or `/demos/gd-vs-sgd`.

Paths above are relative to the site root (`/STAT3612/` on GitHub Pages).
The previous standalone demo overview is preserved at [`demo/`](https://yulequan.github.io/STAT3612/demo/).

The original demos remain single-page HTML files in `public/`. `DemoPage.vue` embeds them
in same-origin iframes within the course header and sidebar. Each frame resizes to its
content, keeping scrolling in the outer course page; navigating away removes the frame,
including its timers and WebGL context. **Open standalone** opens the original page in a
new tab. Demo calculations, controls and visualizations are unchanged. The only change to
the HTML is its course backlink, which targets the top page to avoid nesting the course
site inside the frame. Three.js 0.160.1 and its license are bundled locally.

After deployment, open Tutorial04, enter a practical chapter, wait for **Run Python** to
become available, run an example and download **Notebook + data**. Also open both demos through **Demos**.

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
  course.ts                    section, lecture and demo catalogs
  components/                  course home, catalogs, demo embed, tutorial overview and shared UI
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
Loading and failure messages appear only when needed; there is no persistent runtime status
or repeated step navigation above the chapter. The code editor runs student Python in the
same worker with fresh copies of training and validation arrays on each invocation. It captures printed output and errors. Stopping a run
restarts the worker and clears session models, including when a snippet loops indefinitely.
Returning to the homepage retains the tutorial session; reloading the page does not.
Export results to preserve comparisons. Snippets are local user-authored Python, not a
restricted security sandbox; the provided namespace omits held-out test arrays.

## Notebook

The single **Notebook + data** link at the bottom of the tutorial sidebar downloads a
complete student zip. On phones, open **Menu** to find it. Tutorial04 has
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
failure/retry (including an HTML fallback returned for JSON), asset regeneration while the
development server is running, cancellation, static subdirectory deployment and absence
of external requests.

Demo regression checks compare 123 embedded UI states against values captured from the
original standalone pages (see `tests/fixtures/README.md`). They cover both modes, parameter
updates, initialization, sample and batch sizes, learning rates, speed, back and reset.

Tests use `/usr/bin/google-chrome` when available; set `CHROME_BIN` or run
`npx playwright install chromium` for another environment. Missing dependencies fail the
checks rather than silently skipping them. Screenshots/traces remain disposable test output.
If the default test ports (4173, 4174 and 4175) are occupied, set `TEST_PREVIEW_PORT`,
`TEST_STATIC_PORT` and `TEST_DEV_PORT` to available ports when running verification or browser tests.

## Add course materials

Add published lecture links to `lectures` in `src/course.ts`. Add standalone demo metadata
to `demos` in that file and place its HTML in `public/`. The shared catalogs and sidebar
use this registry; the course homepage never automatically opens a tutorial or demo.

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
