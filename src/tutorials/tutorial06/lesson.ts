import { defineAsyncComponent } from 'vue'
import type { Lesson } from '..'

export default {
  id: 'tutorial06',
  number: '06',
  title: 'Machine Learning for Time Series Data',
  subtitle: 'From data structures and temporal features to learned representations and evaluation',
  tutor: { name: 'Yinghao Zhu', email: 'yhzhu99@connect.hku.hk' },
  materials: [
    { title: 'Download Jupyter notebook', file: 'time_series_tutorial.ipynb' },
    { title: 'Notebook + setup (ZIP)', file: 'student.zip' },
  ],
  overview: {
    task: 'Turn time-stamped observations into useful machine-learning inputs, choose a prediction task, and evaluate it without leaking future information.',
    motivation:
      'A synthetic ICU vital-sign example connects data shapes, missingness, temporal features and learned representations. The closing slides introduce the learning-activity group project without providing a project solution.',
    stages: [
      {
        title: 'Read the slides',
        description:
          '34 slides cover time-series structure, feature construction, missing values, sequence encoders, ARIMA, validation and the group-project introduction. Allow about 60 minutes with discussion.',
        chapters: ['slides'],
      },
      {
        title: 'Experiment in Jupyter',
        description:
          'Download the companion notebook below. It includes saved outputs, 33 short code cells and 14 figures. Allow 60-90 minutes to read and experiment; all example data are generated locally.',
        chapters: ['slides'],
      },
    ],
    objectives: [
      'Distinguish tabular matrices, sequence tensors and the input/output shapes of different time-series tasks.',
      'Construct temporal features and choose appropriate binning, missingness and imputation semantics.',
      'Explain how learned representations support classification and forecasting, and distinguish trained models from illustrative architecture mechanics.',
      'Recognize the roles of differencing, seasonality and external predictors in ARIMA-style forecasting.',
      'Design validation around prediction-time availability, evaluation units and an independent final test.',
    ],
    prerequisites:
      'Basic Python, NumPy and supervised learning. Reading the slides and saved notebook outputs requires no execution. To run the notebook, use Python 3.10+ and install the supplied requirements; no GPU, PyTorch, external datasets or course project files are needed.',
    outcome:
      'An annotated notebook comparing temporal features and learned representations, with a justified development split and an independent final evaluation. The project slides provide open design questions, not a worked submission.',
    format:
      'Read the PDF here, then use Jupyter locally for the executable companion. The notebook includes saved synthetic outputs; Python does not run inside this tutorial page.',
  },
  component: defineAsyncComponent(() => import('./Tutorial06.vue')),
  chapters: [
    {
      id: 'slides',
      title: 'Slides & notebook',
      question: 'How do we learn from time-series data?',
      heading: 'Time-series slides & notebook',
    },
  ],
} satisfies Lesson
