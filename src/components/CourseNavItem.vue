<script setup lang="ts">
import { computed, ref, useId, watch } from 'vue'
import { matchesCourseItem, type CourseItem } from '../course'

const props = defineProps<{
  item: CourseItem
  depth: number
  activeHref: string
  query: string
}>()
const childrenId = useId()
const childQuery = computed(() =>
  `${props.item.title} ${props.item.description}`.toLowerCase().includes(props.query)
    ? ''
    : props.query,
)
const expanded = ref(props.depth === 0)
const hasChildren = computed(() => Boolean(props.item.children?.length))
function contains(item: CourseItem, href: string): boolean {
  return item.href === href || Boolean(item.children?.some((child) => contains(child, href)))
}
const inActivePath = computed(() => contains(props.item, props.activeHref))
const isCurrent = computed(() => props.item.href === props.activeHref && !hasChildren.value)
const open = computed(() => Boolean(props.query) || expanded.value)
// Reveal the selected branch on direct entry and navigation, without closing others.
watch(
  () => props.activeHref,
  () => {
    if (inActivePath.value) expanded.value = true
  },
  { immediate: true },
)
</script>
<template>
  <li
    v-show="matchesCourseItem(item, query)"
    class="course-tree-item"
    :class="[`tree-level-${depth}`, { 'is-ancestor': hasChildren && inActivePath }]"
  >
    <div
      class="tree-row"
      :class="{ 'is-current': isCurrent || (depth === 0 && item.href === activeHref) }"
    >
      <a
        class="tree-link"
        :href="item.href"
        @click="hasChildren && (expanded = true)"
        :aria-current="isCurrent || (depth === 0 && item.href === activeHref) ? 'page' : undefined"
        >{{ item.title }}</a
      >
      <button
        v-if="hasChildren"
        type="button"
        class="tree-toggle"
        :aria-label="`Toggle ${item.title}`"
        :aria-expanded="open"
        :aria-controls="childrenId"
        :disabled="Boolean(query)"
        @click="expanded = !expanded"
      >
        <svg
          viewBox="0 0 16 16"
          width="16"
          height="16"
          aria-hidden="true"
          :class="{ expanded: open }"
        >
          <path
            d="m6 3 5 5-5 5"
            fill="none"
            stroke="currentColor"
            stroke-width="1.5"
            stroke-linecap="round"
            stroke-linejoin="round"
          />
        </svg>
      </button>
    </div>
    <div v-if="hasChildren" :id="childrenId" v-show="open" class="tree-branch">
      <ul class="course-tree">
        <CourseNavItem
          v-for="child in item.children"
          :key="child.id"
          :item="child"
          :depth="depth + 1"
          :active-href="activeHref"
          :query="childQuery"
        />
      </ul>
    </div>
    <small v-else-if="depth === 0 && item.children" class="outline-empty"
      >Materials coming soon</small
    >
  </li>
</template>
