<script setup lang="ts">
import { computed, ref, watch } from 'vue'

export type EvidenceTerm = {
  name: string
  value: number
  feature?: number
  weight?: number
  ham?: number
  spam?: number
}
export type ScoreEvidence = {
  text?: string
  bias: number
  score: number
  probability: number
  priors?: number[]
  contributions: EvidenceTerm[]
}
const props = defineProps<{ evidence: ScoreEvidence; kind: 'nb' | 'logistic'; title: string }>()
const terms = computed(() => {
  const all = props.evidence.contributions
  return all.length <= 9
    ? all
    : [
        ...all.slice(0, 8),
        {
          name: 'Other ' + (all.length - 8) + ' features',
          value: all.slice(8).reduce((s, t) => s + t.value, 0),
        },
      ]
})
const step = ref(terms.value.length)
watch(
  () => props.evidence,
  () => {
    step.value = terms.value.length
  },
)
const stages = computed(() => {
  let total = props.evidence.bias
  return [
    { name: props.kind === 'nb' ? 'Class prior' : 'Intercept', start: 0, end: total, value: total },
    ...terms.value.map((term) => {
      const start = total
      total += term.value
      return { ...term, start, end: total }
    }),
  ]
})
const bounds = computed(() => {
  const values = [0, ...stages.value.map((s) => s.end)]
  const low = Math.min(...values),
    high = Math.max(...values)
  const pad = Math.max(0.5, (high - low) * 0.15)
  return [low - pad, high + pad]
})
const position = (value: number) =>
  (100 * (value - bounds.value[0]!)) / (bounds.value[1]! - bounds.value[0]!)
const selected = computed(() => stages.value[step.value]!)
const score = computed(() => selected.value.end)
const probability = computed(() => {
  if (step.value === terms.value.length) return props.evidence.probability
  return score.value >= 0
    ? 1 / (1 + Math.exp(-score.value))
    : Math.exp(score.value) / (1 + Math.exp(score.value))
})
const term = computed(() => (step.value ? terms.value[step.value - 1] : undefined))
const signed = (v: number) => (v >= 0 ? '+' : '') + v.toFixed(3)
</script>

<template>
  <figure class="score-journey" :aria-label="title">
    <h3>{{ title }}</h3>
    <p class="direction"><span>← Evidence for ham</span><span>Evidence for spam →</span></p>
    <div class="waterfall" aria-label="Contributions accumulate into the score">
      <button
        v-for="(row, i) in stages"
        :key="i"
        class="evidence-row"
        :class="{ selected: step === i, pending: i > step }"
        :aria-pressed="step === i"
        :aria-label="'Show evidence after ' + row.name"
        @click="step = i"
      >
        <code>{{ row.name }}</code>
        <span class="score-track">
          <i class="zero-line" :style="{ left: position(0) + '%' }" />
          <i
            v-if="row.value !== 0"
            class="score-segment"
            :class="i === 0 ? 'prior' : row.value < 0 ? 'ham' : 'spam'"
            :style="{
              left: position(Math.min(row.start, row.end)) + '%',
              width: Math.abs(position(row.end) - position(row.start)) + '%',
            }"
          />
          <i class="score-end" :style="{ left: position(row.end) + '%' }" />
        </span>
        <span class="score-value">{{ signed(row.value) }}</span>
      </button>
    </div>
    <label class="step-control"
      >Evidence steps: {{ step }} / {{ terms.length }}
      <input
        v-model.number="step"
        aria-label="Evidence steps"
        type="range"
        min="0"
        :max="terms.length"
        step="1"
        :disabled="!terms.length"
      />
    </label>
    <div class="step-buttons">
      <button :disabled="step === 0" @click="step--">Previous evidence step</button>
      <button :disabled="step === terms.length" @click="step++">Next evidence step</button>
    </div>
    <div class="term-inspector" aria-live="polite">
      <template v-if="!term">
        <p v-if="kind === 'nb'">
          Start from the class proportions: ham
          {{ ((evidence.priors?.[0] ?? 1 - evidence.probability) * 100).toFixed(1) }}%, spam
          {{ ((evidence.priors?.[1] ?? evidence.probability) * 100).toFixed(1) }}%. Log prior ratio
          = {{ evidence.bias.toFixed(3) }}.
        </p>
        <p v-else>
          The intercept starts the score at {{ evidence.bias.toFixed(3) }} before word
          contributions.
        </p>
      </template>
      <template v-else>
        <p>
          <code>{{ term.name }}</code> adds <strong>{{ signed(term.value) }}</strong> to the
          previous score.
        </p>
        <p v-if="term.feature !== undefined && term.weight !== undefined" class="calculation">
          <span
            >Feature value <code>{{ term.feature.toFixed(3) }}</code></span
          ><b>×</b>
          <span
            >{{ kind === 'nb' ? 'Log likelihood ratio' : 'Weight' }}
            <code>{{ signed(term.weight) }}</code></span
          ><b>=</b>
          <span
            >Contribution <code>{{ signed(term.value) }}</code></span
          >
        </p>
        <p v-if="term.ham !== undefined && term.spam !== undefined">
          P(word | ham) = {{ term.ham.toPrecision(3) }} · P(word | spam) =
          {{ term.spam.toPrecision(3) }}.
        </p>
      </template>
      <p class="result">
        {{ step === terms.length ? 'Full score' : 'Score so far' }}
        <strong>{{ score.toFixed(3) }}</strong> →
        <strong data-testid="journey-probability"
          >{{ (100 * probability).toFixed(1) }}% spam estimate</strong
        >
      </p>
      <div
        class="probability-meter"
        :aria-label="'Spam estimate ' + (probability * 100).toFixed(1) + '%'"
      >
        <span class="ham" :style="{ width: 100 * (1 - probability) + '%' }" />
        <span class="spam" :style="{ width: 100 * probability + '%' }" />
        <i class="half-mark" />
      </div>
      <p class="meter-caption">Ham <span>50% reference</span> Spam</p>
      <p v-if="step < terms.length" class="hint">
        Only the shown evidence is included; advance to see the full prediction.
      </p>
      <p v-else-if="!terms.length" class="hint">
        No active features: only the starting score remains.
      </p>
    </div>
  </figure>
</template>

<style scoped>
.score-journey {
  margin: 24px 0;
  min-width: 0;
}
h3 {
  margin-bottom: 14px;
}
.direction,
.meter-caption {
  display: flex;
  justify-content: space-between;
  gap: 10px;
  font-size: 0.76rem;
  color: var(--muted);
}
.waterfall {
  margin: 12px 0 18px;
}
.evidence-row {
  display: grid;
  grid-template-columns: 120px minmax(0, 1fr) 65px;
  align-items: center;
  gap: 12px;
  width: 100%;
  margin: 0;
  padding: 9px 8px;
  border: 1px solid transparent;
  background: transparent;
  text-align: left;
}
.evidence-row code {
  font-size: 0.82rem;
  overflow-wrap: anywhere;
}
.evidence-row.selected {
  border-color: #a9bfce;
  background: #f2f6f8;
}
.evidence-row.pending {
  opacity: 0.35;
}
.score-track {
  position: relative;
  height: 27px;
  background: #f3f5f6;
}
.zero-line {
  position: absolute;
  top: 0;
  bottom: 0;
  border-left: 1px dashed #87949d;
}
.score-segment {
  position: absolute;
  top: 6px;
  height: 15px;
}
.ham {
  background: #45657e;
}
.spam {
  background: #aa613d;
}
.prior {
  background: #84929c;
}
.score-end {
  position: absolute;
  top: 4px;
  height: 19px;
  border-left: 2px solid #202e3a;
}
.score-value {
  font-size: 0.8rem;
  text-align: right;
  font-variant-numeric: tabular-nums;
}
.step-control {
  display: block;
  font-size: 0.85rem;
}
.step-control input {
  display: block;
  width: 100%;
  margin-top: 10px;
}
.step-buttons {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin: 10px 0 18px;
}
.term-inspector {
  padding: 14px 18px;
  border: 1px solid var(--line);
  background: #f6f8f9;
  min-width: 0;
}
.term-inspector p {
  margin: 4px 0 12px;
  font-size: 0.88rem;
  overflow-wrap: anywhere;
}
.calculation {
  display: flex;
  flex-wrap: wrap;
  gap: 8px 12px;
  align-items: center;
}
.calculation span {
  padding: 6px;
  background: white;
  border: 1px solid #d9e2e9;
}
.result strong {
  white-space: nowrap;
}
.probability-meter {
  display: flex;
  height: 22px;
  position: relative;
  border-radius: 3px;
  overflow: hidden;
}
.half-mark {
  position: absolute;
  left: 50%;
  top: 0;
  bottom: 0;
  border-left: 2px solid white;
}
.term-inspector .meter-caption {
  font-size: 0.72rem;
}
.hint {
  color: var(--muted);
}
@media (max-width: 600px) {
  .evidence-row {
    grid-template-columns: 72px minmax(0, 1fr) 48px;
    gap: 6px;
    padding: 9px 3px;
  }
  .evidence-row code,
  .score-value {
    font-size: 0.72rem;
  }
  .term-inspector {
    padding: 12px;
  }
}
</style>
