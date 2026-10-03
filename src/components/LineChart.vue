<script setup lang="ts">
import { computed } from 'vue'
const props = defineProps<{
  series: { name: string; values: number[]; color: string }[]
  xLabel?: string
  yLabel: string
  xStart?: number
  xEnd?: number
}>()
const finite = computed(() => props.series.flatMap((s) => s.values).filter(Number.isFinite))
const lower = computed(() => Math.min(0, ...finite.value))
const upper = computed(() => Math.max(0.01, ...finite.value) * 1.08)
const xMax = computed(
  () => props.xEnd ?? Math.max(1, ...props.series.map((s) => s.values.length - 1)),
)
function path(values: number[]) {
  return values
    .map(
      (v, i) =>
        `${i ? 'L' : 'M'}${54 + (i / Math.max(1, values.length - 1)) * 530},${228 - ((v - lower.value) / (upper.value - lower.value)) * 202}`,
    )
    .join(' ')
}
const fmt = (value: number) => (Math.abs(value) > 999 ? value.toExponential(1) : value.toFixed(2))
</script>

<template>
  <figure class="chart">
    <svg viewBox="0 0 610 282" role="img" :aria-label="`${yLabel} versus ${xLabel || 'epoch'}`">
      <g v-for="i in [0, 1, 2, 3, 4]" :key="i">
        <line x1="54" x2="584" :y1="228 - i * 50.5" :y2="228 - i * 50.5" stroke="#e2e7e1" />
        <text x="46" :y="232 - i * 50.5" text-anchor="end">
          {{ fmt(lower + ((upper - lower) * i) / 4) }}
        </text>
      </g>
      <path
        v-for="line in series"
        :key="line.name"
        :d="path(line.values)"
        :stroke="line.color"
        fill="none"
        stroke-width="2.8"
      />
      <text x="54" y="248">{{ xStart ?? 0 }}</text>
      <text x="584" y="248" text-anchor="end">{{ xMax }}</text>
      <text x="320" y="273" text-anchor="middle">{{ xLabel || 'epoch' }}</text>
      <text x="54" y="15">{{ yLabel }}</text>
    </svg>
    <figcaption class="legend">
      <span v-for="line in series" :key="line.name"
        ><i :style="{ background: line.color }" />{{ line.name }}</span
      >
    </figcaption>
  </figure>
</template>
