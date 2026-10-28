<script setup lang="ts">
import { computed } from 'vue'

// Render only inline code markup; all text remains escaped by Vue.
const props = defineProps<{ text: string | number }>()
const parts = computed(() => String(props.text).split(/(`[^`]+`)/g))
</script>

<template>
  <template v-for="(part, i) in parts" :key="i">
    <code v-if="part.startsWith('`') && part.endsWith('`')">{{ part.slice(1, -1) }}</code>
    <template v-else>{{ part }}</template>
  </template>
</template>

<style scoped>
code {
  font-family: var(--mono, 'SFMono-Regular', Consolas, monospace);
  font-size: 0.88em;
  padding: 0.12em 0.3em;
  border-radius: 3px;
  background: #eef2f5;
  overflow-wrap: anywhere;
  white-space: break-spaces;
}
</style>
