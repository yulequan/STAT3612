<script setup lang="ts">
import { computed, nextTick, onUnmounted, ref, watch } from 'vue'
import { tutorials } from './tutorials'
import HomePage from './components/HomePage.vue'
import TutorialOverview from './components/TutorialOverview.vue'
import CourseCatalog from './components/CourseCatalog.vue'
import DemoPage from './components/DemoPage.vue'
import { courseSections, demos } from './course'
function readHash() {
  const current = window.location.hash
  const canonical = current
    .replace(/^#\/demo(?:\/)?$/, '#/demos')
    .replace(/^#\/(tutorial\d+)(?=\/|$)/, '#/tutorials/$1')
  if (current !== canonical) window.history.replaceState(null, '', canonical)
  return canonical
}
const hash = ref(readHash())
const menuOpen = ref(false)
const search = ref('')
const collapsed = ref<Record<string, boolean>>({})
const sync = () => {
  hash.value = readHash()
  menuOpen.value = false
  search.value = ''
  window.scrollTo({ top: 0 })
}
window.addEventListener('hashchange', sync)
onUnmounted(() => window.removeEventListener('hashchange', sync))
const parts = computed(() => hash.value.replace(/^#\/?/, '').split('/'))
const isHome = computed(() => !parts.value[0])
const courseSection = computed(() => courseSections.find((s) => s.id === parts.value[0]))
const catalog = computed(() => (!parts.value[1] ? courseSection.value : undefined))
const lesson = computed(() =>
  parts.value[0] === 'tutorials' ? tutorials.find((t) => t.id === parts.value[1]) : undefined,
)
const demo = computed(() =>
  parts.value[0] === 'demos' ? demos.find((d) => d.id === parts.value[1]) : undefined,
)
const index = computed(() => lesson.value?.chapters.findIndex((c) => c.id === parts.value[2]) ?? -1)
const chapter = computed(() => lesson.value?.chapters[index.value])
const outlineSections = computed(() => {
  const query = search.value.trim().toLowerCase()
  if (!query) return courseSections
  return courseSections.map((section) => ({
    ...section,
    items: section.items.filter((item) =>
      `${item.title} ${item.description}`.toLowerCase().includes(query),
    ),
  }))
})
const activeHref = computed(() =>
  lesson.value ? `#/tutorials/${lesson.value.id}/overview` : hash.value || '#/',
)
const notebook = computed(
  () => `${import.meta.env.BASE_URL}tutorials/${lesson.value?.id}/student.zip`,
)
function changeChapter(event: Event) {
  window.location.hash = `#/tutorials/${lesson.value!.id}/${(event.target as HTMLSelectElement).value}`
}
function link(i: number) {
  return `#/tutorials/${lesson.value!.id}/${lesson.value!.chapters[i]!.id}`
}
function section(id: string) {
  document.getElementById(id)?.scrollIntoView({ behavior: 'smooth', block: 'start' })
}
function focusMain() {
  document.getElementById('main')?.focus()
}
watch(
  hash,
  async () => {
    await nextTick()
    document.title = chapter.value
      ? `${chapter.value.title} · STAT3612`
      : lesson.value
        ? `Overview · ${lesson.value.title} · STAT3612`
        : demo.value
          ? `${demo.value.title} · STAT3612`
          : catalog.value
            ? `${catalog.value.title} · STAT3612`
            : 'STAT3612 · Statistical Machine Learning'
  },
  { immediate: true },
)
</script>
<template>
  <a class="skip-link" href="#main" @click.prevent="focusMain">Skip to content</a>
  <header class="site-header">
    <a class="site-brand" href="#/"
      ><span class="brand-mark">S</span
      ><span>STAT / SDST 3612<small>STATISTICAL MACHINE LEARNING</small></span></a
    >
    <div class="header-links">
      <span class="header-term">2026–27</span
      ><button
        class="mobile-menu"
        :aria-expanded="menuOpen"
        aria-controls="course-sidebar"
        @click="menuOpen = !menuOpen"
      >
        Course menu {{ menuOpen ? '−' : '+' }}
      </button>
    </div>
  </header>
  <aside id="course-sidebar" class="sidebar" :class="{ 'is-open': menuOpen }">
    <label class="chapter-search">
      <span class="sr-only">Find course content</span>
      <input v-model="search" placeholder="Find material…" type="search" />
    </label>
    <nav class="course-outline" aria-label="Course outline">
      <a href="#/" :class="{ active: isHome }" :aria-current="isHome ? 'page' : undefined"
        >Course home</a
      >
      <div v-for="item in outlineSections" :key="item.id" class="outline-section">
        <button
          class="outline-section-toggle"
          :aria-expanded="!collapsed[item.id]"
          :aria-controls="`outline-${item.id}`"
          :aria-label="item.title"
          @click="collapsed[item.id] = !collapsed[item.id]"
        >
          <span
            class="outline-chevron"
            :class="{ collapsed: collapsed[item.id] }"
            aria-hidden="true"
            >⌄</span
          >
          <span>{{ item.title }}</span>
          <span class="outline-count" aria-hidden="true">{{ item.items.length }}</span>
        </button>
        <div :id="`outline-${item.id}`" v-show="!collapsed[item.id]">
          <ul class="outline-children">
            <li v-for="entry in item.items" :key="entry.id">
              <a
                :href="entry.href"
                :class="{ active: activeHref === entry.href }"
                :aria-current="activeHref === entry.href ? 'page' : undefined"
                >{{ entry.title }}</a
              >
            </li>
          </ul>
          <small v-if="!search && !item.items.length" class="outline-empty"
            >Materials coming soon</small
          >
        </div>
      </div>
      <p v-if="search && !outlineSections.some((section) => section.items.length)" class="muted">
        No matching material.
      </p>
    </nav>
    <div v-if="lesson" class="sidebar-bottom">
      <span class="eyebrow">TUTORIAL {{ lesson.number }} · MATERIALS</span>
      <a class="download-link" :href="notebook" download>↓ Notebook + data</a>
    </div>
  </aside>
  <main id="main" tabindex="-1" class="lesson-main">
    <HomePage v-if="isHome" />
    <CourseCatalog v-else-if="catalog" :section="catalog" />
    <DemoPage v-else-if="demo" :key="demo.id" :demo="demo" />
    <div v-else-if="!lesson" class="not-found">
      <span class="eyebrow">PAGE NOT FOUND</span>
      <h1>This page is not available.</h1>
      <p>Choose a section from the course home.</p>
      <a class="button primary" href="#/">Return to course home →</a>
    </div>
    <div v-if="lesson" class="doc-preface">
      <div>
        <a href="#/">Course</a><span> / </span><a href="#/tutorials">Tutorials</a><span> / </span
        ><a :href="`#/tutorials/${lesson.id}/overview`">Tutorial {{ lesson.number }}</a
        ><span> / </span><span>{{ chapter?.title ?? 'Overview' }}</span>
      </div>
    </div>
    <div v-if="lesson" class="tutorial-toolbar">
      <label for="tutorial-chapter">Chapter</label>
      <select
        id="tutorial-chapter"
        aria-label="Tutorial chapter"
        :value="chapter?.id ?? 'overview'"
        @change="changeChapter"
      >
        <option value="overview">Overview</option>
        <option v-for="(item, i) in lesson.chapters" :key="item.id" :value="item.id">
          {{ String(i + 1).padStart(2, '0') }} · {{ item.title }}
        </option>
      </select>
      <span v-if="chapter" class="chapter-progress"
        >{{ index + 1 }} / {{ lesson.chapters.length }}</span
      >
    </div>
    <div v-if="lesson" class="chapter-heading">
      <span class="eyebrow">TUTORIAL {{ lesson.number }} · {{ chapter?.title ?? 'Overview' }}</span>
      <h1>{{ chapter?.question ?? lesson.title }}</h1>
      <div v-if="chapter" class="chapter-jumps" aria-label="Learning sections">
        <button @click="section('concept')">Understand</button><span>→</span
        ><button @click="section('experiment')">Explore</button><span>→</span
        ><button @click="section('python')">Read the Python</button><span>→</span
        ><button @click="section('practice')">Try it yourself</button>
      </div>
    </div>
    <div class="content" v-show="lesson">
      <TutorialOverview v-if="lesson && !chapter" :lesson="lesson" />
      <KeepAlive :max="2"
        ><component
          v-if="lesson && chapter"
          :is="lesson.component"
          :key="lesson.id"
          :chapter="chapter.id"
      /></KeepAlive>
      <footer v-if="lesson && chapter" class="chapter-footer">
        <a v-if="index > 0" :href="link(index - 1)"
          ><small>PREVIOUS</small>← {{ lesson.chapters[index - 1]!.title }}</a
        ><a v-else :href="`#/tutorials/${lesson.id}/overview`"><small>PREVIOUS</small>← Overview</a
        ><a v-if="index < lesson.chapters.length - 1" :href="link(index + 1)"
          ><small>NEXT CHAPTER</small>{{ lesson.chapters[index + 1]!.title }} →</a
        ><a v-else :href="`#/tutorials/${lesson.id}/overview`"
          ><small>TUTORIAL COMPLETE</small>Return to overview →</a
        >
      </footer>
    </div>
  </main>
</template>
