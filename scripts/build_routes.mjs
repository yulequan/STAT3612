import { mkdir, readFile, writeFile } from 'node:fs/promises'
import { resolve } from 'node:path'
import { createServer } from 'vite'

// Read the actual course catalog through Vite, including its discovered lessons.
// No second list of chapters needs maintaining when a lesson is added.
const server = await createServer({
  server: { middlewareMode: true, hmr: false },
  optimizeDeps: { noDiscovery: true, include: [] },
  appType: 'custom',
})
try {
  const { courseSections } = await server.ssrLoadModule('/src/course.ts')
  const { tutorials } = await server.ssrLoadModule('/src/tutorials/index.ts')
  const routes = new Set()
  function collect(item) {
    const route = item.href.slice(1)
    // Public assets such as standalone quizzes are copied by Vite and already
    // have a concrete file path. Only generate directory entries for SPA URLs.
    if (!/\.[^/]+$/.test(route)) routes.add(route)
    item.children?.forEach(collect)
  }
  for (const section of courseSections) {
    routes.add(section.id)
    section.items.forEach(collect)
  }
  for (const lesson of tutorials) routes.add(`tutorials/${lesson.id}`)
  const html = await readFile('dist/index.html', 'utf8')
  for (const route of routes) {
    const folder = resolve('dist', route)
    await mkdir(folder, { recursive: true })
    const base = '../'.repeat(route.split('/').length)
    await writeFile(
      resolve(folder, 'index.html'),
      html.replace('<base href="./"', `<base href="${base}"`),
    )
  }
  console.log(`Generated ${routes.size} static course route entries.`)
} finally {
  await server.close()
}
