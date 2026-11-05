<script setup lang="ts">
import { courseHref } from '../../navigation'

defineProps<{ chapter: string }>()
const asset = (file: string) => courseHref(`tutorials/tutorial11/${file}`)
const slides = asset('transformer_slides.pdf')
</script>

<template>
  <article class="transformer-materials">
    <p>
      From Transformer to LLMs, Agentic AI and Hugging Face. Read the 24-slide deck here and
      download the executable companion notebook for Jupyter.
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
      title="Tutorial 11: Transformer, LLMs and Agentic AI slides"
    ></iframe>
    <section aria-labelledby="notebook-setup">
      <h2 id="notebook-setup">Run the companion notebook</h2>
      <p>
        The notebook includes saved outputs, 18 code cells and 6 figures covering PyTorch Scaled
        Dot-Product Self-Attention, causal masking, a Mini Vision Transformer (ViT), GRPO advantage
        calculation, a multi-step ReAct Agent with tool calling, and Hugging Face
        <code>transformers</code> tokenization, embeddings, and sequence classification. Download
        and extract the ZIP, then run:
      </p>
      <pre><code>python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m jupyterlab transformer_tutorial.ipynb</code></pre>
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
