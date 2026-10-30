<script setup lang="ts">
import { courseHref } from '../../navigation'

defineProps<{ chapter: string }>()
const asset = (file: string) => courseHref(`tutorials/tutorial07/${file}`)
const slides = asset('midterm_review_slides.pdf')
</script>

<template>
  <article class="review-materials">
    <p>
      Midterm Review Tutorial: 33 slides covering the exam format, the core concepts and fully
      worked problems from Practice Paper 1, Practice Paper 2 and Midterm 2022.
    </p>
    <div class="material-actions" aria-label="Tutorial downloads">
      <a class="button" :href="slides" target="_blank" rel="noopener">Open PDF in a new tab</a>
      <a class="button primary" :href="slides" download>Download slides (PDF)</a>
    </div>
    <p class="muted">
      Answers reveal one page at a time, so the deck runs to 69 PDF pages. If your browser cannot
      display the embedded PDF, use the buttons above.
    </p>
    <iframe
      class="slides-frame"
      :src="`${slides}#view=FitH&pagemode=none`"
      title="Tutorial 07: Midterm review slides"
    ></iframe>
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
</style>
