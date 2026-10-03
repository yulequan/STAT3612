<script setup lang="ts">
import { tutorials } from '../tutorials'
const base = import.meta.env.BASE_URL
</script>
<template>
  <section id="tutorial-catalog" class="course-index">
    <p class="eyebrow">STATISTICAL MACHINE LEARNING · 2026–27</p>
    <h1>Tutorials</h1>
    <ul class="tutorial-list">
      <li v-for="lesson in tutorials" :key="lesson.id">
        <a :href="`#/${lesson.id}/overview`">
          <span class="tutorial-list-number">{{ lesson.number }}</span>
          <span
            ><strong>{{ lesson.title }}</strong
            ><small>{{ lesson.subtitle }}</small></span
          >
          <span class="tutorial-list-arrow" aria-hidden="true">→</span>
        </a>
      </li>
    </ul>
  </section>
  <section id="demo-catalog" class="course-index" aria-labelledby="demo-heading">
    <h2 id="demo-heading">Demo</h2>
    <p>Explore optimization through the course's interactive demonstrations.</p>
    <ul class="tutorial-list">
      <li>
        <a :href="`${base}gradient-descent-step-by-step.html`">
          <span class="tutorial-list-number">01</span>
          <span>
            <strong>Gradient Descent Step by Step</strong>
            <small>Follow predictions, loss, gradients and parameter updates in 1D and 2D.</small>
          </span>
          <span class="tutorial-list-arrow" aria-hidden="true">→</span>
        </a>
      </li>
      <li>
        <a :href="`${base}gd-vs-sgd-logistic-regression.html`">
          <span class="tutorial-list-number">02</span>
          <span>
            <strong>GD vs SGD: Logistic Regression</strong>
            <small>Compare full-data and mini-batch updates on a 3D logistic-loss surface.</small>
          </span>
          <span class="tutorial-list-arrow" aria-hidden="true">→</span>
        </a>
      </li>
    </ul>
    <p><a :href="`${base}demo/`">Demo overview →</a></p>
  </section>
</template>
