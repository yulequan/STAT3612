<script setup lang="ts">
import { computed, nextTick, onUnmounted, ref, watch } from 'vue'
import { tutorials } from './tutorials'
import HomePage from './components/HomePage.vue'
import TutorialOverview from './components/TutorialOverview.vue'
import CourseCatalog from './components/CourseCatalog.vue'
import DemoPage from './components/DemoPage.vue'
import { courseSections, demos, matchesCourseItem } from './course'
import CourseNavItem from './components/CourseNavItem.vue'
import { courseHref, navigateCourse, readPath } from './navigation'
const path = ref(readPath())
const menuOpen = ref(false)
const menuButton = ref<HTMLButtonElement>()
const mobileViewport = window.matchMedia('(max-width: 850px)')
const smallViewport = ref(mobileViewport.matches)
const search = ref('')
const sync = () => {
  path.value = readPath()
  menuOpen.value = false
  search.value = ''
  window.scrollTo({ top: 0 })
}
function onClick(event: MouseEvent) {
  if (navigateCourse(event)) sync()
}
function closeMenu() {
  menuOpen.value = false
  menuButton.value?.focus()
}
function onKeydown(event: KeyboardEvent) {
  if (event.key === 'Escape' && menuOpen.value) closeMenu()
}
function onViewportChange(event: MediaQueryListEvent) {
  smallViewport.value = event.matches
  menuOpen.value = false
}
watch(menuOpen, async (open) => {
  document.body.style.overflow = open && smallViewport.value ? 'hidden' : ''
  if (open) {
    await nextTick()
    document.querySelector<HTMLInputElement>('.chapter-search input')?.focus()
  }
})
window.addEventListener('popstate', sync)
document.addEventListener('click', onClick)
document.addEventListener('keydown', onKeydown)
mobileViewport.addEventListener('change', onViewportChange)
onUnmounted(() => {
  window.removeEventListener('popstate', sync)
  document.removeEventListener('click', onClick)
  document.removeEventListener('keydown', onKeydown)
  mobileViewport.removeEventListener('change', onViewportChange)
  document.body.style.overflow = ''
})
const parts = computed(() => path.value.split('/'))
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
const outlineSections = courseSections.map((section) => ({
  ...section,
  href: courseHref(section.id),
  children: section.items,
}))
const searchQuery = computed(() => search.value.trim().toLowerCase())
const hasSearchResults = computed(() =>
  outlineSections.some((item) => matchesCourseItem(item, searchQuery.value)),
)
const activeHref = computed(() =>
  lesson.value && !chapter.value
    ? courseHref(`tutorials/${lesson.value.id}/overview`)
    : courseHref(path.value),
)
const notebook = computed(() => courseHref(`tutorials/${lesson.value?.id}/student.zip`))
function link(i: number) {
  return courseHref(`tutorials/${lesson.value!.id}/${lesson.value!.chapters[i]!.id}`)
}
function selectChapter(event: Event) {
  const chapterId = (event.target as HTMLSelectElement).value
  window.history.pushState(null, '', courseHref(`tutorials/${lesson.value!.id}/${chapterId}`))
  sync()
}
function focusMain() {
  document.getElementById('main')?.focus()
}
watch(
  path,
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
  <header class="site-header flex items-center justify-between gap-4">
    <a class="site-brand flex items-center gap-3" :href="courseHref()"
      ><span class="brand-mark" aria-hidden="true">
        <svg viewBox="0 0 32 32" width="26" height="26" fill="none">
          <path
            d="M25 6H7l9 10-9 10h18"
            stroke="currentColor"
            stroke-width="3.5"
            stroke-linejoin="miter"
          />
        </svg> </span
      ><span>STAT / SDST 3612<small>Statistical machine learning</small></span></a
    >
    <div class="header-links">
      <nav class="primary-navigation" aria-label="Course sections">
        <a
          v-for="section in courseSections"
          :key="section.id"
          :href="courseHref(section.id)"
          :aria-current="parts[0] === section.id ? 'page' : undefined"
          >{{ section.title }}</a
        >
      </nav>
      <button
        ref="menuButton"
        class="mobile-menu"
        :aria-label="menuOpen ? 'Close course menu' : 'Open course menu'"
        :aria-expanded="menuOpen"
        aria-controls="course-menu-panel"
        @click="menuOpen = !menuOpen"
      >
        <span>Contents</span>
        <svg viewBox="0 0 20 20" width="18" height="18" fill="none" aria-hidden="true">
          <path
            :d="menuOpen ? 'm5 5 10 10M5 15 15 5' : 'M3 6h14M3 14h14'"
            stroke="currentColor"
            stroke-width="1.5"
          />
        </svg>
      </button>
    </div>
  </header>
  <button
    v-if="menuOpen"
    class="menu-backdrop"
    tabindex="-1"
    aria-label="Dismiss course menu"
    @click="closeMenu"
  />
  <aside id="course-menu-panel" class="course-menu-panel" :class="{ 'is-open': menuOpen }">
    <label class="chapter-search">
      <span class="sr-only">Find course content</span>
      <svg viewBox="0 0 20 20" width="16" height="16" fill="none" aria-hidden="true">
        <circle cx="8.5" cy="8.5" r="5.5" stroke="currentColor" stroke-width="1.5" />
        <path d="m13 13 4 4" stroke="currentColor" stroke-width="1.5" />
      </svg>
      <input v-model="search" placeholder="Find course content…" type="search" />
    </label>
    <nav class="course-outline" aria-label="Course outline">
      <ul class="course-tree course-tree-root">
        <CourseNavItem
          v-for="item in outlineSections"
          :key="item.id"
          :item="item"
          :depth="0"
          :active-href="activeHref"
          :query="searchQuery"
        />
      </ul>
      <p v-if="searchQuery && !hasSearchResults" class="muted">No matching material.</p>
    </nav>
  </aside>
  <main id="main" tabindex="-1" class="lesson-main" :inert="menuOpen && smallViewport">
    <div v-if="lesson" class="tutorial-navigation">
      <label class="chapter-picker">
        <span>Tutorial {{ lesson.number }}</span>
        <select
          aria-label="Tutorial chapter"
          :value="chapter?.id || 'overview'"
          @change="selectChapter"
        >
          <option value="overview">Overview</option>
          <option v-for="item in lesson.chapters" :key="item.id" :value="item.id">
            {{ item.title }}
          </option>
        </select>
      </label>
      <a :href="notebook" download>↓ Notebook + data</a>
    </div>
    <HomePage v-if="isHome" />
    <CourseCatalog v-else-if="catalog" :section="catalog" />
    <DemoPage v-else-if="demo" :key="demo.id" :demo="demo" />
    <div v-else-if="!lesson" class="not-found">
      <span class="eyebrow">PAGE NOT FOUND</span>
      <h1>This page is not available.</h1>
      <p>Choose a section from the course home.</p>
      <a class="button primary" :href="courseHref()">Return to course home →</a>
    </div>
    <div v-if="lesson" class="chapter-heading">
      <div class="flex flex-wrap items-center justify-between gap-3">
        <span class="eyebrow"
          >TUTORIAL {{ lesson.number }} / {{ chapter?.title ?? 'Overview' }}</span
        >
        <span v-if="chapter" class="text-xs text-muted tabular-nums"
          >{{ String(index + 1).padStart(2, '0') }} /
          {{ String(lesson.chapters.length).padStart(2, '0') }} chapters</span
        >
      </div>
      <h1>{{ chapter?.question ?? lesson.title }}</h1>
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
        ><a v-else :href="courseHref(`tutorials/${lesson.id}/overview`)"
          ><small>PREVIOUS</small>← Overview</a
        ><a v-if="index < lesson.chapters.length - 1" :href="link(index + 1)"
          ><small>NEXT CHAPTER</small>{{ lesson.chapters[index + 1]!.title }} →</a
        ><a v-else :href="courseHref(`tutorials/${lesson.id}/overview`)"
          ><small>TUTORIAL COMPLETE</small>Return to overview →</a
        >
      </footer>
    </div>
  </main>
</template>
