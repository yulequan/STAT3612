import { defineAsyncComponent } from 'vue'
import type { Lesson } from '..'
export default {
  id: 'tutorial04',
  number: '04',
  title: 'From pixels to a classifier',
  subtitle: 'Image classification with stochastic gradient descent',
  overview: {
    task: 'Build a classifier that distinguishes handwritten 3s from 8s, then use evidence from its mistakes to decide what to improve.',
    motivation:
      'We begin with logistic regression because its complete learning process is small enough to inspect: pixels become a score, a score becomes a prediction, and a loss tells us how to adjust the parameters. The aim is to understand and carry out that process, so you can make informed changes to the data, the training setup or the model.',
    stages: [
      {
        title: 'Define what the model will learn from',
        description:
          'Turn images into examples, features and labels. Separate training, validation and test data, then decide how to prepare the inputs. These choices define the problem the model actually sees.',
        chapters: ['data', 'prepare'],
      },
      {
        title: 'Connect a prediction to a learning signal',
        description:
          'Combine pixels into a probability, choose a loss that measures the error, and follow the gradient through one update. This explains why each part of the training algorithm is needed.',
        chapters: ['model', 'loss', 'update'],
      },
      {
        title: 'Run a complete experiment',
        description:
          'Repeat updates with minibatches, inspect learning curves and validation errors, and compare one motivated change. Choose your model before the final test evaluation.',
        chapters: ['train', 'evaluate'],
      },
      {
        title: 'Decide when to change the model itself',
        description:
          'Distinguish optimisation problems from limitations of a linear decision rule. Use XOR and a local filter to see what nonlinear features and convolution add, and frame a next experiment with an MLP or CNN.',
        chapters: ['beyond'],
      },
    ],
    objectives: [
      'Represent an image dataset as arrays with consistent shapes and labels, and explain the different roles of the training, validation and test sets.',
      'Connect the logistic prediction, cross-entropy loss and gradient update; predict how an inked or blank pixel affects one update.',
      'Run and modify a minibatch SGD experiment in Python, explaining how input scale, learning rate and batch size affect training.',
      'Use validation curves and individual mistakes to propose and compare a change, then justify a model choice and interpret its held-out test result.',
      'Explain a limitation of linear models and how a different representation or model could address it, including the locality and weight sharing used in convolution.',
    ],
    prerequisites:
      'Basic Python and NumPy arrays, matrix multiplication, and the idea of a derivative. You do not need prior experience building an image classifier; the tutorial introduces the model and its training loop.',
    outcome:
      'An executed notebook with a working baseline, one motivated experiment, a fair validation comparison, and your explanation of the selected model’s test result and limitations.',
  },
  component: defineAsyncComponent(() => import('./Tutorial04.vue')),
  chapters: [
    { id: 'data', title: 'Meet the data', question: 'What does an image look like to a model?' },
    { id: 'prepare', title: 'Prepare the inputs', question: 'What do we change before learning?' },
    { id: 'model', title: 'Make a prediction', question: 'How do pixels become a probability?' },
    { id: 'loss', title: 'Define the objective', question: 'How do we measure a bad prediction?' },
    { id: 'update', title: 'Take one step', question: 'Which way should the parameters move?' },
    {
      id: 'train',
      title: 'Train the classifier',
      question: 'What happens when we repeat the update?',
    },
    {
      id: 'evaluate',
      title: 'Evaluate & improve',
      question: 'What will you try in your next experiment?',
    },
    {
      id: 'beyond',
      title: 'Beyond a linear model',
      question: 'What would a different model change?',
    },
  ],
} satisfies Lesson
