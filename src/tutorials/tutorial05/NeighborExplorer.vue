<script setup lang="ts">
import { computed, ref, watch } from 'vue'

export type Neighbor = { text: string; label: number; distance: number; index?: number }
export type ToyPoint = { text: string; label: number; x: number; y: number }
const props = defineProps<{
  title: string
  neighbors: Neighbor[]
  probability?: number
  metric?: string
  zeroVector?: boolean
  points?: ToyPoint[]
  query?: { x: number; y: number }
}>()
const selected = ref(0)
const shown = ref(props.neighbors.length)
watch(
  () => props.neighbors,
  () => {
    selected.value = 0
    shown.value = props.neighbors.length
  },
)
const votes = computed(() => props.neighbors.slice(0, shown.value))
const spam = computed(() => votes.value.filter((n) => n.label === 1).length)
const probability = computed(() =>
  shown.value === props.neighbors.length && props.probability !== undefined
    ? props.probability
    : spam.value / Math.max(1, votes.value.length),
)
const nearest = computed(() => new Set(votes.value.map((n) => n.index)))
const selectedNeighbor = computed(() => props.neighbors[selected.value])
const selectedIndex = computed(() => selectedNeighbor.value?.index)
const distanceMax = computed(() => Math.max(0.1, ...props.neighbors.map((n) => n.distance)) * 1.1)
const color = (label: number) => (label ? '#aa613d' : '#45657e')
function selectPoint(index: number) {
  const rank = props.neighbors.findIndex((n) => n.index === index)
  if (rank >= 0) selected.value = rank
}
</script>

<template>
  <figure class="neighbor-explorer" :aria-label="title">
    <h3>{{ title }}</h3>
    <div class="neighbor-chart">
      <svg
        v-if="points && query"
        viewBox="0 0 400 360"
        role="img"
        aria-label="Toy word vectors and nearest neighbours"
      >
        <path d="M60 35V300H350" fill="none" stroke="#9dabb5" />
        <path
          d="M60 45 A255 255 0 0 1 315 300"
          fill="none"
          stroke="#d9e2e9"
          stroke-dasharray="4 4"
        />
        <text x="65" y="20">class weight ↑</text>
        <text x="220" y="345" text-anchor="middle" class="word-axis">prize weight →</text>
        <text x="60" y="322">0</text>
        <text x="310" y="322">1</text>
        <text x="40" y="300">0</text>
        <text x="40" y="45">1</text>
        <line
          v-for="n in votes"
          :key="'line' + n.index"
          :x1="60 + query.x * 255"
          :y1="300 - query.y * 255"
          :x2="60 + points[n.index!]!.x * 255"
          :y2="300 - points[n.index!]!.y * 255"
          stroke="#aebfc9"
          stroke-dasharray="3 4"
        />
        <g v-for="(point, i) in points" :key="i">
          <circle
            :cx="60 + point.x * 255"
            :cy="300 - point.y * 255"
            r="9"
            :fill="color(point.label)"
            :opacity="nearest.has(i) ? 1 : 0.3"
            :stroke="selectedIndex === i ? '#202e3a' : 'white'"
            :stroke-width="selectedIndex === i ? 3 : 1"
          />
          <circle
            v-if="nearest.has(i)"
            :cx="60 + point.x * 255"
            :cy="300 - point.y * 255"
            r="17"
            fill="transparent"
            stroke="#667e8d"
            tabindex="0"
            role="button"
            :aria-label="'Inspect toy neighbour ' + (i + 1)"
            @click="selectPoint(i)"
            @keydown.enter="selectPoint(i)"
            @keydown.space.prevent="selectPoint(i)"
          />
        </g>
        <path
          :d="'M' + (60 + query.x * 255) + ',' + (288 - query.y * 255) + 'l11 19h-22z'"
          fill="#202e3a"
        />
        <text :x="Math.min(270, 75 + query.x * 255)" :y="Math.max(32, 283 - query.y * 255)">
          New message
        </text>
      </svg>
      <svg
        v-else-if="neighbors.length"
        :viewBox="'0 0 500 ' + (68 + neighbors.length * 32)"
        role="img"
        aria-label="Fitted neighbour distances"
      >
        <line
          x1="68"
          x2="460"
          :y1="24 + neighbors.length * 32"
          :y2="24 + neighbors.length * 32"
          stroke="#9dabb5"
        />
        <g v-for="(n, i) in neighbors" :key="i">
          <text x="12" :y="29 + i * 32">#{{ i + 1 }}</text>
          <line
            x1="68"
            :x2="68 + (n.distance / distanceMax) * 375"
            :y1="24 + i * 32"
            :y2="24 + i * 32"
            stroke="#e1e7eb"
          />
          <circle
            :cx="68 + (n.distance / distanceMax) * 375"
            :cy="24 + i * 32"
            r="8"
            :fill="color(n.label)"
            :opacity="i < shown ? 1 : 0.25"
            :stroke="selected === i ? '#202e3a' : 'white'"
            :stroke-width="selected === i ? 3 : 1"
            tabindex="0"
            role="button"
            :aria-label="
              'Inspect neighbour ' +
              (i + 1) +
              ', ' +
              (n.label ? 'spam' : 'ham') +
              ', distance ' +
              n.distance.toFixed(3)
            "
            @click="selected = i"
            @keydown.enter="selected = i"
            @keydown.space.prevent="selected = i"
          />
        </g>
        <text x="68" :y="49 + neighbors.length * 32">0</text>
        <text x="460" :y="49 + neighbors.length * 32" text-anchor="end">
          {{ distanceMax.toFixed(2) }}
        </text>
        <text x="260" :y="65 + neighbors.length * 32" text-anchor="middle">
          {{ metric || 'Cosine' }} distance · smaller = nearer
        </text>
      </svg>
    </div>
    <p class="legend">
      <span class="ham-key">● Ham</span><span class="spam-key">● Spam</span>
      <span v-if="points">▲ New message · circled points vote</span
      ><span v-else>Click a point to read its message</span>
    </p>
    <p v-if="zeroVector" class="empty-vector">
      No known word features.
      {{
        points
          ? 'Add a known word to compare directions.'
          : 'These distance ties provide little word evidence.'
      }}
    </p>
    <template v-if="neighbors.length">
      <label class="vote-control"
        >Neighbours included: {{ shown }} / {{ neighbors.length }}
        <input
          v-model.number="shown"
          aria-label="Neighbours included"
          type="range"
          min="1"
          :max="neighbors.length"
          step="1"
        />
      </label>
      <div class="voters" aria-label="Neighbour votes">
        <button
          v-for="(n, i) in neighbors"
          :key="i"
          :class="[n.label ? 'spam' : 'ham', { omitted: i >= shown, selected: selected === i }]"
          :aria-pressed="selected === i"
          :aria-label="'Read neighbour ' + (i + 1)"
          @click="selected = i"
        >
          #{{ i + 1 }}
        </button>
      </div>
      <p class="vote-result" aria-live="polite">
        {{ shown === neighbors.length ? 'Full vote' : 'Vote from the shown neighbours' }}:
        <strong
          >{{ spam }} spam / {{ shown }} votes =
          <span data-testid="neighbor-probability"
            >{{ (100 * probability).toFixed(1) }}%</span
          ></strong
        >
      </p>
      <article v-if="selectedNeighbor" class="neighbor-message" aria-live="polite">
        <strong
          >Neighbour #{{ selected + 1 }} · {{ selectedNeighbor.label ? 'Spam' : 'Ham' }} · distance
          {{ selectedNeighbor.distance.toFixed(3) }}</strong
        >
        <p>
          <code>{{ selectedNeighbor.text }}</code>
        </p>
      </article>
      <details v-if="!points">
        <summary>All {{ neighbors.length }} neighbour messages</summary>
        <ol>
          <li v-for="(n, i) in neighbors" :key="i">
            <strong>{{ n.label ? 'Spam' : 'Ham' }} · {{ n.distance.toFixed(3) }}</strong> ·
            <code>{{ n.text }}</code>
          </li>
        </ol>
      </details>
      <figcaption v-if="shown < neighbors.length">
        Advance to include every neighbour used by the fitted vote.
      </figcaption>
    </template>
  </figure>
</template>

<style scoped>
.neighbor-explorer {
  margin: 24px 0;
  min-width: 0;
}
.neighbor-chart {
  overflow-x: auto;
  max-width: 100%;
}
svg {
  display: block;
  width: 100%;
  min-width: 340px;
  font: 14px system-ui;
  fill: var(--ink);
}
svg [role='button'] {
  cursor: pointer;
}
svg [role='button']:focus {
  outline: 2px solid #3d8a96;
}
.word-axis {
  font-family: ui-monospace, monospace;
}
.legend {
  display: flex;
  flex-wrap: wrap;
  gap: 10px 18px;
  color: var(--muted);
  font-size: 0.8rem;
}
.ham-key {
  color: #45657e;
}
.spam-key {
  color: #aa613d;
}
.vote-control {
  display: block;
  font-size: 0.85rem;
}
.vote-control input {
  display: block;
  width: 100%;
  margin-top: 10px;
}
.voters {
  display: flex;
  flex-wrap: wrap;
  gap: 7px;
  margin: 16px 0;
}
.voters button {
  color: white;
  padding: 6px 10px;
  border: 2px solid transparent;
  border-radius: 20px;
  margin: 0;
}
.ham {
  background: #45657e;
}
.spam {
  background: #aa613d;
}
.voters .omitted {
  opacity: 0.3;
}
.voters .selected {
  border-color: #202e3a;
}
.vote-result {
  font-size: 0.94rem;
}
.neighbor-message {
  padding: 14px 18px;
  border: 1px solid var(--line);
  background: #f6f8f9;
  font-size: 0.85rem;
}
.neighbor-message code {
  white-space: break-spaces;
  overflow-wrap: anywhere;
}
.neighbor-message p {
  margin-bottom: 0;
}
details {
  margin-top: 18px;
}
summary {
  color: var(--accent);
  cursor: pointer;
}
li {
  margin: 12px 0;
  font-size: 0.85rem;
  overflow-wrap: anywhere;
}
figcaption,
.empty-vector {
  color: var(--muted);
  font-size: 0.85rem;
  margin-top: 12px;
}
</style>
