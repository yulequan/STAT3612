import type { Component } from 'vue'
export type Lesson = {
  id: string
  number: string
  title: string
  subtitle: string
  tutor?: { name: string; email: string }
  overview: {
    task: string
    motivation: string
    stages: { title: string; description: string; chapters: string[] }[]
    objectives: string[]
    prerequisites: string
    outcome: string
  }
  component: Component
  chapters: { id: string; title: string; question: string }[]
}
// Vite discovers each lesson at build time; no shared navigation edits are needed.
const modules = import.meta.glob<{ default: Lesson }>('./*/lesson.ts', { eager: true })
export const tutorials = Object.values(modules)
  .map((m) => m.default)
  .sort((a, b) => a.id.localeCompare(b.id))
