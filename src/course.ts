import { courseHref } from './navigation'
import { tutorials } from './tutorials'

export type CourseItem = {
  id: string
  title: string
  description: string
  href: string
  children?: CourseItem[]
}
export type CourseSection = { id: string; title: string; description: string; items: CourseItem[] }
export type Demo = CourseItem & { file: string }

// Add lecture links here as materials are published.
export const lectures: CourseItem[] = []
export const demos: Demo[] = [
  {
    id: 'gradient-descent',
    title: 'Gradient Descent Step by Step',
    description: 'Follow predictions, loss, gradients and parameter updates in 1D and 2D.',
    href: courseHref('demos/gradient-descent'),
    file: 'gradient-descent-step-by-step.html',
  },
  {
    id: 'gd-vs-sgd',
    title: 'GD vs SGD: Logistic Regression',
    description: 'Compare full-data and mini-batch updates on a 3D logistic-loss surface.',
    href: courseHref('demos/gd-vs-sgd'),
    file: 'gd-vs-sgd-logistic-regression.html',
  },
  {
    id: 'svm',
    title: 'Support Vector Machines',
    description:
      'Explore maximum margins, support vectors, hinge loss, feature maps and RBF generalization.',
    href: courseHref('demos/svm'),
    file: 'svm-explorations.html',
  },
]

export const quizzes: CourseItem[] = [
  {
    id: 'lecture-3-classification',
    title: 'Lecture 3 · Classification',
    description:
      'Check your understanding of classification, GLMs, discriminant analysis and evaluation.',
    href: courseHref('quizzes/lecture-3-classification.html'),
  },
  {
    id: 'lecture-4-model-selection',
    title: 'Lecture 4 · Model Selection & Feature Engineering',
    description:
      'Reason through cross-validation, regularization, preprocessing, polynomial regression and GAM.',
    href: courseHref('quizzes/lecture-4-model-selection.html'),
  },
]

export const courseSections: CourseSection[] = [
  {
    id: 'lectures',
    title: 'Lectures',
    description: 'Course concepts, lecture notes and slides.',
    items: lectures,
  },
  {
    id: 'tutorials',
    title: 'Tutorials',
    description: 'Guided practice with Python experiments and companion notebooks.',
    items: tutorials.map((lesson) => ({
      id: lesson.id,
      title: `Tutorial ${lesson.number} · ${lesson.title}`,
      description: lesson.subtitle,
      href: courseHref(`tutorials/${lesson.id}/overview`),
      children: [
        {
          id: 'overview',
          title: 'Overview',
          description: 'Task, objectives and learning route',
          href: courseHref(`tutorials/${lesson.id}/overview`),
        },
        ...lesson.chapters.map((chapter) => ({
          id: chapter.id,
          title: chapter.title,
          description: chapter.question,
          href: courseHref(`tutorials/${lesson.id}/${chapter.id}`),
        })),
      ],
    })),
  },
  {
    id: 'group-project',
    title: 'Group Project',
    description: 'Fall 2026 project assessment, deliverables and submission deadlines.',
    items: [
      {
        id: 'submission-guidelines',
        title: 'Submission Guidelines & Deadlines',
        description:
          'Proposal: 12 November. Final report, code, predictions and presentation: 6 December. Both at 23:59 HKT.',
        href: courseHref('group-project/submission-guidelines'),
      },
    ],
  },
  {
    id: 'demos',
    title: 'Demos',
    description: 'Interactive demonstrations to explore how the methods work.',
    items: demos,
  },
  {
    id: 'quizzes',
    title: 'Quizzes',
    description: 'Self-check questions with explanations for each lecture topic.',
    items: quizzes,
  },
]

export function matchesCourseItem(item: CourseItem, query: string): boolean {
  return (
    `${item.title} ${item.description}`.toLowerCase().includes(query) ||
    Boolean(item.children?.some((child) => matchesCourseItem(child, query)))
  )
}
