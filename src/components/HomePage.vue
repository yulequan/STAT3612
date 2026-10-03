<script setup lang="ts">
import { courseSections } from '../course'
</script>
<template>
  <section class="course-index course-home">
    <p class="eyebrow">STAT / SDST 3612 · 2026–27</p>
    <h1>Statistical Machine Learning</h1>
    <p class="course-instructor">Instructor: <strong>Prof. Lequan Yu</strong></p>
    <p class="course-intro">
      Explore the course through lectures, guided tutorials and interactive demonstrations.
    </p>
    <section
      v-for="section in courseSections"
      :key="section.id"
      class="home-section"
      :aria-labelledby="`home-${section.id}`"
    >
      <h2 :id="`home-${section.id}`">
        <a :href="`#/${section.id}`">{{ section.title }}</a>
      </h2>
      <p class="section-description">{{ section.description }}</p>
      <p v-if="!section.items.length" class="muted">Materials coming soon.</p>
      <ul v-else class="home-materials">
        <li v-for="item in section.items" :key="item.id">
          <a class="material-title" :href="item.href"
            >{{ item.title }} <span aria-hidden="true">→</span></a
          >
          <p>{{ item.description }}</p>
        </li>
      </ul>
    </section>
  </section>
</template>
