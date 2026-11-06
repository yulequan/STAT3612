import { defineAsyncComponent } from 'vue'
import type { Lesson } from '..'

export default {
  id: 'tutorial09',
  number: '09',
  title: 'Unsupervised Learning: Dimensionality Reduction and Clustering',
  subtitle: 'From PCA, Kernel PCA and t-SNE to K-Means, Hierarchical Clustering, DBSCAN and Gaussian Mixtures',
  tutor: { name: 'Yinghao Zhu', email: 'yhzhu99@connect.hku.hk' },
  materials: [{ title: 'Notebook + setup (ZIP)', file: 'student.zip' }],
  overview: {
    task: 'Compress high-dimensional datasets with Standardized PCA, Kernel PCA and t-SNE, then partition unlabeled data using K-Means, Ward Hierarchical Clustering, DBSCAN and Gaussian Mixture Models.',
    motivation:
      'When ground-truth labels are unavailable or features are collinear, unsupervised dimensionality reduction and clustering uncover intrinsic low-dimensional manifolds, denoise distance-based classifiers like KNN, and discover latent behavioral personas.',
    stages: [
      {
        title: 'Read the slides',
        description:
          '24 slides cover PCA geometry, why StandardScaler is mandatory before PCA, scree plots (explained_variance_ratio_), 2D/3D Iris projections, PCA vs. LDA, RBF KernelPCA on concentric circles, t-SNE on 64D digits, K-Means elbow and silhouette diagnostics, Ward dendrograms, Gaussian Mixtures, and practical end-to-end PCA + KNN and PCA + Clustering pipelines.',
        chapters: ['slides'],
      },
      {
        title: 'Run the companion notebook in Jupyter',
        description:
          'Download and extract the ZIP below for the companion notebook (20 code cells, 12 plots) covering PCA, KernelPCA, t-SNE, KMeans, AgglomerativeClustering, DBSCAN, GaussianMixture, PCA + KNeighborsClassifier denoising, and high-dimensional PCA + KMeans pipelines.',
        chapters: ['slides'],
      },
    ],
    objectives: [
      'Standardize features with StandardScaler and select the number of principal components using scree plots and cumulative explained_variance_ratio_.',
      'Contrast unsupervised PCA against supervised LinearDiscriminantAnalysis (LDA), non-linear KernelPCA, and manifold TSNE.',
      'Select the optimal cluster count K using the inertia elbow and silhouette_score, and diagnose K-Means failure modes on non-convex or elongated clusters.',
      'Combine Standardized PCA with KNeighborsClassifier and high-dimensional KMeans/GMM clustering in leak-free pipelines.',
    ],
    prerequisites:
      'Basic Python, NumPy, SciPy and scikit-learn. Reading the slides and saved notebook outputs requires no execution. To run the notebook locally, use Python 3.10+ and install the supplied requirements.',
    outcome:
      'An executed companion notebook covering dimensionality reduction, clustering, and practical unsupervised learning pipelines.',
    format:
      'Read the PDF slides here, then use Jupyter locally for the executable companion notebook. Python does not run inside this tutorial page.',
  },
  component: defineAsyncComponent(() => import('./Tutorial09.vue')),
  chapters: [
    {
      id: 'slides',
      title: 'Slides & notebook',
      question: 'How do dimensionality reduction and clustering uncover structure without labels?',
      heading: 'Unsupervised learning slides and notebook',
    },
  ],
} satisfies Lesson
