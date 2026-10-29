import { defineAsyncComponent } from 'vue'
import type { Lesson } from '..'

export default {
  id: 'tutorial07',
  number: '07',
  title: 'Midterm Review',
  subtitle: 'Core concepts, worked past-paper problems and the traps that cost marks',
  tutor: { name: 'Yinghao Zhu', email: 'yhzhu99@connect.hku.hk' },
  materials: [{ title: 'Slides (PDF)', file: 'midterm_review_slides.pdf' }],
  overview: {
    task: 'Review the midterm: the concepts it tests and fully worked problems from Practice Paper 1, Practice Paper 2 and Midterm 2022.',
    motivation:
      'Every applied problem in the deck is shown with its data table, plot and intermediate calculations, so you can check a full solution instead of only a final number.',
    stages: [
      {
        title: 'Read the deck',
        description:
          'Part 1 covers regression vs. classification, parametric vs. non-parametric, generative vs. discriminative, gradient descent and SGD, the bias-variance tradeoff, and validation. Parts 2 to 4 work linear models, classification and trees/SVM problems; part 5 lists the traps to reread last. Allow about 75 minutes.',
        chapters: ['slides'],
      },
    ],
    objectives: [
      'Decide between regression and classification from the target variable Y, and place each STAT3612 model on the parametric / non-parametric map.',
      'Fit small linear models by hand with the normal equations, and match OLS, Ridge and LASSO estimates to their paths.',
      'Compare classifiers by training error, read precision, recall and ROC, and compute a Gini split, a tree partition and an SVM margin.',
      'Spot the recurring exam traps: feature scaling, greedy stepwise selection, GLM vs. GAM, and which hyperparameters change flexibility.',
    ],
    prerequisites:
      'The lecture notes for weeks 1-6 and both practice papers. No Python is needed: every calculation is done by hand on six- to eleven-point datasets printed on the slides.',
    outcome:
      'A set of hand-worked answers to the past-paper and midterm problems, each with the reason it is right or wrong.',
    format:
      'Slides only, with no notebook. Answers reveal one page at a time, so 33 numbered slides occupy 69 PDF pages.',
  },
  component: defineAsyncComponent(() => import('./Tutorial07.vue')),
  chapters: [
    {
      id: 'slides',
      title: 'Review slides',
      question: 'How do the concepts connect to the exam questions?',
      heading: 'Midterm review slides',
    },
  ],
} satisfies Lesson
