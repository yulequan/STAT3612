<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import MathText from '../../components/MathText.vue'
import PythonCode from '../../components/PythonCode.vue'
import PixelImage from '../../components/PixelImage.vue'
type Snapshot = { line: number; values: Record<string, number | number[]> }
const props = defineProps<{
  code: string
  result?: { trace: Snapshot[]; pixels: number[]; after: number; label: number }
  lr: number
}>()
const selected = ref(0)
const feature = ref(350)
watch(
  () => props.result,
  (result) => {
    selected.value = 0
    if (result) feature.value = result.pixels.indexOf(Math.max(...result.pixels))
  },
  { immediate: true },
)
const snapshot = computed(() => props.result?.trace[selected.value])
const values = computed(() => snapshot.value?.values ?? {})
const steps: Record<number, { title: string; explanation: string; tex: string }> = {
  2: {
    title: 'Turn the inputs into scores',
    explanation:
      'The matrix product sums pixel contributions. Zero initial weights and bias give a score of zero for every example.',
    tex: '\\mathbf{z}=X\\mathbf{w}+b',
  },
  3: {
    title: 'Map scores to probabilities',
    explanation:
      'The sigmoid maps any real score into (0, 1). These are probabilities of class 1: the digit 8.',
    tex: '\\mathbf{p}=\\sigma(\\mathbf{z}),\\qquad \\sigma(z)=\\frac{1}{1+e^{-z}}',
  },
  4: {
    title: 'Compare prediction with target',
    explanation:
      'For cross-entropy with a sigmoid output, the derivative with respect to the score simplifies to p − y. Its sign tells us how the score should change.',
    tex: '\\frac{\\partial\\ell}{\\partial z}=p-y',
  },
  5: {
    title: 'Assign the error to the weights',
    explanation:
      'Multiply each input by its residual, then average across the batch. A zero-valued pixel contributes zero to this update.',
    tex: '\\nabla_{\\mathbf{w}}L=\\frac{1}{m}X^\\top(\\mathbf{p}-\\mathbf{y})',
  },
  6: {
    title: 'Compute the bias gradient',
    explanation:
      'The bias affects every score with derivative 1. Its gradient is the average residual, with no pixel multiplier.',
    tex: '\\frac{\\partial L}{\\partial b}=\\frac{1}{m}\\sum_{i=1}^m(p_i-y_i)',
  },
  7: {
    title: 'Move the weights against the gradient',
    explanation:
      'The learning rate sets the distance. Subtracting a negative gradient increases the corresponding weight.',
    tex: '\\mathbf{w}_{\\mathrm{new}}=\\mathbf{w}-\\eta\\nabla_{\\mathbf{w}}L',
  },
  8: {
    title: 'Update the bias as well',
    explanation:
      'The bias is a learnable parameter too. The two updates use gradients computed at the same original parameter values.',
    tex: 'b_{\\mathrm{new}}=b-\\eta\\frac{\\partial L}{\\partial b}',
  },
  9: {
    title: 'Return the new parameters',
    explanation:
      'One update is complete. Evaluate the same image again to see the effect; generalisation requires other examples.',
    tex: '(\\mathbf{w},b)\\leftarrow(\\mathbf{w}_{\\mathrm{new}},b_{\\mathrm{new}})',
  },
}
const explanation = computed(() => steps[snapshot.value?.line ?? 2]!)
const array = (key: string) =>
  Array.isArray(values.value[key]) ? (values.value[key] as number[]) : undefined
const scalar = (key: string) => {
  const v = values.value[key]
  return Array.isArray(v) ? v[0] : v
}
const fmt = (value: number | undefined) =>
  value === undefined ? 'not computed yet' : value.toFixed(4)
function selectLine(line: number) {
  const index = props.result?.trace.findIndex((s) => s.line === line)
  if (index !== undefined && index >= 0) selected.value = index
}
</script>
<template>
  <section class="step-explorer" aria-label="Step through the Python update">
    <div class="section-caption">
      <span class="eyebrow">FOLLOW THE EXECUTION</span>
      <h2>One update, line by line.</h2>
      <p>
        These are intermediate values captured from the actual Python training function. Choose a
        line or move through the trace. Changing the image or learning rate recomputes it.
      </p>
    </div>
    <div class="step-layout">
      <PythonCode
        :code="code"
        title="experiment.py · step()"
        :active-line="snapshot?.line"
        selectable
        @select="selectLine"
      />
      <div class="step-observation">
        <div class="step-controls">
          <button :disabled="!result || selected === 0" @click="selected--">← Previous step</button
          ><span>{{ result ? selected + 1 : 0 }} / {{ result?.trace.length ?? 8 }}</span
          ><button :disabled="!result || selected === result.trace.length - 1" @click="selected++">
            Next step →
          </button>
        </div>
        <h3>{{ explanation.title }}</h3>
        <MathText :tex="explanation.tex" />
        <p>{{ explanation.explanation }}</p>
        <div class="variable-grid">
          <div>
            <span>score z</span><code>{{ fmt(scalar('z')) }}</code>
          </div>
          <div>
            <span>probability p</span><code>{{ fmt(scalar('p')) }}</code>
          </div>
          <div>
            <span>residual p − y</span><code>{{ fmt(scalar('residual')) }}</code>
          </div>
          <div>
            <span>bias gradient</span><code>{{ fmt(scalar('db')) }}</code>
          </div>
        </div>
        <p v-if="snapshot?.line === 9 && result" class="step-result">
          After this update: <strong>p(8) = {{ result.after.toFixed(4) }}</strong> for a true
          {{ result.label === 1 ? '8' : '3' }}.
        </p>
      </div>
    </div>
    <div v-if="result" class="feature-inspector">
      <label
        >Inspect pixel index j<input v-model.number="feature" type="range" min="0" max="783"
      /></label>
      <div>
        <span>x[{{ feature }}]</span><strong>{{ result.pixels[feature]?.toFixed(4) }}</strong>
      </div>
      <div>
        <span>∂L / ∂w[{{ feature }}]</span><strong>{{ fmt(array('dw')?.[feature]) }}</strong>
      </div>
      <div>
        <span>new w[{{ feature }}]</span><strong>{{ fmt(array('w_new')?.[feature]) }}</strong>
      </div>
    </div>
    <div v-if="array('dw') || array('w_new')" class="trace-images">
      <PixelImage
        v-if="array('dw')"
        :pixels="array('dw')!"
        label="Gradient from this executed line"
        signed
        :size="140"
      /><PixelImage
        v-if="array('w_new')"
        :pixels="array('w_new')!"
        label="Updated weights from this executed line"
        signed
        :size="140"
      />
      <p>
        The gradient and the weight update have opposite signs. The colour ranges are independently
        scaled; inspect the numbers to compare magnitudes.
      </p>
    </div>
  </section>
</template>
