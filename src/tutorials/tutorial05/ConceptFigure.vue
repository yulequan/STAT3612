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

// Regularization: constructed fit curves and illustrative coefficient shrinkage.
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
      <!-- 3 · One message becomes five numbers -->
      <svg
        v-if="chapter === 'features'"
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
            ['Tokens', 4],
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
        <text class="head" x="390" y="18">Illustrative word weights (sketch)</text>
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
          stronger penalty
          <tspan :fill="SPAM">■</tspan>
          weaker penalty
        </text>
        <text class="axis" x="390" y="244">Rare words can look predictive by chance.</text>
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
          <text class="axis" :x="offset + 30" y="208">log(1 + characters) →</text>
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
