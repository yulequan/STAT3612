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
    task: 'Connect the STAT3612 concepts to the questions that test them, and work the applied problems through to a justified answer.',
    motivation:
      'The review deck starts from the exam format and the distinctions that True/False questions target, then solves problems from Practice Paper 1, Practice Paper 2 and Midterm 2022 on small datasets. Each problem is shown with its data table, plot and every intermediate calculation, so you can check a full solution rather than only a final number.',
    stages: [
      {
        title: 'Revisit the concepts',
        description:
          'Part 1 covers what the exam tests: regression vs. classification, parametric vs. non-parametric, generative vs. discriminative, gradient descent and SGD, the bias-variance tradeoff, and validation vs. k-fold cross-validation. Allow about 15 minutes.',
        chapters: ['slides'],
      },
      {
        title: 'Work the problems, then check the traps',
        description:
          'Parts 2 to 4 solve problems from Practice Paper 1, Practice Paper 2 and Midterm 2022: 2×2 normal equations and polynomial interpolation, matching OLS/Ridge/LASSO, reading regularization paths, a logistic boundary, a single-split tree and 3-NN, a classifier comparison, a Gini split, a 2D tree partition, and an SVM margin. Pause at each question before the next page reveals the answer; allow about 60 minutes. Part 5 closes with the recurring traps, such as where feature scaling matters, greedy stepwise selection, GLM as a special case of GAM, and which hyperparameter moves a model up or down the flexibility scale.',
        chapters: ['slides'],
      },
    ],
    objectives: [
      'Decide between regression and classification from the target variable Y, and place each STAT3612 model on the parametric / non-parametric map.',
      'Explain how generative and discriminative classifiers differ, and name which models in the course belong to each group.',
      'Describe how gradient descent and SGD update parameters, and what the learning rate changes.',
      'Read a bias-variance diagnosis from training and validation error, and choose between a validation set and k-fold cross-validation.',
      'Fit small linear and polynomial models by hand with the normal equations, and match OLS, Ridge and LASSO estimates to their paths.',
      'Compare classifiers by training error, read precision, recall and ROC, and compute a Gini split, a tree partition and an SVM margin.',
    ],
    prerequisites:
      'The lecture notes for weeks 1-6 and both practice papers. No Python is needed: every calculation in the deck is done by hand on six- to eleven-point datasets, and the deck includes the data tables and plots it refers to.',
    outcome:
      'Hand-worked answers to the past-paper and midterm problems, each with the reason it is right or wrong, plus your own short list of traps to reread before the exam.',
    format:
      'Slides only: read the deck here or download it for offline revision. There is no notebook. Questions in the deck reveal their answer one page at a time, so the 33 numbered slides occupy 69 PDF pages.',
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
