<script setup lang="ts">
import MathText from '../../components/MathText.vue'
import type { LearningSection } from './learning'
defineProps<{ section: LearningSection }>()
</script>
<template>
  <section id="concept" class="chapter-theory">
    <div class="section-label"><span>01</span> UNDERSTAND THE IDEA</div>
    <h2>{{ section.title }}</h2>
    <div class="theory-paragraphs">
      <p v-for="paragraph in section.paragraphs" :key="paragraph">{{ paragraph }}</p>
    </div>
    <div class="equation-card">
      <MathText :tex="section.equation" />
      <dl class="notation-list">
        <div v-for="[symbol, meaning] in section.notation" :key="symbol">
          <dt><MathText :tex="symbol" inline /></dt>
          <dd>{{ meaning }}</dd>
        </div>
      </dl>
    </div>
    <aside class="concept-note">
      <span>Keep this distinction</span>
      <p>{{ section.insight }}</p>
    </aside>
  </section>
</template>
