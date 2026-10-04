<script setup lang="ts">
import { computed } from 'vue'
type Point = { x: number; y: number; label?: number }
const props = defineProps<{
  title: string
  xLabel: string
  yLabel: string
  lines?: { name: string; color: string; points: number[][]; dashed?: boolean }[]
  points?: Point[]
  bounds?: number[]
}>()
const bounds = computed(() => {
  if (props.bounds) return props.bounds
  const points = [
    ...(props.points ?? []).map((p) => [p.x, p.y]),
    ...(props.lines ?? []).flatMap((l) => l.points),
  ]
  const xs = points.map((p) => p[0]!),
    ys = points.map((p) => p[1]!)
  const a = Math.min(0, ...xs),
    b = Math.max(1, ...xs),
    c = Math.min(0, ...ys),
    d = Math.max(1, ...ys)
  return [
    a < 0 ? a - (b - a) * 0.04 : 0,
    b + (b - a) * 0.04,
    c < 0 ? c - (d - c) * 0.08 : 0,
    d + (d - c) * 0.08,
  ]
})
const x = (v: number) => 62 + ((v - bounds.value[0]!) / (bounds.value[1]! - bounds.value[0]!)) * 490
const y = (v: number) =>
  230 - ((v - bounds.value[2]!) / (bounds.value[3]! - bounds.value[2]!)) * 192
const path = (points: number[][]) =>
  points.map((p, i) => `${i ? 'L' : 'M'}${x(p[0]!)},${y(p[1]!)}`).join(' ')
</script>
<template>
  <figure class="spam-plot">
    <svg viewBox="0 0 600 290" role="img" :aria-label="title">
      <defs>
        <clipPath :id="`clip-${title.replace(/\W/g, '')}`">
          <rect x="62" y="38" width="490" height="192" />
        </clipPath>
      </defs>
      <g v-for="i in [0, 1, 2, 3, 4]" :key="i">
        <line x1="62" x2="552" :y1="230 - i * 48" :y2="230 - i * 48" stroke="#e2e7eb" />
        <text x="54" :y="234 - i * 48" text-anchor="end">
          {{ (bounds[2]! + (i / 4) * (bounds[3]! - bounds[2]!)).toFixed(2) }}
        </text>
        <text :x="62 + i * 122.5" y="250" text-anchor="middle">
          {{ (bounds[0]! + (i / 4) * (bounds[1]! - bounds[0]!)).toFixed(1) }}
        </text>
      </g>
      <g :clip-path="`url(#clip-${title.replace(/\W/g, '')})`">
        <line
          v-if="bounds[2]! < 0"
          x1="62"
          x2="552"
          :y1="y(0)"
          :y2="y(0)"
          stroke="#84929c"
          stroke-dasharray="4 4"
        />
        <circle
          v-for="(p, i) in points"
          :key="i"
          :cx="x(p.x)"
          :cy="y(p.y)"
          r="3"
          :fill="p.label === 1 ? '#aa613d' : '#45657e'"
          opacity=".48"
        />
        <path
          v-for="line in lines"
          :key="line.name"
          :d="path(line.points)"
          :stroke="line.color"
          fill="none"
          stroke-width="2.5"
          :stroke-dasharray="line.dashed ? '6 4' : undefined"
        />
      </g>
      <text x="62" y="20">{{ yLabel }}</text>
      <text x="306" y="280" text-anchor="middle">{{ xLabel }}</text>
    </svg>
    <figcaption>
      {{ title
      }}<span v-for="line in lines" :key="line.name" class="plot-key"
        ><i :style="{ background: line.color }" />{{ line.name }}</span
      >
    </figcaption>
  </figure>
</template>
<style scoped>
.spam-plot {
  margin: 18px 0;
  max-width: 100%;
}
.spam-plot svg {
  width: 100%;
  display: block;
}
.spam-plot text {
  font: 11px system-ui;
  fill: #65717c;
}
.spam-plot figcaption {
  font-size: 0.74rem;
  color: var(--muted);
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}
.plot-key {
  display: inline-flex;
  gap: 5px;
  align-items: center;
}
.plot-key i {
  width: 13px;
  height: 3px;
  display: inline-block;
}
</style>
