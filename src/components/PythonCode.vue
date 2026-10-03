<script setup lang="ts">
import { computed, ref } from 'vue'
import hljs from 'highlight.js/lib/core'
import python from 'highlight.js/lib/languages/python'
hljs.registerLanguage('python', python)
const props = withDefaults(
  defineProps<{ code: string; title?: string; activeLine?: number; selectable?: boolean }>(),
  { title: 'Python', activeLine: 0, selectable: false },
)
const emit = defineEmits<{ select: [line: number] }>()
const lines = computed(() =>
  hljs.highlight(props.code.trimEnd(), { language: 'python' }).value.split('\n'),
)
const copied = ref(false)
async function copy() {
  try {
    await navigator.clipboard.writeText(props.code)
    copied.value = true
  } catch {
    copied.value = false
  }
}
</script>
<template>
  <div class="python-code">
    <div class="code-toolbar">
      <span>{{ title }}</span
      ><button @click="copy">{{ copied ? 'Copied' : 'Copy code' }}</button>
    </div>
    <pre><code><template v-for="(line, i) in lines" :key="i"><button v-if="selectable" class="code-line" :class="{ 'line-active': activeLine === i + 1 }" :aria-label="`Inspect Python line ${i + 1}`" :aria-current="activeLine === i + 1 ? 'step' : undefined" @click="emit('select', i + 1)"><span class="line-number" aria-hidden="true">{{ i + 1 }}</span><span v-html="line || ' '" /></button><span v-else class="code-line" :class="{ 'line-active': activeLine === i + 1 }"><span class="line-number" aria-hidden="true">{{ i + 1 }}</span><span v-html="line || ' '" /></span></template></code></pre>
  </div>
</template>
