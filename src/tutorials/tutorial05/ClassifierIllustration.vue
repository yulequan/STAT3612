<script setup lang="ts">
import { computed, reactive, ref, watch } from 'vue'
import ScoreJourney, { type ScoreEvidence } from './ScoreJourney.vue'
import NeighborExplorer from './NeighborExplorer.vue'
import examples from './model_examples.json'
import InlineText from './InlineText.vue'
import FlowDiagram from './FlowDiagram.vue'

const props = defineProps<{ chapter: string }>()
const kind = computed(() =>
  props.chapter === 'naive' ? 'nb' : props.chapter === 'logistic' ? 'logistic' : 'knn',
)
const example = computed(() => examples[kind.value])
const nbCounts = reactive(Object.fromEntries(examples.nb.words.map((w) => [w.name, w.initial])))
const lrCounts = reactive(
  Object.fromEntries(examples.logistic.words.map((w) => [w.name, w.initial])),
)
const alpha = ref(1)
const queryCounts = reactive([...examples.knn.query])
const k = ref(examples.knn.k)
const queryChoice = ref(0)
const queries = computed(() =>
  kind.value === 'logistic' ? examples.logistic.queries : examples.knn.queries,
)
watch(queryChoice, () => {
  if (kind.value === 'logistic') {
    const counts = examples.logistic.queries[queryChoice.value]!.counts
    for (const word of examples.logistic.words)
      lrCounts[word.name] = (counts as Record<string, number | undefined>)[word.name] ?? 0
  } else {
    queryCounts.splice(0, 2, ...examples.knn.queries[queryChoice.value]!.counts)
  }
})
const sigmoid = (score: number) =>
  score >= 0 ? 1 / (1 + Math.exp(-score)) : Math.exp(score) / (1 + Math.exp(score))
const evidence = computed<ScoreEvidence>(() => {
  const nb = kind.value === 'nb'
  const bias = nb
    ? Math.log(examples.nb.priors[1]! / examples.nb.priors[0]!)
    : examples.logistic.bias
  const contributions = nb
    ? examples.nb.words
        .filter((w) => nbCounts[w.name]! > 0)
        .map((w) => {
          const ham =
            (w.counts[0]! + alpha.value) /
            (examples.nb.totals[0]! + alpha.value * examples.nb.vocabulary)
          const spam =
            (w.counts[1]! + alpha.value) /
            (examples.nb.totals[1]! + alpha.value * examples.nb.vocabulary)
          const weight = Math.log(spam / ham),
            feature = nbCounts[w.name]!
          return { name: w.name, feature, weight, value: feature * weight, ham, spam }
        })
    : examples.logistic.words
        .filter((w) => lrCounts[w.name]! > 0)
        .map((w) => ({
          name: w.name,
          feature: lrCounts[w.name]!,
          weight: w.weight,
          value: lrCounts[w.name]! * w.weight,
        }))
  const score = bias + contributions.reduce((s, t) => s + t.value, 0)
  return {
    bias,
    score,
    probability: sigmoid(score),
    contributions,
    ...(nb ? { priors: examples.nb.priors } : {}),
  }
})
function normalize(values: number[]) {
  const norm = Math.hypot(...values)
  return { x: norm ? values[0]! / norm : 0, y: norm ? values[1]! / norm : 0 }
}
const points = examples.knn.points.map((p) => ({ ...p, ...normalize(p.counts) }))
const query = computed(() => normalize(queryCounts))
const zeroVector = computed(() => queryCounts.every((n) => n === 0))
const ranked = computed(() =>
  zeroVector.value
    ? []
    : points
        .map((p, index) => ({
          text: p.text,
          label: p.label,
          index,
          distance: Math.max(0, 1 - p.x * query.value.x - p.y * query.value.y),
        }))
        .sort((a, b) => a.distance - b.distance || a.index - b.index),
)
const neighbors = computed(() => ranked.value.slice(0, k.value))
const algorithm = computed(() =>
  kind.value === 'logistic' ? examples.logistic.flow : examples.knn.flow,
)
const flowValues = computed(() => {
  let text = queries.value[queryChoice.value]?.text ?? ''
  if (kind.value === 'logistic') {
    const chosen = examples.logistic.queries[queryChoice.value]!.counts as Record<
      string,
      number | undefined
    >
    if (examples.logistic.words.some((w) => lrCounts[w.name] !== (chosen[w.name] ?? 0)))
      text =
        examples.logistic.words.flatMap((w) => Array(lrCounts[w.name]).fill(w.name)).join(' ') ||
        '(empty message)'
  } else if (queryCounts.some((n, i) => n !== examples.knn.queries[queryChoice.value]!.counts[i])) {
    text =
      examples.knn.words.flatMap((word, i) => Array(queryCounts[i]).fill(word)).join(' ') ||
      '(empty message)'
  }
  if (kind.value === 'logistic') {
    const state = evidence.value
    return {
      text,
      weights: '[' + examples.logistic.words.map((w) => w.weight.toFixed(3)).join(', ') + ']',
      bias: state.bias.toFixed(3),
      vector: '[' + examples.logistic.words.map((w) => lrCounts[w.name]).join(', ') + ']',
      calculation:
        state.bias.toFixed(3) +
        state.contributions
          .map((t) => ' + (' + t.feature + ' × ' + t.weight!.toFixed(3) + ')')
          .join(''),
      score: state.score.toFixed(3),
      probability: (100 * state.probability).toFixed(1),
      hamProbability: (100 * (1 - state.probability)).toFixed(1),
      prediction: state.probability > 0.5 ? 'Spam' : 'Ham',
    }
  }
  const spam = neighbors.value.filter((n) => n.label).length
  return {
    text,
    vector: '[' + queryCounts.join(', ') + ']',
    direction: '[' + [query.value.x, query.value.y].map((v) => v.toFixed(3)).join(', ') + ']',
    ranking: ranked.value
      .map(
        (n, i) =>
          (i < k.value ? '✓ ' : '  ') +
          '#' +
          (i + 1) +
          ' · ' +
          n.distance.toFixed(3) +
          ' · ' +
          (n.label ? 'Spam' : 'Ham') +
          ' · ' +
          n.text,
      )
      .join('\n'),
    labels: neighbors.value.map((n) => (n.label ? 'Spam' : 'Ham')).join(', '),
    spam: String(spam),
    k: String(neighbors.value.length),
    probability: neighbors.value.length ? ((100 * spam) / neighbors.value.length).toFixed(1) : '—',
    prediction: !neighbors.value.length
      ? 'Add a known word first'
      : spam > neighbors.value.length / 2
        ? 'Spam'
        : 'Ham',
  }
})
</script>

<template>
  <section class="classifier-illustration" :aria-label="example.title">
    <div class="example-header">
      <span>{{ 'Algorithm walkthrough with real SMS' }}</span>
      <p><InlineText :text="example.caption" /></p>
    </div>
    <p><InlineText :text="example.challenge" /></p>
    <p v-if="kind === 'nb'">
      Real validation SMS: <code>{{ examples.nb.text }}</code>
    </p>
    <template v-if="kind !== 'nb'">
      <h3>Training messages → word-count vectors</h3>
      <p>
        Column order:
        <code>{{ kind === 'logistic' ? '[free, prize, class, meet]' : '[prize, call]' }}</code>
      </p>
      <div class="training-table">
        <table aria-label="Real SMS training excerpts">
          <thead>
            <tr>
              <th>Row</th>
              <th>Label</th>
              <th>Training message</th>
              <th>Vector</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="(row, i) in kind === 'logistic'
                ? examples.logistic.training
                : examples.knn.points"
              :key="i"
            >
              <th>{{ i + 1 }}</th>
              <th>{{ row.label ? 'Spam' : 'Ham' }}</th>
              <td>
                <code>{{ row.text }}</code>
              </td>
              <td>
                <code>[{{ row.counts.join(', ') }}]</code>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      <label
        >New message to predict<select
          v-model.number="queryChoice"
          aria-label="Walkthrough message"
        >
          <option v-for="(q, i) in queries" :key="i" :value="i">{{ q.text }}</option>
        </select></label
      >
      <label v-if="kind === 'knn'"
        >Number of neighbours <code>k</code
        ><select v-model.number="k" aria-label="Walkthrough neighbour count">
          <option v-for="n in [1, 3, 5]" :key="n" :value="n">{{ n }}</option>
        </select></label
      >
      <NeighborExplorer
        v-if="kind === 'knn'"
        :title="example.title"
        :points="points"
        :axis-labels="examples.knn.words"
        :query="query"
        :neighbors="neighbors"
        :zero-vector="zeroVector"
        metric="Cosine"
      />
      <FlowDiagram :flow="algorithm" :values="flowValues" />
    </template>
    <section class="arithmetic-details">
      <h3>
        {{
          kind === 'nb'
            ? 'Inspect the log-space calculation'
            : kind === 'logistic'
              ? 'Inspect individual contributions'
              : 'Inspect word directions and distances'
        }}
      </h3>
      <div v-if="kind === 'nb'" class="toy-controls">
        <label v-for="w in examples.nb.words" :key="w.name"
          >Count of <code>{{ w.name }}</code
          >: {{ nbCounts[w.name] }}
          <input
            v-model.number="nbCounts[w.name]"
            :aria-label="'NB count of ' + w.name"
            type="range"
            min="0"
            max="3"
            step="1"
          />
        </label>
        <label
          >Smoothing alpha: {{ alpha.toFixed(1) }}
          <input
            v-model.number="alpha"
            aria-label="NB smoothing alpha"
            type="range"
            min=".1"
            max="5"
            step=".1"
          />
        </label>
      </div>
      <div v-else-if="kind === 'logistic'" class="toy-controls">
        <label v-for="w in examples.logistic.words" :key="w.name"
          >Count of <code>{{ w.name }}</code
          >: {{ lrCounts[w.name] }}
          <input
            v-model.number="lrCounts[w.name]"
            :aria-label="'LR count of ' + w.name"
            type="range"
            min="0"
            max="3"
            step="1"
          />
        </label>
      </div>
      <div v-else class="toy-controls">
        <label v-for="(word, i) in examples.knn.words" :key="word"
          >Count of <code>{{ word }}</code
          >: {{ queryCounts[i] }}
          <input
            v-model.number="queryCounts[i]"
            :aria-label="'KNN count of ' + word"
            type="range"
            min="0"
            max="5"
            step="1"
          />
        </label>
        <label
          >Number of neighbours k
          <select v-model.number="k" aria-label="KNN neighbour count">
            <option v-for="n in [1, 3, 5]" :key="n" :value="n">{{ n }}</option>
          </select>
        </label>
      </div>
      <ScoreJourney
        v-if="kind !== 'knn'"
        :evidence="evidence"
        :kind="kind"
        :title="example.title"
      />
    </section>
  </section>
</template>

<style scoped>
.classifier-illustration {
  padding: 20px;
  border: 1px solid var(--line);
  background: white;
  border-radius: 5px;
  margin: 24px 0;
  min-width: 0;
}
.example-header span {
  color: var(--accent);
  font-size: 0.76rem;
  font-weight: 600;
}
.example-header p {
  color: var(--muted);
  font-size: 0.85rem;
}
.toy-controls {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px 22px;
}
.training-table {
  overflow-x: auto;
  margin: 14px 0 24px;
}
table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.83rem;
}
th,
td {
  text-align: left;
  border-bottom: 1px solid var(--line);
  padding: 10px 8px;
}
td:last-child {
  white-space: nowrap;
}
summary {
  cursor: pointer;
  color: var(--accent);
  font-size: 0.85rem;
  margin: 18px 0;
}
.toy-controls label {
  font-size: 0.83rem;
  margin: 0;
}
.toy-controls input {
  display: block;
  width: 100%;
  margin-top: 8px;
}
@media (max-width: 600px) {
  .classifier-illustration {
    padding: 14px;
  }
  .toy-controls {
    grid-template-columns: 1fr;
    gap: 14px;
  }
}
</style>
