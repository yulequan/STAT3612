<script setup lang="ts">
import { computed, onMounted, onUnmounted, reactive, ref, watch } from 'vue'
import { createPython } from '../../runtime/python'
import MathText from '../../components/MathText.vue'
import PythonCode from '../../components/PythonCode.vue'
import PythonEditor from '../../components/PythonEditor.vue'
import LineChart from '../../components/LineChart.vue'
import { courseHref } from '../../navigation'
import curriculum from './curriculum.json'
import BoundaryPlot from './BoundaryPlot.vue'
import ConfusionTable from './ConfusionTable.vue'
import InlineText from './InlineText.vue'
import source from './experiment.py?raw'

type Metrics = {
  accuracy: number
  precision: number
  recall: number
  f1: number
  confusion: number[][]
}
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
type Curve = { n: number[]; train: number[]; validation: number[] }
type Run = {
  id: string
  kind: string
  name: string
  params: Record<string, string | number | null>
  dataset: string
  feature_names: string[]
  train: Metrics
  validation: Metrics
  plot: Plot
  nodes?: number
  leaves?: number
  actual_depth?: number
  rules?: string[]
  importance?: number[]
  oob?: number | null
  curve?: Curve
  best_n?: number
  support_count?: number
}
type Initial = {
  seed: number
  counts: Record<string, Record<string, { total: number; class0: number; class1: number }>>
  baseline: Record<string, Metrics>
  plots: Record<string, Plot>
}
type Detail = {
  row: Run
  plot: Plot
  errors: { x: number; y: number; label: number; prediction: number }[]
  metrics: Metrics
}
type Final = {
  key: string
  name: string
  reason: string
  configuration: Record<string, unknown>
  validation: Metrics
  test: Metrics
}

const props = defineProps<{ chapter: string }>()
const section = computed(
  () => curriculum.chapters.find((c) => c.id === props.chapter) ?? curriculum.chapters[0]!,
)
const runtime = createPython('tutorial08')
const { ready, status } = runtime
const initial = ref<Initial>()
const error = ref('')
const busy = ref(false)
const running = ref(false)
const operation = ref('')
const runs = reactive<Record<string, Run>>({})
const drafts = reactive<Record<string, string>>({})
const outputs = reactive<Record<string, { stdout: string; error: string | null }>>({})
const dataDataset = ref<'moons' | 'iris' | 'xor'>('moons')
const treeDepth = ref(4)
const treeLeaf = ref(1)
const forestMode = ref<'forest' | 'bagging'>('forest')
const forestTrees = ref(100)
const forestFeatures = ref('sqrt')
const boostMode = ref<'gradient' | 'adaboost'>('gradient')
const boostTrees = ref(100)
const boostLR = ref(0.1)
const marginC = ref(1)
const kernel = ref<'rbf' | 'poly' | 'linear'>('rbf')
const kernelC = ref(1)
const kernelGamma = ref(1)
const kernelDegree = ref(3)
const kernelDataset = ref<'moons' | 'xor'>('moons')
const comparison = ref<{ rows: Run[]; best: string | null }>()
const selectedKey = ref('')
const detail = ref<Detail>()
const reason = ref('')
const final = ref<Final>()
let generation = 0

const code = computed({
  get: () => drafts[props.chapter] ?? section.value.starter,
  set: (value) => {
    drafts[props.chapter] = value
  },
})
const currentRun = computed(() => runs[props.chapter])
const dataPlot = computed(() => initial.value?.plots[dataDataset.value])
const dataNames: Record<string, string> = {
  moons: 'Two moons',
  iris: 'Iris petals',
  xor: 'XOR quadrants',
}
const dataTitle = computed(() => `${dataNames[dataDataset.value]} · train + validation`)
const dataXLabel = computed(() => (dataDataset.value === 'iris' ? 'petal length (cm)' : 'x1'))
const dataYLabel = computed(() => (dataDataset.value === 'iris' ? 'petal width (cm)' : 'x2'))
const dataCounts = computed(() => initial.value?.counts[dataDataset.value])
const dataBaseline = computed(() => initial.value?.baseline[dataDataset.value])
const validationShare = computed(() => {
  const validation = dataCounts.value?.val
  return validation ? validation.class1 / validation.total : 0
})
const currentImportance = computed(() => Math.max(0.01, ...(currentRun.value?.importance ?? [])))
const curveSeries = computed(() => {
  const curve = currentRun.value?.curve
  if (!curve) return []
  return [
    { name: 'Training accuracy', color: '#45657e', values: curve.train },
    { name: 'Validation accuracy', color: '#aa613d', values: curve.validation },
  ]
})
const curveEnd = computed(() => currentRun.value?.curve?.n.at(-1) ?? 1)
const actionLabel = computed(
  () =>
    ({
      tree: 'Fit decision tree',
      forest: 'Fit ensemble',
      boosting: 'Fit boosting model',
      margins: 'Fit linear SVM',
      kernels: 'Fit kernel SVM',
    })[props.chapter] ?? 'Fit model',
)
const finalDisabled = computed(() => !reason.value.trim() || !selectedKey.value || !!final.value)
const kernelNeedsGamma = computed(() => kernel.value !== 'linear')
const kernelNeedsDegree = computed(() => kernel.value === 'poly')
const featureName = (run: Run | undefined, index: number) =>
  run?.feature_names?.[index] ?? `x${index + 1}`
const pct = (value: number) => `${(100 * value).toFixed(1)}%`
const keyOf = (row: Run) => String(row.params.key ?? '')
const splitName = (key: string) =>
  key === 'val' ? 'Validation' : key === 'train' ? 'Training' : 'Test (hidden)'
const candidateText = (row: Run) =>
  `${row.name} · train ${pct(row.train.accuracy)} · validation ${pct(row.validation.accuracy)}`

function codeFor(name: string) {
  const match = source.match(
    new RegExp(`^def ${name}\\([\\s\\S]*?(?=^def |^class |$(?![\\s\\S]))`, 'm'),
  )
  return match?.[0].trim() ?? ''
}
async function act<T>(
  name: string,
  action: string,
  params: Record<string, unknown> = {},
): Promise<T | undefined> {
  if (!ready.value || busy.value) return
  const epoch = generation
  busy.value = true
  operation.value = name
  error.value = ''
  try {
    return await runtime.request<T>(action, params)
  } catch (e) {
    if (epoch === generation) error.value = String(e)
  } finally {
    if (epoch === generation) {
      busy.value = false
      operation.value = ''
    }
  }
}
async function start() {
  generation++
  busy.value = false
  running.value = false
  error.value = ''
  operation.value = ''
  initial.value = undefined
  comparison.value = undefined
  detail.value = undefined
  final.value = undefined
  selectedKey.value = ''
  reason.value = ''
  Object.keys(runs).forEach((key) => delete runs[key])
  Object.keys(outputs).forEach((key) => delete outputs[key])
  try {
    initial.value = await runtime.start<Initial>()
  } catch (e) {
    error.value = String(e)
  }
}
async function fitCurrent() {
  const chapter = props.chapter
  let row: Run | undefined
  if (chapter === 'tree') {
    row = await act<Run>('Fitting the decision tree', 'fit_tree', {
      depth: treeDepth.value,
      min_leaf: treeLeaf.value,
    })
  } else if (chapter === 'forest') {
    row = await act<Run>('Fitting the ensemble', 'fit_forest', {
      mode: forestMode.value,
      n_estimators: forestTrees.value,
      max_features: forestFeatures.value,
    })
  } else if (chapter === 'boosting') {
    row = await act<Run>('Fitting the boosting model', 'fit_boosting', {
      mode: boostMode.value,
      n_estimators: boostTrees.value,
      learning_rate: boostLR.value,
    })
  } else if (chapter === 'margins') {
    row = await act<Run>('Fitting the linear SVM', 'fit_margin', { C: marginC.value })
  } else if (chapter === 'kernels') {
    row = await act<Run>('Fitting the kernel SVM', 'fit_kernel', {
      dataset: kernelDataset.value,
      kernel: kernel.value,
      C: kernelC.value,
      gamma: kernelGamma.value,
      degree: kernelDegree.value,
    })
  }
  if (row) runs[chapter] = row
}
async function compareModels() {
  const result = await act<{ rows: Run[]; best: string | null }>(
    'Training and validating all candidates',
    'compare',
  )
  if (!result) return
  comparison.value = result
  selectedKey.value = result.best ?? (result.rows[0] ? keyOf(result.rows[0]) : '')
  detail.value = undefined
  final.value = undefined
}
async function inspectCandidate() {
  if (!selectedKey.value) return
  const result = await act<Detail>('Inspecting validation errors', 'inspect_candidate', {
    key: selectedKey.value,
  })
  if (result) detail.value = result
}
async function finalTest() {
  const result = await act<Final>('Evaluating the frozen choice on test data', 'final_test', {
    key: selectedKey.value,
    reason: reason.value,
  })
  if (result) final.value = result
}
async function runCode() {
  const chapter = props.chapter
  running.value = true
  const output = await act<{ stdout: string; error: string | null }>(
    'Running your Python',
    'execute',
    { code: code.value },
  )
  if (output) outputs[chapter] = output
  running.value = false
}
function resetCode() {
  drafts[props.chapter] = section.value.starter
}
function exportRecord() {
  const payload = {
    seed: initial.value?.seed,
    comparison: comparison.value?.rows,
    final: final.value,
  }
  const url = URL.createObjectURL(
    new Blob([JSON.stringify(payload, null, 2)], { type: 'application/json' }),
  )
  const a = document.createElement('a')
  a.href = url
  a.download = 'tutorial08-experiment.json'
  a.click()
  URL.revokeObjectURL(url)
}
watch(
  () => props.chapter,
  () => {
    error.value = ''
    if (props.chapter !== 'compare') detail.value = undefined
  },
)
onMounted(start)
onUnmounted(() => {
  generation++
  runtime.dispose()
})
</script>

<template>
  <div class="ensemble-lesson">
    <section id="concept" class="chapter-theory">
      <div class="section-label"><span>01</span> UNDERSTAND THE IDEA</div>
      <h2>{{ section.conceptTitle }}</h2>
      <p class="concept-intro"><InlineText :text="section.idea" /></p>
      <ul class="key-points">
        <li v-for="point in section.points" :key="point"><InlineText :text="point" /></li>
      </ul>
      <div v-if="section.equation" class="equation-card">
        <h3>Formula and notation</h3>
        <MathText :tex="section.equation" />
        <dl class="notation-list">
          <div v-for="[symbol, meaning] in section.notation" :key="symbol">
            <dt><MathText :tex="symbol!" inline /></dt>
            <dd>{{ meaning }}</dd>
          </div>
        </dl>
      </div>
      <p v-for="[title, url] in section.links" :key="url" class="documentation-link">
        <a :href="url" target="_blank" rel="noreferrer">{{ title }} ↗</a>
      </p>
    </section>

    <section class="chapter-experiment" aria-label="Interactive experiment">
      <div class="section-label"><span>02</span> EXPLORE THE MECHANISM</div>
      <h2>{{ section.activityTitle }}</h2>
      <p><InlineText :text="section.experiment" /></p>
      <p v-if="!ready && !error" role="status">{{ status }}</p>
      <div v-if="error" class="execution-error" role="alert">
        {{ error }} <button @click="start">Restart Python</button>
      </div>
      <p v-if="busy" role="status">{{ operation }}…</p>

      <template v-if="chapter === 'data' && initial">
        <div class="panel">
          <div class="control-row">
            <label
              >Dataset<select v-model="dataDataset">
                <option value="moons">Two moons · nonlinear</option>
                <option value="iris">Iris petals · margin example</option>
                <option value="xor">XOR quadrants · kernel example</option>
              </select></label
            >
          </div>
          <div class="split-cards" v-if="dataCounts">
            <div v-for="split in ['train', 'val', 'test']" :key="split">
              <span>{{ splitName(split) }}</span>
              <strong>{{ dataCounts[split]!.total }}</strong>
              <small
                >class 0: {{ dataCounts[split]!.class0 }} · class 1:
                {{ dataCounts[split]!.class1 }}</small
              >
            </div>
          </div>
          <BoundaryPlot
            v-if="dataPlot"
            :plot="dataPlot"
            :title="dataTitle"
            :x-label="dataXLabel"
            :y-label="dataYLabel"
            note="Test points are not drawn. Validation points have a white outline."
          />
          <div v-if="dataBaseline" class="metric-row">
            <div>
              <span>Majority-class validation accuracy</span
              ><strong>{{ pct(dataBaseline.accuracy) }}</strong>
            </div>
            <div>
              <span>Validation class 1 share</span><strong>{{ pct(validationShare) }}</strong>
            </div>
          </div>
          <p class="muted">
            The two moons reward a curved boundary. Iris petals make a linear margin easy to
            inspect. XOR is a stress test for kernels: no straight line separates its quadrants.
          </p>
        </div>
      </template>

      <template v-if="['tree', 'forest', 'boosting', 'margins', 'kernels'].includes(chapter)">
        <div class="panel controls-panel">
          <div v-if="chapter === 'tree'" class="control-row">
            <label
              >Maximum depth<select v-model.number="treeDepth">
                <option :value="1">1 · one split</option>
                <option :value="2">2</option>
                <option :value="3">3</option>
                <option :value="4">4</option>
                <option :value="6">6</option>
                <option :value="0">Unlimited</option>
              </select></label
            >
            <label
              >Minimum rows per leaf<input
                v-model.number="treeLeaf"
                type="number"
                min="1"
                max="40"
                step="1"
            /></label>
          </div>
          <div v-if="chapter === 'forest'" class="control-row">
            <label
              >Ensemble<select v-model="forestMode">
                <option value="forest">Random forest · feature randomness</option>
                <option value="bagging">Bagged trees · rows only</option>
              </select></label
            >
            <label
              >Number of trees<select v-model.number="forestTrees">
                <option :value="10">10</option>
                <option :value="50">50</option>
                <option :value="100">100</option>
                <option :value="200">200</option>
              </select></label
            >
            <label v-if="forestMode === 'forest'"
              >Features per split<select v-model="forestFeatures">
                <option value="sqrt">√2 · random subset</option>
                <option value="all">All features</option>
              </select></label
            >
          </div>
          <div v-if="chapter === 'boosting'" class="control-row">
            <label
              >Boosting method<select v-model="boostMode">
                <option value="gradient">Gradient boosting</option>
                <option value="adaboost">AdaBoost · stumps</option>
              </select></label
            >
            <label
              >Number of trees<select v-model.number="boostTrees">
                <option :value="20">20</option>
                <option :value="50">50</option>
                <option :value="100">100</option>
                <option :value="200">200</option>
              </select></label
            >
            <label
              >Learning rate<select v-model.number="boostLR">
                <option :value="0.05">0.05</option>
                <option :value="0.1">0.1</option>
                <option :value="0.5">0.5</option>
                <option :value="1">1.0</option>
              </select></label
            >
          </div>
          <div v-if="chapter === 'margins'" class="control-row">
            <label
              >Soft-margin C<select v-model.number="marginC">
                <option :value="0.01">0.01 · wide margin</option>
                <option :value="0.1">0.1</option>
                <option :value="1">1</option>
                <option :value="10">10</option>
                <option :value="100">100 · narrow margin</option>
              </select></label
            >
          </div>
          <div v-if="chapter === 'kernels'" class="control-row">
            <label
              >Dataset<select v-model="kernelDataset">
                <option value="moons">Two moons</option>
                <option value="xor">XOR quadrants</option>
              </select></label
            >
            <label
              >Kernel<select v-model="kernel">
                <option value="linear">Linear</option>
                <option value="poly">Polynomial</option>
                <option value="rbf">RBF · Gaussian</option>
              </select></label
            >
            <label v-if="kernelNeedsGamma"
              >Gamma γ<input
                v-model.number="kernelGamma"
                type="number"
                min="0.05"
                max="20"
                step="0.1"
            /></label>
            <label v-if="kernelNeedsDegree"
              >Degree d<select v-model.number="kernelDegree">
                <option :value="2">2</option>
                <option :value="3">3</option>
                <option :value="4">4</option>
              </select></label
            >
          </div>
          <button class="primary" :disabled="!ready || busy || !!final" @click="fitCurrent">
            {{ actionLabel }}
          </button>
          <p class="muted">
            Every fit uses the same training rows. Change one setting, refit, and compare validation
            results rather than training results.
          </p>
        </div>

        <template v-if="currentRun">
          <div class="panel">
            <div class="panel-heading">
              <div>
                <span class="eyebrow">FITTED MODEL</span>
                <h3>{{ currentRun.name }}</h3>
              </div>
              <span class="pill">Validation {{ pct(currentRun.validation.accuracy) }}</span>
            </div>
            <BoundaryPlot
              :plot="currentRun.plot"
              :title="`${currentRun.name} · decision boundary`"
              :x-label="currentRun.feature_names?.[0]"
              :y-label="currentRun.feature_names?.[1]"
              note="The shaded regions show the model's class tendency; circles are training and validation rows."
            />
            <div class="metric-row">
              <div>
                <span>Training accuracy</span><strong>{{ pct(currentRun.train.accuracy) }}</strong>
              </div>
              <div>
                <span>Validation accuracy</span
                ><strong>{{ pct(currentRun.validation.accuracy) }}</strong>
              </div>
              <div>
                <span>Validation F1</span><strong>{{ pct(currentRun.validation.f1) }}</strong>
              </div>
            </div>

            <div v-if="chapter === 'tree'" class="two-col">
              <div>
                <h3>First rules in the fitted tree</h3>
                <pre class="tree-rules">{{ currentRun.rules?.join('\n') }}</pre>
                <p class="muted">
                  {{ currentRun.nodes }} nodes · {{ currentRun.leaves }} leaves · actual depth
                  {{ currentRun.actual_depth }}
                </p>
              </div>
              <div>
                <h3>Feature importance</h3>
                <div class="importance">
                  <div v-for="(value, i) in currentRun.importance" :key="i" class="importance-row">
                    <span>{{ featureName(currentRun, i) }}</span>
                    <div class="bar">
                      <i :style="{ width: `${(100 * value) / currentImportance}%` }" />
                    </div>
                    <em>{{ value.toFixed(2) }}</em>
                  </div>
                </div>
              </div>
            </div>

            <div v-if="chapter === 'forest'">
              <h3>Accuracy as trees are added</h3>
              <LineChart
                v-if="curveSeries.length"
                :series="curveSeries"
                y-label="accuracy"
                x-label="number of trees"
                :x-start="1"
                :x-end="curveEnd"
              />
              <div class="metric-row">
                <div>
                  <span>Out-of-bag score</span
                  ><strong>{{ currentRun.oob == null ? 'n/a' : pct(currentRun.oob) }}</strong>
                </div>
                <div>
                  <span>Trees in ensemble</span
                  ><strong>{{ currentRun.params.n_estimators }}</strong>
                </div>
              </div>
              <div class="importance">
                <div v-for="(value, i) in currentRun.importance" :key="i" class="importance-row">
                  <span>{{ featureName(currentRun, i) }}</span>
                  <div class="bar">
                    <i :style="{ width: `${(100 * value) / currentImportance}%` }" />
                  </div>
                  <em>{{ value.toFixed(2) }}</em>
                </div>
              </div>
            </div>

            <div v-if="chapter === 'boosting'">
              <h3>Staged validation curve</h3>
              <LineChart
                v-if="curveSeries.length"
                :series="curveSeries"
                y-label="accuracy"
                x-label="number of trees"
                :x-start="1"
                :x-end="curveEnd"
              />
              <div class="metric-row">
                <div>
                  <span>Best staged validation tree</span><strong>{{ currentRun.best_n }}</strong>
                </div>
                <div>
                  <span>Learning rate</span><strong>{{ currentRun.params.learning_rate }}</strong>
                </div>
              </div>
              <p class="muted">
                The best staged tree is the point with the highest validation accuracy in this run.
                More trees after that do not necessarily improve generalization.
              </p>
            </div>

            <div v-if="chapter === 'margins'">
              <div class="metric-row">
                <div>
                  <span>Support vectors</span><strong>{{ currentRun.support_count }}</strong>
                </div>
                <div>
                  <span>Soft-margin C</span><strong>{{ currentRun.params.C }}</strong>
                </div>
              </div>
              <p class="muted">
                Dark rings mark support vectors. Solid line: decision boundary; dashed lines: the
                two margins. Only the support vectors define this linear boundary.
              </p>
            </div>

            <div v-if="chapter === 'kernels'">
              <div class="metric-row">
                <div>
                  <span>Dataset</span><strong>{{ currentRun.dataset }}</strong>
                </div>
                <div>
                  <span>Support vectors</span><strong>{{ currentRun.support_count }}</strong>
                </div>
                <div>
                  <span>Kernel</span><strong>{{ currentRun.params.kernel }}</strong>
                </div>
              </div>
              <p class="muted">
                On XOR, try the linear kernel first, then RBF with a moderate gamma. Very large
                gamma values make the boundary local and jagged.
              </p>
            </div>
          </div>
        </template>
      </template>

      <template v-if="chapter === 'compare'">
        <div class="panel">
          <h3>One validation table for every family</h3>
          <p>
            This fits a fixed tree, bagged trees, a random forest, AdaBoost, gradient boosting and
            two SVM kernels. All use the same two-moons training and validation rows. The table is
            sorted by validation accuracy, but you should inspect the errors before choosing.
          </p>
          <button class="primary" :disabled="!ready || busy || !!final" @click="compareModels">
            Run validation comparison
          </button>
        </div>
        <template v-if="comparison">
          <div class="panel">
            <div class="table-scroll">
              <table class="ensemble-table" aria-label="Validation comparison">
                <thead>
                  <tr>
                    <th>Candidate</th>
                    <th>Train accuracy</th>
                    <th>Validation accuracy</th>
                    <th>Validation F1</th>
                    <th>Support vectors</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="row in comparison.rows" :key="row.id">
                    <th>
                      <button
                        class="candidate-button"
                        :aria-pressed="keyOf(row) === selectedKey"
                        :disabled="!!final"
                        @click="selectedKey = keyOf(row)"
                      >
                        {{ row.name }}
                      </button>
                    </th>
                    <td>{{ pct(row.train.accuracy) }}</td>
                    <td>{{ pct(row.validation.accuracy) }}</td>
                    <td>{{ pct(row.validation.f1) }}</td>
                    <td>{{ row.support_count ?? '—' }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
            <div class="control-row">
              <label
                >Selected candidate<select v-model="selectedKey" :disabled="!!final">
                  <option v-for="row in comparison.rows" :key="row.id" :value="keyOf(row)">
                    {{ candidateText(row) }}
                  </option>
                </select></label
              >
              <button :disabled="!ready || busy || !!final" @click="inspectCandidate">
                Inspect validation errors
              </button>
            </div>
            <p class="muted">
              The selected model is the one that will be frozen for the final test. Changing the
              selection after seeing test results would make the test no longer independent.
            </p>
          </div>

          <div v-if="detail && keyOf(detail.row) === selectedKey" class="panel">
            <div class="panel-heading">
              <div>
                <span class="eyebrow">VALIDATION DIAGNOSTIC</span>
                <h3>{{ detail.row.name }}</h3>
              </div>
              <span class="pill">Validation {{ pct(detail.metrics.accuracy) }}</span>
            </div>
            <BoundaryPlot
              :plot="detail.plot"
              :title="`${detail.row.name} · validation diagnostic`"
              :x-label="detail.row.feature_names?.[0]"
              :y-label="detail.row.feature_names?.[1]"
            />
            <div class="two-col">
              <div>
                <h3>Validation confusion matrix</h3>
                <ConfusionTable
                  :matrix="detail.metrics.confusion"
                  label="Selected candidate validation confusion matrix"
                />
              </div>
              <div>
                <h3>Validation errors</h3>
                <p v-if="!detail.errors.length">
                  No validation errors in this run. That is a result, not a guarantee.
                </p>
                <div v-else class="table-scroll">
                  <table class="ensemble-table" aria-label="Validation errors">
                    <thead>
                      <tr>
                        <th>True</th>
                        <th>Predicted</th>
                        <th>x1</th>
                        <th>x2</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr v-for="(item, i) in detail.errors" :key="i">
                        <th>{{ item.label }}</th>
                        <td>{{ item.prediction }}</td>
                        <td>{{ item.x.toFixed(2) }}</td>
                        <td>{{ item.y.toFixed(2) }}</td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          </div>

          <div class="panel final-panel">
            <h3>Freeze a choice, then test once</h3>
            <p>
              Write why this model is appropriate, including a tradeoff or limitation. The test
              split is evaluated only after the rationale is non-empty.
            </p>
            <label
              >Model choice rationale<textarea
                v-model="reason"
                rows="4"
                placeholder="I selected … because validation …; I accept …"
                :disabled="!!final"
              />
            </label>
            <button class="primary" :disabled="finalDisabled" @click="finalTest">
              Freeze decision and evaluate test set
            </button>
            <div v-if="final" class="final-result">
              <h3>Final test result · decision frozen</h3>
              <div class="metric-row">
                <div>
                  <span>Test accuracy</span><strong>{{ pct(final.test.accuracy) }}</strong>
                </div>
                <div>
                  <span>Test F1</span><strong>{{ pct(final.test.f1) }}</strong>
                </div>
                <div>
                  <span>Test precision</span><strong>{{ pct(final.test.precision) }}</strong>
                </div>
                <div>
                  <span>Test recall</span><strong>{{ pct(final.test.recall) }}</strong>
                </div>
              </div>
              <ConfusionTable :matrix="final.test.confusion" label="Final test confusion matrix" />
              <p class="muted">{{ final.reason }}</p>
              <button class="text-button" @click="exportRecord">Export experiment record ↓</button>
            </div>
          </div>
        </template>
      </template>
    </section>

    <section id="python" class="chapter-python">
      <div class="section-label"><span>03</span> CONNECT THE PYTHON</div>
      <h2>The idea, written as code.</h2>
      <p>
        These are the functions used by the browser experiment and included in the student notebook.
        Read the inputs and the return value before changing a setting.
      </p>
      <PythonCode
        v-for="name in section.functions"
        :key="name"
        :code="codeFor(name)"
        :title="`experiment.py · ${name}()`"
      />
    </section>

    <section id="practice" class="python-practice">
      <div class="section-label"><span>04</span> TRY IT YOURSELF</div>
      <h2>A small experiment. Your next decision.</h2>
      <p class="practice-challenge"><InlineText :text="section.experiment" /></p>
      <div class="editor-toolbar">
        <span>Python · editable experiment</span
        ><button :disabled="running" @click="resetCode">Reset example</button>
      </div>
      <PythonEditor v-model="code" />
      <div class="editor-actions">
        <button class="primary" :disabled="!ready || busy" @click="runCode">
          {{ running ? 'Running Python…' : 'Run Python →' }}</button
        ><button v-if="running" @click="start">Stop and reset Python</button
        ><span
          >Fresh training / validation arrays on each run. No test rows are provided here.</span
        >
      </div>
      <div v-if="outputs[chapter]" class="python-output" aria-label="Python output">
        <span class="eyebrow">OUTPUT</span>
        <pre>{{
          outputs[chapter]!.stdout ||
          (outputs[chapter]!.error ? '' : 'Finished. Use print(...) to inspect a value.')
        }}</pre>
        <p v-if="outputs[chapter]!.error" role="alert" class="execution-error">
          {{ outputs[chapter]!.error }}
        </p>
      </div>
      <details class="available-variables">
        <summary>Available in this experiment</summary>
        <p>
          <code>np</code>, <code>metrics</code>, <code>build_tree</code>, <code>build_forest</code>,
          <code>build_boosting</code>, <code>build_svm</code>, <code>X_train</code>,
          <code>y_train</code>, <code>X_val</code>, <code>y_val</code>, <code>X_iris_train</code>,
          <code>y_iris_train</code>, <code>X_iris_val</code>, <code>y_iris_val</code>,
          <code>X_xor_train</code>, <code>y_xor_train</code>, <code>X_xor_val</code>,
          <code>y_xor_val</code>, and <code>lab</code>. The test arrays are deliberately absent.
        </p>
      </details>
      <div class="notebook-bridge">
        <div>
          <span class="eyebrow">CONTINUE IN YOUR NOTEBOOK</span>
          <h3>{{ section.pythonTitle }}</h3>
          <p>
            Keep your prediction, change one setting, and explain the validation result. Download
            the complete notebook from the sidebar or the overview.
          </p>
        </div>
        <a class="button" :href="courseHref('tutorials/tutorial08/overview')">Open overview →</a>
      </div>
    </section>
  </div>
</template>

<style scoped>
.concept-intro {
  max-width: 880px;
}
.key-points {
  max-width: 930px;
  padding-left: 20px;
  font-size: 0.9rem;
  line-height: 1.85;
  color: #50504d;
}
.key-points li {
  margin: 11px 0;
}
.documentation-link {
  font-size: 0.8rem;
}
.split-cards {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
  margin: 18px 0 22px;
}
.split-cards > div {
  border: 1px solid var(--line);
  border-radius: 4px;
  background: #fbfcfd;
  padding: 15px;
}
.split-cards span,
.split-cards small {
  display: block;
  color: var(--muted);
  font-size: 0.7rem;
}
.split-cards strong {
  display: block;
  font-size: 1.45rem;
  font-weight: 500;
  color: var(--accent);
  margin: 4px 0;
}
.metric-row {
  display: flex;
  flex-wrap: wrap;
  gap: 18px;
  margin: 20px 0 10px;
  padding-top: 16px;
  border-top: 1px solid var(--line);
}
.metric-row > div {
  flex: 1;
  min-width: 130px;
}
.metric-row span {
  display: block;
  font-size: 0.68rem;
  color: var(--muted);
  margin-bottom: 5px;
}
.metric-row strong {
  font-size: 1.35rem;
  font-weight: 550;
  color: var(--accent);
  font-variant-numeric: tabular-nums;
}
.tree-rules {
  background: #f5f7f9;
  border: 1px solid var(--line);
  border-radius: 4px;
  padding: 12px;
  font-size: 0.72rem;
  line-height: 1.65;
  max-height: 360px;
}
.importance {
  margin: 16px 0;
}
.importance-row {
  display: grid;
  grid-template-columns: 100px minmax(0, 1fr) 48px;
  align-items: center;
  gap: 10px;
  margin: 9px 0;
  font-size: 0.74rem;
}
.importance-row > span {
  overflow-wrap: anywhere;
}
.importance-row .bar {
  height: 8px;
  background: #e7eef3;
  border-radius: 4px;
  overflow: hidden;
}
.importance-row .bar i {
  display: block;
  height: 100%;
  background: #45657e;
}
.importance-row em {
  font-style: normal;
  color: var(--muted);
  text-align: right;
  font-variant-numeric: tabular-nums;
}
.ensemble-table {
  border-collapse: collapse;
  width: 100%;
  font-size: 0.76rem;
}
.ensemble-table th,
.ensemble-table td {
  padding: 10px 12px;
  border-bottom: 1px solid var(--line);
  text-align: left;
  vertical-align: top;
}
.ensemble-table th {
  font-weight: 550;
}
.candidate-button {
  border: 0;
  background: transparent;
  color: var(--accent);
  padding: 3px 0;
  font-size: 0.76rem;
  font-weight: 600;
  text-align: left;
}
.candidate-button[aria-pressed='true'] {
  color: #202e3a;
  text-decoration: underline;
  text-underline-offset: 4px;
}
.final-panel {
  margin-top: 26px;
}
.final-result {
  margin-top: 26px;
  padding-top: 18px;
  border-top: 1px solid var(--line);
}
.ensemble-lesson textarea {
  display: block;
  width: 100%;
  border: 1px solid #d6d6d3;
  background: #fbfcfd;
  border-radius: 5px;
  color: #333333;
  padding: 9px 10px;
  font-size: 0.8rem;
  margin-top: 7px;
  resize: vertical;
}
.ensemble-lesson label {
  display: block;
  color: #50504d;
  font-size: 0.75rem;
  font-weight: 550;
  margin-bottom: 16px;
}
.ensemble-lesson button {
  margin-right: 8px;
  margin-top: 8px;
}
@media (max-width: 650px) {
  .split-cards {
    grid-template-columns: 1fr;
  }
  .metric-row > div {
    min-width: 110px;
  }
  .importance-row {
    grid-template-columns: 82px minmax(0, 1fr) 42px;
    font-size: 0.68rem;
  }
}
</style>
