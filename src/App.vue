<script setup lang="ts">
import { computed, nextTick, onUnmounted, ref, watch } from 'vue'
import { tutorials } from './tutorials'
import HomePage from './components/HomePage.vue'
import TutorialOverview from './components/TutorialOverview.vue'
const hash = ref(window.location.hash)
const menuOpen = ref(false)
const search = ref('')
const sync = () => {
  hash.value = window.location.hash
  menuOpen.value = false
  search.value = ''
  window.scrollTo({ top: 0 })
}
window.addEventListener('hashchange', sync)
onUnmounted(() => window.removeEventListener('hashchange', sync))
const parts = computed(() => hash.value.replace(/^#\/?/, '').split('/'))
const isHome = computed(() => !parts.value[0] || ['tutorials', 'demo'].includes(parts.value[0]))
const lesson = computed(() => tutorials.find((t) => t.id === parts.value[0]))
const index = computed(() => lesson.value?.chapters.findIndex((c) => c.id === parts.value[1]) ?? -1)
const chapter = computed(() => lesson.value?.chapters[index.value])
const chapters = computed(
  () =>
    lesson.value?.chapters.filter((c) =>
      `${c.title} ${c.question}`.toLowerCase().includes(search.value.toLowerCase()),
    ) ?? [],
)
const notebook = computed(
  () => `${import.meta.env.BASE_URL}tutorials/${lesson.value?.id}/student.zip`,
)
function link(i: number) {
  return `#/${lesson.value!.id}/${lesson.value!.chapters[i]!.id}`
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
        : parts.value[0] === 'demo'
          ? 'Demo · STAT3612'
          : 'STAT3612 · Statistical Machine Learning'
    if (parts.value[0] === 'tutorials') section('tutorial-catalog')
    if (parts.value[0] === 'demo') section('demo-catalog')
  },
  { immediate: true },
)
</script>
<template>
  <a class="skip-link" href="#main" @click.prevent="focusMain">Skip to content</a>
  <header class="site-header">
    <a class="site-brand" href="#/"
      ><span class="brand-mark">S</span
      ><span>STAT / SDST 3612<small>THE LEARNING COMPANION</small></span></a
    >
    <div class="header-links">
      <a href="#/tutorials">All tutorials</a><a href="#/demo">Demo</a
      ><a v-if="lesson" class="header-download" :href="notebook" download>Notebook + data ↓</a
      ><span class="header-term">2026–27</span
      ><button
        v-if="lesson"
        class="mobile-menu"
        :aria-expanded="menuOpen"
        aria-controls="chapter-sidebar"
        @click="menuOpen = !menuOpen"
      >
        Chapters {{ menuOpen ? '−' : '+' }}
      </button>
    </div>
  </header>
  <aside v-if="lesson" id="chapter-sidebar" class="sidebar" :class="{ 'is-open': menuOpen }">
    <a class="back-home" href="#/">← Course home</a>
    <div class="sidebar-title">
      <span class="eyebrow">TUTORIAL {{ lesson.number }}</span>
      <h2>{{ lesson.title }}</h2>
    </div>
    <label class="chapter-search"
      ><span class="sr-only">Find a chapter</span
      ><input v-model="search" placeholder="Find a chapter…" type="search"
    /></label>
    <nav aria-label="Tutorial chapters">
      <a
        v-if="!search || 'overview'.includes(search.toLowerCase())"
        :href="`#/${lesson.id}/overview`"
        :class="{ active: !chapter }"
        :aria-current="!chapter ? 'page' : undefined"
        ><span class="chapter-number">○</span><span>Overview</span></a
      >
      <a
        v-for="item in chapters"
        :key="item.id"
        :href="`#/${lesson.id}/${item.id}`"
        :aria-current="item.id === chapter?.id ? 'page' : undefined"
        :class="{ active: item.id === chapter?.id }"
        ><span class="chapter-number">{{
          String(lesson.chapters.indexOf(item) + 1).padStart(2, '0')
        }}</span
        ><span>{{ item.title }}</span></a
      >
      <p v-if="!chapters.length && !'overview'.includes(search.toLowerCase())" class="muted">
        No matching chapter.
      </p>
    </nav>
    <div class="sidebar-bottom">
      <span class="eyebrow">FROM READING TO DOING</span>
      <p>Understand the question.<br />Explore the mechanism.<br />Make the experiment yours.</p>
      <a class="download-link" :href="notebook" download>↓ Notebook + data</a>
    </div>
  </aside>
  <main id="main" tabindex="-1" :class="{ 'lesson-main': lesson }">
    <HomePage v-if="isHome" />
    <div v-else-if="!lesson" class="not-found">
      <span class="eyebrow">PAGE NOT FOUND</span>
      <h1>This tutorial is not available.</h1>
      <p>Choose a published tutorial from the course home.</p>
      <a class="button primary" href="#/">Return to course home →</a>
    </div>
    <div v-if="lesson" class="doc-preface">
      <div>
        <a href="#/">Course</a><span> / </span
        ><a :href="`#/${lesson.id}/overview`">Tutorial {{ lesson.number }}</a
        ><span> / </span><span>{{ chapter?.title ?? 'Overview' }}</span>
      </div>
      <span v-if="chapter"
        >{{ String(index + 1).padStart(2, '0') }} of {{ lesson.chapters.length }}</span
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
        ><a v-else :href="`#/${lesson.id}/overview`"><small>PREVIOUS</small>← Overview</a
        ><a v-if="index < lesson.chapters.length - 1" :href="link(index + 1)"
          ><small>NEXT CHAPTER</small>{{ lesson.chapters[index + 1]!.title }} →</a
        ><a v-else :href="notebook" download
          ><small>CONTINUE INDEPENDENTLY</small>Open the notebook ↓</a
        >
      </footer>
    </div>
  </main>
</template>
