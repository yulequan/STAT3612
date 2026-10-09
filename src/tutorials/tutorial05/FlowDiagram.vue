<script setup lang="ts">
import InlineText from './InlineText.vue'

export type TeachingFlow = {
  title: string
  layout: string
  stages: { title: string; nodes: { label: string; text: string; code: string }[] }[]
  caption: string
}
const props = defineProps<{ flow: TeachingFlow; values?: object | null }>()

function resolve(value: string): string {
  return value.replace(/\{([\w.]+)\}/g, (_, path: string) => {
    let result: unknown = props.values
    for (const key of path.split('.')) {
      if (typeof result !== 'object' || result === null) return '…'
      result = (result as Record<string, unknown>)[key]
    }
    return typeof result === 'number' ? result.toLocaleString('en-US') : '…'
  })
}
</script>

<template>
  <figure class="teaching-flow" :class="flow.layout" :aria-label="flow.title">
    <h3>{{ flow.title }}</h3>
    <ol class="flow-stages">
      <li v-for="stage in flow.stages" :key="stage.title" class="flow-stage">
        <div class="stage-title">{{ stage.title }}</div>
        <div class="flow-nodes">
          <div v-for="node in stage.nodes" :key="node.label" class="flow-node">
            <strong><InlineText :text="resolve(node.label)" /></strong>
            <code v-if="node.code" class="flow-code">{{ node.code }}</code>
            <p v-if="node.text"><InlineText :text="resolve(node.text)" /></p>
          </div>
        </div>
      </li>
    </ol>
    <figcaption v-if="flow.caption"><InlineText :text="flow.caption" /></figcaption>
  </figure>
</template>

<style scoped>
.teaching-flow {
  margin: 28px 0;
  min-width: 0;
}
.flow-stages {
  list-style: none;
  margin: 18px 0 0;
  padding: 0;
  display: flex;
  gap: 32px;
}
.flow-stage {
  position: relative;
  flex: 1;
  min-width: 0;
}
.flow-stage + .flow-stage::before {
  content: '→';
  position: absolute;
  top: 48px;
  left: -25px;
  color: var(--muted);
  font-size: 1.25rem;
}
.stage-title {
  font-size: 0.8rem;
  color: var(--accent);
  font-weight: 600;
  margin-bottom: 8px;
}
.flow-nodes {
  display: flex;
  gap: 14px;
}
.flow-node {
  flex: 1;
  min-width: 0;
  padding: 14px 16px;
  background: #f3f6f8;
  border: 1px solid #d9e2e9;
  border-radius: 5px;
  overflow-wrap: anywhere;
}
.flow-node strong {
  display: block;
  font-size: 0.94rem;
}
.flow-node p {
  margin: 8px 0 0;
  font-size: 0.85rem;
  line-height: 1.65;
}
.flow-code {
  display: block;
  margin-top: 10px;
  font-family: var(--mono, 'SFMono-Regular', Consolas, monospace);
  font-size: 0.82rem;
  white-space: break-spaces;
  line-height: 1.65;
}
figcaption {
  margin-top: 14px;
  color: var(--muted);
  font-size: 0.85rem;
  line-height: 1.65;
}
.vertical .flow-stages {
  flex-direction: column;
}
.vertical .flow-stage + .flow-stage::before {
  content: '↓';
  top: -31px;
  left: 50%;
}
@media (max-width: 700px) {
  .flow-stages {
    flex-direction: column;
  }
  .flow-stage + .flow-stage::before {
    content: '↓';
    top: -31px;
    left: 50%;
  }
  .flow-nodes {
    flex-direction: column;
  }
}
</style>
