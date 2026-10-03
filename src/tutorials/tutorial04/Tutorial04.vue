<script setup lang="ts">
import { computed, onMounted, onUnmounted, reactive, ref, watch } from 'vue'
import PixelImage from '../../components/PixelImage.vue'
import LineChart from '../../components/LineChart.vue'
import { createPython } from '../../runtime/python'
import pythonSource from './experiment.py?raw'
import { learning } from './learning'
import ChapterTheory from './ChapterTheory.vue'
import PythonPractice from './PythonPractice.vue'
import StepExplorer from './StepExplorer.vue'
import BeyondLinear from './BeyondLinear.vue'
import PythonCode from '../../components/PythonCode.vue'

const props = defineProps<{ chapter: string }>()
const learningSection = computed(() => learning[props.chapter] ?? learning.data!)
type Digit = { id: number; pixels: number[]; label: number }
type Initial = { counts: { train: number; validation: number; test: number }; gallery: Digit[] }
type Metrics = { loss: number; accuracy: number; confusion: number[][] }
type Row = { epoch: number; train: Metrics; validation: Metrics }
type Config = {
  lr: number
  epochs: number
  batch: number
  representation: string
  normalize: boolean
  augment: boolean
}
type Run = {
  id: string
  config: Config
  history: Row[]
  weights: number[]
  bias: number
  updates: number
  trainingSize: number
  errors: { pixels: number[]; label: number; probability: number }[]
}
type Preview = {
  pixels: number[]
  original: number[]
  label: number
  minimum: number
  maximum: number
  mean: number
}
type Score = {
  pixels: number[]
  weights: number[]
  contributions: number[]
  score: number
  probability: number
  label: number
}
type Update = {
  pixels: number[]
  trace: { line: number; values: Record<string, number | number[]> }[]
  label: number
  before: number
  after: number
  lossBefore: number
  lossAfter: number
  residual: number
  gradient: number[]
  weights: number[]
  bias: number
  biasGradient: number
}
const runtime = createPython('tutorial04')
const { ready, status, error: runtimeError } = runtime
const initial = ref<Initial>()
const sample = ref(0)
const digit = computed(() => initial.value?.gallery.find((d) => d.id === sample.value))
const preview = ref<Preview>()
const score = ref<Score>()
const update = ref<Update>()
const kind = ref('raw')
const amount = ref(1)
const weight = ref(1)
const bias = ref(0)
const rate = ref(0.1)
const probability = ref(0.5)
const actual = ref(1)
const config = reactive<Config>({
  lr: 0.1,
  epochs: 25,
  batch: 32,
  representation: 'raw',
  normalize: true,
  augment: false,
})
const runs = ref<Run[]>([])
const currentId = ref('')
const current = computed(() => runs.value.find((r) => r.id === currentId.value))
const progress = ref<Row[]>([])
const training = ref(false)
const executing = ref(false)
const practiceOutputs = reactive<Record<string, { stdout: string; error: string | null }>>({})
const evaluating = ref(false)
const error = ref('')
const shifted = ref<Metrics>()
const testResult = ref<Metrics>()
const decision = ref('')
const testedId = ref('')
const sceneBusy = ref(false)
const pct = (v: number) => `${(v * 100).toFixed(1)}%`
const num = (v: number) => (Math.abs(v) > 999 ? v.toExponential(2) : v.toFixed(3))
const label = (v: number) => (v === 1 ? '8' : '3')
const history = computed(() => (training.value ? progress.value : (current.value?.history ?? [])))
const final = computed(() => current.value?.history.at(-1))
const curves = computed(() => [
  { name: 'Training', color: '#1a725a', values: history.value.map((r) => r.train.loss) },
  { name: 'Validation', color: '#c45d3b', values: history.value.map((r) => r.validation.loss) },
])
const lossValue = computed(
  () => -(actual.value ? Math.log(probability.value) : Math.log(1 - probability.value)),
)
const lossCurves = [
  {
    name: 'Actual digit: 8 (y = 1)',
    color: '#1a725a',
    values: Array.from({ length: 99 }, (_, i) => -Math.log((i + 1) / 100)),
  },
  {
    name: 'Actual digit: 3 (y = 0)',
    color: '#c45d3b',
    values: Array.from({ length: 99 }, (_, i) => -Math.log(1 - (i + 1) / 100)),
  },
]
const amountRange = computed(() =>
  kind.value === 'shift'
    ? { min: -4, max: 4, step: 1 }
    : kind.value === 'brightness'
      ? { min: -0.3, max: 0.3, step: 0.05 }
      : { min: 0.2, max: 3, step: 0.2 },
)
function code(name: string) {
  const start = pythonSource.indexOf(`def ${name}(`)
  const end = pythonSource.indexOf('\n\ndef ', start + 1)
  return pythonSource.slice(start, end < 0 ? undefined : end).trim()
}
let revision = 0
let session = 0
let timer: ReturnType<typeof setTimeout> | undefined
async function refreshScene() {
  if (!ready.value || training.value || executing.value) return
  const ticket = ++revision
  sceneBusy.value = true
  try {
    if (props.chapter === 'prepare') {
      const result = await runtime.request<Preview>('preview', {
        sample: sample.value,
        kind: kind.value,
        amount: amount.value,
      })
      if (ticket === revision) preview.value = result
    } else if (props.chapter === 'model') {
      const result = await runtime.request<Score>('score', {
        sample: sample.value,
        weight: weight.value,
        bias: bias.value,
      })
      if (ticket === revision) score.value = result
    } else if (props.chapter === 'update') {
      const result = await runtime.request<Update>('update', {
        sample: sample.value,
        lr: rate.value,
      })
      if (ticket === revision) update.value = result
    }
  } catch (e) {
    if (ticket === revision) error.value = String(e)
  } finally {
    if (ticket === revision) sceneBusy.value = false
  }
}
watch(
  [() => props.chapter, sample, kind, amount, weight, bias, rate, ready, training, executing],
  () => {
    ++revision
    clearTimeout(timer)
    timer = setTimeout(refreshScene, 100)
  },
)
watch(kind, (k) => {
  amount.value = k === 'brightness' ? 0.15 : 1
})
watch(currentId, () => {
  shifted.value = undefined
  testResult.value = undefined
  testedId.value = ''
  decision.value = ''
})
async function start() {
  ++revision
  const generation = ++session
  sceneBusy.value = false
  runs.value = []
  currentId.value = ''
  progress.value = []
  preview.value = undefined
  score.value = undefined
  update.value = undefined
  training.value = false
  executing.value = false
  evaluating.value = false
  error.value = ''
  initial.value = undefined
  try {
    const result = await runtime.start<Initial>()
    if (generation !== session) return
    initial.value = result
    sample.value = initial.value.gallery[0]!.id
  } catch (e) {
    if (generation === session) error.value = String(e)
  }
}
async function fit() {
  const generation = session
  training.value = true
  progress.value = []
  error.value = ''
  try {
    const result = await runtime.request<Run>('fit', { ...config }, (row) =>
      progress.value.push(row as Row),
    )
    if (generation !== session) return
    runs.value = [...runs.value, result].slice(-8)
    currentId.value = result.id
  } catch (e) {
    if (generation === session) error.value = String(e)
  } finally {
    if (generation === session) training.value = false
  }
}
async function evaluate(split: 'test' | 'validation') {
  if (!current.value) return
  evaluating.value = true
  error.value = ''
  const generation = session
  try {
    const result = await runtime.request<Metrics>('evaluate', {
      model_id: current.value.id,
      split,
      shift: split === 'validation' ? 1 : 0,
    })
    if (generation !== session) return
    if (split === 'validation') shifted.value = result
    else {
      testResult.value = result
      testedId.value = current.value.id
    }
  } catch (e) {
    if (generation === session) error.value = String(e)
  } finally {
    if (generation === session) evaluating.value = false
  }
}
async function executeSnippet(code: string) {
  if (!ready.value || executing.value || training.value || evaluating.value) return
  const generation = session
  const chapter = props.chapter
  executing.value = true
  try {
    const result = await runtime.request<{ stdout: string; error: string | null }>('execute', {
      code,
    })
    if (generation === session) practiceOutputs[chapter] = result
  } catch (e) {
    if (generation === session) practiceOutputs[chapter] = { stdout: '', error: String(e) }
  } finally {
    if (generation === session) executing.value = false
  }
}
function exportRuns() {
  const data = runs.value.map((r) => ({
    id: r.id,
    config: r.config,
    history: r.history,
    updates: r.updates,
  }))
  const blob = new Blob(
    [
      JSON.stringify(
        {
          dataset: 'MNIST 3 vs 8',
          splitSeed: 3612,
          runs: data,
          selectedRunId: currentId.value,
          decision: decision.value,
          shiftedValidation: shifted.value,
          test: testResult.value,
        },
        null,
        2,
      ),
    ],
    { type: 'application/json' },
  )
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = 'tutorial04-experiments.json'
  a.click()
  setTimeout(() => URL.revokeObjectURL(url), 1000)
}
onMounted(start)
onUnmounted(() => {
  ++revision
  clearTimeout(timer)
  runtime.dispose()
})
</script>

<template>
  <div v-if="!ready && !runtimeError" class="runtime-bar" role="status">{{ status }}</div>
  <div v-if="error || runtimeError" role="alert" class="error-box">
    {{ error || runtimeError }}
    <p>
      Check the local assets, then restart Python. Earlier experiments in this session will be
      cleared.
    </p>
    <button @click="start">Restart Python</button>
  </div>

  <ChapterTheory :section="learningSection" />
  <section id="experiment" class="chapter-experiment" :aria-busy="sceneBusy">
    <div class="section-label"><span>02</span> EXPLORE THE MECHANISM</div>
    <template v-if="chapter === 'data'">
      <p class="lede">
        Our task: learn to distinguish handwritten <strong>3s</strong> and <strong>8s</strong>, then
        classify images the model has not trained on.
      </p>
      <div class="panel">
        <div class="panel-heading">
          <div>
            <span class="eyebrow">THE DATASET</span>
            <h2>Different handwriting. Two labels.</h2>
          </div>
          <span class="pill">MNIST · 28 × 28</span>
        </div>
        <div v-if="initial" class="gallery">
          <button
            v-for="item in initial.gallery"
            :key="item.id"
            :class="['digit-button', { selected: sample === item.id }]"
            :aria-label="`Inspect digit ${label(item.label)}, sample ${item.id}`"
            :aria-pressed="sample === item.id"
            @click="sample = item.id"
          >
            <PixelImage
              :pixels="item.pixels"
              :label="`${label(item.label)} · y = ${item.label}`"
              :size="70"
            />
          </button>
        </div>
        <p v-else class="placeholder">Loading the handwritten digits…</p>
      </div>
      <div class="two-col">
        <div class="panel">
          <h2>One image → one row</h2>
          <div v-if="digit" class="image-and-text">
            <PixelImage :pixels="digit.pixels" label="One training image" />
            <div>
              <div class="equation">28 × 28 → 784</div>
              <p>
                Flattening changes the shape of the array. It preserves every pixel in a fixed
                order.
              </p>
              <code>x[28 × row + col]</code>
            </div>
          </div>
          <p class="muted">
            A feature here is a pixel at a particular position. A label tells us which digit the
            image represents.
          </p>
        </div>
        <div class="panel">
          <h2>Three sets, three jobs</h2>
          <dl class="split-list">
            <div>
              <dt>960 <span>training</span></dt>
              <dd>Used to update the model's parameters.</dd>
            </div>
            <div>
              <dt>240 <span>validation</span></dt>
              <dd>Used to compare settings and choose a model.</dd>
            </div>
            <div>
              <dt>800 <span>test</span></dt>
              <dd>Kept aside until the final evaluation.</dd>
            </div>
          </dl>
          <p class="muted">
            Fixed, balanced splits. The original 1,200 training images are split into training and
            validation; the original test set stays separate.
          </p>
        </div>
      </div>
      <div class="question">
        <span>THINK BEFORE YOU CHANGE IT</span>
        <p>
          If you shuffled the images without shuffling their labels in the same way, what would the
          model learn?
        </p>
      </div>
    </template>

    <template v-else-if="chapter === 'prepare'">
      <p class="lede">
        Make the input explicit: its shape, its scale, and the information it contains. A
        transformation is useful only if it serves the task.
      </p>
      <div class="panel">
        <div class="control-row">
          <label
            >Image operation<select v-model="kind" :disabled="!ready || training || executing">
              <option value="raw">Original</option>
              <option value="blur">Gaussian blur</option>
              <option value="edges">Sobel edges</option>
              <option value="shift">Horizontal translation</option>
              <option value="brightness">Brightness offset (clipped)</option>
            </select></label
          ><label v-if="['blur', 'shift', 'brightness'].includes(kind)"
            >Amount: {{ amount
            }}<input
              v-model.number="amount"
              type="range"
              v-bind="amountRange"
              :disabled="!ready || training || executing" /></label
          ><label
            >Training example<select
              v-model.number="sample"
              :disabled="!ready || training || executing"
            >
              <option v-for="item in initial?.gallery" :key="item.id" :value="item.id">
                {{ label(item.label) }} · sample {{ item.id }}
              </option>
            </select></label
          >
        </div>
        <div v-if="preview" class="image-row">
          <PixelImage
            :pixels="preview.original"
            label="Original · fixed 0–1 display scale"
            :size="224"
          /><span class="image-arrow">→</span
          ><PixelImage
            :pixels="preview.pixels"
            :label="`${kind} · same display scale`"
            :size="224"
          />
          <div class="stat-stack">
            <span>OUTPUT ARRAY</span><strong>28 × 28</strong><span>NUMERICAL RANGE</span
            ><strong>{{ num(preview.minimum) }} → {{ num(preview.maximum) }}</strong>
            <p class="muted">
              Display values above 1 are clipped; the experiment keeps their numerical values.
            </p>
          </div>
        </div>
      </div>
      <div class="two-col">
        <div class="panel">
          <h2>Scale is a training choice</h2>
          <label class="check"
            ><input v-model="config.normalize" type="checkbox" :disabled="training || executing" />
            Divide pixel intensities by 255</label
          >
          <div class="equation">
            {{ config.normalize ? '0 … 255 → 0 … 1' : '0 … 255 → 0 … 255' }}
          </div>
          <p>
            This changes gradient magnitudes and the learning rate that works well. Keep the same
            preprocessing for training, validation and test.
          </p>
          <p class="muted">
            This setting carries forward to the training panel. No model has been retrained here.
          </p>
        </div>
        <div class="panel">
          <h2>Three different decisions</h2>
          <ul class="spaced-list">
            <li><strong>Scaling:</strong> change the numerical units.</li>
            <li>
              <strong>Representation:</strong> feed raw pixels, blurred pixels or edges to the
              model.
            </li>
            <li>
              <strong>Augmentation:</strong> add transformed training examples whose labels remain
              valid.
            </li>
          </ul>
          <p>We will compare these decisions using validation data.</p>
        </div>
      </div>
      <div class="question">
        <span>MAKE A PREDICTION</span>
        <p>
          Would blur help distinguish 3 from 8, or remove useful detail? What comparison would help
          you decide?
        </p>
      </div>
    </template>

    <template v-else-if="chapter === 'model'">
      <p class="lede">
        A logistic classifier gives each pixel a weight, adds the contributions, and converts the
        score into a probability.
      </p>
      <div class="panel">
        <div class="control-row">
          <label
            >Training example<select
              v-model.number="sample"
              :disabled="!ready || training || executing"
            >
              <option v-for="item in initial?.gallery" :key="item.id" :value="item.id">
                {{ label(item.label) }} · sample {{ item.id }}
              </option>
            </select></label
          ><label
            >Weight multiplier: {{ weight
            }}<input
              v-model.number="weight"
              type="range"
              min="-2"
              max="2"
              step=".1"
              :disabled="!ready || training || executing" /></label
          ><label
            >Bias: {{ bias
            }}<input
              v-model.number="bias"
              type="range"
              min="-12"
              max="12"
              step=".5"
              :disabled="!ready || training || executing"
          /></label>
        </div>
        <div v-if="score" class="image-row">
          <PixelImage :pixels="score.pixels" label="Input x" /><PixelImage
            :pixels="score.weights"
            label="Weight w at each position"
            signed
          /><PixelImage :pixels="score.contributions" label="Contribution x × w" signed />
        </div>
        <p class="muted">
          Illustrative weights = mean training 8 − mean training 3, multiplied by the control above.
          These are not SGD-trained weights. Each signed map uses its own colour range.
        </p>
        <div v-if="score" class="metrics">
          <div>
            <span>Score</span><strong>{{ num(score.score) }}</strong>
          </div>
          <div>
            <span>Probability of 8</span><strong>{{ pct(score.probability) }}</strong>
          </div>
          <div>
            <span>Prediction · threshold 0.5</span
            ><strong>{{ score.probability >= 0.5 ? '8' : '3' }}</strong>
          </div>
          <div>
            <span>Actual label</span><strong>{{ label(score.label) }}</strong>
          </div>
        </div>
      </div>
      <div class="question">
        <span>CONNECT THE PICTURE TO THE MODEL</span>
        <p>
          What changes when you reverse the weights? Why can an empty pixel have a large weight but
          contribute zero to this prediction?
        </p>
      </div>
      <div class="takeaway">
        The learnable quantities are <strong>784 weights and one bias</strong>. Next we need an
        objective that tells us how to improve them.
      </div>
    </template>

    <template v-else-if="chapter === 'loss'">
      <p class="lede">
        Accuracy counts correct labels. Training also needs to distinguish a hesitant correct
        prediction from a confident one—and penalise confidently wrong predictions.
      </p>
      <div class="two-col">
        <div class="panel">
          <h2>One prediction, one loss</h2>
          <label
            >Actual digit<select v-model.number="actual">
              <option :value="1">8 · y = 1</option>
              <option :value="0">3 · y = 0</option>
            </select></label
          ><label
            >Predicted probability of 8: {{ pct(probability)
            }}<input v-model.number="probability" type="range" min=".01" max=".99" step=".01"
          /></label>
          <div class="metrics">
            <div>
              <span>Cross-entropy loss</span><strong>{{ num(lossValue) }}</strong>
            </div>
            <div>
              <span>Correct at threshold 0.5?</span
              ><strong>{{ probability >= 0.5 === Boolean(actual) ? 'Yes' : 'No' }}</strong>
            </div>
          </div>
          <p>
            Try p = 0.51 and p = 0.99 when the actual digit is 8. Both count as correct, but their
            losses differ.
          </p>
        </div>
        <div class="panel">
          <LineChart
            :series="lossCurves"
            y-label="cross-entropy loss"
            x-label="predicted probability of 8"
            :x-start="0.01"
            :x-end="0.99"
          />
        </div>
      </div>
      <div class="question">
        <span>WHY THIS OBJECTIVE?</span>
        <p>
          For a true 8, which should cost more: p(8) = 0.4 or p(8) = 0.01? What information would be
          lost if we used only correct / incorrect?
        </p>
      </div>
    </template>

    <template v-else-if="chapter === 'update'">
      <p class="lede">
        Start with zero weights and bias: every image gets p(8) = 0.5. Use one labelled image to
        decide how those parameters should move.
      </p>
      <div class="panel">
        <div class="control-row">
          <label
            >Learn from this image<select
              v-model.number="sample"
              :disabled="!ready || training || executing"
            >
              <option v-for="item in initial?.gallery" :key="item.id" :value="item.id">
                {{ label(item.label) }} · sample {{ item.id }}
              </option>
            </select></label
          ><label
            >Learning rate η<select
              v-model.number="rate"
              :disabled="!ready || training || executing"
            >
              <option v-for="v in [0.001, 0.01, 0.1, 1]" :key="v" :value="v">{{ v }}</option>
            </select></label
          >
        </div>
        <div v-if="update" class="image-row">
          <PixelImage
            v-if="digit"
            :pixels="digit.pixels"
            :label="`Actual digit: ${label(update.label)}`"
          /><PixelImage
            :pixels="update.gradient"
            label="Gradient at zero weights"
            signed
          /><PixelImage :pixels="update.weights" label="Weights after one update" signed />
        </div>
        <div v-if="update" class="metrics">
          <div>
            <span>p − y</span><strong>{{ update.residual }}</strong>
          </div>
          <div>
            <span>p(8), before → after</span
            ><strong>{{ pct(update.before) }} → {{ pct(update.after) }}</strong>
          </div>
          <div>
            <span>Loss on this image</span
            ><strong>{{ num(update.lossBefore) }} → {{ num(update.lossAfter) }}</strong>
          </div>
          <div>
            <span>New bias</span><strong>{{ num(update.bias) }}</strong>
          </div>
        </div>
      </div>
      <div class="question">
        <span>REASON ABOUT THE SIGN</span>
        <p>
          For a true 8, p − y is negative. We subtract the gradient. Should the weights on inked
          pixels increase or decrease?
        </p>
      </div>
      <div class="takeaway">
        Improving this one image does not guarantee improvement on other images. Repeated updates
        from different examples are what turn this into training.
      </div>
    </template>

    <template v-else-if="chapter === 'train'">
      <p class="lede">
        Repeat the update over shuffled batches. Change one setting, train again, and compare the
        learning curves on the same validation set.
      </p>
      <div class="takeaway">
        <strong>Why use batches?</strong> A full-data gradient reads every training example before
        each update. A small batch gives a cheaper, noisier estimate, allowing more frequent
        updates. Batch size 1 is stochastic gradient descent; a small group is minibatch SGD; the
        full set is batch gradient descent. An epoch is one complete pass through the training
        examples.
      </div>
      <div class="training-layout">
        <div class="panel controls-panel">
          <h2>Set up an experiment</h2>
          <fieldset :disabled="!ready || training || executing || evaluating">
            <label
              >Learning rate<select v-model.number="config.lr">
                <option v-for="v in [0.0001, 0.001, 0.01, 0.1, 1, 10]" :key="v" :value="v">
                  {{ v }}
                </option>
              </select></label
            ><label
              >Epochs<input v-model.number="config.epochs" type="number" min="1" max="100" /></label
            ><label
              >Batch size<select v-model.number="config.batch">
                <option v-for="v in [1, 16, 32, 128, 1920]" :key="v" :value="v">
                  {{ v === 1920 ? 'Full training set' : v }}
                </option>
              </select></label
            ><label
              >Representation<select v-model="config.representation">
                <option value="raw">Raw pixels</option>
                <option value="blur">Gaussian blur · σ = 1</option>
                <option value="edges">Sobel edges</option>
              </select></label
            ><label class="check"
              ><input v-model="config.normalize" type="checkbox" /> Scale inputs by 1/255</label
            ><label class="check"
              ><input v-model="config.augment" type="checkbox" /> Add copies shifted 1 px
              right</label
            >
          </fieldset>
          <button
            class="primary"
            :disabled="!ready || training || executing || evaluating"
            @click="fit"
          >
            {{
              training
                ? `Training · epoch ${progress.at(-1)?.epoch ?? 0}/${config.epochs}`
                : 'Train classifier →'
            }}</button
          ><button v-if="training" class="text-button" @click="start">Stop and reset Python</button>
          <p class="muted">
            Same split and seed across runs. Batches are reshuffled every epoch. Augmentation
            doubles training examples and updates per epoch.
          </p>
        </div>
        <div class="panel">
          <div class="panel-heading">
            <h2>Watch the model learn</h2>
            <span class="pill">{{
              training ? 'Training…' : current ? `Run ${current.id}` : 'Ready for your first run'
            }}</span>
          </div>
          <LineChart v-if="history.length" :series="curves" y-label="mean cross-entropy loss" />
          <div v-else class="empty-chart">
            <span>↗</span>
            <h3>Your experiment starts here.</h3>
            <p>
              Train once with the defaults.<br />Then predict what a different learning rate will
              change.
            </p>
          </div>
          <div v-if="final && !training" class="metrics">
            <div>
              <span>Training accuracy</span><strong>{{ pct(final.train.accuracy) }}</strong>
            </div>
            <div>
              <span>Validation accuracy</span><strong>{{ pct(final.validation.accuracy) }}</strong>
            </div>
            <div>
              <span>Parameter updates</span><strong>{{ current?.updates }}</strong>
            </div>
          </div>
          <p v-if="history.length" class="muted">
            Epoch 0 is the untrained model. Losses use the current weights over each whole set;
            individual minibatch losses can fluctuate.
          </p>
        </div>
      </div>
      <div v-if="runs.length" class="panel">
        <div class="panel-heading">
          <h2>Compare your runs</h2>
          <button class="text-button" @click="exportRuns">Export results ↓</button>
        </div>
        <div class="table-scroll">
          <table>
            <thead>
              <tr>
                <th>Run</th>
                <th>Learning rate</th>
                <th>Epochs / batch</th>
                <th>Inputs</th>
                <th>Train accuracy</th>
                <th>Validation accuracy</th>
                <th>Validation loss</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="r in runs" :key="r.id" :class="{ 'selected-row': r.id === currentId }">
                <td>
                  <button
                    :disabled="training || executing || evaluating"
                    :aria-pressed="r.id === currentId"
                    @click="currentId = r.id"
                  >
                    {{ r.id === currentId ? '● ' : '' }}{{ r.id }}
                  </button>
                </td>
                <td>{{ r.config.lr }}</td>
                <td>
                  {{ r.config.epochs }} / {{ r.config.batch === 1920 ? 'full' : r.config.batch }}
                </td>
                <td>
                  {{ r.config.representation }} · {{ r.config.normalize ? 'scaled' : 'unscaled'
                  }}{{ r.config.augment ? ' + shift' : '' }}
                </td>
                <td>{{ pct(r.history.at(-1)!.train.accuracy) }}</td>
                <td>{{ pct(r.history.at(-1)!.validation.accuracy) }}</td>
                <td>{{ num(r.history.at(-1)!.validation.loss) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
        <p class="muted">
          Last eight runs in this session. Selecting a row selects the model used in “Evaluate &
          improve”. Reloading clears runs; export to keep your comparison.
        </p>
      </div>
      <div class="question">
        <span>CHOOSE YOUR NEXT EXPERIMENT</span>
        <p>
          If loss barely changes, what will you try first? If training improves but validation gets
          worse, would more epochs necessarily help?
        </p>
      </div>
    </template>

    <template v-else-if="chapter === 'evaluate'">
      <p class="lede">
        Look at individual mistakes, try a targeted change, then decide which model to keep. Use
        validation results for these decisions.
      </p>
      <div v-if="!current" class="panel empty-chart">
        <h2>Start with a trained model.</h2>
        <p>Run the default experiment first. Its validation errors will appear here.</p>
        <a class="button primary" href="#/tutorials/tutorial04/train">Go to training →</a>
      </div>
      <template v-else>
        <div class="panel">
          <div class="panel-heading">
            <div>
              <span class="eyebrow">SELECTED MODEL · RUN {{ current.id }}</span>
              <h2>What did it learn—and miss?</h2>
            </div>
            <span class="pill">Validation: {{ pct(final!.validation.accuracy) }}</span>
          </div>
          <div class="two-col">
            <div>
              <PixelImage
                :pixels="current.weights"
                label="Learned weights · positive favours 8"
                signed
                :size="224"
              />
              <p class="muted">
                Each weight belongs to a fixed input position. For processed inputs, these weights
                act on {{ current.config.representation }}, not the original intensities.
              </p>
            </div>
            <div>
              <h3>Confusion matrix</h3>
              <table class="confusion">
                <thead>
                  <tr>
                    <th>Actual ↓ / predicted →</th>
                    <th>3</th>
                    <th>8</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="(row, i) in final!.validation.confusion" :key="i">
                    <th>{{ label(i) }}</th>
                    <td v-for="(count, j) in row" :key="j" :class="{ diagonal: i === j }">
                      {{ count }}
                    </td>
                  </tr>
                </tbody>
              </table>
              <p>
                Inspect the most confident mistakes below. Is the image ambiguous, or do you see a
                pattern worth investigating?
              </p>
            </div>
          </div>
          <div class="gallery errors">
            <PixelImage
              v-for="(item, i) in current.errors"
              :key="i"
              :pixels="item.pixels"
              :label="`True ${label(item.label)} · p(8) ${pct(item.probability)}`"
              :size="92"
            />
          </div>
          <p v-if="!current.errors.length">
            No validation errors in this run. This does not establish performance on other data.
          </p>
        </div>
        <div class="two-col">
          <div class="panel">
            <span class="eyebrow">TRY A CONCRETE CHANGE</span>
            <h2>Move the image one pixel</h2>
            <p>
              Keep the weights fixed. Translate validation images one pixel right with zero padding,
              then apply the same preprocessing.
            </p>
            <button
              :disabled="!ready || training || executing || evaluating"
              @click="evaluate('validation')"
            >
              Evaluate shifted validation images
            </button>
            <div v-if="shifted" class="metrics">
              <div>
                <span>Original</span><strong>{{ pct(final!.validation.accuracy) }}</strong>
              </div>
              <div>
                <span>Shifted 1 px right</span><strong>{{ pct(shifted.accuracy) }}</strong>
              </div>
            </div>
            <p>
              Next: add shifted <em>training</em> images and retrain. Compare both original and
              shifted validation accuracy. Does the change help, and what does it cost?
            </p>
            <a href="#/tutorials/tutorial04/train">Return to the training controls →</a>
            <p class="muted">
              One successful shift experiment does not establish invariance to all shifts.
            </p>
          </div>
          <div class="panel">
            <span class="eyebrow">FINISH THE EXPERIMENT</span>
            <h2>Choose, then test</h2>
            <p>
              Write why you selected this run before evaluating on the untouched 800 test images. If
              you subsequently tune to this result, the test set is no longer an independent final
              check.
            </p>
            <label
              >Your model choice<textarea
                v-model="decision"
                placeholder="I selected run … because …"
                rows="3"
                :disabled="!!testResult"
              /></label
            ><button
              :disabled="
                !ready ||
                !decision.trim() ||
                training ||
                executing ||
                evaluating ||
                testedId === current.id
              "
              @click="evaluate('test')"
            >
              Evaluate selected model on test set
            </button>
            <div v-if="testResult" class="metrics">
              <div>
                <span>Final test accuracy</span><strong>{{ pct(testResult.accuracy) }}</strong>
              </div>
              <div>
                <span>Test loss</span><strong>{{ num(testResult.loss) }}</strong>
              </div>
            </div>
            <button v-if="testResult" class="text-button" @click="exportRuns">
              Export experiment and decision ↓
            </button>
          </div>
        </div>
      </template>
      <div class="question">
        <span>YOUR NOTEBOOK TASK</span>
        <p>
          Choose one change. State what you expect, compare it fairly with a baseline, and explain
          what the result supports. An experiment that does not improve accuracy can still teach you
          something.
        </p>
      </div>
    </template>
    <BeyondLinear
      v-if="chapter === 'beyond'"
      :ready="ready && !training && !executing"
      :sample="sample"
      :request="runtime.request"
    />
  </section>
  <section id="python" class="chapter-python">
    <div class="section-label"><span>03</span> CONNECT THE PYTHON</div>
    <StepExplorer v-if="chapter === 'update'" :code="code('step')" :result="update" :lr="rate" />
    <template v-else>
      <h2>The idea, written as an operation.</h2>
      <p>
        Read the inputs, follow the operation, then identify the output. This is the implementation
        used by the browser experiment and included in your notebook.
      </p>
      <PythonCode
        v-for="name in learningSection.functions"
        :key="name"
        :code="code(name)"
        :title="`experiment.py · ${name}()`"
      />
    </template>
  </section>
  <PythonPractice
    :chapter="chapter"
    :section="learningSection"
    :ready="ready"
    :busy="training || executing || evaluating"
    :running="executing"
    :output="practiceOutputs[chapter]"
    @run="executeSnippet"
    @stop="start"
  />
</template>
