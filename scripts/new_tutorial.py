#!/usr/bin/env python3
"""Scaffold a discovered Vue lesson and a Python Experiment; no old engine to copy."""
import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
parser.add_argument('number', type=int)
parser.add_argument('--title', required=True)
args = parser.parse_args()
if not 1 <= args.number <= 99:
    parser.error('number must be between 1 and 99')
identity = f'tutorial{args.number:02d}'
folder = ROOT / 'src/tutorials' / identity
if folder.exists():
    parser.error(f'{identity} already exists; refusing to overwrite it')
folder.mkdir(parents=True)
(folder / 'experiment.py').write_text('''"""Replace this example with the tutorial's scientific operations."""
import json
import numpy as np

class Experiment:
    def __init__(self, path):
        pass  # Load the optional dataset here.

    def initialize(self):
        return {'values': np.arange(5).tolist()}

    def dispatch(self, action, params):
        if action != 'initialize':
            raise ValueError(f'Unknown action: {action}')
        return json.dumps(self.initialize())
''')
(folder / 'README.md').write_text(f'# {args.title}\n\nReplace the scaffold with a practice task and a notebook.\n')
(folder / 'tutorial.json').write_text(json.dumps({
    'id': identity, 'title': args.title, 'experiment': 'experiment.py', 'dataset': None,
    'python_packages': ['numpy'], 'web_assets': ['experiment.py'],
    'student_files': ['experiment.py', 'README.md'],
}, indent=2) + '\n')
(folder / 'lesson.ts').write_text('''import { defineAsyncComponent } from 'vue'
import type { Lesson } from '..'
export default {
  id: ID, number: NUMBER, title: TITLE, subtitle: 'Practice lab',
  overview: {
    task: 'Describe the concrete problem students will solve.',
    motivation: 'Explain why this problem needs the methods introduced here.',
    stages: [{ title: 'Investigate the question', description: 'Replace this with the reasoning that connects the chapters.', chapters: ['explore'] }],
    objectives: ['Replace with observable skills students will practise.'],
    prerequisites: 'State the knowledge students will build on.',
    outcome: 'Describe the experiment or notebook students will complete.',
  },
  component: defineAsyncComponent(() => import('./Lesson.vue')),
  chapters: [{ id: 'explore', title: 'Explore', question: 'What will you investigate?' }],
} satisfies Lesson
'''.replace('ID', json.dumps(identity)).replace('NUMBER', json.dumps(f'{args.number:02d}')).replace('TITLE', json.dumps(args.title)))
(folder / 'Lesson.vue').write_text('''<script setup lang="ts">
import { onMounted, onUnmounted, ref } from 'vue'
import { createPython } from '../../runtime/python'
defineProps<{ chapter: string }>()
const runtime = createPython(ID)
const result = ref<unknown>()
const error = ref('')
onMounted(async () => {
  try { result.value = await runtime.start() }
  catch (e) { error.value = String(e) }
})
onUnmounted(runtime.dispose)
</script>
<template>
  <div class="panel"><h2>Start with a concrete question</h2>
    <p v-if="!runtime.ready.value && !error" role="status">{{ runtime.status.value }}</p>
    <p v-if="error" role="alert">{{ error }}</p>
    <pre v-if="result">{{ result }}</pre>
  </div>
</template>
'''.replace('ID', json.dumps(identity)))
print(f'Created {identity}. Edit its Vue lesson and Python experiment, add the notebook, then npm run build.')
