<script setup lang="ts">
import type { Lesson } from '../tutorials'
defineProps<{ lesson: Lesson }>()
</script>
<template>
  <article class="tutorial-overview">
    <section class="overview-intro">
      <h2>The task</h2>
      <p class="lede">{{ lesson.overview.task }}</p>
      <p>{{ lesson.overview.motivation }}</p>
    </section>
    <section>
      <h2>How the pieces fit together</h2>
      <ol class="overview-route">
        <li v-for="(stage, index) in lesson.overview.stages" :key="stage.title">
          <span class="overview-stage-number">{{ String(index + 1).padStart(2, '0') }}</span>
          <div>
            <h3>{{ stage.title }}</h3>
            <p>{{ stage.description }}</p>
            <div class="overview-chapter-links">
              <a v-for="id in stage.chapters" :key="id" :href="`#/${lesson.id}/${id}`">
                {{ lesson.chapters.find((chapter) => chapter.id === id)?.title }} →
              </a>
            </div>
          </div>
        </li>
      </ol>
    </section>
    <section>
      <h2>Learning objectives</h2>
      <p>By the end of this tutorial, you should be able to:</p>
      <ul class="overview-objectives">
        <li v-for="objective in lesson.overview.objectives" :key="objective">{{ objective }}</li>
      </ul>
    </section>
    <section class="overview-preparation">
      <div>
        <h2>Before you start</h2>
        <p>{{ lesson.overview.prerequisites }}</p>
      </div>
      <div>
        <h2>Your finished work</h2>
        <p>{{ lesson.overview.outcome }}</p>
      </div>
    </section>
    <p class="overview-format">
      Explore the ideas and run small Python experiments here. Use the companion notebook to keep
      your code, comparisons and reasoning together.
    </p>
    <a class="button primary" :href="`#/${lesson.id}/${lesson.chapters[0]!.id}`"
      >Begin: {{ lesson.chapters[0]!.title }} →</a
    >
  </article>
</template>
