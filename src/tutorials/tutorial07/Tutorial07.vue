<script setup lang="ts">
import { courseHref } from '../../navigation'

defineProps<{ chapter: string }>()
const asset = (file: string) => courseHref(`tutorials/tutorial07/${file}`)
const slides = asset('midterm_review_slides.pdf')
</script>

<template>
  <article class="review-materials">
    <p>
      Midterm Review Tutorial: 33 slides on the exam format, the distinctions the questions target
      and fully worked past-paper and midterm problems. Page through the deck here, pausing at each
      question before the next page reveals its answer.
    </p>
    <div class="material-actions" aria-label="Tutorial downloads">
      <a class="button primary" :href="slides" target="_blank" rel="noopener"
        >Open PDF in a new tab</a
      >
      <a class="button" :href="asset('student.zip')" download>Slides + README (ZIP)</a>
    </div>
    <p class="muted">
      If your browser cannot display the embedded PDF, use the link above to open or save it.
    </p>
    <iframe
      class="slides-frame"
      :src="`${slides}#view=FitH&pagemode=none`"
      title="Tutorial 07: Midterm review slides"
    ></iframe>
    <section aria-labelledby="deck-contents">
      <h2 id="deck-contents">What the deck covers</h2>
      <ol class="review-parts">
        <li>
          <strong>Exam overview and core concepts.</strong> What the three question types test, then
          regression vs. classification, parametric vs. non-parametric, generative vs.
          discriminative, gradient descent and SGD, the bias-variance tradeoff, and validation vs.
          k-fold cross-validation.
        </li>
        <li>
          <strong>Linear models.</strong> The normal equations on a six-point dataset, a fifth-order
          polynomial that interpolates it, why we regularize, Ridge vs. LASSO, how to read
          regularization paths, and Elastic Net.
        </li>
        <li>
          <strong>Classification models.</strong> Precision, recall and ROC; linear vs. quadratic
          boundaries; k-nearest neighbors; a logistic boundary, a single-split tree and 3-NN on the
          same six points; and matching six classifiers to their training errors.
        </li>
        <li>
          <strong>Trees, ensembles and SVM.</strong> Impurity measures and a full Gini split
          calculation, the 2D partition a fitted tree induces, bagging, random forests and boosting,
          then support vectors, margins and the effect of the cost parameter C.
        </li>
        <li>
          <strong>Final advice.</strong> The recurring exam traps: where feature scaling matters and
          where it does not, greedy stepwise selection, GLM as a special case of GAM, and which
          hyperparameters raise or lower flexibility.
        </li>
      </ol>
    </section>
    <section aria-labelledby="how-to-use">
      <h2 id="how-to-use">How to work through it</h2>
      <p>
        The deck reveals each answer one page at a time, so 33 numbered slides occupy 69 PDF pages
        and a slide may appear several times with one more step visible. Sketch the points, the
        boundary or the tree on paper and compare before advancing.
      </p>
      <p>
        Applied matching questions expect a written reason, not only a pairing: state the geometric
        or algebraic justification, because an unexplained match earns no marks.
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
.review-parts {
  display: grid;
  gap: 12px;
  padding-left: 1.25rem;
}
.review-parts li {
  padding-left: 0.25rem;
}
</style>
