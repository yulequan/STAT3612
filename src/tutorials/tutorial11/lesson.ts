import { defineAsyncComponent } from 'vue'
import type { Lesson } from '..'

export default {
  id: 'tutorial11',
  number: '11',
  title: 'From Transformer to LLMs and Agentic AI',
  subtitle: 'Self-Attention, Vision Transformers, Post-Training RL (RLHF/GRPO), ReAct Agents and Hugging Face Pipelines',
  tutor: { name: 'Yinghao Zhu', email: 'yhzhu99@connect.hku.hk' },
  materials: [{ title: 'Notebook + setup (ZIP)', file: 'student.zip' }],
  overview: {
    task: 'Implement Scaled Dot-Product Self-Attention and a mini Vision Transformer (ViT) in PyTorch, trace the evolution from BERT and GPT to Reasoning RL (GRPO) and ReAct Agents, and fine-tune a Hugging Face sequence classifier.',
    motivation:
      'The Transformer architecture unified natural language processing, computer vision (ViT), multimodal foundation models, and autonomous tool-using AI agents under a single self-attention paradigm.',
    stages: [
      {
        title: 'Read the slides',
        description:
          '25 slides cover the RNN bottleneck vs. parallel Self-Attention, Query/Key/Value lookup, 1/sqrt(d_k) scaling, PyTorch Scaled Dot-Product Attention, Multi-Head Attention, Bidirectional (BERT) vs. Causal (GPT) masking, Vision Transformer (ViT) patchification, scaling laws, 3-stage post-training (Pre-training -> SFT -> RLHF/GRPO), ReAct Coding & DeepResearch Agents, Hugging Face pipelines/tokenizers/models, full-course synthesis, and recommended Stanford/Berkeley open courses.',
        chapters: ['slides'],
      },
      {
        title: 'Run the companion notebook in Jupyter',
        description:
          'Download and extract the ZIP below for the companion notebook (18 code cells, 6 plots) covering PyTorch Self-Attention, causal masking, MiniViT image classification, GRPO advantage calculation, a multi-step ReAct Agent with tool calling, and Hugging Face sequence classification.',
        chapters: ['slides'],
      },
    ],
    objectives: [
      'Implement Scaled Dot-Product Self-Attention with causal and padding masks in PyTorch.',
      'Contrast Encoder-only (BERT Masked LM), Decoder-only (GPT Causal LM), and Vision Transformer (ViT) architectures.',
      'Understand the 3-stage LLM post-training lifecycle (Pre-training, SFT, RLHF/GRPO) and the ReAct (Reason -> Act -> Observe) agent loop.',
      'Use Hugging Face tokenizers, contextual [CLS] embeddings, and sequence classification models for transfer learning.',
    ],
    prerequisites:
      'PyTorch fundamentals from Tutorial 10. To run the notebook locally, use Python 3.10+ and install PyTorch, einops, and transformers from requirements.txt.',
    outcome:
      'An executed companion notebook spanning PyTorch Self-Attention, Vision Transformers, ReAct tool-using agents, and Hugging Face transfer learning.',
    format:
      'Read the PDF slides here, then use Jupyter locally for the executable companion notebook. Python does not run inside this tutorial page.',
  },
  component: defineAsyncComponent(() => import('./Tutorial11.vue')),
  chapters: [
    {
      id: 'slides',
      title: 'Slides & notebook',
      question: 'How did Self-Attention evolve into Vision Transformers, LLMs, and Frontier Agentic AI?',
      heading: 'Transformer, LLMs & Agentic AI slides and notebook',
    },
  ],
} satisfies Lesson
