import { defineAsyncComponent } from 'vue'
import type { Lesson } from '..'

export default {
  id: 'tutorial10',
  number: '10',
  title: 'Deep Learning I: Neural Networks and Introduction to PyTorch',
  subtitle: 'From Tensors, einops and Automatic Differentiation to End-to-End MLP and CNN Training',
  tutor: { name: 'Yinghao Zhu', email: 'yhzhu99@connect.hku.hk' },
  materials: [{ title: 'Notebook + setup (ZIP)', file: 'student.zip' }],
  overview: {
    task: 'Master PyTorch tensor manipulation, einops rearrangement, dynamic computational graphs (autograd), and the canonical 5-step training loop for Multi-Layer Perceptrons (MLP) and 2D Convolutional Neural Networks (LeNet).',
    motivation:
      'Modern deep learning relies on hardware-accelerated tensors and automatic differentiation. Understanding tensor shapes, zero_grad(), torch.no_grad(), and modular nn.Module pipelines lets you build and debug arbitrary neural architectures.',
    stages: [
      {
        title: 'Read the slides',
        description:
          '25 slides cover PyTorch vs. NumPy, tensor attributes, device management, matrix multiplication (@) vs. elementwise product (*), reductions along dim, reshape/permute/squeeze/unsqueeze, einops.rearrange, reverse-mode autograd, why optimizer.zero_grad() is mandatory, Dataset/DataLoader, nn.Module MLPs, activation functions, SGD vs. Adam, 2D CNNs, and a Group Project tabular MLP starter.',
        chapters: ['slides'],
      },
      {
        title: 'Run the companion notebook in Jupyter',
        description:
          'Download and extract the ZIP below for the companion notebook (20 code cells, 7 plots) covering PyTorch tensors, einops, autograd, MLP and CNN training, and blending a PyTorch Tabular MLP with XGBoost.',
        chapters: ['slides'],
      },
    ],
    objectives: [
      'Manipulate PyTorch tensors across devices, reductions along dim, reshape/permute, and einops.rearrange.',
      'Trace forward and backward passes with requires_grad=True, .backward(), optimizer.zero_grad(), and torch.no_grad().',
      'Build custom Dataset/DataLoader pipelines and train nn.Module MLPs and 2D CNNs using CrossEntropyLoss and Adam.',
      'Train a calibrated Tabular MLP with BCEWithLogitsLoss inside GroupKFold and blend probabilities with tree ensembles.',
    ],
    prerequisites:
      'Basic Python, NumPy and linear algebra. To run the notebook locally, use Python 3.10+ and install PyTorch and einops from requirements.txt.',
    outcome:
      'An executed companion notebook covering PyTorch tensors, autograd, MLP/CNN training, and a tabular neural baseline for the Final Group Project.',
    format:
      'Read the PDF slides here, then use Jupyter locally for the executable companion notebook. Python does not run inside this tutorial page.',
  },
  component: defineAsyncComponent(() => import('./Tutorial10.vue')),
  chapters: [
    {
      id: 'slides',
      title: 'Slides & notebook',
      question: 'How do PyTorch tensors, autograd, and nn.Module power deep neural networks?',
      heading: 'Introduction to PyTorch slides and notebook',
    },
  ],
} satisfies Lesson
