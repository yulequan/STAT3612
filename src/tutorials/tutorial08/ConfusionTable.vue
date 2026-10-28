<script setup lang="ts">
import { computed } from 'vue'
const props = defineProps<{ matrix: number[][]; label: string }>()
const max = computed(() => Math.max(1, ...props.matrix.flat()))
const cells = [
  [
    { name: 'TN', meaning: 'class 0 correct', mistake: false },
    { name: 'FP', meaning: 'false class 1', mistake: true },
  ],
  [
    { name: 'FN', meaning: 'missed class 1', mistake: true },
    { name: 'TP', meaning: 'class 1 correct', mistake: false },
  ],
]
const shade = (value: number, mistake: boolean) =>
  `rgba(${mistake ? '170, 97, 61' : '69, 101, 126'}, ${0.08 + 0.45 * Math.sqrt(value / max.value)})`
</script>

<template>
  <table class="ensemble-confusion" :aria-label="label">
    <thead>
      <tr>
        <th></th>
        <th>Predicted 0</th>
        <th>Predicted 1</th>
      </tr>
    </thead>
    <tbody>
      <tr v-for="(row, i) in cells" :key="i">
        <th>Actual {{ i }}</th>
        <td
          v-for="(cell, j) in row"
          :key="j"
          :class="{ mistake: cell.mistake }"
          :style="{ background: shade(matrix[i]?.[j] ?? 0, cell.mistake) }"
        >
          <strong>{{ matrix[i]?.[j] ?? 0 }}</strong
          >{{ cell.name }} · {{ cell.meaning }}
        </td>
      </tr>
    </tbody>
  </table>
</template>

<style scoped>
.ensemble-confusion {
  border-collapse: separate;
  border-spacing: 4px;
  width: 100%;
  max-width: 560px;
  font-size: 0.73rem;
  table-layout: fixed;
  margin: 12px 0;
}
.ensemble-confusion th {
  font-weight: 600;
  color: var(--muted);
  padding: 6px;
}
.ensemble-confusion td {
  padding: 14px 8px;
  text-align: center;
  border-radius: 4px;
  overflow-wrap: anywhere;
}
.ensemble-confusion strong {
  display: block;
  font-size: 1.6rem;
  font-weight: 500;
  color: var(--ink);
}
.ensemble-confusion td.mistake strong {
  color: #8d4e2a;
}
@media (max-width: 650px) {
  .ensemble-confusion th,
  .ensemble-confusion td {
    font-size: 0.64rem;
    padding: 10px 4px;
  }
}
</style>
