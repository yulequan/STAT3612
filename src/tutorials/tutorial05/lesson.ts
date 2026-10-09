import { defineAsyncComponent } from 'vue'
import type { Lesson } from '..'
import curriculum from './curriculum.json'
export default {
  id: 'tutorial05',
  number: '05',
  title: curriculum.title,
  subtitle: curriculum.subtitle,
  tutor: { name: 'Yinghao Zhu', email: 'yhzhu99@connect.hku.hk' },
  overview: {
    task: curriculum.task,
    motivation: curriculum.motivation,
    stages: curriculum.stages,
    objectives: curriculum.objectives,
    prerequisites: curriculum.prerequisites,
    outcome: curriculum.outcome,
    dataset: curriculum.dataset,
  },
  component: defineAsyncComponent(() => import('./Tutorial05.vue')),
  chapters: curriculum.chapters.map(({ id, title, question }) => ({
    id,
    title,
    question,
    heading: title,
  })),
} satisfies Lesson
