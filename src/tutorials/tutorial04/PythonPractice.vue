<script setup lang="ts">
import { ref, watch } from 'vue'
import PythonEditor from '../../components/PythonEditor.vue'
import type { LearningSection } from './learning'
const props = defineProps<{
  chapter: string
  section: LearningSection
  ready: boolean
  busy: boolean
  output?: { stdout: string; error: string | null }
  running: boolean
}>()
const emit = defineEmits<{ run: [code: string]; stop: [] }>()
const drafts: Record<string, string> = {}
const downloadLink = `${import.meta.env.BASE_URL}tutorials/tutorial04/student.zip`
const code = ref(props.section.starter)
watch(
  () => props.chapter,
  (current, old) => {
    drafts[old] = code.value
    code.value = drafts[current] ?? props.section.starter
  },
)
</script>
<template>
  <section id="practice" class="python-practice">
    <div class="section-label"><span>04</span> TRY IT YOURSELF</div>
    <h2>A small experiment. Your next decision.</h2>
    <p class="practice-challenge">{{ section.challenge }}</p>
    <div class="editor-toolbar">
      <span>Python · editable experiment</span
      ><button :disabled="running" @click="code = section.starter">Reset example</button>
    </div>
    <PythonEditor v-model="code" />
    <div class="editor-actions">
      <button class="primary" :disabled="!ready || busy" @click="emit('run', code)">
        {{ running ? 'Running Python…' : 'Run Python →' }}</button
      ><button v-if="running" @click="emit('stop')">Stop and reset Python</button
      ><span>Fresh training / validation arrays on each run. No test data is provided here.</span>
    </div>
    <div v-if="output" class="python-output" aria-label="Python output">
      <span class="eyebrow">OUTPUT</span>
      <pre>{{
        output.stdout || (output.error ? '' : 'Finished. Use print(...) to inspect a value.')
      }}</pre>
      <p v-if="output.error" role="alert" class="execution-error">{{ output.error }}</p>
    </div>
    <details class="available-variables">
      <summary>Available in this experiment</summary>
      <p>
        <code>np</code>, <code>images</code>, <code>X_train</code>, <code>y_train</code>,
        <code>X_val</code>, <code>y_val</code>, and the tutorial’s functions: <code>sigmoid</code>,
        <code>loss</code>, <code>gradient</code>, <code>step</code>, <code>train</code>,
        <code>metrics</code>, <code>transform</code>, <code>features</code>,
        <code>convolution_map</code>. Changes to these arrays do not change the classroom model.
      </p>
    </details>
    <div class="notebook-bridge">
      <div>
        <span class="eyebrow">CONTINUE IN YOUR NOTEBOOK</span>
        <h3>{{ section.notebook }}</h3>
        <p>
          Keep your prediction, change one decision, and explain the result. The notebook gives you
          the complete dataset and editable implementation.
        </p>
      </div>
      <a :href="downloadLink" download>Download the lab ↗</a>
    </div>
  </section>
</template>
