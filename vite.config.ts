import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { existsSync, readFileSync } from 'node:fs'
import { resolve } from 'node:path'

export default defineConfig({
  base: './',
  // Asset preparation updates files in place so a live dev server keeps its public-file index.
  publicDir: '.cache/public',
  plugins: [
    vue(),
    {
      name: 'development-site-base',
      apply: 'serve',
      transformIndexHtml: (html) => html.replace('<base href="./"', '<base href="/"'),
    },
    {
      name: 'preview-directory-entries',
      configurePreviewServer(server) {
        // Match static hosts: a directory URL redirects before resolving its entry's base.
        server.middlewares.use((request, response, next) => {
          const url = new URL(request.url || '/', 'http://localhost')
          const directoryEntry = existsSync(
            resolve(
              server.config.root,
              server.config.build.outDir,
              `.${url.pathname}`,
              'index.html',
            ),
          )
          if (!url.pathname.endsWith('/') && directoryEntry) {
            response.writeHead(308, { Location: `${url.pathname}/${url.search}` })
            response.end()
          } else if (
            !directoryEntry &&
            request.headers.accept?.includes('text/html') &&
            !/\.[^/]+$/.test(url.pathname)
          ) {
            // Vite's SPA fallback needs an absolute base for unknown nested paths.
            const html = readFileSync(
              resolve(server.config.root, server.config.build.outDir, 'index.html'),
              'utf8',
            )
            response.writeHead(404, { 'Content-Type': 'text/html' })
            response.end(html.replace('<base href="./"', '<base href="/"'))
          } else next()
        })
      },
    },
  ],
  build: { outDir: 'dist', emptyOutDir: true },
})
