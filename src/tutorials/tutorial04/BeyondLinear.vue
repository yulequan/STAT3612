<script setup lang="ts">
import { computed, onUnmounted, ref, watch } from 'vue'
import MathText from '../../components/MathText.vue'
import PixelImage from '../../components/PixelImage.vue'
const props = defineProps<{
  ready: boolean
  sample: number
  request: <T>(action: string, params?: Record<string, unknown>) => Promise<T>
}>()
const mode = ref('linear')
const points = [
  [0, 0, 0],
  [0, 1, 1],
  [1, 0, 1],
  [1, 1, 0],
]
function score(x: number, y: number) {
  if (mode.value === 'interaction') return 4 * (x + y - 2 * x * y - 0.5)
  if (mode.value === 'hidden') return 4 * (Math.max(0, x - y) + Math.max(0, y - x) - 0.5)
  return 4 * (x + y - 0.5)
}
const cells = computed(() =>
  Array.from({ length: 900 }, (_, i) => {
    const x = i % 30,
      y = Math.floor(i / 30)
    const p = 1 / (1 + Math.exp(-score(x / 29, y / 29)))
    return { x: 50 + x * 8, y: 280 - y * 8, p }
  }),
)
const correct = computed(
  () => points.filter(([x, y, target]) => Number(score(x!, y!) >= 0) === target).length,
)
const formula = computed(() =>
  mode.value === 'linear'
    ? 'z=4(x_1+x_2-0.5)'
    : mode.value === 'interaction'
      ? 'z=4(x_1+x_2-2x_1x_2-0.5)'
      : 'h_1=\\operatorname{ReLU}(x_1-x_2),\\;h_2=\\operatorname{ReLU}(x_2-x_1),\\;z=4(h_1+h_2-0.5)',
)
const kind = ref('vertical'),
  row = ref(10),
  col = ref(10)
type Convolution = {
  image: number[]
  kernel: number[][]
  patch: number[][]
  products: number[][]
  output: number[]
  value: number
}
const convolution = ref<Convolution>()
const error = ref('')
let revision = 0
let timer: ReturnType<typeof setTimeout>
watch(
  [() => props.ready, () => props.sample, kind, row, col],
  () => {
    const ticket = ++revision
    clearTimeout(timer)
    if (!props.ready) return
    timer = setTimeout(async () => {
      try {
        const result = await props.request<Convolution>('convolution', {
          sample: props.sample,
          kind: kind.value,
          row: row.value,
          col: col.value,
        })
        if (ticket === revision) {
          convolution.value = result
          error.value = ''
        }
      } catch (e) {
        if (ticket === revision) error.value = String(e)
      }
    }, 100)
  },
  { immediate: true },
)
onUnmounted(() => {
  revision++
  clearTimeout(timer)
})
</script>
<template>
  <section class="beyond-section">
    <h2>1. What a straight boundary cannot do</h2>
    <p>
      In XOR, the target is 1 when the two inputs differ. The positive examples occupy opposite
      corners. Any line that separates one pair of corners fails on the other pair. This is a
      limitation of the decision rule, not a reason to run more SGD steps.
    </p>
    <div class="panel">
      <div class="control-row">
        <label
          >Decision rule<select v-model="mode">
            <option value="linear">Linear score on the original inputs</option>
            <option value="interaction">Add a hand-designed interaction</option>
            <option value="hidden">Use two ReLU hidden units</option>
          </select></label
        ><span class="pill">{{ correct }} / 4 XOR examples classified correctly</span>
      </div>
      <div class="xor-layout">
        <svg
          viewBox="0 0 350 340"
          class="xor-plot"
          role="img"
          aria-label="Decision regions for the four XOR examples"
        >
          <rect
            v-for="(cell, i) in cells"
            :key="i"
            :x="cell.x"
            :y="cell.y"
            width="8.5"
            height="8.5"
            :fill="cell.p >= 0.5 ? '#bbccd9' : '#ead0ba'"
          />
          <g v-for="([x, y, target], i) in points" :key="i">
            <circle
              :cx="54 + x! * 232"
              :cy="284 - y! * 232"
              r="10"
              :fill="target ? '#1b365d' : '#b66a41'"
              stroke="#faf9f5"
              stroke-width="3"
            />
            <text :x="54 + x! * 232" :y="y ? 34 : 316" text-anchor="middle">
              ({{ x }}, {{ y }}) · y={{ target }}
            </text>
          </g>
          <text x="165" y="337" text-anchor="middle">input x₁</text>
          <text transform="translate(16 180) rotate(-90)" text-anchor="middle">input x₂</text>
        </svg>
        <div>
          <MathText :tex="formula" />
          <p v-if="mode === 'linear'">
            This particular line gets three examples right. No alternative straight line can
            classify all four correctly. Moving the same kind of boundary cannot remove that
            limitation.
          </p>
          <p v-else-if="mode === 'interaction'">
            The interaction x₁x₂ changes the feature space. Logistic regression can now separate the
            examples: it remains linear in its features, but the features are nonlinear in the
            original inputs.
          </p>
          <p v-else>
            The hidden units compute nonlinear features. This is a tiny MLP with constructed
            weights. In a learned MLP, backpropagation would update the hidden weights as well as
            the output weights.
          </p>
          <p class="muted">
            These are constructed decision rules, not training results. Background colours show
            predicted regions; the point colours show true labels. Switching rules changes the
            assumption, not just the optimiser.
          </p>
        </div>
      </div>
    </div>
  </section>
  <section class="beyond-section">
    <h2>2. What if a useful pattern moves?</h2>
    <p>
      A dense layer can learn a separate weight for every location. Convolution applies the
      <em>same</em> small filter at every location. Move the highlighted window and inspect the
      multiply-and-sum operation. A CNN learns these filters from data; the filters here are fixed
      examples so their behaviour is visible.
    </p>
    <div class="panel">
      <div class="control-row">
        <label
          >Example filter<select v-model="kind" :disabled="!ready">
            <option value="vertical">Vertical contrast</option>
            <option value="horizontal">Horizontal contrast</option>
            <option value="average">Local average</option>
          </select></label
        ><label
          >Window row: {{ row
          }}<input v-model.number="row" type="range" min="0" max="25" :disabled="!ready" /></label
        ><label
          >Window column: {{ col
          }}<input v-model.number="col" type="range" min="0" max="25" :disabled="!ready"
        /></label>
      </div>
      <p v-if="error" role="alert">{{ error }}</p>
      <div v-if="convolution" class="convolution-layout">
        <PixelImage
          :pixels="convolution.image"
          label="Input · highlighted 3 × 3 window"
          :patch="{ row, col, size: 3 }"
          :size="224"
        />
        <div class="kernel-calculation">
          <span class="eyebrow">PATCH × SHARED FILTER</span>
          <div class="kernel-grid">
            <template v-for="(line, i) in convolution.patch" :key="i"
              ><span v-for="(pixel, j) in line" :key="j"
                >{{ pixel.toFixed(2)
                }}<small>× {{ convolution.kernel[i]![j]!.toFixed(2) }}</small></span
              ></template
            >
          </div>
          <span class="kernel-result"
            >sum = <strong>{{ convolution.value.toFixed(4) }}</strong></span
          >
        </div>
        <PixelImage
          :pixels="convolution.output"
          :side="26"
          label="Feature map · 26 × 26"
          :patch="{ row, col, size: 1 }"
          signed
          :size="208"
        />
      </div>
      <MathText tex="a_{r,c}=\sum_{u=0}^{2}\sum_{v=0}^{2}K_{u,v}\,x_{r+u,c+v}" />
      <p class="muted">
        Stride 1, no padding, no bias: 28 − 3 + 1 = 26 positions per axis. Deep-learning libraries
        usually call this cross-correlation operation “convolution”; the kernel is not flipped.
      </p>
    </div>
    <div class="concept-note">
      <span>From an operation to an architecture</span>
      <p>
        One filter is not a classifier. A CNN usually combines learned convolutions, nonlinearities
        and a classification head. Downsampling or pooling changes spatial resolution; global
        pooling can reduce position dependence, but padding, stride, finite images and the rest of
        the architecture still matter.
      </p>
    </div>
  </section>
  <section class="beyond-section">
    <h2>3. Choose the next method for a reason</h2>
    <div class="table-scroll">
      <table>
        <thead>
          <tr>
            <th>Direction</th>
            <th>What changes?</th>
            <th>A useful next question</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td>Better features + logistic regression</td>
            <td>Keep the transparent classifier; change the representation.</td>
            <td>Does the feature preserve the information and robustness the task needs?</td>
          </tr>
          <tr>
            <td>Nearest neighbours / kernel methods</td>
            <td>Use similarity, possibly in a nonlinear feature space.</td>
            <td>Does the distance make sense for shifted images? What is the prediction cost?</td>
          </tr>
          <tr>
            <td>MLP</td>
            <td>Learn nonlinear feature interactions with dense layers.</td>
            <td>Can it fit useful interactions without overfitting this small dataset?</td>
          </tr>
          <tr>
            <td>CNN</td>
            <td>Add local connections and shared filters.</td>
            <td>Do the image’s local patterns and shifts justify these assumptions?</td>
          </tr>
        </tbody>
      </table>
    </div>
    <div class="question">
      <span>DESIGN THE NEXT INVESTIGATION</span>
      <p>
        Compare the linear baseline, a small MLP and a small CNN on the same splits. Choose settings
        using validation data. Report both original-image and shifted-image performance, together
        with training cost. What result would make you keep the simpler model?
      </p>
    </div>
    <p class="further-reading">
      Continue learning:
      <a href="https://cs231n.github.io/convolutional-networks/" target="_blank" rel="noreferrer"
        >CS231n · Convolutional networks ↗</a
      >
      ·
      <a
        href="https://docs.pytorch.org/tutorials/beginner/basics/intro.html"
        target="_blank"
        rel="noreferrer"
        >PyTorch · A complete learning workflow ↗</a
      >
    </p>
  </section>
</template>
