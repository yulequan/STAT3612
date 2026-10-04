<script setup lang="ts">
import { courseHref } from '../navigation'
import { courseSections } from '../course'
</script>
<template>
  <section class="course-index course-home">
    <div class="home-hero">
      <h1>Statistical Machine Learning</h1>
      <p class="course-instructor">Instructor: <strong>Prof. Lequan Yu</strong></p>
    </div>
    <section
      v-for="section in courseSections"
      :key="section.id"
      class="home-section grid gap-6 sm:grid-cols-[180px_minmax(0,1fr)] sm:gap-10"
      :aria-labelledby="`home-${section.id}`"
    >
      <div>
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
              ><span class="material-arrow" aria-hidden="true">→</span>
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
