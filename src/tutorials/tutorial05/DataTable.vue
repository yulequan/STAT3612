<script setup lang="ts">
import { computed, ref, watch } from 'vue'
type Row = { split: string; label: number; text: string; features: number[] }
const props = defineProps<{ rows: Row[]; features?: boolean; caption: string }>()
const FEATURES = ['Chars', 'Tokens', 'Links', 'Digits', '!']
const query = ref('')
const label = ref('all')
const split = ref('all')
const sortBy = ref(-1)
const page = ref(0)
const size = 10
const filtered = computed(() => {
  const q = query.value.trim().toLowerCase()
  const rows = props.rows
    .map((row, index) => ({ ...row, index: index + 1 }))
    .filter(
      (r) =>
        (label.value === 'all' || String(r.label) === label.value) &&
        (split.value === 'all' || r.split === split.value) &&
        (!q || r.text.toLowerCase().includes(q)),
    )
  return sortBy.value < 0
    ? rows
    : rows.sort((a, b) => b.features[sortBy.value]! - a.features[sortBy.value]!)
})
const pages = computed(() => Math.max(1, Math.ceil(filtered.value.length / size)))
const visible = computed(() => filtered.value.slice(page.value * size, (page.value + 1) * size))
const spamShare = computed(
  () => filtered.value.filter((r) => r.label).length / Math.max(1, filtered.value.length),
)
watch([query, label, split, sortBy], () => (page.value = 0))
// Highlight the searched text, or the measured characters in feature mode.
const pattern = computed(() => {
  const q = query.value.trim().replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
  if (q) return new RegExp(`(${q})`, 'gi')
  return props.features ? /(https?:\/\/\S+|www\.\S+|\d+|!+)/gi : undefined
})
const parts = (text: string) => (pattern.value ? text.split(pattern.value) : [text])
</script>

<template>
  <div class="data-table">
    <div class="table-controls">
      <label
        >Search messages<input v-model="query" type="search" placeholder="e.g. free, call, love"
      /></label>
      <label
        >Label<select v-model="label">
          <option value="all">All</option>
          <option value="0">Ham</option>
          <option value="1">Spam</option>
        </select></label
      >
      <label
        >Split<select v-model="split">
          <option value="all">Train + validation</option>
          <option value="train">Train</option>
          <option value="validation">Validation</option>
        </select></label
      >
      <label v-if="features"
        >Sort by<select v-model.number="sortBy">
          <option :value="-1">Original order</option>
          <option v-for="(name, i) in FEATURES" :key="name" :value="i">{{ name }} (largest)</option>
        </select></label
      >
    </div>
    <p class="table-summary">
      <strong>{{ filtered.length.toLocaleString() }}</strong> messages ·
      <span class="spam-text">{{ (100 * spamShare).toFixed(1) }}% spam</span> · {{ caption }}
    </p>
    <div class="table-scroll">
      <table class="sheet" :aria-label="caption">
        <thead>
          <tr>
            <th class="num">#</th>
            <th>Split</th>
            <th>Label</th>
            <th class="message">Message</th>
            <template v-if="features"
              ><th
                v-for="(name, i) in FEATURES"
                :key="name"
                class="num"
                :class="{ sorted: sortBy === i }"
              >
                {{ name }}
              </th></template
            >
          </tr>
        </thead>
        <tbody>
          <tr v-for="row in visible" :key="row.index">
            <td class="num muted">{{ row.index }}</td>
            <td class="muted">{{ row.split === 'train' ? 'train' : 'val' }}</td>
            <td>
              <span class="tag" :class="row.label ? 'spam' : 'ham'">{{
                row.label ? 'spam' : 'ham'
              }}</span>
            </td>
            <td class="message">
              <template v-for="(piece, i) in parts(row.text)" :key="i"
                ><mark v-if="i % 2">{{ piece }}</mark
                ><template v-else>{{ piece }}</template></template
              >
            </td>
            <template v-if="features"
              ><td
                v-for="(value, i) in row.features"
                :key="i"
                class="num"
                :class="{ sorted: sortBy === i }"
              >
                {{ value }}
              </td></template
            >
          </tr>
          <tr v-if="!visible.length">
            <td :colspan="features ? 9 : 4" class="muted">No messages match.</td>
          </tr>
        </tbody>
      </table>
    </div>
    <div class="pager">
      <button :disabled="page === 0" @click="page--">← Previous</button>
      <span>Page {{ page + 1 }} / {{ pages }}</span>
      <button :disabled="page + 1 >= pages" @click="page++">Next →</button>
    </div>
  </div>
</template>

<style scoped>
.data-table {
  margin: 18px 0;
}
.table-controls {
  display: grid;
  grid-template-columns: 2fr repeat(3, minmax(0, 1fr));
  gap: 12px;
}
.table-controls label {
  margin: 0;
  font-size: 0.78rem;
}
.table-controls input,
.table-controls select {
  display: block;
  width: 100%;
  margin-top: 6px;
  padding: 8px 10px;
  border: 1px solid var(--line);
  border-radius: 3px;
  background: white;
}
.table-summary {
  font-size: 0.8rem;
  color: var(--muted);
  margin: 14px 0 8px;
}
.spam-text {
  color: #aa613d;
}
.table-scroll {
  overflow: auto;
  border: 1px solid var(--line);
  border-radius: 4px;
  background: var(--surface);
}
.sheet {
  border-collapse: collapse;
  width: 100%;
  font-size: 0.78rem;
}
.sheet th {
  position: sticky;
  top: 0;
  background: #f1f4f6;
  text-align: left;
  font-weight: 600;
  padding: 8px 10px;
  border-bottom: 1px solid var(--line);
  white-space: nowrap;
}
.sheet td {
  padding: 7px 10px;
  border-bottom: 1px solid #eef1f3;
  vertical-align: top;
}
.sheet tbody tr:nth-child(even) {
  background: #fafbfc;
}
.sheet .message {
  min-width: 260px;
  overflow-wrap: anywhere;
}
.num {
  text-align: right !important;
  font-variant-numeric: tabular-nums;
}
.muted {
  color: var(--muted);
}
.sorted {
  background: #e7eef3 !important;
  font-weight: 600;
}
.tag {
  display: inline-block;
  padding: 1px 8px;
  border-radius: 10px;
  font-size: 0.7rem;
  font-weight: 600;
  color: white;
}
.tag.ham {
  background: #45657e;
}
.tag.spam {
  background: #aa613d;
}
mark {
  background: #f6dccb;
  color: inherit;
  padding: 0 1px;
}
.pager {
  display: flex;
  gap: 12px;
  align-items: center;
  margin-top: 10px;
  font-size: 0.8rem;
  color: var(--muted);
}
.pager button {
  margin: 0 !important;
}
@media (max-width: 650px) {
  .table-controls {
    grid-template-columns: 1fr 1fr;
  }
  .table-controls label:first-child {
    grid-column: 1 / -1;
  }
}
</style>
