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
window.addEventListener('popstate', sync)
document.addEventListener('click', onClick)
onUnmounted(() => {
  window.removeEventListener('popstate', sync)
  document.removeEventListener('click', onClick)
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
  <header class="site-header">
    <a class="site-brand" :href="courseHref()"
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
      <a
        :href="courseHref()"
        :class="{ active: isHome }"
        :aria-current="isHome ? 'page' : undefined"
        >Course home</a
      >
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
      <a class="button primary" :href="courseHref()">Return to course home →</a>
    </div>
    <div v-if="lesson" class="chapter-heading">
      <span class="eyebrow">TUTORIAL {{ lesson.number }} · {{ chapter?.title ?? 'Overview' }}</span>
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
