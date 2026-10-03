<script setup lang="ts">
import type { courseSections } from '../course'
defineProps<{ section: (typeof courseSections)[number] }>()
</script>
<template>
  <section class="course-index">
    <a class="back-home" href="#/">← Course home</a>
    <h1>{{ section.title }}</h1>
    <p>{{ section.description }}</p>
    <ul v-if="section.items.length" class="tutorial-list">
      <li v-for="(item, index) in section.items" :key="item.id">
        <a :href="item.href">
          <span class="tutorial-list-number">{{ String(index + 1).padStart(2, '0') }}</span>
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
      <a href="#/tutorials">Browse tutorials →</a>
    </div>
  </section>
</template>
