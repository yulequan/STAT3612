import { defineAsyncComponent } from 'vue'
import type { Lesson } from '..'
import curriculum from './curriculum.json'

export default {
  id: 'tutorial08',
  number: '08',
  title: curriculum.title,
  subtitle: curriculum.subtitle,
  tutor: { name: 'Yinghao Zhu', email: 'yhzhu99@connect.hku.hk' },
  materials: [{ title: 'Notebook + data', file: 'student.zip' }],
  overview: {
    task: curriculum.task,
    motivation: curriculum.motivation,
    stages: curriculum.stages,
    objectives: curriculum.objectives,
    prerequisites: curriculum.prerequisites,
    outcome: curriculum.outcome,
  },
  component: defineAsyncComponent(() => import('./Tutorial08.vue')),
  chapters: curriculum.chapters.map(({ id, title, question }) => ({
    id,
    title,
    question,
    heading: title,
  })),
} satisfies Lesson
