<script setup lang="ts">
import { computed, onMounted, onUnmounted, reactive, ref, watch } from 'vue'
import { createPython } from '../../runtime/python'
import MathText from '../../components/MathText.vue'
import PythonCode from '../../components/PythonCode.vue'
import PythonEditor from '../../components/PythonEditor.vue'
import Plot from './Plot.vue'
import ConceptFigure from './ConceptFigure.vue'
import DataTable from './DataTable.vue'
import Confusion from './Confusion.vue'
import { courseHref } from '../../navigation'
import curriculum from './curriculum.json'
import source from './experiment.py?raw'

const props = defineProps<{ chapter: string }>()
const section = computed(
  () => curriculum.chapters.find((c) => c.id === props.chapter) ?? curriculum.chapters[0]!,
)
type Metrics = {
  accuracy: number
  precision: number
  recall: number
  f1: number
  confusion: number[][]
  average_precision: number
  roc_auc: number
  log_loss: number
  false_positive_rate: number
}
type Run = {
  id: string
  kind: string
  representation: string
  C: number
  alpha: number
  k: number
  parameters: number
  train: Metrics
  validation: Metrics
  thresholds: Omit<Metrics, 'average_precision' | 'roc_auc' | 'log_loss'>[]
  histogram: number[][]
}
type Initial = {
  raw: number
  excluded: number
  unique: number
  duplicates: number
  counts: Record<string, { total: number; ham: number; spam: number }>
  examples: { text: string; label: number }[]
  baseline: Metrics
  points: { x: number; y: number; label: number }[]
  distributions: { name: string; edges: number[]; groups: number[][] }[]
  preview: string[]
  table: { split: string; label: number; text: string; features: number[] }[]
}
type Vector = {
  documents: string[]
  text: string
  representation: string
  vocabulary: string[]
  matrix: number[][]
  transformed: number[]
  tokens: string[]
  unknown: string[]
  numeric: number[]
  idf: number[]
  counts: number[][]
  df: number[]
  weighted: number[][]
  norms: number[]
}
type Explanation = {
  text: string
  bias?: number
  score?: number
  probability: number
  contributions?: { name: string; value: number }[]
  neighbors?: { text: string; label: number; distance: number }[]
  priors?: number[]
  evidence?: { word: string; value: number; ham: number; spam: number; contribution: number }[]
}
type Evaluation = {
  threshold: number
  metrics: Metrics
  pr: number[][]
  roc: number[][]
  prevalence: number
  errors: { text: string; label: number; probability: number; prediction: number }[]
}
type CV = {
  rows: {
    C: number
    folds: number[]
    train: number
    mean: number
    std: number
    vocabulary_sizes: number[]
  }[]
  best: number
  fold_sizes: number[]
  fold_unknown: string[]
  run: Run
}
type LDA = {
  run: Run
  points: { x: number; y: number; label: number }[]
  means: number[][]
  ellipses: number[][][]
  boundary: { w: number[]; b: number }
  priors: number[]
}
type GAM = {
  run: Run
  reference: number[]
  curves: { name: string; x: number[]; effect: number[] }[]
}
type Final = { id: string; threshold: number; reason: string; test: Metrics; validation: Metrics }
const runtime = createPython('tutorial05')
const { ready, status } = runtime
const initial = ref<Initial>()
const error = ref('')
const busy = ref(false)
const running = ref(false)
const operation = ref('')
const message = ref('Congratulations! Claim your free prize now!')
const tokenText = ref('Congratulations! Claim your FREE prize now!')
const tokenResult = ref<{
  text: string
  lowercase: string
  raw_tokens: string[]
  tokens: string[]
}>()
const toyDocuments = ref('Free prize now\nAre you free after class\nWin a prize prize')
const toyText = ref('free meeting tomorrow')
const toyRepresentation = ref('count')
const vector = ref<Vector>()
const word = ref('free')
const feature = ref(0)
const representation = ref('count')
const C = ref(1)
const alpha = ref(1)
const k = ref(5)
const runs = ref<Run[]>([])
const selected = ref('')
const explanation = ref<Explanation>()
const explanationRun = ref('')
const sweep = ref<{
  rows: Run[]
  weights: number[]
  paths: { word: string; weights: number[] }[]
}>()
const cv = ref<CV>()
const fold = ref(0)
const lda = ref<LDA>()
const gam = ref<GAM>()
const threshold = ref(0.5)
const evaluation = ref<Evaluation>()
const evaluationRun = ref('')
const reason = ref('')
const final = ref<Final>()
const drafts = reactive<Record<string, string>>({})
const outputs = reactive<Record<string, { stdout: string; error: string | null }>>({})
const code = computed({
  get: () => drafts[props.chapter] ?? section.value.starter,
  set: (v) => {
    drafts[props.chapter] = v
  },
})
const activeRun = computed(() => runs.value.find((r) => r.id === selected.value))
const currentExplanation = computed(() =>
  explanationRun.value === selected.value ? explanation.value : undefined,
)
const currentEvaluation = computed(() =>
  evaluationRun.value === selected.value ? evaluation.value : undefined,
)
const fmt = (n: number) => (100 * n).toFixed(1) + '%'
const label = (n: number) => (n ? 'Spam' : 'Ham')
const PALETTE = [
  '#45657e',
  '#aa613d',
  '#336a51',
  '#7a5c99',
  '#b08a2e',
  '#3d8a96',
  '#9a4f6b',
  '#65717c',
]
const runName = (r: Run) =>
  `${r.id} · ${r.kind === 'gam' ? 'additive spline' : r.kind.toUpperCase()} · ${r.representation}${r.kind === 'knn' ? ` · k=${r.k}` : r.kind === 'nb' ? ` · α=${r.alpha}` : r.kind === 'lda' ? '' : ` · C=${r.C}`}`
const chapterModel = computed(
  () =>
    ({ naive: 'nb', logistic: 'logistic', neighbors: 'knn' })[
      props.chapter as 'naive' | 'logistic' | 'neighbors'
    ],
)
const comparisonGroup = ref('text')
const comparisonRuns = computed(() =>
  runs.value.filter(
    (row) =>
      comparisonGroup.value === 'all' ||
      (row.representation === 'numeric') === (comparisonGroup.value === 'numeric'),
  ),
)
const wordIndex = computed(() => vector.value?.vocabulary.indexOf(word.value) ?? -1)
const distribution = computed(() => initial.value?.distributions[feature.value])
const maxHistogram = computed(() => Math.max(0.01, ...(distribution.value?.groups.flat() ?? [])))
const maxContribution = computed(() =>
  Math.max(0.01, ...(currentExplanation.value?.contributions?.map((v) => Math.abs(v.value)) ?? [])),
)
const sourceCode = computed(() =>
  section.value.functions
    .map((name) => {
      const match = source.match(
        new RegExp(`^def ${name}\\([\\s\\S]*?(?=^def |^class |$(?![\\s\\S]))`, 'm'),
      )
      return match?.[0].trim() ?? ''
    })
    .join('\n\n'),
)
const sweepLines = computed(() =>
  !sweep.value
    ? []
    : [
        {
          name: 'Training AP',
          color: '#45657e',
          points: sweep.value.rows.map((r) => [Math.log10(r.C), r.train.average_precision]),
        },
        {
          name: 'Validation AP',
          color: '#aa613d',
          points: sweep.value.rows.map((r) => [Math.log10(r.C), r.validation.average_precision]),
        },
      ],
)
const ldaLines = computed(() => {
  if (!lda.value) return []
  const d = lda.value,
    [wx, wy] = d.boundary.w
  const boundary =
    Math.abs(wy!) > 1e-9
      ? [-3, 6].map((x) => [x, -(d.boundary.b + wx! * x) / wy!])
      : [
          [-d.boundary.b / wx!, -3],
          [-d.boundary.b / wx!, 6],
        ]
  return [
    { name: 'Ham covariance contour', color: '#45657e', points: d.ellipses[0]! },
    { name: 'Spam covariance contour', color: '#aa613d', points: d.ellipses[1]! },
    { name: 'Two-feature marginal boundary', color: '#65717c', points: boundary, dashed: true },
  ]
})
const pathLines = computed(() =>
  (sweep.value?.paths ?? []).map((path, i) => ({
    name: path.word,
    color: PALETTE[i]!,
    points: sweep.value!.rows.map((r, j) => [Math.log10(r.C), path.weights[j]!]),
  })),
)
const scoreMax = computed(() => Math.max(1, ...(activeRun.value?.histogram.flat() ?? [])))
const vectorMax = computed(() => Math.max(1e-9, ...(vector.value?.matrix.flat() ?? [])))
const heat = (v: number) =>
  v
    ? {
        background: `rgba(69, 101, 126, ${0.12 + 0.6 * Math.min(1, v / vectorMax.value)})`,
        color: v / vectorMax.value > 0.6 ? 'white' : undefined,
      }
    : undefined
const sigmoidPoints = Array.from({ length: 81 }, (_, i) => {
  const z = -8 + i / 5
  return [z, 1 / (1 + Math.exp(-z))]
})
let generation = 0
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
function addRun(row: Run) {
  if (!runs.value.some((r) => r.id === row.id)) runs.value.push(row)
  selected.value = row.id
  threshold.value = 0.5
  evaluation.value = undefined
  explanation.value = undefined
}
async function vectorize() {
  const value = await act<Vector>('Transforming the message', 'vectorize', {
    documents: toyDocuments.value.split('\n').filter((s) => s.trim()),
    text: toyText.value,
    representation: toyRepresentation.value,
  })
  if (value) {
    vector.value = value
    if (!value.vocabulary.includes(word.value)) word.value = value.vocabulary[0] ?? ''
  }
}
async function tokenize() {
  const value = await act<NonNullable<typeof tokenResult.value>>(
    'Tokenizing the message',
    'tokenize',
    { text: tokenText.value },
  )
  if (value) tokenResult.value = value
}
async function fit(kind = 'logistic', input = representation.value) {
  const row = await act<Run>('Fitting the classifier', 'fit', {
    kind,
    representation: input,
    C: C.value,
    k: k.value,
    alpha: alpha.value,
  })
  if (row) {
    addRun(row)
    if (['naive', 'logistic', 'neighbors'].includes(props.chapter)) await explain()
  }
}
async function compareCore(mode: 'representation' | 'classifier') {
  comparisonGroup.value = 'text'
  const configs =
    mode === 'representation'
      ? [
          { kind: 'nb', representation: 'count' },
          { kind: 'nb', representation: 'tfidf' },
        ]
      : ['nb', 'logistic', 'knn'].map((kind) => ({ kind, representation: 'tfidf' }))
  for (const config of configs) {
    const row = await act<Run>('Fitting comparison candidates', 'fit', {
      ...config,
      C: 1,
      k: 5,
      alpha: 1,
    })
    if (!row) break
    addRun(row)
  }
}
async function explain() {
  const id = selected.value
  const result = await act<Explanation>('Computing this message’s prediction', 'explain', {
    id,
    text: message.value,
  })
  if (result) {
    explanation.value = result
    explanationRun.value = id
  }
}
async function regularize() {
  const result = await act<typeof sweep.value>(
    'Fitting the regularization path',
    'regularization',
    { representation: representation.value },
  )
  if (result) {
    sweep.value = result
    result.rows.forEach(addRun)
  }
}
async function crossValidate() {
  const result = await act<CV>('Fitting 20 pipelines across five folds', 'cv', {
    representation: representation.value,
  })
  if (result) {
    cv.value = result
    addRun(result.run)
  }
}
async function fitLDA() {
  const result = await act<LDA>('Fitting the class distributions', 'lda')
  if (result) {
    lda.value = result
    addRun(result.run)
  }
}
async function fitGAM() {
  const result = await act<GAM>('Fitting the additive spline model', 'gam', { C: C.value })
  if (result) {
    gam.value = result
    addRun(result.run)
  }
}
async function evaluate() {
  const id = selected.value
  const result = await act<Evaluation>('Inspecting validation decisions', 'evaluate', {
    id,
    threshold: threshold.value,
  })
  if (result) {
    evaluation.value = result
    evaluationRun.value = id
  }
}
const liveMetrics = computed(() => {
  const row = activeRun.value
  if (!row) return undefined
  return { ...row.validation, ...row.thresholds[Math.round(threshold.value * 100)] }
})
const errorsCurrent = computed(() => currentEvaluation.value?.threshold === threshold.value)
const liveErrors = computed(() => {
  const row = activeRun.value
  if (!row || !currentEvaluation.value || !errorsCurrent.value) return []
  // The detailed error list is refreshed by Python on slider release.
  return currentEvaluation.value.errors
})
async function finalTest() {
  const result = await act<Final>('Evaluating the frozen decision on test data', 'final_test', {
    id: selected.value,
    threshold: threshold.value,
    reason: reason.value,
  })
  if (result) final.value = result
}
async function runCode() {
  const chapter = props.chapter,
    epoch = generation
  if (!ready.value || busy.value) return
  running.value = true
  const output = await act<{ stdout: string; error: string | null }>(
    'Running your Python',
    'execute',
    { code: code.value },
  )
  if (output) outputs[chapter] = output
  if (epoch === generation) running.value = false
}
function exportResults() {
  const payload = {
    dataset: 'Original UCI SMS Spam Collection',
    seed: 3612,
    counts: initial.value?.counts,
    runs: runs.value.map(({ thresholds: _grid, ...row }) => row),
    cv: cv.value?.rows,
    final: final.value,
  }
  const url = URL.createObjectURL(
    new Blob([JSON.stringify(payload, null, 2)], { type: 'application/json' }),
  )
  const a = document.createElement('a')
  a.href = url
  a.download = 'tutorial05-experiment.json'
  a.click()
  URL.revokeObjectURL(url)
}
async function start() {
  generation++
  busy.value = false
  running.value = false
  error.value = ''
  runs.value = []
  selected.value = ''
  final.value = undefined
  explanation.value = undefined
  evaluation.value = undefined
  sweep.value = undefined
  cv.value = undefined
  lda.value = undefined
  gam.value = undefined
  tokenResult.value = undefined
  try {
    initial.value = await runtime.start<Initial>()
    await vectorize()
    await tokenize()
  } catch (e) {
    error.value = String(e)
  }
}
watch(
  () => props.chapter,
  () => {
    error.value = ''
    if (props.chapter === 'neighbors') representation.value = 'tfidf'
    if (props.chapter === 'naive' && representation.value === 'numeric')
      representation.value = 'count'
    if (['text', 'tfidf'].includes(props.chapter)) {
      vector.value = undefined
      toyRepresentation.value = props.chapter === 'tfidf' ? 'tfidf' : 'count'
      toyDocuments.value =
        props.chapter === 'tfidf'
          ? 'claim your prize\ncheck your timetable\nsend your notes'
          : 'free prize now\nare you free after class\nwin a prize prize'
      toyText.value =
        props.chapter === 'tfidf' ? 'claim your prize tomorrow' : 'free meeting tomorrow'
      if (ready.value && !busy.value) void vectorize()
    }
  },
  { immediate: true },
)
onMounted(start)
onUnmounted(() => {
  generation++
  runtime.dispose()
})
</script>

<template>
  <div class="spam-lesson">
    <nav class="learning-route" aria-label="Text classification workflow">
      <span>Message</span><span aria-hidden="true">→</span><span>Tokens</span
      ><span aria-hidden="true">→</span><span>BoW / TF–IDF</span><span aria-hidden="true">→</span
      ><span>Classifier</span><span aria-hidden="true">→</span><span>Prediction</span>
    </nav>
    <aside v-if="section.extension" class="extension-note">
      <strong>Extension</strong> · Complete material for further study. You can follow the core
      route directly to
      <a :href="courseHref('tutorials/tutorial05/decision')">Evaluation and Error Analysis →</a>
    </aside>
    <section id="concept" class="chapter-theory">
      <div class="section-label">UNDERSTAND THE IDEA</div>
      <h2>{{ section.idea }}</h2>
      <ul class="key-points">
        <li v-for="point in section.points" :key="point">{{ point }}</li>
      </ul>
      <article v-for="item in section.worked" :key="item.title" class="worked-example">
        <h3>{{ item.title }}</h3>
        <p v-for="paragraph in item.text" :key="paragraph">{{ paragraph }}</p>
        <div v-if="item.columns.length" class="table-scroll">
          <table class="spam-table" :aria-label="item.title">
            <thead>
              <tr>
                <th v-for="column in item.columns" :key="column">{{ column }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(row, i) in item.rows" :key="i">
                <template v-for="(value, j) in row" :key="j"
                  ><th v-if="j === 0" scope="row">{{ value }}</th>
                  <td v-else>{{ value }}</td></template
                >
              </tr>
            </tbody>
          </table>
        </div>
      </article>
      <ConceptFigure v-if="section.extension" :chapter="chapter" />
      <div v-if="section.equation && ['tfidf', 'naive'].includes(chapter)" class="equation-card">
        <MathText :tex="section.equation" />
        <dl class="notation-list">
          <div v-for="[symbol, meaning] in section.notation" :key="symbol">
            <dt><MathText :tex="symbol!" inline /></dt>
            <dd>{{ meaning }}</dd>
          </div>
        </dl>
      </div>
      <details v-else-if="section.equation" class="formula-recap">
        <summary>Formula recap</summary>
        <div class="equation-card">
          <MathText :tex="section.equation" />
          <dl class="notation-list">
            <div v-for="[symbol, meaning] in section.notation" :key="symbol">
              <dt><MathText :tex="symbol!" inline /></dt>
              <dd>{{ meaning }}</dd>
            </div>
          </dl>
        </div>
      </details>
      <p v-for="[title, url] in section.links" :key="url" class="documentation-link">
        <a :href="url" target="_blank" rel="noreferrer">{{ title }} ↗</a>
      </p>
    </section>
    <section class="chapter-experiment" aria-label="Interactive experiment">
      <div class="section-label">EXPLORE THE RESULT</div>
      <ol class="mechanism">
        <li v-for="step in section.steps" :key="step">{{ step }}</li>
      </ol>
      <p v-if="!ready && !error" role="status">{{ status }}</p>
      <div v-if="error" class="execution-error" role="alert">
        {{ error }} <button @click="start">Restart Python</button>
      </div>
      <p v-if="busy" role="status">{{ operation }}…</p>

      <template v-if="chapter === 'inbox'">
        <div class="task-flow" aria-label="A text classification example">
          <p>
            <strong>Training example:</strong> “Claim your free prize!” + label
            <span class="tag spam">Spam</span>
          </p>
          <p>
            <strong>New input:</strong> “Are you free after class?” → tokens → vector → trained
            classifier → predicted label
          </p>
          <p>The classifier must learn from the surrounding words as well as “free”.</p>
        </div>
      </template>

      <template v-if="chapter === 'tokenize'">
        <div class="panel">
          <h3>Follow your message through preprocessing</h3>
          <label>Message to tokenize<textarea v-model="tokenText" rows="3" /></label>
          <button class="primary" :disabled="!ready || busy" @click="tokenize">
            Tokenize message
          </button>
          <dl v-if="tokenResult" class="token-stages">
            <dt>Original</dt>
            <dd>{{ tokenResult.text }}</dd>
            <dt>Lowercase</dt>
            <dd>{{ tokenResult.lowercase }}</dd>
            <dt>NLTK tokens</dt>
            <dd>
              <code>{{ JSON.stringify(tokenResult.raw_tokens) }}</code>
            </dd>
            <dt>Retained tokens</dt>
            <dd>
              <code>{{ JSON.stringify(tokenResult.tokens) }}</code>
            </dd>
          </dl>
        </div>
      </template>

      <template v-if="chapter === 'data' && initial">
        <div class="panel">
          <h3>1 · The raw file, exactly as stored</h3>
          <p>
            <code>SMSSpamCollection.txt</code>: one message per line, label
            <span class="tab-mark">⇥ tab</span> message. Source:
            <a
              href="https://archive.ics.uci.edu/dataset/228/sms+spam+collection"
              target="_blank"
              rel="noopener"
              >UCI SMS Spam Collection ↗</a
            >
          </p>
          <div class="raw-file" aria-label="First lines of the raw data file">
            <div v-for="(line, i) in initial.preview" :key="i">
              <span class="line-no">{{ i + 1 }}</span
              ><span class="tag" :class="line.startsWith('spam') ? 'spam' : 'ham'">{{
                line.split('\t')[0]
              }}</span
              ><span class="tab-mark">⇥</span>{{ line.split('\t').slice(1).join('\t') }}
            </div>
            <div class="muted">
              … {{ (initial.raw - initial.preview.length).toLocaleString() }} more lines
            </div>
          </div>
        </div>
        <div class="panel">
          <h3>2 · Clean and split</h3>
          <div class="audit">
            <span>{{ initial.raw }}<small>raw records</small></span
            ><b>→</b><span>{{ initial.excluded }}<small>empty texts removed</small></span
            ><b>→</b><span>{{ initial.duplicates }}<small>duplicates removed</small></span
            ><b>→</b><span>{{ initial.unique }}<small>unique messages</small></span>
          </div>
          <div v-for="(counts, name) in initial.counts" :key="name" class="split-row">
            <strong>{{ name }} · {{ counts.total }}</strong>
            <div
              class="class-bar"
              :aria-label="`${name}: ${counts.ham} ham and ${counts.spam} spam`"
            >
              <span :style="{ width: fmt(counts.ham / counts.total) }">Ham {{ counts.ham }}</span
              ><span class="spam" :style="{ width: fmt(counts.spam / counts.total) }">{{
                counts.spam
              }}</span>
            </div>
            <small>Spam {{ fmt(counts.spam / counts.total) }}</small>
          </div>
        </div>
        <div class="panel">
          <h3>3 · The always-ham trap</h3>
          <div class="spam-metrics">
            <span
              >Accuracy<strong>{{ fmt(initial.baseline.accuracy) }}</strong></span
            ><span
              >Spam recall<strong class="spam-text">{{
                fmt(initial.baseline.recall)
              }}</strong></span
            >
          </div>
          <Confusion :matrix="initial.baseline.confusion" label="Always-ham confusion matrix" />
        </div>
        <h3>4 · Browse the data</h3>
        <p class="muted">
          Training and validation messages. The 1,032 test messages stay hidden until the final
          chapter.
        </p>
        <DataTable :rows="initial.table" caption="Cleaned dataset (train + validation)" />
      </template>

      <template v-if="chapter === 'features'">
        <div class="panel">
          <h3>Measure one message</h3>
          <label>Message to measure<textarea v-model="toyText" rows="3" /></label
          ><button :disabled="!ready || busy" @click="vectorize">Measure message features</button>
          <p v-if="vector">Measured message: {{ vector.text }}</p>
          <div v-if="vector" class="spam-metrics">
            <span v-for="(value, i) in vector.numeric" :key="i"
              >{{ ['Characters', 'Tokens', 'Links', 'Digits', 'Exclamation marks'][i]
              }}<strong>{{ value }}</strong></span
            >
          </div>
        </div>
        <h3>Every message as a row of five numbers</h3>
        <p class="muted">Sort by a feature: which label rises to the top?</p>
        <DataTable
          v-if="initial"
          :rows="initial.table"
          features
          caption="Feature table (train + validation)"
        />
        <div v-if="distribution" class="panel">
          <h3>Ham vs spam, one feature at a time</h3>
          <label
            >Measured feature<select v-model.number="feature">
              <option v-for="(d, i) in initial?.distributions" :key="i" :value="i">
                {{ d.name }}
              </option>
            </select></label
          >
          <figure class="histogram">
            <svg
              viewBox="0 0 600 280"
              role="img"
              :aria-label="`${distribution.name} distributions by class`"
            >
              <g v-for="(value, i) in distribution.groups[0]" :key="i">
                <rect
                  :x="50 + i * 44"
                  :y="230 - (value / maxHistogram) * 180"
                  width="18"
                  :height="(value / maxHistogram) * 180"
                  fill="#45657e"
                />
                <rect
                  :x="69 + i * 44"
                  :y="230 - (distribution.groups[1]![i]! / maxHistogram) * 180"
                  width="18"
                  :height="(distribution.groups[1]![i]! / maxHistogram) * 180"
                  fill="#aa613d"
                />
              </g>
              <line x1="46" x2="580" y1="230" y2="230" stroke="#9dabb5" />
              <text x="50" y="20">Share of each class (tallest bar {{ fmt(maxHistogram) }})</text>
              <text
                v-for="(edge, i) in distribution.edges.slice(0, -1)"
                :key="i"
                :x="68 + i * 44"
                y="248"
                text-anchor="middle"
              >
                {{ edge.toFixed(0) }}{{ i === distribution.edges.length - 2 ? '+' : '' }}
              </text>
              <text x="300" y="274" text-anchor="middle">
                {{ distribution.name }} (bin start; last bin includes the tail)
              </text>
            </svg>
            <figcaption>
              <span class="ham-key">Ham</span> · <span class="spam-key">Spam</span>
            </figcaption>
          </figure>
        </div>
        <Plot
          v-if="initial"
          title="Training messages · two-feature projection"
          x-label="Characters"
          y-label="Digits"
          :points="initial.points"
        />
        <button
          class="primary"
          :disabled="!ready || busy || !!final"
          @click="fit('logistic', 'numeric')"
        >
          Fit numerical logistic baseline
        </button>
        <p v-if="activeRun?.representation === 'numeric'">
          {{ runName(activeRun) }} · Validation AP {{ fmt(activeRun.validation.average_precision) }}
        </p>
      </template>

      <template v-if="['text', 'tfidf'].includes(chapter)">
        <div class="panel">
          <h3>Build a vocabulary from these training documents</h3>
          <label
            >Toy training documents · one per line<textarea
              v-model="toyDocuments"
              rows="4"
            /></label
          ><label
            >Representation<select v-model="toyRepresentation">
              <option value="count">Word counts</option>
              <option value="tfidf">TF–IDF · smoothed IDF + L2 normalization</option>
            </select></label
          ><label>New message to transform<textarea v-model="toyText" rows="2" /></label
          ><button class="primary" :disabled="!ready || busy" @click="vectorize">
            Build and transform toy vectors
          </button>
          <template v-if="vector"
            ><div class="word-list">
              <button
                v-for="v in vector.vocabulary"
                :key="v"
                :aria-pressed="word === v"
                @click="word = v"
              >
                {{ v }}
              </button>
            </div>
            <p>
              Selected word: <strong>{{ word }}</strong
              >. Each column keeps its meaning for every message.
            </p>
            <div
              v-if="vector.representation === 'tfidf' && wordIndex >= 0"
              class="calculation panel"
            >
              <h3>Calculate the weight of “{{ word }}”</h3>
              <p>
                {{ vector.documents.length }} training documents; {{ vector.df[wordIndex] }} contain
                this word. IDF = log((1 + {{ vector.documents.length }}) / (1 +
                {{ vector.df[wordIndex] }})) + 1 = {{ vector.idf[wordIndex]!.toFixed(3) }}.
              </p>
              <div class="table-scroll">
                <table class="spam-table" aria-label="TF–IDF calculation">
                  <thead>
                    <tr>
                      <th>Document</th>
                      <th>TF</th>
                      <th>TF × IDF</th>
                      <th>Row L2 norm</th>
                      <th>Normalized value</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="(row, i) in vector.counts" :key="i">
                      <th>{{ vector.documents[i] }}</th>
                      <td>{{ row[wordIndex] }}</td>
                      <td>{{ vector.weighted[i]![wordIndex]!.toFixed(3) }}</td>
                      <td>{{ vector.norms[i]!.toFixed(3) }}</td>
                      <td>{{ vector.matrix[i]![wordIndex]!.toFixed(3) }}</td>
                    </tr>
                  </tbody>
                </table>
              </div>
              <p>
                A word repeated twice has TF = 2, but adds only one to DF for that document. Row
                norms use all vocabulary columns.
              </p>
            </div>
            <div class="table-scroll">
              <table class="spam-table" aria-label="Document–term matrix">
                <thead>
                  <tr>
                    <th>Document</th>
                    <th v-for="v in vector.vocabulary" :key="v" :class="{ highlight: word === v }">
                      {{ v }}
                    </th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="(row, i) in vector.matrix" :key="i">
                    <th>
                      {{ i + 1 }} ·
                      {{ vector.documents[i] }}
                    </th>
                    <td
                      v-for="(v, j) in row"
                      :key="j"
                      class="heat"
                      :class="{ highlight: word === vector.vocabulary[j] }"
                      :style="heat(v)"
                    >
                      {{ v.toFixed(vector.representation === 'count' ? 0 : 3) }}
                    </td>
                  </tr>
                  <tr>
                    <th>New message</th>
                    <td
                      v-for="(v, j) in vector.transformed"
                      :key="j"
                      class="heat"
                      :class="{ highlight: word === vector.vocabulary[j] }"
                      :style="heat(v)"
                    >
                      {{ v.toFixed(vector.representation === 'count' ? 0 : 3) }}
                    </td>
                  </tr>
                  <tr v-if="vector.representation === 'tfidf'">
                    <th>Training IDF</th>
                    <td v-for="(v, j) in vector.idf" :key="j">{{ v.toFixed(3) }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
            <p>Transformed message: {{ vector.text }}</p>
            <p>Tokens in new message: {{ vector.tokens.join(' · ') || '(none)' }}</p>
            <p>
              Ignored unknown words: <strong>{{ vector.unknown.join(', ') || '(none)' }}</strong>
            </p>
            <p class="muted">
              Real pipelines: sparse matrices, words seen in ≥ 2 training messages, at most 2,500
              columns.
            </p></template
          >
        </div>
      </template>

      <template v-if="chapter === 'naive'">
        <div class="panel">
          <h3>Fit Naive Bayes on the real messages</h3>
          <div class="control-row">
            <label
              >NB representation<select v-model="representation">
                <option value="count">Word counts</option>
                <option value="tfidf">TF–IDF</option>
              </select></label
            >
            <label
              >Smoothing alpha<input
                v-model.number="alpha"
                type="number"
                min="0.01"
                max="100"
                step="0.1"
            /></label>
          </div>
          <button
            class="primary"
            :disabled="!ready || busy || !!final"
            @click="fit('nb', representation === 'numeric' ? 'count' : representation)"
          >
            Fit Naive Bayes classifier
          </button>
          <template v-if="activeRun?.kind === 'nb'">
            <p>
              {{ runName(activeRun) }} · Validation AP
              {{ fmt(activeRun.validation.average_precision) }} · Precision
              {{ fmt(activeRun.validation.precision) }} · Recall
              {{ fmt(activeRun.validation.recall) }}
            </p>
            <label>Message for Naive Bayes<textarea v-model="message" rows="3" /></label>
            <button :disabled="!ready || busy" @click="explain">
              Inspect Naive Bayes evidence
            </button>
          </template>
        </div>
        <div v-if="activeRun?.kind === 'nb' && currentExplanation?.evidence" class="panel">
          <h3>Class priors and word evidence</h3>
          <p>
            Training priors: Ham {{ fmt(currentExplanation.priors![0]!) }} · Spam
            {{ fmt(currentExplanation.priors![1]!) }}
          </p>
          <div class="table-scroll">
            <table class="spam-table" aria-label="Naive Bayes word evidence">
              <thead>
                <tr>
                  <th>Word</th>
                  <th>Feature value</th>
                  <th>P(word | ham)</th>
                  <th>P(word | spam)</th>
                  <th>Log evidence for spam</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="item in currentExplanation.evidence" :key="item.word">
                  <th>{{ item.word }}</th>
                  <td>{{ item.value.toFixed(3) }}</td>
                  <td>{{ item.ham.toPrecision(3) }}</td>
                  <td>{{ item.spam.toPrecision(3) }}</td>
                  <td :class="item.contribution > 0 ? 'spam-text' : 'ham-key'">
                    {{ item.contribution.toFixed(3) }}
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
          <p v-if="!currentExplanation.evidence.length">
            No known words remain. This prediction uses only the learned class priors.
          </p>
          <p>
            Positive log evidence favours spam; negative favours ham. Each term is feature value ×
            log(P(word | spam) / P(word | ham)). Add the log prior ratio
            {{ currentExplanation.bias!.toFixed(3) }} to get
            {{ currentExplanation.score!.toFixed(3) }}.
          </p>
          <p><strong>Message:</strong> {{ currentExplanation.text }}</p>
          <p>
            <strong>Estimated spam probability: {{ fmt(currentExplanation.probability) }}</strong>
          </p>
          <p v-if="activeRun.representation === 'tfidf'" class="muted">
            With TF–IDF, these are fitted nonnegative weight-based estimates rather than literal
            token frequencies.
          </p>
        </div>
      </template>

      <template v-if="['logistic', 'neighbors'].includes(chapter)">
        <div class="panel">
          <h3>
            {{
              chapter === 'neighbors'
                ? 'Fit a local-vote classifier'
                : 'Fit a learned weighted rule'
            }}
          </h3>
          <div class="control-row">
            <label
              >Model representation<select v-model="representation">
                <option value="count">Word counts</option>
                <option value="tfidf">TF–IDF</option>
                <option value="numeric">Five numerical features</option>
              </select></label
            ><label v-if="chapter === 'neighbors'"
              >Neighbour count k<select v-model.number="k">
                <option v-for="n in [1, 3, 5, 9, 15, 31]" :key="n" :value="n">{{ n }}</option>
              </select></label
            >
          </div>
          <details v-if="chapter === 'logistic'" class="formula-recap">
            <summary>Optional: LR regularization setting</summary>
            <label
              >Inverse regularization C<input
                v-model.number="C"
                type="number"
                min="0.001"
                max="100"
                step="0.1"
            /></label>
            <p>Use the default C = 1 first. Explore its effect in the Regularization extension.</p>
          </details>
          <button
            class="primary"
            :disabled="!ready || busy || !!final"
            @click="fit(chapter === 'neighbors' ? 'knn' : 'logistic')"
          >
            {{ chapter === 'neighbors' ? 'Fit KNN classifier' : 'Fit logistic classifier' }}
          </button>
          <template v-if="activeRun?.kind === chapterModel"
            ><p>
              {{ runName(activeRun) }} · Training AP {{ fmt(activeRun.train.average_precision) }} ·
              Validation AP {{ fmt(activeRun.validation.average_precision) }}
            </p>
            <label>Message to classify<textarea v-model="message" rows="3" /></label
            ><button :disabled="!ready || busy" @click="explain">
              Inspect message prediction
            </button></template
          >
        </div>
        <template v-if="activeRun?.kind === chapterModel && currentExplanation"
          ><div class="panel">
            <p class="colored-message">{{ currentExplanation.text }}</p>
            <div class="spam-metrics">
              <span
                >Spam score<strong>{{ fmt(currentExplanation.probability) }}</strong></span
              ><span v-if="currentExplanation.score !== undefined"
                >Linear score z<strong>{{ currentExplanation.score.toFixed(3) }}</strong></span
              ><span v-if="currentExplanation.bias !== undefined"
                >Intercept b<strong>{{ currentExplanation.bias.toFixed(3) }}</strong></span
              >
            </div>
            <template v-if="currentExplanation.contributions"
              ><h3>Message-specific contributions wⱼxⱼ</h3>
              <p class="muted">Largest 14 shown. z = intercept + sum of all contributions.</p>
              <div
                v-for="item in currentExplanation.contributions.slice(0, 14)"
                :key="item.name"
                class="contribution"
              >
                <code>{{ item.name }}</code>
                <div class="signed-track">
                  <i
                    :class="item.value < 0 ? 'negative' : 'positive'"
                    :style="{ width: `${(Math.abs(item.value) / maxContribution) * 48}%` }"
                  />
                </div>
                <span>{{ item.value.toFixed(3) }}</span>
              </div></template
            >
            <template v-if="currentExplanation.neighbors"
              ><h3>The neighbours that voted</h3>
              <div class="vote-bar" aria-label="Neighbour vote">
                <span
                  v-for="(item, i) in currentExplanation.neighbors"
                  :key="i"
                  :class="item.label ? 'spam' : 'ham'"
                  >{{ label(item.label) }}</span
                >
              </div>
              <article
                v-for="(item, i) in currentExplanation.neighbors"
                :key="i"
                class="mail-card neighbour"
              >
                <div class="neighbour-head">
                  <span class="tag" :class="item.label ? 'spam' : 'ham'">{{
                    label(item.label)
                  }}</span>
                  <span class="distance-track"
                    ><i :style="{ width: `${Math.min(100, item.distance * 100)}%` }"
                  /></span>
                  <span class="muted">distance {{ item.distance.toFixed(3) }}</span>
                </div>
                <p>{{ item.text }}</p>
              </article>
              <p class="muted">Spam vote = spam neighbours / k.</p></template
            >
          </div>
          <details v-if="currentExplanation.score !== undefined" class="formula-recap">
            <summary>Recall the score-to-probability mapping</summary>
            <Plot
              title="Linear score mapped through the sigmoid"
              x-label="Linear score z"
              y-label="Spam probability"
              :lines="[{ name: 'Sigmoid', color: '#45657e', points: sigmoidPoints }]"
              :points="[
                { x: currentExplanation.score, y: currentExplanation.probability, label: 1 },
              ]"
              :bounds="[-8, 8, 0, 1]"
            /></details
        ></template>
      </template>

      <template v-if="chapter === 'regularization'">
        <div class="panel">
          <h3>Keep the representation fixed; change C</h3>
          <label
            >Text representation<select v-model="representation">
              <option value="count">Word counts</option>
              <option value="tfidf">TF–IDF</option>
            </select></label
          ><button class="primary" :disabled="!ready || busy || !!final" @click="regularize">
            Fit regularization path
          </button>
          <p>
            Five fitted candidates are retained for comparison. Smaller C gives stronger
            regularization.
          </p>
        </div>
        <template v-if="sweep"
          ><Plot
            title="Regularization path · same split and representation"
            x-label="log₁₀(C) · stronger penalty ← → weaker penalty"
            y-label="Average precision"
            :lines="sweepLines"
            :bounds="[-3, 1, 0, 1]"
          /><Plot
            title="Word weights shrink as the penalty grows"
            x-label="log₁₀(C) · stronger penalty ← → weaker penalty"
            y-label="Weight w (count model)"
            :lines="pathLines"
            :bounds="[
              -3,
              1,
              Math.min(0, ...pathLines.flatMap((l) => l.points.map((p) => p[1]!))),
              Math.max(1, ...pathLines.flatMap((l) => l.points.map((p) => p[1]!))),
            ]"
          />
          <p class="muted">
            The eight words with the largest weights at C = 10. Do they all look like genuine spam
            evidence?
          </p>
          <Plot
            title="Coefficient magnitude along the path"
            x-label="log₁₀(C)"
            y-label="L2 coefficient norm"
            :lines="[
              {
                name: 'Weight norm',
                color: '#45657e',
                points: sweep.rows.map((r, i) => [Math.log10(r.C), sweep!.weights[i]!]),
              },
            ]"
          />
          <div class="table-scroll">
            <table class="spam-table">
              <thead>
                <tr>
                  <th>C</th>
                  <th>Training AP</th>
                  <th>Validation AP</th>
                  <th>Weight norm</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(row, i) in sweep.rows" :key="row.id">
                  <td>{{ row.C }}</td>
                  <td>{{ fmt(row.train.average_precision) }}</td>
                  <td>{{ fmt(row.validation.average_precision) }}</td>
                  <td>{{ sweep.weights[i]?.toFixed(2) }}</td>
                </tr>
              </tbody>
            </table>
          </div></template
        >
      </template>

      <template v-if="chapter === 'validation'">
        <div class="panel">
          <h3>A complete pipeline fitted inside each training fold</h3>
          <label
            >Held-out fold<select v-model.number="fold">
              <option v-for="i in 5" :key="i" :value="i - 1">Fold {{ i }}</option>
            </select></label
          >
          <div class="folds">
            <span v-for="i in 5" :key="i" :class="{ heldout: fold === i - 1 }"
              >Fold {{ i }}<small>{{ fold === i - 1 ? 'Score only' : 'Fit pipeline' }}</small></span
            >
          </div>
          <div class="pipeline">
            <span>Four training folds</span><b>→</b><span>Fit vocabulary / IDF</span><b>→</b
            ><span>Fit classifier</span><b>→</b><span>Transform &amp; score held-out fold</span>
          </div>
          <p>
            The fold selector illustrates data roles. Computed results below come from all five
            actual training-only folds.
          </p>
          <label
            >CV representation<select v-model="representation">
              <option value="count">Word counts</option>
              <option value="tfidf">TF–IDF</option>
            </select></label
          ><button class="primary" :disabled="!ready || busy || !!final" @click="crossValidate">
            Run five-fold cross-validation
          </button>
        </div>
        <template v-if="cv"
          ><Plot
            title="Training-only five-fold CV"
            x-label="log₁₀(C)"
            y-label="Mean average precision"
            :lines="[
              {
                name: 'Fold training AP',
                color: '#45657e',
                points: cv.rows.map((r) => [Math.log10(r.C), r.train]),
              },
              {
                name: 'Held-out fold AP',
                color: '#aa613d',
                points: cv.rows.map((r) => [Math.log10(r.C), r.mean]),
              },
            ]"
            :bounds="[-2, 1, 0, 1]"
          />
          <div class="table-scroll">
            <table class="spam-table">
              <thead>
                <tr>
                  <th>C</th>
                  <th v-for="i in 5" :key="i">Fold {{ i }} AP</th>
                  <th>Mean ± SD</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="row in cv.rows" :key="row.C" :class="{ highlight: row.C === cv.best }">
                  <th>{{ row.C }}</th>
                  <td v-for="(value, i) in row.folds" :key="i">{{ fmt(value) }}</td>
                  <td>{{ fmt(row.mean) }} ± {{ fmt(row.std) }}</td>
                </tr>
              </tbody>
            </table>
          </div>
          <p>
            Selected C = <strong>{{ cv.best }}</strong
            >. Refitted on all training messages; validation AP =
            {{ fmt(cv.run.validation.average_precision) }}.
          </p>
          <p>
            Vocabulary sizes across folds: {{ cv.rows[0]?.vocabulary_sizes.join(', ') }}. These
            refer to the actual vectorizers fitted in each fold.
          </p>
          <p>
            First-fold held-out words absent from its retained training vocabulary:
            {{ cv.fold_unknown.join(', ') }}. They are ignored when that fold is scored; min_df and
            feature limits can also exclude words.
          </p></template
        >
      </template>

      <template v-if="chapter === 'lda'">
        <div class="panel">
          <h3>Fit LDA on the five numerical features</h3>
          <button class="primary" :disabled="!ready || busy || !!final" @click="fitLDA">
            Fit LDA classifier</button
          ><button :disabled="!ready || busy || !!final" @click="fit('logistic', 'numeric')">
            Fit numerical logistic comparison
          </button>
          <p>Shared Gaussian covariance with shrinkage; training-estimated class priors.</p>
        </div>
        <template v-if="lda"
          ><Plot
            title="LDA · two-feature marginal of the fitted distributions"
            x-label="Standardized log(1 + characters)"
            y-label="Standardized log(1 + digits)"
            :points="lda.points"
            :lines="ldaLines"
            :bounds="[-3, 6, -2, 6]"
          />
          <p>
            Estimated priors: Ham {{ fmt(lda.priors[0]!) }} · Spam {{ fmt(lda.priors[1]!) }}. Full
            five-feature validation AP: {{ fmt(lda.run.validation.average_precision) }}.
          </p>
          <p>
            Contours show shared covariance. The dashed line uses the two-feature marginal;
            full-model predictions use all five numerical features.
          </p></template
        >
      </template>

      <template v-if="chapter === 'gam'">
        <div class="panel">
          <h3>Fit separate smooth effects with a binomial link</h3>
          <label
            >Additive model C<input
              v-model.number="C"
              type="number"
              min=".001"
              max="100"
              step=".1" /></label
          ><button class="primary" :disabled="!ready || busy || !!final" @click="fitGAM">
            Fit additive spline classifier</button
          ><button :disabled="!ready || busy || !!final" @click="fit('logistic', 'numeric')">
            Fit numerical logistic comparison
          </button>
          <p>
            Training-fitted cubic spline bases → standardization → regularized logistic regression.
            Five separate effects, no interactions.
          </p>
        </div>
        <template v-if="gam"
          ><div class="small-multiples">
            <Plot
              v-for="c in gam.curves"
              :key="c.name"
              :title="`Additive effect of ${c.name}`"
              :x-label="c.name + ' (raw count)'"
              y-label="Change in log-odds"
              :lines="[
                {
                  name: 'f(x)',
                  color: '#aa613d',
                  points: c.x.map((x, i) => [x, c.effect[i]!]),
                },
              ]"
            />
          </div>
          <p>
            Each curve varies one feature; the others stay at their training medians ({{
              gam.reference.join(', ')
            }}). 0 = the median message. Validation AP:
            <strong>{{ fmt(gam.run.validation.average_precision) }}</strong
            >.
          </p></template
        >
      </template>

      <template v-if="chapter === 'decision'">
        <div class="panel">
          <h3>Compare representations, then classifiers</h3>
          <p>
            These comparisons work even if you skipped the extensions. All candidates use the same
            train / validation split.
          </p>
          <div class="control-row">
            <button
              class="primary"
              :disabled="!ready || busy || !!final"
              @click="compareCore('representation')"
            >
              Compare BoW and TF–IDF with NB
            </button>
            <button :disabled="!ready || busy || !!final" @click="compareCore('classifier')">
              Compare NB, LR and KNN with TF–IDF
            </button>
          </div>
          <label v-if="runs.length"
            >Comparison group<select v-model="comparisonGroup">
              <option value="text">Text features</option>
              <option value="numeric">Numerical features</option>
              <option value="all">All candidates (different representations)</option>
            </select></label
          >
          <p v-if="!runs.length">
            Fit a baseline here or visit the model chapters. Every candidate is evaluated on the
            same validation split.
          </p>
          <button v-if="!runs.length" class="primary" :disabled="!ready || busy" @click="fit()">
            Fit logistic baseline for evaluation
          </button>
          <div v-if="runs.length" class="table-scroll">
            <table class="spam-table">
              <thead>
                <tr>
                  <th>Candidate</th>
                  <th>Validation AP</th>
                  <th>ROC AUC</th>
                  <th>Precision at 0.5</th>
                  <th>Recall at 0.5</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="row in comparisonRuns" :key="row.id">
                  <th>{{ runName(row) }}</th>
                  <td>{{ fmt(row.validation.average_precision) }}</td>
                  <td>{{ fmt(row.validation.roc_auc) }}</td>
                  <td>{{ fmt(row.validation.precision) }}</td>
                  <td>{{ fmt(row.validation.recall) }}</td>
                </tr>
              </tbody>
            </table>
          </div>
          <label v-if="runs.length"
            >Selected candidate<select
              v-model="selected"
              :disabled="busy || !!final"
              @change="evaluate"
            >
              <option v-for="row in runs" :key="row.id" :value="row.id">{{ runName(row) }}</option>
            </select></label
          >
          <label v-if="activeRun"
            >Validation decision threshold: {{ threshold.toFixed(2)
            }}<input
              v-model.number="threshold"
              type="range"
              min="0"
              max="1"
              step=".01"
              :disabled="busy || !!final"
              @change="evaluate" /></label
          ><button v-if="activeRun" :disabled="!ready || busy" @click="evaluate">
            Inspect validation errors and curves
          </button>
        </div>
        <template v-if="liveMetrics"
          ><div class="spam-metrics">
            <span
              >Accuracy<strong>{{ fmt(liveMetrics.accuracy) }}</strong></span
            ><span
              >Precision<strong>{{ fmt(liveMetrics.precision) }}</strong></span
            ><span
              >Recall<strong>{{ fmt(liveMetrics.recall) }}</strong></span
            ><span
              >F1<strong>{{ fmt(liveMetrics.f1) }}</strong></span
            >
          </div>
          <figure v-if="activeRun" class="score-histogram">
            <svg
              viewBox="0 0 600 270"
              role="img"
              aria-label="Validation score histograms with the threshold"
            >
              <g v-for="(count, i) in activeRun.histogram[0]" :key="'h' + i">
                <rect
                  :x="40 + i * 26"
                  :y="125 - (Math.sqrt(count) / Math.sqrt(scoreMax)) * 92"
                  width="24"
                  :height="(Math.sqrt(count) / Math.sqrt(scoreMax)) * 92"
                  :fill="i / 20 >= threshold ? '#aa613d' : '#45657e'"
                  :opacity="0.85"
                />
                <text
                  v-if="count"
                  :x="52 + i * 26"
                  :y="120 - (Math.sqrt(count) / Math.sqrt(scoreMax)) * 92"
                  text-anchor="middle"
                >
                  {{ count }}
                </text>
              </g>
              <g v-for="(count, i) in activeRun.histogram[1]" :key="'s' + i">
                <rect
                  :x="40 + i * 26"
                  y="129"
                  width="24"
                  :height="(Math.sqrt(count) / Math.sqrt(scoreMax)) * 92"
                  :fill="i / 20 >= threshold ? '#aa613d' : '#45657e'"
                  :opacity="0.85"
                />
                <text
                  v-if="count"
                  :x="52 + i * 26"
                  :y="141 + (Math.sqrt(count) / Math.sqrt(scoreMax)) * 92"
                  text-anchor="middle"
                >
                  {{ count }}
                </text>
              </g>
              <line x1="38" x2="562" y1="127" y2="127" stroke="#9dabb5" />
              <line
                :x1="40 + threshold * 520"
                :x2="40 + threshold * 520"
                y1="12"
                y2="240"
                stroke="#202e3a"
                stroke-width="2"
              />
              <text :x="44 + threshold * 520" y="22">t = {{ threshold.toFixed(2) }}</text>
              <text x="560" y="22" text-anchor="end" class="strong">Actual ham ↑</text>
              <text x="560" y="240" text-anchor="end" class="strong">Actual spam ↓</text>
              <text x="40" y="262">score 0</text>
              <text x="560" y="262" text-anchor="end">1</text>
              <text x="300" y="262" text-anchor="middle">
                validation messages per score bin (√ scale) · orange = blocked
              </text>
            </svg>
          </figure>
          <div class="confusion-wrap">
            <h3>Validation confusion matrix</h3>
            <Confusion :matrix="liveMetrics.confusion" label="Validation confusion matrix" /></div
        ></template>
        <template v-if="currentEvaluation"
          ><div class="inbox">
            <Plot
              title="Validation precision–recall curve"
              x-label="Recall"
              y-label="Precision"
              :lines="[
                { name: 'Selected classifier', color: '#45657e', points: currentEvaluation.pr },
                {
                  name: 'Constant-score reference',
                  color: '#84929c',
                  points: [
                    [0, currentEvaluation.prevalence],
                    [1, currentEvaluation.prevalence],
                  ],
                  dashed: true,
                },
              ]"
              :points="
                liveMetrics ? [{ x: liveMetrics.recall, y: liveMetrics.precision, label: 1 }] : []
              "
              :bounds="[0, 1, 0, 1]"
            /><Plot
              title="Validation ROC curve"
              x-label="False positive rate"
              y-label="Recall"
              :lines="[
                { name: 'Selected classifier', color: '#45657e', points: currentEvaluation.roc },
                {
                  name: 'Diagonal reference',
                  color: '#84929c',
                  points: [
                    [0, 0],
                    [1, 1],
                  ],
                  dashed: true,
                },
              ]"
              :points="
                liveMetrics
                  ? [
                      {
                        x: liveMetrics.false_positive_rate,
                        y: liveMetrics.recall,
                        label: 1,
                      },
                    ]
                  : []
              "
              :bounds="[0, 1, 0, 1]"
            />
          </div>
          <h3>Inspect false alarms and missed spam</h3>
          <p>Most confident mistakes at the selected threshold are shown first.</p>
          <article v-for="(item, i) in liveErrors" :key="i" class="error-card">
            <span class="pill"
              >True {{ label(item.label) }} → predicted {{ label(item.prediction) }} · score
              {{ fmt(item.probability) }}</span
            >
            <p>{{ item.text }}</p>
          </article>
          <p v-if="errorsCurrent && !liveErrors.length">No validation errors at this threshold.</p>
          <p v-if="!errorsCurrent">Release the slider to update the error examples.</p></template
        >
        <div v-if="activeRun" class="panel final-panel">
          <h3>Freeze a reasoned decision, then test it once</h3>
          <label
            >Model and threshold rationale<textarea
              v-model="reason"
              rows="4"
              :disabled="!!final"
              placeholder="Explain the validation evidence, your error tradeoff and a limitation of this dataset."
            /></label
          ><button
            class="primary"
            :disabled="!ready || busy || !reason.trim() || !!final"
            @click="finalTest"
          >
            Freeze decision and evaluate test set</button
          ><template v-if="final"
            ><h3>Final test result · decision frozen</h3>
            <p>{{ final.id }} · threshold {{ final.threshold.toFixed(2) }} · {{ final.reason }}</p>
            <div class="spam-metrics">
              <span
                >Test accuracy<strong>{{ fmt(final.test.accuracy) }}</strong></span
              ><span
                >Test precision<strong>{{ fmt(final.test.precision) }}</strong></span
              ><span
                >Test recall<strong>{{ fmt(final.test.recall) }}</strong></span
              ><span
                >Test AP<strong>{{ fmt(final.test.average_precision) }}</strong></span
              >
            </div>
            <Confusion :matrix="final.test.confusion" label="Test confusion matrix" />
            <p class="muted">
              The test set has now been used. Refitting cannot make it unseen again.
            </p></template
          ><button :disabled="!runs.length" @click="exportResults">Export experiment record</button>
        </div>
      </template>
      <aside class="concept-note">
        <span>Takeaway</span>
        <p>{{ section.takeaway }}</p>
      </aside>
    </section>
    <section id="python" class="chapter-python">
      <div class="section-label"><span>03</span> READ THE PYTHON</div>
      <h2>Connect the idea to Python</h2>
      <PythonCode :code="section.example" :title="`${section.title} · worked example`" />
      <details v-if="section.functions.length" class="implementation-details">
        <summary>Inspect the supporting functions</summary>
        <PythonCode :code="sourceCode" :title="`experiment.py · ${section.functions.join(', ')}`" />
      </details>
    </section>
    <section class="python-practice">
      <div class="section-label"><span>04</span> RUN AND EXPLAIN</div>
      <h2>{{ section.title }} · a runnable experiment</h2>
      <p>{{ section.experiment }}</p>
      <div class="editor-toolbar">
        <span>Python · editable experiment</span
        ><button :disabled="running" @click="code = section.starter">Reset example</button>
      </div>
      <PythonEditor v-model="code" />
      <div class="editor-actions">
        <button class="primary" :disabled="!ready || busy" @click="runCode">
          {{ running ? 'Running Python…' : 'Run Python →' }}</button
        ><button v-if="running" @click="start">Stop and reset Python</button>
      </div>
      <div v-if="outputs[chapter]" class="python-output" aria-label="Python output">
        <pre>{{ outputs[chapter]!.stdout || 'Use print(...) to inspect a value.' }}</pre>
        <p v-if="outputs[chapter]!.error" class="execution-error" role="alert">
          {{ outputs[chapter]!.error }}
        </p>
      </div>
      <p class="muted">
        Setup supplies np, X_train, y_train, X_val, y_val and the metrics helper. Import the NLTK
        and sklearn tools in your code. Each browser run starts with fresh copies of the train /
        validation arrays; no test arrays are supplied.
      </p>
      <p v-if="section.transition" class="lesson-transition">{{ section.transition }}</p>
      <div class="notebook-bridge">
        <div>
          <span class="eyebrow">THE SAME EXPERIMENT IN YOUR NOTEBOOK</span>
          <h3>
            §{{ curriculum.chapters.findIndex((c) => c.id === chapter) + 1 }} · {{ section.title }}
          </h3>
          <p>
            The downloadable notebook covers every chapter with the same scientific functions,
            figures and executable experiments. Record what you changed, what the evidence shows and
            what it cannot establish.
          </p>
        </div>
      </div>
    </section>
  </div>
</template>
<style scoped>
.spam-lesson {
  padding-bottom: 28px;
}
.learning-route {
  display: flex;
  flex-wrap: wrap;
  gap: 8px 12px;
  align-items: center;
  padding: 14px 0;
  border-bottom: 1px solid var(--line);
  color: var(--muted);
  font-size: 0.84rem;
}
.extension-note {
  margin-top: 20px;
  padding: 14px 18px;
  background: #edf3f7;
  border-radius: 5px;
  line-height: 1.7;
}
.worked-example {
  margin: 24px 0;
}
.worked-example p {
  max-width: 75ch;
}
.formula-recap,
.implementation-details {
  margin: 20px 0;
}
summary {
  cursor: pointer;
  color: var(--accent);
  padding: 10px 0;
  font-weight: 500;
}
.token-stages {
  display: grid;
  gap: 10px;
  margin-top: 20px;
}
.token-stages dt {
  font-weight: 600;
}
.token-stages dd {
  margin: 0 0 10px;
  overflow-wrap: anywhere;
}
.task-flow {
  background: #f4f7f9;
  border-radius: 5px;
  padding: 14px 20px;
}
.lesson-transition {
  padding-top: 18px;
  border-top: 1px solid var(--line);
}
.documentation-link {
  font-size: 0.85rem;
}

.key-points {
  margin: 8px 0 22px;
  padding-left: 0;
  list-style: none;
}
.key-points li {
  position: relative;
  padding: 9px 0 9px 26px;
  border-bottom: 1px solid var(--line);
  font-size: 0.98rem;
}
.key-points li::before {
  content: '';
  position: absolute;
  left: 4px;
  top: 19px;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--accent);
}
.muted {
  color: var(--muted);
  font-size: 0.85rem;
}
.spam-text {
  color: #aa613d;
}
.tag {
  display: inline-block;
  padding: 1px 9px;
  border-radius: 10px;
  font-size: 0.72rem;
  font-weight: 600;
  color: white;
  background: #45657e;
}
.tag.spam {
  background: #aa613d;
}
.spam-lesson mark {
  background: #f6dccb;
  color: inherit;
  padding: 0 2px;
  border-radius: 2px;
}
.raw-file {
  font:
    0.78rem/1.7 ui-monospace,
    Menlo,
    monospace;
  background: #f5f7f9;
  border: 1px solid var(--line);
  border-radius: 4px;
  padding: 12px;
  overflow-x: auto;
}
.raw-file > div {
  white-space: nowrap;
}
.raw-file .tag {
  font-family: var(--font-sans);
  min-width: 42px;
  text-align: center;
}
.line-no {
  display: inline-block;
  width: 24px;
  color: #9dabb5;
}
.tab-mark {
  color: #aa613d;
  margin: 0 6px;
}
.heat {
  text-align: center !important;
  font-variant-numeric: tabular-nums;
}
.spam-table td.highlight {
  outline: 2px solid #aa613d;
  outline-offset: -2px;
}
.colored-message {
  font-size: 1.1rem;
  line-height: 2;
}

.vote-bar {
  display: flex;
  gap: 3px;
  margin: 10px 0 16px;
}
.vote-bar span {
  flex: 1;
  text-align: center;
  padding: 8px 0;
  color: white;
  font-size: 0.75rem;
  font-weight: 600;
  background: #45657e;
  border-radius: 3px;
}
.vote-bar .spam {
  background: #aa613d;
}
.neighbour {
  margin: 8px 0;
  padding: 12px 16px;
}
.neighbour p {
  margin: 6px 0 0;
}
.neighbour-head {
  display: flex;
  gap: 10px;
  align-items: center;
  font-size: 0.75rem;
}
.distance-track {
  flex: 0 1 160px;
  height: 8px;
  background: #eef1f3;
  border-radius: 4px;
  overflow: hidden;
}
.distance-track i {
  display: block;
  height: 100%;
  background: #84929c;
}
.small-multiples {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 0 20px;
}
.score-histogram svg {
  width: 100%;
  display: block;
}
.score-histogram text {
  font: 11px system-ui;
  fill: #65717c;
}
.score-histogram .strong {
  font-weight: 600;
  fill: #202e3a;
}
.mechanism {
  padding-left: 22px;
  font-size: 0.88rem;
  color: var(--muted);
}
.mechanism li {
  margin: 10px 0;
}
.inbox {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
  margin: 20px 0;
}
.mail-card,
.error-card {
  padding: 18px;
  border: 1px solid var(--line);
  background: var(--surface);
  border-radius: 4px;
  overflow-wrap: anywhere;
  min-width: 0;
}
.mail-card p,
.error-card p {
  font-size: 0.84rem;
}
.error-card {
  margin: 12px 0;
  border-left: 3px solid #aa613d;
}
.spam-lesson textarea,
.spam-lesson input[type='text'] {
  display: block;
  width: 100%;
  padding: 10px 12px;
  border: 1px solid var(--line);
  border-radius: 3px;
  background: white;
  color: var(--ink);
  margin-top: 8px;
  resize: vertical;
}
.spam-lesson label {
  margin-top: 16px;
}
.spam-lesson button {
  margin-right: 8px;
  margin-top: 8px;
}
.spam-metrics {
  display: flex;
  gap: 24px;
  flex-wrap: wrap;
  margin: 22px 0;
}
.spam-metrics > span {
  font-size: 0.74rem;
  color: var(--muted);
}
.spam-metrics strong {
  display: block;
  font-size: 1.5rem;
  font-weight: 500;
  color: var(--ink);
}
.audit {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 15px;
  margin: 25px 0;
}
.audit > span {
  font-size: 1.5rem;
  color: var(--accent);
}
.audit small {
  display: block;
  font-size: 0.7rem;
  color: var(--muted);
  max-width: 120px;
}
.audit b {
  font-weight: 400;
  color: var(--muted);
}
.split-row {
  padding: 15px 0;
  border-top: 1px solid var(--line);
  font-size: 0.8rem;
}
.split-row small {
  color: var(--muted);
}
.class-bar {
  display: flex;
  height: 34px;
  color: white;
  border-radius: 3px;
  overflow: hidden;
  margin: 9px 0;
}
.class-bar > span {
  background: #45657e;
  padding: 6px;
  font-size: 0.72rem;
  white-space: nowrap;
  min-width: 0;
}
.class-bar > .spam {
  background: #aa613d;
}
.table-scroll {
  max-width: 100%;
  overflow: auto;
  margin: 20px 0;
}
.spam-table {
  border-collapse: collapse;
  width: 100%;
  font-size: 0.76rem;
}
.spam-table th,
.spam-table td {
  padding: 10px 12px;
  border-bottom: 1px solid var(--line);
  text-align: left;
  vertical-align: top;
}
.spam-table th {
  font-weight: 550;
}
.highlight {
  background: #e7eef3;
}
.spam-table mark {
  background: #d5e4ee;
  color: #29485e;
  padding: 1px 2px;
}
.word-list {
  display: flex;
  flex-wrap: wrap;
  gap: 5px;
  margin: 18px 0;
}
.word-list button {
  margin: 0;
}
.word-list [aria-pressed='true'] {
  background: #45657e;
  color: white;
}
.histogram {
  margin: 20px 0;
}
.histogram svg {
  width: 100%;
  display: block;
}
.histogram text {
  font: 11px system-ui;
  fill: #65717c;
}
.histogram figcaption {
  font-size: 0.75rem;
}
.ham-key {
  color: #45657e;
}
.spam-key {
  color: #aa613d;
}
.contribution {
  display: grid;
  grid-template-columns: minmax(90px, 1fr) 2fr 65px;
  align-items: center;
  gap: 12px;
  margin: 10px 0;
  font-size: 0.78rem;
}
.contribution code {
  overflow-wrap: anywhere;
}
.contribution > span {
  text-align: right;
  font-variant-numeric: tabular-nums;
}
.signed-track {
  height: 20px;
  position: relative;
  background: linear-gradient(to right, #f5f7f9 49.7%, #9dabb5 49.7%, #9dabb5 50.3%, #f5f7f9 50.3%);
}
.signed-track i {
  position: absolute;
  height: 12px;
  top: 4px;
}
.signed-track .positive {
  left: 50%;
  background: #aa613d;
}
.signed-track .negative {
  right: 50%;
  background: #45657e;
}
.folds {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 8px;
  margin: 20px 0;
}
.folds span {
  background: #edf2f6;
  border: 1px solid #cddae4;
  padding: 15px 7px;
  text-align: center;
  font-size: 0.82rem;
}
.folds small {
  display: block;
  font-size: 0.68rem;
}
.folds .heldout {
  background: #fbede5;
  border-color: #b77855;
  color: #8d4e2a;
}
.pipeline {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
  font-size: 0.78rem;
}
.pipeline span {
  padding: 10px;
  background: #f1f4f6;
  border: 1px solid var(--line);
}
.confusion-wrap {
  margin: 25px 0;
}
.final-panel {
  margin-top: 30px;
}
.spam-lesson pre {
  white-space: pre-wrap;
  overflow-wrap: anywhere;
}
.spam-lesson .pill {
  white-space: normal;
}
@media (max-width: 650px) {
  .inbox {
    grid-template-columns: 1fr;
  }
  .folds {
    gap: 3px;
  }
  .folds span {
    padding: 10px 3px;
    font-size: 0.7rem;
  }
  .folds small {
    font-size: 0.6rem;
  }
  .spam-metrics {
    gap: 18px;
  }
  .spam-metrics strong {
    font-size: 1.3rem;
  }
  .small-multiples {
    grid-template-columns: 1fr;
  }
  .contribution {
    grid-template-columns: 80px minmax(0, 1fr) 48px;
    gap: 5px;
  }
  .audit {
    gap: 10px;
  }
  .spam-table th:first-child {
    min-width: 150px;
  }
}
</style>
