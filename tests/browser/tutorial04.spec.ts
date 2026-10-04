import { test, expect, type Page } from '@playwright/test'
import { execFileSync } from 'node:child_process'
import { readFileSync, existsSync } from 'node:fs'

const python = existsSync('.venv/bin/python') ? '.venv/bin/python' : 'python3'
const reference = JSON.parse(
  execFileSync(python, ['tests/native_reference.py'], { encoding: 'utf8' }),
)

async function selectChapter(page: Page, chapter: string) {
  const menu = page.getByRole('button', { name: 'Course menu +' })
  if (await menu.isVisible()) await menu.click()
  await page
    .getByRole('navigation', { name: 'Course outline' })
    .locator(`a[href="/tutorials/tutorial04/${chapter}"]`)
    .last()
    .click()
}

test('all chapters, real Python training, final evaluation and offline downloads', async ({
  page,
  context,
}, info) => {
  const errors: string[] = [],
    external: string[] = []
  page.on('pageerror', (error) => errors.push(error.message))
  context.on('request', (request) => {
    if (/^https?:/.test(request.url()) && new URL(request.url()).hostname !== '127.0.0.1')
      external.push(request.url())
  })
  await context.route(/^https?:\/\/(?!127\.0\.0\.1)/, (route) => route.abort())
  await page.goto('/tutorials/tutorial04/data')
  await expect(page.getByRole('button', { name: 'Run Python →', exact: true })).toBeEnabled({
    timeout: 60_000,
  })
  await expect(page.getByRole('button', { name: /Inspect digit/ })).toHaveCount(12)
  await page.screenshot({ path: info.outputPath('data-desktop.png'), fullPage: true })

  await selectChapter(page, 'prepare')
  await page.getByLabel('Image operation').selectOption('blur')
  await expect(page.getByRole('img', { name: 'blur · same display scale' })).toBeVisible()
  await page.getByLabel('Image operation').selectOption('shift')
  await expect(page.getByRole('img', { name: 'shift · same display scale' })).toBeVisible()
  await selectChapter(page, 'model')
  await expect(page.getByRole('img', { name: 'Contribution x × w' })).toBeVisible()
  await selectChapter(page, 'loss')
  await page.getByLabel('Actual digit').selectOption('0')
  await expect(page.getByText('Cross-entropy loss', { exact: true })).toBeVisible()
  await selectChapter(page, 'update')
  await expect(page.getByRole('img', { name: 'Weights after one update' })).toBeVisible()

  await selectChapter(page, 'train')
  await page.getByRole('button', { name: 'Train classifier →' }).click()
  await expect(page.getByRole('button', { name: 'Train classifier →' })).toBeEnabled({
    timeout: 60_000,
  })
  await expect(page.getByText('Run 1', { exact: true })).toBeVisible()
  await expect(page.getByRole('alert')).toHaveCount(0)
  const downloaded = page.waitForEvent('download')
  await page.getByRole('button', { name: 'Export results ↓' }).click()
  const result = JSON.parse(readFileSync((await (await downloaded).path())!, 'utf8'))
  expect(result.runs[0].history).toHaveLength(reference.history.length)
  for (const [i, row] of result.runs[0].history.entries()) {
    for (const split of ['train', 'validation']) {
      expect(row[split].loss).toBeCloseTo(reference.history[i][split].loss, 8)
      expect(row[split].accuracy).toBe(reference.history[i][split].accuracy)
    }
  }
  await page.screenshot({ path: info.outputPath('training-desktop.png'), fullPage: true })

  await selectChapter(page, 'evaluate')
  await page.getByRole('button', { name: 'Evaluate shifted validation images' }).click()
  await expect(page.getByText('Shifted 1 px right', { exact: true })).toBeVisible()
  const testButton = page.getByRole('button', { name: 'Evaluate selected model on test set' })
  await expect(testButton).toBeDisabled()
  await page.getByLabel('Your model choice').fill('Baseline chosen using validation results.')
  await testButton.click()
  await expect(page.getByText('Final test accuracy')).toBeVisible()
  const finalDownload = page.waitForEvent('download')
  await page.getByRole('button', { name: 'Export experiment and decision ↓' }).click()
  const final = JSON.parse(readFileSync((await (await finalDownload).path())!, 'utf8'))
  expect(final.test.accuracy).toBe(reference.test.accuracy)
  expect(final.test.loss).toBeCloseTo(reference.test.loss, 8)
  await page.screenshot({ path: info.outputPath('evaluation-desktop.png'), fullPage: true })

  const zip = page.waitForEvent('download')
  await page.getByRole('link', { name: '↓ Notebook + data' }).click()
  expect(
    readFileSync((await (await zip).path())!)
      .subarray(0, 2)
      .toString(),
  ).toBe('PK')
  expect(errors).toEqual([])
  expect(external).toEqual([])
})

test('phone layout and direct chapter entry work without a trained model', async ({
  page,
}, info) => {
  await page.setViewportSize({ width: 390, height: 844 })
  await page.goto('/tutorials/tutorial04/evaluate')
  await expect(page.getByRole('heading', { name: 'Start with a trained model.' })).toBeVisible()
  await expect(page.getByRole('button', { name: 'Run Python →', exact: true })).toBeEnabled({
    timeout: 60_000,
  })
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBeTruthy()
  await page.screenshot({ path: info.outputPath('mobile.png'), fullPage: true })
})

test('runtime loading failure has a visible retry that recovers', async ({ page, context }) => {
  await context.route('**/python/pyodide.mjs', (route) => route.abort())
  await page.goto('/tutorials/tutorial04/data')
  await expect(page.getByRole('alert')).toBeVisible()
  await context.unroute('**/python/pyodide.mjs')
  await page.getByRole('button', { name: 'Restart Python', exact: true }).click()
  await expect(page.getByRole('button', { name: 'Run Python →', exact: true })).toBeEnabled({
    timeout: 60_000,
  })
  await expect(page.getByRole('alert')).toHaveCount(0)
})

test('training can be stopped without freezing the page or leaving a stale error', async ({
  page,
}) => {
  await page.goto('/tutorials/tutorial04/train')
  await expect(page.getByRole('button', { name: 'Run Python →', exact: true })).toBeEnabled({
    timeout: 60_000,
  })
  await page.getByLabel('Epochs', { exact: true }).fill('100')
  await page.getByRole('combobox', { name: 'Batch size', exact: true }).selectOption('1')
  await page.getByRole('button', { name: 'Train classifier →' }).click()
  await page.getByRole('button', { name: 'Stop and reset Python' }).click()
  await expect(page.getByRole('button', { name: 'Run Python →', exact: true })).toBeEnabled({
    timeout: 60_000,
  })
  await expect(page.getByRole('button', { name: 'Train classifier →' })).toBeEnabled()
  await expect(page.getByRole('alert')).toHaveCount(0)
  await expect(page.getByRole('heading', { name: 'Your experiment starts here.' })).toBeVisible()
})

test('built site works under a subdirectory on an ordinary static server', async ({ page }) => {
  const errors: string[] = []
  page.on('pageerror', (error) => errors.push(error.message))
  await page.goto(
    `http://127.0.0.1:${process.env.TEST_STATIC_PORT || '4174'}/dist/tutorials/tutorial04/update`,
  )
  await expect(page.getByRole('button', { name: 'Run Python →', exact: true })).toBeEnabled({
    timeout: 60_000,
  })
  await expect(page.getByRole('img', { name: 'Weights after one update' })).toBeVisible()
  const file = page.waitForEvent('download')
  await page.getByRole('link', { name: '↓ Notebook + data' }).click()
  expect(
    readFileSync((await (await file).path())!)
      .subarray(0, 2)
      .toString(),
  ).toBe('PK')
  expect(errors).toEqual([])
})

test('course home offers a choice without starting Python and preserves the chosen lab', async ({
  page,
}, info) => {
  const pythonRequests: string[] = []
  page.on('request', (request) => {
    if (/\/python\/|\.whl|\.wasm/.test(request.url())) pythonRequests.push(request.url())
  })
  await page.goto('/')
  await expect(
    page.getByRole('heading', { name: 'Statistical Machine Learning', exact: true }),
  ).toBeVisible()
  expect(page.workers()).toHaveLength(0)
  expect(pythonRequests).toEqual([])
  await page.screenshot({ path: info.outputPath('course-home.png'), fullPage: true })
  await page
    .getByRole('main')
    .getByRole('link', { name: /From pixels to a classifier/ })
    .click()
  await expect(page).toHaveURL(/\/tutorials\/tutorial04\/overview$/)
  await expect(
    page.getByRole('heading', { name: 'Learning objectives', exact: true }),
  ).toBeVisible()
  await expect(
    page.getByRole('heading', { name: 'How the pieces fit together', exact: true }),
  ).toBeVisible()
  expect(page.workers()).toHaveLength(0)
  expect(pythonRequests).toEqual([])
  await page.screenshot({ path: info.outputPath('tutorial-overview.png'), fullPage: true })
  await page.getByRole('link', { name: 'Begin: Meet the data →', exact: true }).click()
  await expect(page.getByRole('button', { name: 'Run Python →', exact: true })).toBeEnabled({
    timeout: 60_000,
  })
  const worker = page.workers()[0]
  const editor = page.getByRole('textbox', { name: 'Editable Python experiment' })
  await editor.fill('print("my preserved experiment")')
  await page.getByRole('link', { name: 'Course home', exact: true }).click()
  await expect(
    page.getByRole('heading', { name: 'Statistical Machine Learning', exact: true }),
  ).toBeVisible()
  await page
    .getByRole('main')
    .getByRole('link', { name: /From pixels to a classifier/ })
    .click()
  await page.getByRole('link', { name: 'Begin: Meet the data →', exact: true }).click()
  await expect(editor).toContainText('my preserved experiment')
  expect(page.workers()).toEqual([worker])
  await page.goto('/tutorials/tutorial04')
  await expect(
    page.getByRole('heading', { name: 'Learning objectives', exact: true }),
  ).toBeVisible()
  await page.getByRole('link', { name: 'Begin: Meet the data →', exact: true }).click()
  await page
    .locator('.chapter-footer')
    .getByRole('link', { name: /Overview/ })
    .click()
  await expect(page).toHaveURL(/\/tutorials\/tutorial04\/overview$/)
  await page.getByLabel('Find course content').fill('gradient-does-not-exist')
  await expect(page.getByText('No matching material.')).toBeVisible()
  await page.goto('/tutorials/tutorial99/data')
  await expect(page.getByRole('heading', { name: 'This page is not available.' })).toBeVisible()
})

test('every chapter connects rendered maths, highlighted source and runnable Python', async ({
  page,
}) => {
  await page.goto('/tutorials/tutorial04/data')
  await expect(page.getByRole('button', { name: 'Run Python →', exact: true })).toBeEnabled({
    timeout: 60_000,
  })
  const chapters = ['data', 'prepare', 'model', 'loss', 'update', 'train', 'evaluate', 'beyond']
  const outputs = [
    'same value:',
    'mean absolute change:',
    'contribution:',
    'loss=',
    'new p(8):',
    'validation:',
    'Nearest-centroid validation accuracy:',
    'predictions:',
  ]
  for (const [i, chapter] of chapters.entries()) {
    await selectChapter(page, chapter)
    await expect(page.locator('a[download][href$="student.zip"]')).toHaveCount(1)
    await expect(page.locator('#concept .katex').first()).toBeVisible()
    await expect(page.locator('.katex-error')).toHaveCount(0)
    await expect(page.locator('#python .hljs-keyword').first()).toBeVisible()
    await page.getByRole('button', { name: 'Run Python →', exact: true }).click()
    await expect(page.getByLabel('Python output')).toContainText(outputs[i]!, { timeout: 60_000 })
    await expect(page.getByRole('alert')).toHaveCount(0)
  }
})

test('trace exposes values only after their line executes; edited snippets recover and can be stopped', async ({
  page,
}, info) => {
  await page.goto('/tutorials/tutorial04/update')
  await expect(page.getByRole('button', { name: 'Run Python →', exact: true })).toBeEnabled({
    timeout: 60_000,
  })
  const stepper = page.getByRole('region', { name: 'Step through the Python update' })
  const variable = (name: string) =>
    stepper.locator('.variable-grid > div').filter({ has: page.getByText(name, { exact: true }) })
  await expect(stepper.locator('[aria-current="step"]')).toHaveAttribute(
    'aria-label',
    'Inspect Python line 2',
  )
  await expect(variable('score z')).toContainText('0.0000')
  await expect(variable('probability p')).toContainText('not computed yet')
  await page.getByRole('button', { name: 'Next step →' }).click()
  await expect(variable('probability p')).toContainText('0.5000')
  await expect(variable('residual p − y')).toContainText('not computed yet')
  await page.getByRole('button', { name: 'Inspect Python line 7', exact: true }).click()
  await expect(
    page.getByRole('img', { name: 'Updated weights from this executed line' }),
  ).toBeVisible()
  await page.screenshot({ path: info.outputPath('execution-trace.png'), fullPage: true })
  const editor = page.getByRole('textbox', { name: 'Editable Python experiment' })
  await editor.fill('print("partial output")\nraise ValueError("change this line")')
  await page.getByRole('button', { name: 'Run Python →', exact: true }).click()
  await expect(page.getByRole('alert')).toContainText('ValueError: change this line')
  await expect(page.getByLabel('Python output')).toContainText('partial output')
  await editor.fill('print("recovered", X_train.shape)')
  await page.getByRole('button', { name: 'Run Python →', exact: true }).click()
  await expect(page.getByLabel('Python output')).toContainText('recovered (960, 784)')
  await expect(page.getByRole('alert')).toHaveCount(0)
  await selectChapter(page, 'loss')
  await expect(editor).toContainText('cross_entropy')
  await selectChapter(page, 'update')
  await expect(editor).toContainText('recovered')
  await editor.fill('while True:\n    pass')
  await page.getByRole('button', { name: 'Run Python →', exact: true }).click()
  await page.getByRole('button', { name: 'Stop and reset Python', exact: true }).click()
  await expect(page.getByRole('button', { name: 'Run Python →', exact: true })).toBeEnabled({
    timeout: 60_000,
  })
  await editor.fill('print("after restart")')
  await page.getByRole('button', { name: 'Run Python →', exact: true }).click()
  await expect(page.getByLabel('Python output')).toContainText('after restart')
})

test('nonlinear rules solve XOR and Python convolution responds to the window and filter', async ({
  page,
}, info) => {
  await page.goto('/tutorials/tutorial04/beyond')
  await expect(page.getByRole('button', { name: 'Run Python →', exact: true })).toBeEnabled({
    timeout: 60_000,
  })
  await expect(page.getByText('3 / 4 XOR examples classified correctly')).toBeVisible()
  for (const mode of ['interaction', 'hidden']) {
    await page.getByLabel('Decision rule').selectOption(mode)
    await expect(page.getByText('4 / 4 XOR examples classified correctly')).toBeVisible()
    await expect(page.locator('.katex-error')).toHaveCount(0)
  }
  await expect(page.getByRole('img', { name: 'Feature map · 26 × 26' })).toBeVisible()
  await page.getByLabel('Example filter').selectOption('average')
  await expect(page.locator('.kernel-grid small').first()).toHaveText('× 0.11')
  await page.getByLabel('Window row:').fill('0')
  await page.getByLabel('Window column:').fill('0')
  await expect(page.locator('.kernel-result')).toHaveText('sum = 0.0000')
  await page.getByLabel('Window row:').fill('10')
  await page.getByLabel('Window column:').fill('10')
  await expect(page.locator('.kernel-result')).not.toHaveText('sum = 0.0000')
  // The independent student calculation must agree with the displayed window sum.
  const editor = page.getByRole('textbox', { name: 'Editable Python experiment' })
  await editor.fill(
    'i = int(np.flatnonzero(y_train == 0)[0])\nprint(f"sum = {images[i, 10:13, 10:13].mean():.4f}")',
  )
  await page.getByRole('button', { name: 'Run Python →', exact: true }).click()
  const expected = await page.locator('.kernel-result').innerText()
  await expect(page.getByLabel('Python output')).toContainText(expected)
  await page.screenshot({ path: info.outputPath('beyond-linear.png'), fullPage: true })
})

test('phone home, chapter menu, equations and editor stay within the viewport', async ({
  page,
}, info) => {
  await page.setViewportSize({ width: 390, height: 844 })
  await page.goto('/')
  await page.screenshot({ path: info.outputPath('home-mobile.png'), fullPage: true })
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBeTruthy()
  await page
    .getByRole('main')
    .getByRole('link', { name: /From pixels to a classifier/ })
    .click()
  await expect(
    page.getByRole('heading', { name: 'Learning objectives', exact: true }),
  ).toBeVisible()
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBeTruthy()
  await page.screenshot({ path: info.outputPath('overview-mobile.png'), fullPage: true })
  await page.getByRole('link', { name: 'Begin: Meet the data →', exact: true }).click()
  await expect(page.getByRole('button', { name: 'Run Python →', exact: true })).toBeEnabled({
    timeout: 60_000,
  })
  for (const chapter of ['update', 'beyond']) {
    await selectChapter(page, chapter)
    await expect(page.locator('a[download][href$="student.zip"]')).toHaveCount(1)
    await expect(page.locator('#concept .katex').first()).toBeVisible()
    await expect(page.getByRole('textbox', { name: 'Editable Python experiment' })).toBeVisible()
    expect(
      await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth),
    ).toBeTruthy()
    await page.screenshot({ path: info.outputPath(`${chapter}-mobile.png`), fullPage: true })
  }
  await page.getByRole('button', { name: 'Course menu +' }).click()
  await expect(page.locator('.sidebar-bottom a[download]')).toBeInViewport()
  await expect(page.locator('a[download][href$="student.zip"]')).toHaveCount(1)
  const outline = page.getByRole('navigation', { name: 'Course outline' })
  await expect(
    outline.getByRole('link', { name: 'Beyond a linear model', exact: true }),
  ).toHaveAttribute('aria-current', 'page')
  await page.screenshot({ path: info.outputPath('course-menu-mobile.png') })
  await outline.getByRole('button', { name: /Toggle Tutorial 04/ }).click()
  await expect(outline.getByRole('link', { name: 'Overview', exact: true })).toBeHidden()
  await expect(page.locator('.sidebar-bottom a[download]')).toBeInViewport()
  await outline.getByRole('button', { name: /Toggle Tutorial 04/ }).click()
  await outline.getByRole('link', { name: 'Overview', exact: true }).click()
  await expect(page).toHaveURL(/\/tutorials\/tutorial04\/overview$/)
  await expect(page.getByRole('button', { name: 'Course menu +' })).toHaveAttribute(
    'aria-expanded',
    'false',
  )
})
