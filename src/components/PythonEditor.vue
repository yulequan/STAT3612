<script setup lang="ts">
import { onMounted, onUnmounted, ref, watch } from 'vue'
import { EditorView, basicSetup } from 'codemirror'
import { python } from '@codemirror/lang-python'
const props = defineProps<{ modelValue: string }>()
const emit = defineEmits<{ 'update:modelValue': [value: string] }>()
const host = ref<HTMLElement>()
let view: EditorView | undefined
onMounted(() => {
  view = new EditorView({
    parent: host.value,
    doc: props.modelValue,
    extensions: [
      basicSetup,
      python(),
      EditorView.lineWrapping,
      EditorView.contentAttributes.of({ 'aria-label': 'Editable Python experiment' }),
      EditorView.updateListener.of((update) => {
        if (update.docChanged) emit('update:modelValue', update.state.doc.toString())
      }),
    ],
  })
})
watch(
  () => props.modelValue,
  (value) => {
    if (view && value !== view.state.doc.toString())
      view.dispatch({ changes: { from: 0, to: view.state.doc.length, insert: value } })
  },
)
onUnmounted(() => view?.destroy())
</script>
<template><div ref="host" class="python-editor" /></template>
