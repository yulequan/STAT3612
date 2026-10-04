<script setup lang="ts">
import { courseHref } from '../navigation'
import { courseSections } from '../course'
</script>
<template>
  <section class="course-index course-home">
    <div class="home-hero">
      <p class="eyebrow">HKU · STAT / SDST 3612</p>
      <h1>Statistical Machine Learning</h1>
      <div class="grid gap-6 sm:grid-cols-[minmax(0,1fr)_180px] sm:gap-12">
        <p class="course-intro">
          Explore the ideas. Experiment with real code. Build your understanding of statistical
          machine learning, one step at a time.
        </p>
        <p class="course-instructor">Instructor<strong>Prof. Lequan Yu</strong></p>
      </div>
    </div>
    <section
      v-for="(section, index) in courseSections"
      :key="section.id"
      class="home-section grid gap-6 sm:grid-cols-[180px_minmax(0,1fr)] sm:gap-10"
      :aria-labelledby="`home-${section.id}`"
    >
      <div>
        <span class="section-index" aria-hidden="true">{{
          String(index + 1).padStart(2, '0')
        }}</span>
        <h2 :id="`home-${section.id}`">
          <a :href="courseHref(section.id)">{{ section.title }}</a>
        </h2>
        <p class="section-description">{{ section.description }}</p>
      </div>
      <div>
        <p v-if="!section.items.length" class="muted">Materials coming soon.</p>
        <ul v-else class="home-materials">
          <li v-for="item in section.items" :key="item.id">
            <a class="material-title" :href="item.href">
              <span>{{ item.title }}</span
              ><span class="material-arrow" aria-hidden="true">↗</span>
            </a>
            <p>{{ item.description }}</p>
          </li>
        </ul>
      </div>
    </section>
    <p class="course-endnote">
      Department of Statistics &amp; Actuarial Science · The University of Hong Kong
    </p>
  </section>
</template>
