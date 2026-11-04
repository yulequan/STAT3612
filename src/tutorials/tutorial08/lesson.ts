import { defineAsyncComponent } from 'vue'
import type { Lesson } from '..'

export default {
  id: 'tutorial08',
  number: '08',
  title: 'Ensemble Learning and Support Vector Machines',
  subtitle: 'From decision trees, bagging and boosting to maximum-margin kernel classifiers',
  tutor: { name: 'Yinghao Zhu', email: 'yhzhu99@connect.hku.hk' },
  materials: [{ title: 'Notebook + setup (ZIP)', file: 'student.zip' }],
  overview: {
    task: 'Compare a single decision tree against bagging, random forests and boosting (AdaBoost, Gradient Boosting, XGBoost) on make_moons, then visualize SVM margins, support vectors and kernels (linear, polynomial, RBF, sigmoid) on Iris and XOR.',
    motivation:
      'A single unrestricted decision tree easily overfits noisy data. Combining trees via bagging or boosting improves generalization, while support vector machines find the maximum-margin hyperplane and use kernels for non-linear boundaries.',
    stages: [
      {
        title: 'Read the slides',
        description:
          '23 slides cover high-level ensemble and SVM design intuition, DecisionTree depth diagnostics, Bagging (oob_score), Random Forest, AdaBoost, Gradient Boosting, XGBoost, SVM margins/kernels, (C, gamma) sensitivity, and a two-slide Final Group Project starter baseline.',
        chapters: ['slides'],
      },
      {
        title: 'Run the companion notebook in Jupyter',
        description:
          'Download and extract the ZIP below for the companion notebook and setup files. The notebook includes saved outputs, 28 code cells and 14 figures, plus a self-contained Final Group Project starter pipeline (multi-table feature aggregation, GroupKFold and log_loss evaluation).',
        chapters: ['slides'],
      },
    ],
    objectives: [
      'Contrast how Bagging (parallel bootstrap trees) reduces variance while Boosting (sequential weak learners) reduces bias.',
      'Train and visualize DecisionTreeClassifier, BaggingClassifier, RandomForestClassifier, AdaBoostClassifier, GradientBoostingClassifier and XGBClassifier on make_moons.',
      'Visualize SVM decision boundaries, margins and support vectors using DecisionBoundaryDisplay and SVC.',
      'Compare Linear, Polynomial, RBF and Sigmoid kernels on the 2D Iris and non-linear XOR datasets, and apply feature scaling for Assignment 3.',
    ],
    prerequisites:
      'Basic Python, NumPy and scikit-learn. Reading the slides and saved notebook outputs requires no execution. To run the notebook locally, use Python 3.10+ and install the supplied requirements (including xgboost).',
    outcome:
      'An executed companion notebook comparing six tree/ensemble classifiers and four SVM kernels, ready to adapt for Assignment 3.',
    format:
      'Read the PDF slides here, then use Jupyter locally for the executable companion notebook. Python does not run inside this tutorial page.',
  },
  component: defineAsyncComponent(() => import('./Tutorial08.vue')),
  chapters: [
    {
      id: 'slides',
      title: 'Slides & notebook',
      question: 'How do ensembles and kernel SVMs build non-linear boundaries?',
      heading: 'Ensemble learning & SVM slides and notebook',
    },
  ],
} satisfies Lesson
