<script setup lang="ts">
import { courseHref } from '../navigation'
import type { courseSections } from '../course'
defineProps<{ section: (typeof courseSections)[number] }>()
</script>
<template>
  <section class="course-index">
    <h1>{{ section.title }}</h1>
    <p>{{ section.description }}</p>
    <ul v-if="section.items.length" class="tutorial-list">
      <li v-for="item in section.items" :key="item.id">
        <a :href="item.href">
          <span
            ><strong>{{ item.title }}</strong
            ><small>{{ item.description }}</small></span
          >
          <span class="tutorial-list-arrow" aria-hidden="true">→</span>
        </a>
      </li>
    </ul>
    <div v-else class="catalog-empty">
      <h2>Lecture materials are coming soon.</h2>
      <p>Visit Tutorials for guided practice or Demos for interactive examples.</p>
      <a :href="courseHref('tutorials')">Browse tutorials →</a>
    </div>
  </section>
</template>
