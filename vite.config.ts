import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  base: './',
  // Asset preparation updates files in place so a live dev server keeps its public-file index.
  publicDir: '.cache/public',
  plugins: [vue()],
  build: { outDir: 'dist', emptyOutDir: true },
})
