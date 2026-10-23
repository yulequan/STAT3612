<script setup lang="ts">
import { courseHref } from '../../navigation'

defineProps<{ chapter: string }>()
const asset = (file: string) => courseHref(`tutorials/tutorial06/${file}`)
const slides = asset('time_series_slides.pdf')
</script>

<template>
  <article class="time-series-materials">
    <p>
      Machine Learning for Time Series Data: From Data Structures to Learned Representations. Read
      the 34-slide deck here and download the executable companion for Jupyter.
    </p>
    <div class="material-actions" aria-label="Tutorial downloads">
      <a class="button" :href="slides" target="_blank" rel="noopener">Open PDF in a new tab</a>
      <a class="button primary" :href="asset('student.zip')" download>Notebook + setup (ZIP)</a>
    </div>
    <p class="muted">
      If your browser cannot display the embedded PDF, use the link above to open or save it.
    </p>
    <iframe
      class="slides-frame"
      :src="`${slides}#view=FitH&pagemode=none`"
      title="Tutorial 06: Time-series slides"
    ></iframe>
    <section aria-labelledby="notebook-setup">
      <h2 id="notebook-setup">Run the companion notebook</h2>
      <p>
        The notebook includes saved outputs and 14 figures, so you can read it before running it.
        All examples use synthetic data generated locally. No GPU, PyTorch or project files are
        required. Download and extract the ZIP, then run these commands from its folder with Python
        3.10+:
      </p>
      <pre><code>python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m jupyterlab time_series_tutorial.ipynb</code></pre>
      <p>
        On Windows, activate with <code>.venv\Scripts\activate</code> instead. In Jupyter, choose
        <strong>Restart Kernel and Run All Cells</strong>. Allow 60-90 minutes to read and
        experiment; execution itself takes only a few seconds on a typical CPU.
      </p>
      <p>
        The ZIP includes <code>requirements.txt</code> and <code>README.md</code>. See the README
        for the suggested route and the distinction between trained examples and illustrative
        architecture weights.
      </p>
    </section>
  </article>
</template>

<style scoped>
.material-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin: 24px 0;
}
.slides-frame {
  display: block;
  width: 100%;
  height: 75vh;
  min-height: 360px;
  border: 1px solid var(--line);
  border-radius: 3px;
  background: var(--surface);
}
pre {
  max-width: 100%;
  overflow-x: auto;
  padding: 18px;
  border: 1px solid var(--line);
  background: var(--surface);
}
</style>
