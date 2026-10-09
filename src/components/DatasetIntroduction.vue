<script setup lang="ts">
import { courseHref } from '../navigation'
import type { Lesson } from '../tutorials'
defineProps<{ dataset: NonNullable<Lesson['overview']['dataset']> }>()
</script>

<template>
  <section class="dataset-introduction" aria-label="Dataset source and real SMS records">
    <h2>{{ dataset.title }}</h2>
    <p>
      Source:
      <a :href="dataset.source" target="_blank" rel="noreferrer">UCI SMS Spam Collection ↗</a>
    </p>
    <p>{{ dataset.description }}</p>
    <p class="dataset-downloads">
      <a :href="dataset.archive">Download original UCI ZIP ↓</a>
      <a :href="courseHref(dataset.file)" download="SMSSpamCollection.txt"
        >Download SMS text file ↓</a
      >
    </p>
    <p>
      Raw data: <strong>{{ dataset.counts.total.toLocaleString('en-US') }} SMS</strong> ·
      {{ dataset.counts.ham.toLocaleString('en-US') }} ham (normal) ·
      {{ dataset.counts.spam.toLocaleString('en-US') }} spam. No header row.
    </p>
    <h3>First records, exactly as downloaded</h3>
    <div class="dataset-records" aria-label="Original SMS records">
      <div v-for="(row, i) in dataset.preview" :key="i">
        <span>{{ i + 1 }}</span>
        <code>{{ row.label }}<span class="delimiter"> ⇥ TAB </span>{{ row.text }}</code>
      </div>
    </div>
    <p>
      Read the normal conversation and the promotional offer above. Which words, numbers or
      punctuation could help distinguish their labels? A row is a complete message, not one word.
    </p>
    <p>{{ dataset.limitations }}</p>
  </section>
</template>

<style scoped>
.dataset-introduction {
  margin: 24px 0;
  min-width: 0;
}
.dataset-downloads {
  display: flex;
  flex-wrap: wrap;
  gap: 12px 24px;
}
.dataset-records {
  border: 1px solid var(--line);
  background: #f6f8f9;
  padding: 12px;
}
.dataset-records > div {
  display: flex;
  gap: 12px;
  padding: 10px 0;
  border-bottom: 1px solid var(--line);
}
.dataset-records > div:last-child {
  border-bottom: 0;
}
.dataset-records code {
  white-space: break-spaces;
  overflow-wrap: anywhere;
  min-width: 0;
  font-size: 0.85rem;
}
.delimiter {
  color: var(--accent);
  font-weight: 600;
}
</style>
