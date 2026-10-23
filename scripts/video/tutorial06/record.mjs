// Record the Tutorial 06 sample from a local slide stage.
// Usage: node scripts/video/tutorial06/record_sample.mjs .cache/video/tutorial06-sample
import { chromium } from '@playwright/test'
import { readFile } from 'node:fs/promises'
import { existsSync } from 'node:fs'
import { spawn } from 'node:child_process'
import { performance } from 'node:perf_hooks'
import path from 'node:path'
import { SceneCapture } from './capture.mjs'

const output = path.resolve(process.argv[2] || '.cache/video/tutorial06-sample')
const spec = JSON.parse(await readFile(path.join(output, 'record.json'), 'utf8'))
const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms))
const port = 4192

const server = spawn(
  'python3',
  ['-m', 'http.server', String(port), '--bind', '127.0.0.1', '--directory', output],
  { stdio: ['ignore', 'ignore', 'pipe'], detached: false },
)
server.stderr.on('data', (data) => process.stderr.write(data))

let browser
try {
  let online = false
  for (let i = 0; i < 100; i += 1) {
    if (server.exitCode !== null) throw new Error(`Preview server exited; check port ${port}`)
    try {
      const response = await fetch(`http://127.0.0.1:${port}/stage.html`)
      if (response.ok) {
        online = true
        break
      }
    } catch {
      // Server is still starting.
    }
    await sleep(100)
  }
  if (!online) throw new Error('Slide stage server failed to start')

  browser = await chromium.launch({
    executablePath:
      process.env.CHROME_BIN ||
      (existsSync('/usr/bin/google-chrome') ? '/usr/bin/google-chrome' : undefined),
    args: ['--no-sandbox'],
  })
  const page = await browser.newPage({
    viewport: { width: 1920, height: 1080 },
    deviceScaleFactor: 1,
  })
  page.setDefaultTimeout(15000)
  const errors = []
  page.on('pageerror', (error) => errors.push(error.message))
  await page.route(/^https?:\/\/(?!127\.0\.0\.1:4192\/)/, (route) => route.abort())
  await page.goto(`http://127.0.0.1:${port}/stage.html`)
  await page.evaluate(() => document.fonts.ready)

  for (const [index, scene] of spec.scenes.entries()) {
    const folder = path.join(output, scene.id + '-frames')
    await page.evaluate(
      ({ image, cues, showPointer }) => window.prepareScene({ image, cues, showPointer }),
      { image: scene.image, cues: scene.cues, showPointer: scene.showPointer !== false },
    )
    const capture = new SceneCapture(page)
    await capture.start(folder)
    await page.evaluate(
      ({ cues, lead }) => window.playScene({ cues, lead }),
      { cues: scene.cues, lead: scene.lead },
    )
    const total = scene.lead + scene.duration + scene.tail
    await sleep(total * 1000)
    await page.evaluate(() => window.stopScene())
    const meta = await capture.stop()
    if (meta.actionSeconds < total - 0.35) {
      throw new Error(
        `Capture for ${scene.id} is too short: ${meta.actionSeconds.toFixed(2)}s < ${total.toFixed(2)}s`,
      )
    }
    console.log(
      `Recorded ${String(index + 1).padStart(2, '0')}/${spec.scenes.length} ${scene.id}: ` +
        `${meta.actionSeconds.toFixed(2)}s, ${meta.frames.length} frames`,
    )
  }
  if (errors.length) throw new Error(`Page errors:\n${errors.join('\n')}`)
} finally {
  if (browser) await browser.close()
  server.kill('SIGTERM')
}
