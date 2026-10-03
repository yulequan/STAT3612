<script setup lang="ts">
import { onBeforeUnmount, ref } from 'vue'
import type { Demo } from '../course'
defineProps<{ demo: Demo }>()
const base = import.meta.env.BASE_URL
const frame = ref<HTMLIFrameElement>()
const height = ref(900)
let observer: ResizeObserver | undefined

function fitContent() {
  observer?.disconnect()
  // Same-origin HTML stays independent, while the outer course page owns scrolling.
  const app = frame.value?.contentDocument?.querySelector<HTMLElement>('.app')
  if (!app) return
  const resize = () => {
    height.value = Math.ceil(app.offsetTop + app.offsetHeight) + 2
  }
  observer = new ResizeObserver(resize)
  observer.observe(app)
  resize()
}
onBeforeUnmount(() => observer?.disconnect())
</script>
<template>
  <section class="demo-page" :aria-label="demo.title">
    <div class="demo-toolbar">
      <div class="demo-breadcrumb" aria-label="Breadcrumb">
        <a href="#/">Course</a><span aria-hidden="true"> / </span> <a href="#/demos">Demos</a
        ><span aria-hidden="true"> / </span>
        <span>{{ demo.title }}</span>
      </div>
      <a :href="`${base}${demo.file}`" target="_blank" rel="noopener">Open standalone ↗</a>
    </div>
    <iframe
      ref="frame"
      class="demo-frame"
      :src="`${base}${demo.file}`"
      :title="demo.title"
      :style="{ height: `${height}px` }"
      @load="fitContent"
    ></iframe>
  </section>
</template>
