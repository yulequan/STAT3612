import { test, before, after } from 'node:test'
import assert from 'node:assert/strict'
import { chromium } from '@playwright/test'
import { existsSync } from 'node:fs'
import { mkdtemp, readFile, rm } from 'node:fs/promises'
import os from 'node:os'
import path from 'node:path'
import { Presentation, PRESENTATION_VERSION } from '../../scripts/video/presentation.mjs'
import { SceneCapture } from '../../scripts/video/capture.mjs'

let browser
before(async () => {
  browser = await chromium.launch({
    executablePath: existsSync('/usr/bin/google-chrome') ? '/usr/bin/google-chrome' : undefined,
    args: ['--no-sandbox'],
  })
})
after(async () => {
  await browser?.close()
})

async function fixture() {
  const page = await browser.newPage({ viewport: { width: 1920, height: 1080 } })
  await page.setContent(`<style>
    body { margin:0; background:#f5f4ed; font:20px/1.6 sans-serif; }
    main { margin-left:248px; padding-top:80px; }
    aside { position:fixed; left:0; top:80px; width:248px; height:900px; }
    .content { width:1200px; margin:auto; }
    .panel { padding:30px; border:1px solid #ddd; margin:40px 0; }
    .chapter-heading { width:1100px; margin:auto; padding:24px; }
    .theory-paragraphs { width:860px; margin:100px auto; }
    .equation-card { padding:30px; }
    .python-code { margin:40px 0; }
    .code-line { display:block; height:28px; }
    .step-layout { display:flex; gap:30px; margin:40px 0; }
    .step-layout > div { width:50%; }
  </style><aside id="sidebar">All chapters remain visible</aside><main><div class="chapter-heading"><h1>Meet the data</h1></div><div class="content">
    <div class="theory-paragraphs"><p id="paragraph">An image becomes one feature vector. Neighbouring pixels are not automatically treated as similar.</p><p>Keep the input shape and pixel order consistent.</p></div>
    <div class="panel"><h2>Inspect the model</h2><label>Rate <input id="slider" type="range" min="0" max="100"></label><p>Compare the actual output, not a simulated result.</p></div>
    <div class="equation-card">z = x · w + b<p>Convert a score into a probability.</p></div>
    <div class="python-code"><code>${Array.from({ length: 28 }, (_, i) => `<span class="code-line">line ${i + 1}: calculate a real value</span>`).join('')}</code></div>
    <div class="step-layout"><div class="python-code">Executed Python<br>z = X @ w + b</div><div class="step-observation"><h3>Map scores to probabilities</h3><p id="value">probability p: 0.5000</p></div></div>
  </div></main>`)
  const presentation = new Presentation(page)
  await presentation.install()
  return { page, presentation }
}

for (const [name, selector] of [
  ['opening heading', '.chapter-heading'],
  ['paragraph context', '#paragraph'],
  ['formula', '.equation-card'],
  ['slider card', '#slider'],
  ['code and values together', '#value'],
]) {
  test(`${name} preserves the full page and scrolls its context into view`, async () => {
    const { page, presentation } = await fixture()
    try {
      const before = await page.locator(selector).boundingBox()
      const layout = await presentation.frame(page.locator(selector))
      assert.equal(layout.target.x, before.x)
      assert.ok(layout.target.y >= 80 && layout.target.y + layout.target.height <= 1046)
      assert.equal(await page.locator('#video-matte').count(), 0)
      assert.equal(
        await page.locator('main').evaluate((el) => getComputedStyle(el).transform),
        'none',
      )
      assert.equal(
        await page.locator('main').evaluate((el) => getComputedStyle(el).paddingTop),
        '80px',
      )
      assert.equal(await page.evaluate(() => document.elementFromPoint(100, 200).id), 'sidebar')
      await presentation.hidePointer()
      assert.equal(await page.locator('#video-pointer').isVisible(), false)
    } finally {
      await page.close()
    }
  })
}

test('long code frames the explained range, not just its first line', async () => {
  const { page, presentation } = await fixture()
  try {
    const line = page.locator('.code-line').nth(15)
    await line.evaluate((el) => {
      el.dataset.videoLineCount = '13'
    })
    const layout = await presentation.frame(line)
    assert.equal(layout.target.height, 364)
    assert.ok(layout.target.y >= 100 && layout.target.y + layout.target.height <= 1046)
  } finally {
    await page.close()
  }
})

test('interaction cursor moves, then is absent from the captured hold', async () => {
  const { page, presentation } = await fixture()
  const folder = await mkdtemp(path.join(os.tmpdir(), 'video-presentation-'))
  try {
    await presentation.frame(page.locator('#slider'))
    const box = await page.locator('#slider').boundingBox()
    const capture = new SceneCapture(page)
    await capture.start(folder)
    await presentation.move(box.x + box.width / 2, box.y + box.height / 2)
    await page.mouse.down()
    await presentation.move(box.x + box.width - 9, box.y + box.height / 2)
    await page.mouse.up()
    assert.ok(Number(await page.locator('#slider').inputValue()) > 80)
    await presentation.pulse()
    assert.equal(await page.locator('#video-pointer').isVisible(), true)
    await presentation.hidePointer()
    const result = await capture.stop(PRESENTATION_VERSION)
    assert.equal(result.layout.pointerHidden, true)
    assert.equal(result.layout.ripples, 0)
    assert.ok(result.layout.motionSamples.length > 10)
    const first = result.layout.motionSamples[0],
      last = result.layout.motionSamples.at(-1)
    // The final motion is the half-slider drag, not the earlier approach from the dock.
    assert.ok(Math.hypot(last.x - first.x, last.y - first.y) > 20)
    assert.ok(result.frames.length > 10)
    assert.equal(
      JSON.parse(await readFile(path.join(folder, 'capture.json'))).presentationVersion,
      PRESENTATION_VERSION,
    )
  } finally {
    await page.close()
    await rm(folder, { recursive: true })
  }
})
