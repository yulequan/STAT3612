<script setup lang="ts">
// Static teaching illustrations, one per chapter. Values are constructed for
// explanation unless the caption says they come from this dataset.
defineProps<{ chapter: string }>()
const HAM = '#45657e',
  SPAM = '#aa613d'

// Shared helpers for small function plots.
const curve = (
  f: (t: number) => number,
  x0: number,
  x1: number,
  sx: (t: number) => number,
  sy: (v: number) => number,
  n = 80,
) =>
  Array.from({ length: n + 1 }, (_, i) => {
    const t = x0 + ((x1 - x0) * i) / n
    return `${i ? 'L' : 'M'}${sx(t).toFixed(1)},${sy(f(t)).toFixed(1)}`
  }).join(' ')

// Text: three toy training documents and one new message, as counts.
const toyRows: { text: string; counts: number[] }[] = [
  { text: 'free prize now', counts: [0, 0, 0, 0, 1, 1, 1, 0, 0] },
  { text: 'are you free after class', counts: [0, 1, 1, 1, 1, 0, 0, 0, 1] },
  { text: 'win a prize prize', counts: [1, 0, 0, 0, 0, 0, 2, 1, 0] },
  { text: 'NEW: free meeting tomorrow', counts: [0, 0, 0, 0, 1, 0, 0, 0, 0] },
]

// Logistic: a waterfall of contributions, then the sigmoid.
const steps = [
  { name: 'bias b', value: -3.0 },
  { name: 'claim', value: 1.6 },
  { name: 'free', value: 1.1 },
  { name: 'prize', value: 2.2 },
  { name: 'your', value: -0.4 },
]
const zTotal = steps.reduce((s, v) => s + v.value, 0)
const wy = (z: number) => 30 + (3 - z) * 24
const waterfall = steps.reduce<{ name: string; value: number; from: number; to: number }[]>(
  (bars, s) => {
    const from = bars.at(-1)?.to ?? 0
    return [...bars, { ...s, from, to: from + s.value }]
  },
  [],
)
const sig = (z: number) => 1 / (1 + Math.exp(-z))
const sx = (z: number) => 480 + ((z + 6) / 12) * 220
const sy = (p: number) => 200 - p * 160
const sigmoidPath = curve(sig, -6, 6, sx, sy)

// Regularization: a conceptual fit curve plus real weights from the count model.
const rx = (t: number) => 50 + t * 270
const ry = (v: number) => 200 - v * 150
const trainCurve = curve((t) => 0.35 + 0.63 * (1 - Math.exp(-3.2 * t)), 0, 1, rx, ry)
const validCurve = curve((t) => 0.35 + 0.5 * (1 - Math.exp(-4 * t)) - 0.28 * t * t, 0, 1, rx, ry)
const shrink = [
  { word: 'won', strong: 0.14, weak: 3.19 },
  { word: 'txt', strong: 0.32, weak: 2.74 },
  { word: 'call', strong: 0.52, weak: 2.33 },
  { word: 'arsenal', strong: 0.02, weak: 2.5 },
]

// LDA: prior-weighted Gaussians with a shared standard deviation.
const lda = { m0: -0.6, m1: 1.6, s: 0.8, p0: 0.88, p1: 0.12 }
const gauss = (x: number, m: number) =>
  Math.exp(-0.5 * ((x - m) / lda.s) ** 2) / (lda.s * Math.sqrt(2 * Math.PI))
const lx = (x: number) => 40 + ((x + 3) / 7) * 640
const ly = (v: number) => 190 - v * 250
const hamDensity = curve((x) => lda.p0 * gauss(x, lda.m0), -3, 4, lx, ly, 120)
const spamDensity = curve((x) => lda.p1 * gauss(x, lda.m1), -3, 4, lx, ly, 120)
const midpoint = (lda.m0 + lda.m1) / 2
const ldaBoundary = midpoint + (lda.s ** 2 / (lda.m1 - lda.m0)) * Math.log(lda.p0 / lda.p1)

// GAM: one straight effect versus a sum of local spline pieces.
const centers = [0.1, 0.35, 0.6, 0.85],
  betas = [-1.4, 0.3, 1.2, 1.0]
const bump = (t: number, c: number) => Math.exp(-(((t - c) / 0.14) ** 2))
const smooth = (t: number) => betas.reduce((s, b, m) => s + b * bump(t, centers[m]!), 0)
const gx = (offset: number) => (t: number) => offset + 30 + t * 280
const gy = (v: number) => 115 - v * 42
const linearEffect = curve((t) => -1 + 2.2 * t, 0, 1, gx(0), gy)
const smoothEffect = curve(smooth, 0, 1, gx(370), gy)
const pieces = betas.map((b, m) => curve((t) => b * bump(t, centers[m]!), 0, 1, gx(370), gy))

// KNN: deterministic constructed points; the vote is counted, not hard-coded.
let seed = 7
const random = () => ((seed = (seed * 16807) % 2147483647) - 1) / 2147483646
const normal = () => Math.sqrt(-2 * Math.log(random() + 1e-9)) * Math.cos(2 * Math.PI * random())
const knnPoints = [
  ...Array.from({ length: 34 }, () => ({
    x: 250 + normal() * 85,
    y: 160 + normal() * 45,
    label: 0,
  })),
  ...Array.from({ length: 16 }, () => ({
    x: 430 + normal() * 60,
    y: 95 + normal() * 35,
    label: 1,
  })),
].filter((p) => p.x > 30 && p.x < 690 && p.y > 20 && p.y < 235)
const query = { x: 355, y: 125 }
const byDistance = knnPoints
  .map((p) => ({ ...p, d: Math.hypot(p.x - query.x, p.y - query.y) }))
  .sort((a, b) => a.d - b.d)
const ring = (k: number) => ({
  r: (byDistance[k - 1]!.d + byDistance[k]!.d) / 2,
  spam: byDistance.slice(0, k).filter((p) => p.label).length,
})
const k5 = ring(5),
  k15 = ring(15)

// Decision: mirrored score distributions with a threshold.
const dx = (p: number) => 40 + p * 640
const threshold = 0.55
const hamScore = (p: number) => Math.exp(-(((p - 0.22) / 0.22) ** 2))
const spamScore = (p: number) => 0.6 * Math.exp(-(((p - 0.75) / 0.2) ** 2))
const area = (f: (p: number) => number, a: number, b: number, sign: number) =>
  curve(f, a, b, dx, (v) => 120 - sign * v * 90) + ` L${dx(b)},120 L${dx(a)},120 Z`
</script>

<template>
  <figure class="concept-figure">
    <svg width="0" height="0" aria-hidden="true" style="position: absolute">
      <defs>
        <marker
          id="t5-arrow"
          viewBox="0 0 10 10"
          refX="9"
          refY="5"
          markerWidth="7"
          markerHeight="7"
          orient="auto"
        >
          <path d="M0 0L10 5L0 10z" fill="#84929c" />
        </marker>
      </defs>
    </svg>
    <div class="figure-scroll">
      <!-- 1 · The rule as a pipeline, and the two kinds of mistake -->
      <svg
        v-if="chapter === 'inbox'"
        viewBox="0 0 720 300"
        role="img"
        aria-label="How a keyword rule decides, and the four possible outcomes"
      >
        <g class="box">
          <rect x="10" y="14" width="210" height="64" />
          <rect x="246" y="14" width="150" height="64" />
          <rect x="420" y="14" width="140" height="64" />
          <rect x="584" y="14" width="126" height="64" />
        </g>
        <text class="head" x="22" y="36">Message</text>
        <text x="22" y="60">“Are you free after class?”</text>
        <text class="head" x="258" y="36">Words</text>
        <text x="258" y="60">
          are you
          <tspan class="hit">free</tspan>
          after class
        </text>
        <text class="head" x="432" y="36">Keyword?</text>
        <text x="432" y="60">“free” is in the list</text>
        <text class="head" x="596" y="36">Decision</text>
        <text x="596" y="60" :fill="SPAM" font-weight="600">Spam ✗</text>
        <g class="arrow">
          <path d="M222 46h20" />
          <path d="M398 46h18" />
          <path d="M562 46h18" />
        </g>
        <text class="head" x="360" y="118" text-anchor="middle">
          Two ways to be right, two ways to be wrong
        </text>
        <text class="axis" x="315" y="148" text-anchor="middle">Delivered to inbox (ŷ = 0)</text>
        <text class="axis" x="545" y="148" text-anchor="middle">Blocked as spam (ŷ = 1)</text>
        <text class="axis" x="190" y="196" text-anchor="end">Actually ham (y = 0)</text>
        <text class="axis" x="190" y="258" text-anchor="end">Actually spam (y = 1)</text>
        <rect x="200" y="160" width="226" height="56" class="ok" />
        <rect x="430" y="160" width="226" height="56" class="bad" />
        <rect x="200" y="222" width="226" height="56" class="bad" />
        <rect x="430" y="222" width="226" height="56" class="ok" />
        <text class="head" x="313" y="185" text-anchor="middle">✓ True negative (TN)</text>
        <text x="313" y="205" text-anchor="middle">friend's message arrives</text>
        <text class="head" x="543" y="185" text-anchor="middle" :fill="SPAM">
          False positive (FP)
        </text>
        <text x="543" y="205" text-anchor="middle">real message lost: costly!</text>
        <text class="head" x="313" y="247" text-anchor="middle" :fill="SPAM">
          False negative (FN)
        </text>
        <text x="313" y="267" text-anchor="middle">an advert gets through</text>
        <text class="head" x="543" y="247" text-anchor="middle">✓ True positive (TP)</text>
        <text x="543" y="267" text-anchor="middle">spam caught</text>
      </svg>

      <!-- 2 · From the raw file to three splits -->
      <svg
        v-else-if="chapter === 'data'"
        viewBox="0 0 720 270"
        role="img"
        aria-label="Data flow from 5,574 raw records to train, validation and test splits"
      >
        <g class="box">
          <rect x="10" y="12" width="200" height="62" />
          <rect x="260" y="12" width="200" height="62" />
          <rect x="510" y="12" width="200" height="62" />
        </g>
        <text class="big" x="110" y="42" text-anchor="middle">5,574</text>
        <text x="110" y="63" text-anchor="middle">records in the raw file</text>
        <text class="big" x="360" y="42" text-anchor="middle" :fill="SPAM">−415</text>
        <text x="360" y="63" text-anchor="middle">duplicate messages removed</text>
        <text class="big" x="610" y="42" text-anchor="middle">5,159</text>
        <text x="610" y="63" text-anchor="middle">unique messages</text>
        <g class="arrow">
          <path d="M212 43h44" />
          <path d="M462 43h44" />
          <path d="M610 76v24" />
        </g>
        <rect x="10" y="108" width="418" height="70" fill="#dbe5ec" />
        <rect x="430" y="108" width="139" height="70" fill="#e8eef2" />
        <rect x="571" y="108" width="139" height="70" fill="#efefec" />
        <rect x="376" y="108" width="52" height="70" :fill="SPAM" opacity=".85" />
        <rect x="552" y="108" width="17" height="70" :fill="SPAM" opacity=".85" />
        <rect x="693" y="108" width="17" height="70" :fill="SPAM" opacity=".85" />
        <text class="head" x="22" y="134">Train · 3,095 (60%)</text>
        <text x="22" y="156">fit models, run cross-validation</text>
        <text class="head" x="440" y="134">Validation · 1,032</text>
        <text x="440" y="156">compare, pick t</text>
        <text class="head" x="581" y="134">Test · 1,032</text>
        <text x="581" y="156">final check, once</text>
        <text class="axis" x="10" y="200">
          <tspan :fill="SPAM">■</tspan>
          spam share ≈ 12% in every split (stratified)
        </text>
        <rect x="10" y="218" width="700" height="44" class="bad" />
        <text x="24" y="245">
          <tspan class="head">Trap:</tspan>
          predict “ham” for every validation message → accuracy 903 / 1,032 =
          <tspan class="head">87.5%</tspan>
          , spam recall =
          <tspan class="head" :fill="SPAM">0%</tspan>
        </text>
      </svg>

      <!-- 3 · One message becomes five numbers -->
      <svg
        v-else-if="chapter === 'features'"
        viewBox="0 0 720 230"
        role="img"
        aria-label="A message is measured as five numbers and log-transformed"
      >
        <rect class="card" x="10" y="40" width="240" height="88" />
        <text class="head" x="22" y="30">Message</text>
        <text x="22" y="74" class="mono">
          WIN £
          <tspan class="hit">1000</tspan>
          <tspan class="bang">!</tspan>
          Visit
        </text>
        <text x="22" y="100" class="mono">
          <tspan class="link">https://example.org</tspan>
          now
          <tspan class="bang">!!!</tspan>
        </text>
        <text class="axis" x="10" y="160">
          <tspan class="hit">digits</tspan>
          <tspan class="link">link</tspan>
          <tspan class="bang">exclamation marks</tspan>
        </text>
        <g class="arrow">
          <path d="M256 84h34" />
          <path d="M486 84h34" />
        </g>
        <text class="head" x="300" y="30">Raw counts x</text>
        <text class="head" x="530" y="30">log(1 + x)</text>
        <g
          v-for="(row, i) in [
            ['Characters', 43],
            ['Words', 7],
            ['Links', 1],
            ['Digits', 4],
            ['Exclamations', 4],
          ]"
          :key="i"
        >
          <rect x="300" :y="40 + i * 34" width="180" height="30" class="cell" />
          <text x="310" :y="60 + i * 34">{{ row[0] }}</text>
          <text x="470" :y="60 + i * 34" text-anchor="end" class="head">{{ row[1] }}</text>
          <rect x="530" :y="40 + i * 34" width="100" height="30" class="cell" />
          <text x="620" :y="60 + i * 34" text-anchor="end">
            {{ Math.log1p(row[1] as number).toFixed(2) }}
          </text>
        </g>
        <text class="axis" x="640" y="110">then</text>
        <text class="axis" x="640" y="126">standardize</text>
        <text class="axis" x="640" y="142">(z-score)</text>
      </svg>

      <!-- 4 · Documents → vocabulary columns → count matrix -->
      <svg
        v-else-if="chapter === 'text'"
        viewBox="0 0 720 260"
        role="img"
        aria-label="Three toy documents become rows of a word-count matrix"
      >
        <text class="axis" x="230" y="34" text-anchor="end">vocabulary →</text>
        <g
          v-for="(w, j) in ['a', 'after', 'are', 'class', 'free', 'now', 'prize', 'win', 'you']"
          :key="w"
        >
          <text :x="274 + j * 48" y="34" text-anchor="middle" :class="w === 'free' ? 'head' : ''">
            {{ w }}
          </text>
        </g>
        <g v-for="(row, i) in toyRows" :key="i">
          <text
            x="230"
            :y="i === 3 ? 196 : 66 + i * 36"
            text-anchor="end"
            :class="i === 3 ? 'head' : ''"
          >
            {{ row.text }}
          </text>
          <g v-for="(v, j) in row.counts" :key="j">
            <rect
              :x="251 + j * 48"
              :y="i === 3 ? 174 : 44 + i * 36"
              width="46"
              height="34"
              :fill="HAM"
              :fill-opacity="0.06 + v * 0.4"
            />
            <text
              :x="274 + j * 48"
              :y="i === 3 ? 196 : 66 + i * 36"
              text-anchor="middle"
              :class="v ? 'head' : 'faint'"
            >
              {{ v }}
            </text>
          </g>
        </g>
        <rect x="443" y="42" width="50" height="114" fill="none" :stroke="SPAM" stroke-width="2" />
        <rect x="443" y="172" width="50" height="38" fill="none" :stroke="SPAM" stroke-width="2" />
        <text class="axis" x="250" y="236">
          “meeting”, “tomorrow” are not in the vocabulary → ignored. Word order is gone.
        </text>
        <text class="axis" x="10" y="166">fit on training documents</text>
        <text class="axis" x="10" y="226">transform a new one</text>
      </svg>

      <!-- 5 · Contributions add up to z; the sigmoid gives p -->
      <svg
        v-else-if="chapter === 'logistic'"
        viewBox="0 0 720 250"
        role="img"
        aria-label="Word contributions add up to a score that the sigmoid turns into a probability"
      >
        <text class="head" x="40" y="18">“Claim your free prize”: add up the evidence</text>
        <line x1="30" x2="430" :y1="wy(0)" :y2="wy(0)" class="zero" />
        <text class="axis" x="26" :y="wy(0) + 4" text-anchor="end">0</text>
        <g v-for="(bar, i) in waterfall" :key="bar.name">
          <rect
            :x="40 + i * 66"
            :y="wy(Math.max(bar.from, bar.to))"
            width="50"
            :height="Math.abs(bar.value) * 24"
            :fill="bar.value < 0 ? HAM : SPAM"
          />
          <line
            v-if="i"
            :x1="40 + i * 66 - 16"
            :x2="40 + i * 66"
            :y1="wy(bar.from)"
            :y2="wy(bar.from)"
            class="zero"
          />
          <text :x="65 + i * 66" y="222" text-anchor="middle">{{ bar.name }}</text>
          <text
            :x="65 + i * 66"
            :y="wy(Math.max(bar.from, bar.to)) - 5"
            text-anchor="middle"
            class="head"
          >
            {{ bar.value > 0 ? '+' : '−' }}{{ Math.abs(bar.value).toFixed(1) }}
          </text>
        </g>
        <rect x="370" :y="wy(zTotal)" width="50" :height="zTotal * 24" fill="#202e3a" />
        <text x="395" y="222" text-anchor="middle" class="head">z</text>
        <text x="395" :y="wy(zTotal) - 5" text-anchor="middle" class="head">
          {{ zTotal.toFixed(1) }}
        </text>
        <text class="axis" x="40" y="242">
          <tspan :fill="SPAM">■</tspan>
          pushes towards spam
          <tspan :fill="HAM">■</tspan>
          pushes towards ham
        </text>
        <g class="arrow"><path d="M436 120h28" /></g>
        <text class="head" x="480" y="18">p = σ(z)</text>
        <line :x1="sx(-6)" :x2="sx(6)" :y1="sy(0.5)" :y2="sy(0.5)" class="dashed" />
        <line :x1="sx(0)" :x2="sx(0)" :y1="sy(0)" :y2="sy(1)" class="zero" />
        <path :d="sigmoidPath" fill="none" :stroke="HAM" stroke-width="2.5" />
        <line :x1="sx(zTotal)" :x2="sx(zTotal)" :y1="sy(0)" :y2="sy(sig(zTotal))" class="dashed" />
        <circle
          :cx="sx(zTotal)"
          :cy="sy(sig(zTotal))"
          r="6"
          :fill="SPAM"
          stroke="white"
          stroke-width="2"
        />
        <text :x="sx(zTotal) - 12" :y="sy(sig(zTotal)) - 8" text-anchor="end" class="head">
          p = {{ sig(zTotal).toFixed(2) }} → spam
        </text>
        <text class="axis" :x="sx(-6)" :y="sy(0.5) + 16">threshold 0.5 ⇔ z = 0</text>
        <text class="axis" :x="sx(0)" y="222" text-anchor="middle">z</text>
        <text class="axis" :x="sx(-6)" :y="sy(1) - 4">p = 1</text>
        <text class="axis" :x="sx(-6)" :y="sy(0) + 14">p = 0</text>
      </svg>

      <!-- 6 · Penalty strength: fit curve and weight shrinkage -->
      <svg
        v-else-if="chapter === 'regularization'"
        viewBox="0 0 720 250"
        role="img"
        aria-label="Training and validation performance across penalty strength, and how word weights shrink"
      >
        <text class="head" x="50" y="18">Fit quality as the penalty weakens (sketch)</text>
        <rect x="50" y="40" width="80" height="160" fill="#f1f4f6" />
        <rect x="250" y="40" width="70" height="160" fill="#f8eee6" />
        <text class="axis" x="90" y="56" text-anchor="middle">underfit</text>
        <text class="axis" x="285" y="56" text-anchor="middle">overfit</text>
        <path :d="trainCurve" fill="none" :stroke="HAM" stroke-width="2.5" />
        <path :d="validCurve" fill="none" :stroke="SPAM" stroke-width="2.5" />
        <text :x="rx(0.4)" :y="ry(0.9)" class="axis">training</text>
        <text :x="rx(0.62)" :y="ry(0.6)" class="axis">validation</text>
        <line x1="50" x2="320" y1="200" y2="200" class="zero" />
        <text class="axis" x="50" y="218">small C (strong penalty)</text>
        <text class="axis" x="320" y="218" text-anchor="end">large C</text>
        <text class="head" x="390" y="18">Word weights, count model on this data</text>
        <g v-for="(row, i) in shrink" :key="row.word">
          <text
            x="450"
            :y="58 + i * 44"
            text-anchor="end"
            :class="row.word === 'arsenal' ? 'head' : ''"
          >
            {{ row.word }}
          </text>
          <rect x="460" :y="44 + i * 44" :width="row.strong * 70" height="12" fill="#9dabb5" />
          <rect x="460" :y="58 + i * 44" :width="row.weak * 70" height="12" :fill="SPAM" />
          <text :x="466 + row.weak * 70" :y="69 + i * 44" class="axis">
            {{ row.weak.toFixed(1) }}
          </text>
        </g>
        <text class="axis" x="390" y="226">
          <tspan fill="#9dabb5">■</tspan>
          C = 0.01 (strong)
          <tspan :fill="SPAM">■</tspan>
          C = 10 (weak)
        </text>
        <text class="axis" x="390" y="244">
          “arsenal”, a football club, looks spammy only by chance
        </text>
      </svg>

      <!-- 7 · Five rounds of fit-on-four, score-on-one -->
      <svg
        v-else-if="chapter === 'validation'"
        viewBox="0 0 720 240"
        role="img"
        aria-label="Five-fold cross-validation grid"
      >
        <g v-for="f in 5" :key="'h' + f">
          <text :x="122 + (f - 1) * 68" y="24" text-anchor="middle" class="axis">fold {{ f }}</text>
        </g>
        <g v-for="r in 5" :key="r">
          <text x="80" :y="56 + (r - 1) * 36" text-anchor="end">round {{ r }}</text>
          <g v-for="f in 5" :key="f">
            <rect
              :x="90 + (f - 1) * 68"
              :y="34 + (r - 1) * 36"
              width="64"
              height="32"
              :fill="r === f ? SPAM : '#cddae4'"
            />
            <text
              :x="122 + (f - 1) * 68"
              :y="55 + (r - 1) * 36"
              text-anchor="middle"
              :fill="r === f ? 'white' : '#202e3a'"
            >
              {{ r === f ? 'score' : 'fit' }}
            </text>
          </g>
          <text x="438" :y="56 + (r - 1) * 36">→ AP{{ '₁₂₃₄₅'[r - 1] }}</text>
        </g>
        <g class="box">
          <rect x="500" y="34" width="210" height="40" />
          <rect x="500" y="94" width="210" height="40" />
          <rect x="500" y="154" width="210" height="40" />
        </g>
        <text x="512" y="59">1. learn vocabulary + IDF</text>
        <text x="512" y="119">2. fit logistic regression</text>
        <text x="512" y="179">3. score the held-out fold</text>
        <g class="arrow">
          <path d="M605 76v14" />
          <path d="M605 136v14" />
        </g>
        <text class="axis" x="500" y="22">inside every round, on blue folds only:</text>
        <text class="axis" x="90" y="230">
          CV(C) = average of AP₁ … AP₅ → choose the C with the best average
        </text>
      </svg>

      <!-- 8 · Gaussian classes with a shared width; priors shift the boundary -->
      <svg
        v-else-if="chapter === 'lda'"
        viewBox="0 0 720 240"
        role="img"
        aria-label="Two Gaussian class densities with shared variance and the LDA boundary"
      >
        <path
          :d="hamDensity + ` L${lx(4)},${ly(0)} L${lx(-3)},${ly(0)} Z`"
          :fill="HAM"
          fill-opacity=".15"
          :stroke="HAM"
          stroke-width="2.5"
        />
        <path
          :d="spamDensity + ` L${lx(4)},${ly(0)} L${lx(-3)},${ly(0)} Z`"
          :fill="SPAM"
          fill-opacity=".2"
          :stroke="SPAM"
          stroke-width="2.5"
        />
        <line :x1="lx(-3)" :x2="lx(4)" :y1="ly(0)" :y2="ly(0)" class="zero" />
        <line :x1="lx(midpoint)" :x2="lx(midpoint)" y1="30" :y2="ly(0)" class="dashed" />
        <line
          :x1="lx(ldaBoundary)"
          :x2="lx(ldaBoundary)"
          y1="30"
          :y2="ly(0)"
          stroke="#202e3a"
          stroke-width="2"
        />
        <text :x="lx(midpoint) - 6" y="40" text-anchor="end" class="axis">equal priors</text>
        <text :x="lx(ldaBoundary) + 6" y="40" class="head">LDA boundary (88% / 12% priors)</text>
        <text
          :x="lx(lda.m0)"
          :y="ly(lda.p0 * gauss(lda.m0, lda.m0)) - 8"
          text-anchor="middle"
          class="head"
          :fill="HAM"
        >
          ham: 0.88 × N(μ₀, σ²)
        </text>
        <text
          :x="lx(lda.m1) + 20"
          :y="ly(lda.p1 * gauss(lda.m1, lda.m1)) - 8"
          class="head"
          :fill="SPAM"
        >
          spam: 0.12 × N(μ₁, σ²)
        </text>
        <text class="axis" :x="lx(-3)" y="212">standardized feature, e.g. log(1 + digits) →</text>
        <text class="axis" :x="lx(-3)" y="230">
          same width σ in both classes = shared covariance → straight-line boundary
        </text>
      </svg>

      <!-- 9 · Straight effect versus smooth spline effect -->
      <svg
        v-else-if="chapter === 'gam'"
        viewBox="0 0 720 230"
        role="img"
        aria-label="A linear effect compared with a smooth additive spline effect"
      >
        <text class="head" x="30" y="20">Logistic: w · x (one slope)</text>
        <text class="head" x="400" y="20">GAM: f(x) = Σ β·B (smooth pieces added)</text>
        <g v-for="offset in [0, 370]" :key="offset">
          <line :x1="offset + 30" :x2="offset + 310" :y1="gy(0)" :y2="gy(0)" class="zero" />
          <text class="axis" :x="offset + 30" y="208">characters →</text>
          <text class="axis" :x="offset + 30" y="40">log-odds effect</text>
        </g>
        <path :d="linearEffect" fill="none" :stroke="HAM" stroke-width="2.5" />
        <path
          v-for="(d, m) in pieces"
          :key="m"
          :d="d"
          fill="none"
          stroke="#9dabb5"
          stroke-width="1.5"
          stroke-dasharray="4 3"
        />
        <path :d="smoothEffect" fill="none" :stroke="SPAM" stroke-width="2.5" />
        <text class="axis" x="400" y="226">
          <tspan fill="#9dabb5">- - -</tspan>
          basis pieces β·B
          <tspan :fill="SPAM">━</tspan>
          their sum f(x)
        </text>
        <text class="axis" x="30" y="226">the same change everywhere</text>
      </svg>

      <!-- 10 · Who are the nearest neighbours? -->
      <svg
        v-else-if="chapter === 'neighbors'"
        viewBox="0 0 720 250"
        role="img"
        aria-label="A new message and its nearest labelled neighbours"
      >
        <circle
          :cx="query.x"
          :cy="query.y"
          :r="k15.r"
          fill="none"
          stroke="#9dabb5"
          stroke-dasharray="5 4"
        />
        <circle
          :cx="query.x"
          :cy="query.y"
          :r="k5.r"
          fill="#202e3a"
          fill-opacity=".04"
          stroke="#202e3a"
          stroke-width="1.5"
        />
        <circle
          v-for="(p, i) in knnPoints"
          :key="i"
          :cx="p.x"
          :cy="p.y"
          r="6"
          :fill="p.label ? SPAM : HAM"
          stroke="white"
          stroke-width="1.5"
        />
        <path
          :d="`M${query.x} ${query.y - 11}l3.2 7.3 7.9.6-6 5.2 1.9 7.7-7-4.2-7 4.2 1.9-7.7-6-5.2 7.9-.6z`"
          fill="#f2c94c"
          stroke="#202e3a"
        />
        <rect x="540" y="16" width="170" height="92" class="card" />
        <text class="head" x="552" y="38">k = 5 (solid)</text>
        <text x="552" y="58">{{ k5.spam }} spam / 5 → p̂ = {{ (k5.spam / 5).toFixed(2) }}</text>
        <text class="head" x="552" y="80">k = 15 (dashed)</text>
        <text x="552" y="100">{{ k15.spam }} spam / 15 → p̂ = {{ (k15.spam / 15).toFixed(2) }}</text>
        <text class="axis" x="20" y="244">
          <tspan fill="#d6a823">★</tspan>
          new message
          <tspan :fill="HAM">●</tspan>
          ham
          <tspan :fill="SPAM">●</tspan>
          spam (constructed 2-D example)
        </text>
      </svg>

      <!-- 11 · Scores, threshold and the two error regions -->
      <svg
        v-else-if="chapter === 'decision'"
        viewBox="0 0 720 250"
        role="img"
        aria-label="Score distributions for ham and spam split by a threshold"
      >
        <path
          :d="area(hamScore, 0, 1, 1)"
          :fill="HAM"
          fill-opacity=".18"
          :stroke="HAM"
          stroke-width="2"
        />
        <path
          :d="area(spamScore, 0, 1, -1)"
          :fill="SPAM"
          fill-opacity=".18"
          :stroke="SPAM"
          stroke-width="2"
        />
        <path :d="area(hamScore, threshold, 1, 1)" :fill="SPAM" fill-opacity=".55" />
        <path :d="area(spamScore, 0, threshold, -1)" :fill="HAM" fill-opacity=".55" />
        <line :x1="dx(0)" :x2="dx(1)" y1="120" y2="120" class="zero" />
        <line
          :x1="dx(threshold)"
          :x2="dx(threshold)"
          y1="18"
          y2="222"
          stroke="#202e3a"
          stroke-width="2"
        />
        <text :x="dx(threshold) + 6" y="28" class="head">threshold t</text>
        <text :x="dx(0.04)" y="28" class="head" :fill="HAM">ham scores ↑</text>
        <text :x="dx(0.72)" y="214" class="head" :fill="SPAM">spam scores ↓</text>
        <text :x="dx(threshold) + 8" y="72" class="head" :fill="SPAM">FP: ham blocked</text>
        <text :x="dx(threshold) - 8" y="178" class="head" text-anchor="end" :fill="HAM">
          FN: spam let through
        </text>
        <text class="axis" :x="dx(0)" y="242">model score p: 0</text>
        <text class="axis" :x="dx(1)" y="242" text-anchor="end">1</text>
        <text class="axis" :x="dx(0.5)" y="242" text-anchor="middle">
          move t right: fewer FP, more FN
        </text>
      </svg>
    </div>
  </figure>
</template>

<style scoped>
.concept-figure {
  margin: 22px 0 26px;
  padding: 18px;
  background: var(--surface);
  border: 1px solid var(--line);
  border-radius: 4px;
}
.figure-scroll {
  overflow-x: auto;
}
svg {
  display: block;
  width: 100%;
  min-width: 560px;
  font: 13px var(--font-sans);
  fill: var(--ink);
}
.head {
  font-weight: 600;
}
.big {
  font-size: 24px;
  font-weight: 500;
}
.axis {
  fill: var(--muted);
  font-size: 12px;
}
.faint {
  fill: #b6c0c8;
}
.mono {
  font-family: ui-monospace, Menlo, monospace;
  font-size: 14px;
}
.box rect,
.card {
  fill: #f5f7f9;
  stroke: #cfd8df;
}
.cell {
  fill: #f5f7f9;
  stroke: #e2e7eb;
}
.ok {
  fill: #edf3f7;
  stroke: #cddae4;
}
.bad {
  fill: #f8eee6;
  stroke: #e3c3ae;
}
.hit {
  fill: #aa613d;
  font-weight: 700;
}
.link {
  fill: #45657e;
  text-decoration: underline;
  font-weight: 600;
}
.bang {
  fill: #a84528;
  font-weight: 800;
}
.arrow path {
  stroke: #84929c;
  stroke-width: 2;
  fill: none;
  marker-end: url(#t5-arrow);
}
.zero {
  stroke: #9dabb5;
  stroke-width: 1;
}
.dashed {
  stroke: #84929c;
  stroke-dasharray: 5 4;
}
</style>
