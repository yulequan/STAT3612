// Deterministic browser actions and timestamped screenshot recording.
// No credentials are loaded here; the browser only accesses the local built site.
import { chromium, expect } from '@playwright/test'
import { mkdir, readFile, writeFile } from 'node:fs/promises'
import { existsSync } from 'node:fs'
import { spawn } from 'node:child_process'
import { performance } from 'node:perf_hooks'
import path from 'node:path'

const root = process.cwd()
const output = path.resolve(process.argv[2] || '.cache/video/tutorial04-update')
const spec = JSON.parse(await readFile(path.join(root, 'scripts/video/tutorial04-update.json')))
const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms))
const server = spawn('npm', ['run', 'preview', '--', '--port', '4188', '--strictPort'], {
  stdio: ['ignore', 'ignore', 'pipe'], detached: true,
})
server.stderr.on('data', (data) => process.stderr.write(data))
let browser
try {
  let online = false
  for (let i = 0; i < 100; i++) {
    if (server.exitCode !== null) throw new Error('Preview server exited; check port 4188')
    try {
      const response = await fetch('http://127.0.0.1:4188')
      if (response.ok) { online = true; break }
    } catch {}
    await sleep(100)
  }
  if (!online) throw new Error('Preview server failed to start')
  browser = await chromium.launch({
    executablePath: process.env.CHROME_BIN || (existsSync('/usr/bin/google-chrome') ? '/usr/bin/google-chrome' : undefined),
    args: ['--no-sandbox'],
  })
  const page = await browser.newPage({ viewport: { width: 1920, height: 1080 }, deviceScaleFactor: 1 })
  page.setDefaultTimeout(15000)
  const errors = []
  page.on('pageerror', (error) => errors.push(error.message))
  await page.route(/^https?:\/\/(?!127\.0\.0\.1:4188\/)/, (route) => route.abort())
  await page.goto('http://127.0.0.1:4188/#/tutorial04/update')
  await expect(page.getByRole('status')).toContainText('Python ready', { timeout: 60000 })
  await expect(page.getByRole('img', { name: 'Weights after one update', exact: true })).toBeVisible()
  // Choose the label explicitly so the narration never depends on gallery ordering.
  const sampleSelect = page.getByLabel('Learn from this image')
  const eight = await sampleSelect.locator('option').evaluateAll((options) =>
    options.find((option) => option.textContent.trim().startsWith('8 ·')).value,
  )
  await sampleSelect.selectOption(eight)
  await expect(page.getByRole('img', { name: 'Actual digit: 8', exact: true })).toBeVisible()
  await page.locator('nav a[href="#/tutorial04/overview"]').click()
  await expect(page.locator('.overview-intro')).toBeVisible()
  await page.evaluate(() => document.fonts.ready)
  await page.addStyleTag({ content: `
    html { scroll-behavior: auto !important; }
    .content { max-width: 1550px; }
    .step-layout { grid-template-columns: 1.1fr 1fr; gap: 30px; }
    .step-layout .python-code { position: static; }
    .python-code pre, .python-code code { font-size: 17px; }
    .step-observation p, .trace-images p { font-size: 16px; }
    .step-observation h3 { font-size: 23px; }
    .variable-grid code { font-size: 19px; }
    .variable-grid span, .feature-inspector span { font-size: 15px; }
    .step-controls button { font-size: 15px; padding: 9px 12px; }
    .feature-inspector strong { font-size: 18px; }
    .feature-inspector label { font-size: 16px; }
    .trace-images .pixel-surface, .trace-images canvas { width: 112px !important; height: 112px !important; }
    .trace-images figcaption, .trace-images small { font-size: 14px; }
    #video-header { position: fixed; inset: 0 0 auto; height: 68px; background: #172a30;
      color: #fff; z-index: 2147483600; display: flex; align-items: center; justify-content: space-between;
      padding: 0 36px; font: 500 24px system-ui; pointer-events: none; }
    #video-header small { font-size: 16px; color: #b8d1c6; }
    #video-pointer { position: fixed; width: 30px; height: 38px; z-index: 2147483640;
      pointer-events: none; filter: drop-shadow(0 2px 3px #0007); }
    #video-focus { position: fixed; border: 3px solid #df9a36; border-radius: 7px;
      box-shadow: 0 0 0 5px #df9a3622; z-index: 2147483599; pointer-events: none; }
    .video-ring { position: fixed; width: 20px; height: 20px; border: 4px solid #e59425;
      border-radius: 50%; z-index: 2147483641; pointer-events: none; animation: video-click .8s ease-out forwards; }
    @keyframes video-click { from { transform: translate(-50%,-50%) scale(.5); opacity: 1; }
      to { transform: translate(-50%,-50%) scale(3); opacity: 0; } }
  ` })
  await page.evaluate((title) => {
    const header = document.createElement('div'); header.id = 'video-header'
    const name = document.createElement('span'); name.textContent = title
    const status = document.createElement('small'); status.textContent = 'STAT3612 · REAL BROWSER / PYTHON DEMO'
    header.append(name, status)
    const pointer = document.createElement('div'); pointer.id = 'video-pointer'
    pointer.innerHTML = '<svg width="30" height="38" viewBox="0 0 30 38"><path d="M3 2 L3 29 L10 23 L16 35 L22 32 L16 21 L27 21 Z" fill="white" stroke="#18322d" stroke-width="2"/></svg>'
    const focus = document.createElement('div'); focus.id = 'video-focus'; focus.style.display = 'none'
    document.body.append(header, pointer, focus)
  }, spec.title)
  let pointer = { x: 420, y: 160 }
  async function moveTo(x, y) {
    const start = { ...pointer }
    for (let i = 1; i <= 24; i++) {
      const t = i / 24, eased = t * t * (3 - 2 * t)
      pointer = { x: start.x + (x - start.x) * eased, y: start.y + (y - start.y) * eased }
      await page.mouse.move(pointer.x, pointer.y)
      await page.evaluate(({ x, y }) => {
        const p = document.querySelector('#video-pointer'); p.style.left = `${x}px`; p.style.top = `${y}px`
      }, pointer)
      await sleep(20)
    }
  }
  async function click(locator) {
    await locator.scrollIntoViewIfNeeded()
    const box = await locator.boundingBox()
    if (!box) throw new Error('Click target has no bounding box')
    await moveTo(box.x + box.width / 2, box.y + box.height / 2)
    await page.evaluate(({ x, y }) => {
      const ring = document.createElement('div'); ring.className = 'video-ring'
      ring.style.left = `${x}px`; ring.style.top = `${y}px`; document.body.append(ring)
      setTimeout(() => ring.remove(), 850)
    }, pointer)
    await page.mouse.click(pointer.x, pointer.y)
  }
  async function focus(locator) {
    const box = locator ? await locator.boundingBox() : null
    await page.evaluate((box) => {
      const f = document.querySelector('#video-focus')
      f.style.display = box ? 'block' : 'none'
      if (box) Object.assign(f.style, { left: `${box.x - 6}px`, top: `${box.y - 6}px`, width: `${box.width + 12}px`, height: `${box.height + 12}px` })
    }, box)
  }
  async function scrollTo(locator, padding = 90) {
    await page.evaluate(({ selector, padding }) => {
      window.scrollTo(0, document.querySelector(selector).getBoundingClientRect().top + scrollY - padding)
    }, { selector: locator, padding })
  }
  const stepper = page.getByRole('region', { name: 'Step through the Python update' })
  const variable = (name) => stepper.locator('.variable-grid > div').filter({ has: page.getByText(name, { exact: true }) })
  const timeline = []
  for (const [index, scene] of spec.scenes.entries()) {
    const dir = path.join(output, scene.id + '-frames')
    await mkdir(dir, { recursive: true })
    const meta = JSON.parse(await readFile(path.join(output, scene.id + '.json')))
    const duration = meta.extra_info.audio_length / 1000
    const lead = 2, tail = 1.2, total = lead + duration + tail
    await focus(null)
    await page.evaluate((label) => {
      document.querySelector('#video-header small').textContent = label
    }, `STAT3612 · ${String(index + 1).padStart(2, '0')} / ${spec.scenes.length} · ${scene.id.toUpperCase()}`)
    if (scene.action === 'lesson-task') await scrollTo('.overview-intro', 110)
    else if (scene.action === 'lesson-route') await scrollTo('.overview-route', 110)
    else if (scene.action === 'overview') { /* Navigate visibly in the recorded action. */ }
    else if (scene.action === 'run') await scrollTo('#practice', 100)
    else await scrollTo('.step-layout', scene.action === 'pixel' ? 80 : 100)
    await sleep(250)
    const frames = []
    const actionLog = []
    const begin = performance.now()
    let actionError
    const action = (async () => {
      await sleep(150)
      if (scene.action === 'lesson-task' || scene.action === 'lesson-route') {
        const target = page.locator(scene.action === 'lesson-task' ? '.overview-intro' : '.overview-route')
        await focus(target)
        const box = await target.boundingBox()
        await moveTo(box.x + 40, box.y + 35)
      } else if (scene.action === 'line') {
        await click(page.getByRole('button', { name: `Inspect Python line ${scene.line}`, exact: true }))
      } else if (scene.action === 'next') {
        await click(page.getByRole('button', { name: 'Next step →', exact: true }))
      } else if (scene.action === 'pixel') {
        const slider = page.getByLabel('Inspect pixel index j')
        const box = await slider.boundingBox()
        await moveTo(box.x + box.width * 0.5, box.y + box.height / 2)
        await page.mouse.down()
        await moveTo(box.x + box.width * 0.2, box.y + box.height / 2)
        await moveTo(box.x + box.width * 0.7, box.y + box.height / 2)
        await page.mouse.up()
        await focus(page.locator('.feature-inspector'))
      } else if (scene.action === 'run') {
        await click(page.getByRole('button', { name: 'Run Python →', exact: true }))
        await expect(page.getByLabel('Python output')).toContainText('new p(8):', { timeout: 60000 })
        await focus(page.getByLabel('Python output'))
      } else {
        await click(page.getByRole('navigation').getByRole('link', { name: /Take one step/ }))
        await expect(page.getByRole('status')).toContainText('Python ready')
        await expect(page.getByRole('img', { name: 'Actual digit: 8', exact: true })).toBeVisible()
        await scrollTo('#experiment', 100)
        await focus(page.locator('#experiment .image-row'))
        const box = await page.getByRole('img', { name: 'Actual digit: 8', exact: true }).boundingBox()
        await moveTo(box.x + box.width / 2, box.y + box.height / 2)
      }
      if (scene.line) {
        await expect(stepper.locator('[aria-current="step"]')).toHaveAttribute('aria-label', `Inspect Python line ${scene.line}`)
        if (scene.focus) await focus(variable(scene.focus))
        else if (scene.id === 'complete') await focus(page.locator('.step-result'))
        else await focus(stepper.locator('.python-code'))
      }
      const focusBox = await page.locator('#video-focus').boundingBox()
      if (!focusBox || focusBox.y < 68 || focusBox.y + focusBox.height > 1050) {
        throw new Error(`Focus is outside the usable video viewport: ${scene.id}`)
      }
      actionLog.push({ event: 'action_complete', seconds: (performance.now() - begin) / 1000 })
    })().catch((error) => { actionError = error })
    while ((performance.now() - begin) / 1000 < total) {
      const start = performance.now()
      const filename = `frame-${String(frames.length).padStart(5, '0')}.png`
      await page.screenshot({ path: path.join(dir, filename) })
      frames.push({ file: filename, time: (start - begin) / 1000 })
      if (actionError) throw actionError
      await sleep(Math.max(0, 100 - (performance.now() - start)))
    }
    await action
    if (actionError) throw actionError
    if (scene.id === 'probability') await expect(variable('probability p')).toContainText('0.5000')
    if (scene.id === 'residual') await expect(variable('residual p − y')).toContainText('-0.5000')
    if (scene.id === 'complete') await expect(page.locator('.step-result')).toContainText('true 8')
    const layout = await page.evaluate(() => {
      const selectors = ['.step-layout', '.feature-inspector', '.trace-images', '.python-output', '.overview-intro', '.overview-route', '#video-focus']
      return Object.fromEntries(selectors.map((selector) => {
        const element = document.querySelector(selector)
        const box = element?.getBoundingClientRect()
        return [selector, box ? { x: box.x, y: box.y, width: box.width, height: box.height } : null]
      }))
    })
    await writeFile(path.join(dir, 'layout.json'), JSON.stringify(layout, null, 2))
    await expect(page.locator('#video-caption')).toHaveCount(0)
    await expect(page.getByRole('alert')).toHaveCount(0)
    if (errors.length) throw new Error(errors.join('\n'))
    // Preserve real frame timestamps rather than assuming screenshots arrived at a fixed rate.
    const entries = frames.map((frame, i) => `file '${frame.file}'\nduration ${Math.max(.001, (frames[i + 1]?.time ?? total) - frame.time).toFixed(6)}`)
    entries.push(`file '${frames.at(-1).file}'`)
    await writeFile(path.join(dir, 'frames.txt'), entries.join('\n') + '\n')
    timeline.push({ id: scene.id, lead, duration, total, frames: frames.length, actionLog })
    console.log(`Recorded ${scene.id}: ${total.toFixed(2)}s, ${frames.length} frames`)
  }
  await writeFile(path.join(output, 'timeline.json'), JSON.stringify(timeline, null, 2))
} finally {
  await browser?.close()
  try { process.kill(-server.pid, 'SIGTERM') } catch {}
}
