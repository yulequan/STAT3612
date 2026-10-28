<script setup lang="ts">
import { computed } from 'vue'

type Grid = { x: number[]; y: number[]; z: number[][] }
type Point = { x: number; y: number; label: number; split?: string }
type Line = { name: string; x1: number; y1: number; x2: number; y2: number; dashed?: boolean }
type Plot = {
  bounds: number[]
  grid?: Grid | null
  points: Point[]
  support?: Point[]
  lines?: Line[]
}
const props = defineProps<{
  plot: Plot
  title: string
  xLabel?: string
  yLabel?: string
  note?: string
}>()

let uid = 0
const clip = `boundary-clip-${uid++}`
const left = 62
const top = 24
const width = 580
const height = 330
const bottom = top + height
const right = left + width
const bounds = computed(() => {
  if (props.plot.bounds?.length === 4) return props.plot.bounds
  const xs = props.plot.points.map((p) => p.x)
  const ys = props.plot.points.map((p) => p.y)
  return [Math.min(...xs), Math.max(...xs), Math.min(...ys), Math.max(...ys)]
})
const x = (v: number) =>
  left + ((v - bounds.value[0]!) / (bounds.value[1]! - bounds.value[0]!)) * width
const y = (v: number) =>
  bottom - ((v - bounds.value[2]!) / (bounds.value[3]! - bounds.value[2]!)) * height
const ticks = [0, 1, 2, 3, 4].map((i) => i / 4)
const cells = computed(() => {
  const grid = props.plot.grid
  if (!grid) return []
  const nx = grid.x.length,
    ny = grid.y.length
  const dx = width / Math.max(1, nx - 1),
    dy = height / Math.max(1, ny - 1)
  const out: { x: number; y: number; w: number; h: number; fill: string }[] = []
  for (let j = 0; j < ny; j++) {
    for (let i = 0; i < nx; i++) {
      const value = grid.z[j]?.[i] ?? 0
      const alpha = 0.08 + 0.3 * Math.min(1, Math.abs(value))
      out.push({
        x: x(grid.x[i]!) - dx / 2,
        y: y(grid.y[j]!) - dy / 2,
        w: dx,
        h: dy,
        fill: `rgba(${value >= 0 ? '170, 97, 61' : '69, 101, 126'}, ${alpha.toFixed(3)})`,
      })
    }
  }
  return out
})
const support = computed(() => props.plot.support ?? [])
const lines = computed(() => props.plot.lines ?? [])
const zeroY = computed(() => (bounds.value[2]! < 0 && bounds.value[3]! > 0 ? y(0) : null))
const fmt = (v: number) => (Math.abs(v) >= 10 ? v.toFixed(0) : v.toFixed(2))
</script>

<template>
  <figure class="boundary-figure">
    <svg viewBox="0 0 680 430" role="img" :aria-label="title">
      <defs>
        <clipPath :id="clip">
          <rect :x="left" :y="top" :width="width" :height="height" />
        </clipPath>
      </defs>
      <rect :x="left" :y="top" :width="width" :height="height" fill="#fbfcfd" />
      <g v-for="t in ticks" :key="`grid-${t}`">
        <line
          :x1="left + t * width"
          :x2="left + t * width"
          :y1="top"
          :y2="bottom"
          stroke="#e2e7eb"
        />
        <line
          :x1="left"
          :x2="right"
          :y1="bottom - t * height"
          :y2="bottom - t * height"
          stroke="#e2e7eb"
        />
        <text :x="left + t * width" :y="bottom + 20" text-anchor="middle">
          {{ fmt(bounds[0]! + t * (bounds[1]! - bounds[0]!)) }}
        </text>
        <text :x="left - 10" :y="bottom - t * height + 4" text-anchor="end">
          {{ fmt(bounds[2]! + t * (bounds[3]! - bounds[2]!)) }}
        </text>
      </g>
      <g :clip-path="`url(#${clip})`">
        <rect
          v-for="(cell, i) in cells"
          :key="`cell-${i}`"
          :x="cell.x"
          :y="cell.y"
          :width="cell.w"
          :height="cell.h"
          :fill="cell.fill"
          shape-rendering="crispEdges"
        />
        <line
          v-if="zeroY !== null"
          :x1="left"
          :x2="right"
          :y1="zeroY"
          :y2="zeroY"
          stroke="#84929c"
          stroke-dasharray="4 4"
        />
        <circle
          v-for="(point, i) in plot.points"
          :key="`point-${i}`"
          :cx="x(point.x)"
          :cy="y(point.y)"
          :r="point.split === 'validation' ? 3.8 : 2.7"
          :fill="point.label === 1 ? '#aa613d' : '#45657e'"
          :fill-opacity="point.split === 'validation' ? 0.62 : 0.5"
          :stroke="point.split === 'validation' ? '#fff' : 'none'"
          stroke-width="0.9"
        />
        <circle
          v-for="(point, i) in support"
          :key="`support-${i}`"
          :cx="x(point.x)"
          :cy="y(point.y)"
          r="6.8"
          fill="none"
          stroke="#202e3a"
          stroke-width="1.6"
        />
        <line
          v-for="line in lines"
          :key="line.name"
          :x1="x(line.x1)"
          :y1="y(line.y1)"
          :x2="x(line.x2)"
          :y2="y(line.y2)"
          stroke="#202e3a"
          :stroke-dasharray="line.dashed ? '7 5' : undefined"
          stroke-width="1.8"
        />
      </g>
      <text :x="left + width / 2" y="414" text-anchor="middle" class="axis-label">
        {{ xLabel || 'x1' }}
      </text>
      <text
        x="16"
        :y="top + height / 2"
        text-anchor="middle"
        class="axis-label"
        transform="rotate(-90 16 189)"
      >
        {{ yLabel || 'x2' }}
      </text>
    </svg>
    <figcaption>
      <span class="key"><i class="dot class0" />Class 0</span>
      <span class="key"><i class="dot class1" />Class 1</span>
      <span class="key"><i class="dot train" />Training</span>
      <span class="key"><i class="dot validation" />Validation</span>
      <span v-if="support.length" class="key"><i class="ring" />Support vector</span>
      <span v-for="line in lines" :key="line.name" class="key"
        ><i class="line" :class="{ dashed: line.dashed }" />{{ line.name }}</span
      >
    </figcaption>
    <p v-if="note" class="plot-note">{{ note }}</p>
  </figure>
</template>

<style scoped>
.boundary-figure {
  margin: 18px 0 10px;
  max-width: 100%;
}
.boundary-figure svg {
  display: block;
  width: 100%;
  background: #fbfcfd;
  border: 1px solid var(--line);
  border-radius: 4px;
}
.boundary-figure text {
  font: 11px system-ui;
  fill: #65717c;
}
.boundary-figure .axis-label {
  font-size: 12px;
  fill: #50504d;
}
.boundary-figure figcaption {
  display: flex;
  flex-wrap: wrap;
  gap: 8px 18px;
  margin-top: 10px;
  font-size: 0.72rem;
  color: var(--muted);
}
.key {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}
.dot {
  width: 9px;
  height: 9px;
  border-radius: 50%;
  display: inline-block;
}
.dot.class0 {
  background: #45657e;
}
.dot.class1 {
  background: #aa613d;
}
.dot.train {
  background: #65717c;
}
.dot.validation {
  background: #fff;
  border: 1px solid #65717c;
}
.ring {
  width: 13px;
  height: 13px;
  border: 1.6px solid #202e3a;
  border-radius: 50%;
  display: inline-block;
}
.line {
  width: 18px;
  height: 2px;
  background: #202e3a;
  display: inline-block;
}
.line.dashed {
  background: repeating-linear-gradient(90deg, #202e3a 0 5px, transparent 5px 8px);
}
.plot-note {
  font-size: 0.74rem !important;
  color: var(--muted);
  margin: 6px 0 0;
}
</style>
