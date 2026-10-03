<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'
const props = withDefaults(
  defineProps<{
    pixels: number[]
    label: string
    signed?: boolean
    size?: number
    side?: number
    patch?: { row: number; col: number; size: number }
  }>(),
  { size: 196, signed: false, side: 28 },
)
const canvas = ref<HTMLCanvasElement>()
const hover = ref('')
function draw() {
  const context = canvas.value?.getContext('2d')
  if (!context) return
  const data = context.createImageData(props.side, props.side)
  const limit = props.signed ? Math.max(...props.pixels.map(Math.abs), 1e-12) : 1
  props.pixels.forEach((value, i) => {
    const strength = Math.min(Math.abs(value) / limit, 1)
    const color = props.signed ? (value >= 0 ? [24, 112, 88] : [193, 80, 47]) : [29, 40, 37]
    for (let j = 0; j < 3; j++) data.data[4 * i + j] = 249 * (1 - strength) + color[j] * strength
    data.data[4 * i + 3] = 255
  })
  context.putImageData(data, 0, 0)
}
function inspect(event: MouseEvent) {
  const box = canvas.value!.getBoundingClientRect()
  const x = Math.min(
    props.side - 1,
    Math.floor(((event.clientX - box.left) / box.width) * props.side),
  )
  const y = Math.min(
    props.side - 1,
    Math.floor(((event.clientY - box.top) / box.height) * props.side),
  )
  hover.value = `row ${y}, col ${x} · x[${y * props.side + x}] = ${(props.pixels[y * props.side + x] ?? 0).toFixed(3)}`
}
onMounted(draw)
watch(() => [props.pixels, props.signed, props.side], draw, { deep: true, flush: 'post' })
</script>

<template>
  <figure class="pixel-figure">
    <div class="pixel-surface" :style="{ width: `${size}px`, height: `${size}px` }">
      <canvas
        ref="canvas"
        :width="side"
        :height="side"
        :style="{ width: `${size}px`, height: `${size}px` }"
        role="img"
        :aria-label="label"
        @mousemove="inspect"
        @mouseleave="hover = ''"
      />
      <svg v-if="patch" class="patch-overlay" :viewBox="`0 0 ${side} ${side}`" aria-hidden="true">
        <rect
          :x="patch.col"
          :y="patch.row"
          :width="patch.size"
          :height="patch.size"
          fill="#1b365d22"
          stroke="#1b365d"
          stroke-width=".3"
        />
      </svg>
    </div>
    <figcaption>{{ label }}</figcaption>
    <small v-if="size > 100" class="pixel-inspect">{{
      hover || (signed ? 'green: positive · orange: negative' : 'Hover to inspect a pixel')
    }}</small>
  </figure>
</template>
