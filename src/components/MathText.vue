<script setup lang="ts">
import { computed } from 'vue'
import katex from 'katex'
const props = withDefaults(defineProps<{ tex: string; inline?: boolean }>(), { inline: false })
const html = computed(() =>
  katex.renderToString(props.tex, {
    displayMode: !props.inline,
    throwOnError: false,
    trust: false,
    output: 'htmlAndMathml',
  }),
)
</script>
<template><span :class="inline ? 'math-inline' : 'math-display'" v-html="html" /></template>
