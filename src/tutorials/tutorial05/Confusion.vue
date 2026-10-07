<script setup lang="ts">
import { computed } from 'vue'
// Rows: actual ham/spam; columns: predicted ham/spam. Shade by count.
const props = defineProps<{ matrix: number[][]; label: string }>()
const max = computed(() => Math.max(1, ...props.matrix.flat()))
const cells = [
  [
    { name: 'TN', meaning: 'ham delivered', mistake: false },
    { name: 'FP', meaning: 'ham blocked (false alarm)', mistake: true },
  ],
  [
    { name: 'FN', meaning: 'spam let through (miss)', mistake: true },
    { name: 'TP', meaning: 'spam caught', mistake: false },
  ],
]
const shade = (value: number, mistake: boolean) =>
  `rgba(${mistake ? '170, 97, 61' : '69, 101, 126'}, ${0.08 + 0.5 * Math.sqrt(value / max.value)})`
</script>
<template>
  <table class="decision-matrix" :aria-label="label">
    <thead>
      <tr>
        <th></th>
        <th>Predicted ham</th>
        <th>Predicted spam</th>
      </tr>
    </thead>
    <tbody>
      <tr v-for="(row, i) in cells" :key="i">
        <th>Actual {{ i ? 'spam' : 'ham' }}</th>
        <td
          v-for="(cell, j) in row"
          :key="j"
          :class="{ mistake: cell.mistake }"
          :style="{ background: shade(matrix[i]![j]!, cell.mistake) }"
        >
          <strong>{{ matrix[i]![j] }}</strong
          >{{ cell.name }} · {{ cell.meaning }}
        </td>
      </tr>
    </tbody>
  </table>
</template>
<style scoped>
.decision-matrix {
  border-collapse: separate;
  border-spacing: 4px;
  width: 100%;
  max-width: 560px;
  font-size: 0.75rem;
  table-layout: fixed;
  margin: 12px 0;
}
.decision-matrix th {
  font-weight: 600;
  color: var(--muted);
  padding: 6px;
}
.decision-matrix td {
  padding: 14px 8px;
  text-align: center;
  border-radius: 4px;
  overflow-wrap: anywhere;
  transition: background 0.15s;
}
.decision-matrix strong {
  display: block;
  font-size: 1.7rem;
  font-weight: 500;
  color: var(--ink);
}
.decision-matrix td.mistake strong {
  color: #8d4e2a;
}
@media (max-width: 650px) {
  .decision-matrix th,
  .decision-matrix td {
    font-size: 0.66rem;
    padding: 10px 4px;
  }
}
</style>
