import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  base: './',
  publicDir: '.cache/public',
  plugins: [vue()],
  build: { outDir: 'dist', emptyOutDir: true },
})
