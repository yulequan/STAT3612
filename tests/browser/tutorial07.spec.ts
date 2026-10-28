import { test, expect, type Page } from '@playwright/test'
import { readFileSync } from 'node:fs'

const curriculum = JSON.parse(readFileSync('src/tutorials/tutorial07/curriculum.json', 'utf8')) as {
  chapters: { id: string; title: string }[]
}

async function chapter(page: Page, id: string) {
  if (await page.getByRole('button', { name: 'Open course menu', exact: true }).isVisible())
    await page.getByRole('button', { name: 'Open course menu', exact: true }).click()
  const title = curriculum.chapters.find((c) => c.id === id)!.title
  await page
    .getByRole('navigation', { name: 'Course outline' })
    .getByRole('link', { name: title, exact: true })
    .click()
}
const runPython = (page: Page) => page.getByRole('button', { name: 'Run Python →', exact: true })

test('overview introduces the comparison and packages the notebook', async ({ page }) => {
  await page.goto('/tutorials/tutorial07/overview')
  await expect(
    page.getByRole('heading', { name: 'Learning objectives', exact: true }),
  ).toBeVisible()
  await expect(page.locator('.tutorial-overview')).toContainText('two measurements')
  await expect(page.locator('.tutorial-overview')).toContainText('support vector machines')
  await expect(page.getByRole('link', { name: /^Begin:/ })).toContainText(
    'Two Moons and Iris Petals',
  )
  const materials = page.getByRole('region', { name: 'Tutorial materials' })
  await expect(materials.getByRole('link', { name: 'Notebook + data' })).toBeVisible()
  const downloaded = page.waitForEvent('download')
  await materials.getByRole('link', { name: 'Notebook + data' }).click()
  const download = await downloaded
  expect(download.suggestedFilename()).toBe('student.zip')
  expect(
    readFileSync((await download.path())!)
      .subarray(0, 2)
      .toString(),
  ).toBe('PK')
  expect(page.workers()).toHaveLength(0)
})

test('all model families connect boundaries, validation evidence and Python', async ({
  page,
}, info) => {
  test.setTimeout(300_000)
  const errors: string[] = [],
    external: string[] = []
  page.on('pageerror', (e) => errors.push(e.message))
  page.on('request', (r) => {
    if (/^https?:/.test(r.url()) && new URL(r.url()).hostname !== '127.0.0.1')
      external.push(r.url())
  })
  await page.goto('/tutorials/tutorial07/data')
  await expect(runPython(page)).toBeEnabled({ timeout: 60_000 })
  await expect(
    page.getByRole('img', { name: 'Two moons · train + validation', exact: true }),
  ).toBeVisible()
  const cards = page.locator('.split-cards')
  await expect(cards).toContainText('Training')
  await expect(cards).toContainText('360')
  await expect(cards).toContainText('Validation')
  await expect(cards).toContainText('120')
  await expect(cards).toContainText('Test (hidden)')
  await runPython(page).click()
  await expect(page.getByLabel('Python output')).toContainText('Always-0 validation accuracy: 0.5')
  await expect(page.getByRole('alert')).toHaveCount(0)

  await chapter(page, 'tree')
  const fitTree = page.getByRole('button', { name: 'Fit decision tree', exact: true })
  await fitTree.click()
  await expect(
    page.getByRole('img', { name: 'Decision tree · decision boundary', exact: true }),
  ).toBeVisible({ timeout: 60_000 })
  await expect(page.getByRole('heading', { name: 'First rules in the fitted tree' })).toBeVisible()
  await expect(page.locator('.metric-row')).toContainText('Validation accuracy')
  await page.getByLabel('Maximum depth').selectOption('1')
  await fitTree.click()
  await expect(page.getByRole('img', { name: 'Decision tree · decision boundary' })).toBeVisible()
  await page.screenshot({ path: info.outputPath('tutorial07-tree.png'), fullPage: true })

  await chapter(page, 'forest')
  await page.getByRole('button', { name: 'Fit ensemble', exact: true }).click()
  await expect(
    page.getByRole('img', { name: 'Random forest · decision boundary', exact: true }),
  ).toBeVisible({ timeout: 90_000 })
  await expect(
    page.getByRole('img', { name: 'accuracy versus number of trees', exact: true }),
  ).toBeVisible()
  await expect(page.getByText('Out-of-bag score', { exact: true })).toBeVisible()
  await page.screenshot({ path: info.outputPath('tutorial07-forest.png'), fullPage: true })

  await chapter(page, 'boosting')
  await page.getByRole('button', { name: 'Fit boosting model', exact: true }).click()
  await expect(
    page.getByRole('img', { name: 'Gradient boosting · decision boundary', exact: true }),
  ).toBeVisible({ timeout: 90_000 })
  await expect(page.getByRole('heading', { name: 'Staged validation curve' })).toBeVisible()
  await expect(page.getByText('Best staged validation tree', { exact: true })).toBeVisible()
  await page.screenshot({ path: info.outputPath('tutorial07-boosting.png'), fullPage: true })

  await chapter(page, 'margins')
  await page.getByRole('button', { name: 'Fit linear SVM', exact: true }).click()
  await expect(
    page.getByRole('img', { name: 'Linear SVM · decision boundary', exact: true }),
  ).toBeVisible({ timeout: 60_000 })
  await expect(page.getByText('Support vectors', { exact: true })).toBeVisible()
  await expect(page.getByText('margin f=+1', { exact: true })).toBeVisible()
  await page.screenshot({ path: info.outputPath('tutorial07-margins.png'), fullPage: true })

  await chapter(page, 'kernels')
  await page.getByLabel('Dataset').selectOption('xor')
  await page.getByLabel('Kernel').selectOption('linear')
  const fitKernel = page.getByRole('button', { name: 'Fit kernel SVM', exact: true })
  await fitKernel.click()
  await expect(
    page.getByRole('img', { name: 'SVM · linear · decision boundary', exact: true }),
  ).toBeVisible({ timeout: 60_000 })
  await page.getByLabel('Kernel').selectOption('rbf')
  await fitKernel.click()
  await expect(
    page.getByRole('img', { name: 'SVM · rbf · decision boundary', exact: true }),
  ).toBeVisible({ timeout: 60_000 })
  await expect(page.locator('.metric-row').last()).toContainText('XOR quadrants')
  await page.screenshot({ path: info.outputPath('tutorial07-kernels.png'), fullPage: true })

  await chapter(page, 'compare')
  const compare = page.getByRole('button', { name: 'Run validation comparison', exact: true })
  await compare.click()
  const table = page.getByRole('table', { name: 'Validation comparison', exact: true })
  await expect(table.locator('tbody tr')).toHaveCount(7, { timeout: 120_000 })
  await expect(table).toContainText('Random forest')
  await expect(table).toContainText('RBF SVM')
  await page.getByRole('button', { name: 'Inspect validation errors', exact: true }).click()
  await expect(
    page.getByRole('table', { name: 'Selected candidate validation confusion matrix' }),
  ).toBeVisible({ timeout: 60_000 })
  await expect(
    page.getByRole('img', { name: /validation diagnostic$/, exact: false }),
  ).toBeVisible()
  await expect(
    page.getByRole('heading', { name: 'Final test result · decision frozen' }),
  ).toHaveCount(0)
  const finalButton = page.getByRole('button', {
    name: 'Freeze decision and evaluate test set',
    exact: true,
  })
  await expect(finalButton).toBeDisabled()
  await page
    .getByLabel('Model choice rationale')
    .fill(
      'RBF SVM was selected on validation accuracy; its confusion matrix shows the tradeoff. The synthetic two-moons data limit claims about real tabular data.',
    )
  await expect(finalButton).toBeEnabled()
  await finalButton.click()
  await expect(
    page.getByRole('heading', { name: 'Final test result · decision frozen' }),
  ).toBeVisible({ timeout: 60_000 })
  await expect(page.getByRole('table', { name: 'Final test confusion matrix' })).toBeVisible()
  await expect(page.getByText('Test accuracy', { exact: true })).toBeVisible()
  await page.screenshot({ path: info.outputPath('tutorial07-final.png'), fullPage: true })
  const exported = page.waitForEvent('download')
  await page.getByRole('button', { name: 'Export experiment record ↓', exact: true }).click()
  const record = JSON.parse(readFileSync((await (await exported).path())!, 'utf8'))
  expect(record.comparison).toHaveLength(7)
  expect(record.final.test.confusion.flat().reduce((a: number, b: number) => a + b, 0)).toBe(120)
  expect(errors).toEqual([])
  expect(external).toEqual([])
})

test('plots, tables and the editable snippet remain usable on a narrow screen', async ({
  page,
}, info) => {
  test.setTimeout(180_000)
  await page.setViewportSize({ width: 390, height: 844 })
  await page.goto('/tutorials/tutorial07/tree')
  await expect(runPython(page)).toBeEnabled({ timeout: 60_000 })
  await page.getByRole('button', { name: 'Fit decision tree', exact: true }).click()
  await expect(
    page.getByRole('img', { name: 'Decision tree · decision boundary', exact: true }),
  ).toBeVisible({ timeout: 60_000 })
  for (const id of ['data', 'tree', 'forest', 'boosting', 'margins', 'kernels', 'compare']) {
    await chapter(page, id)
    expect(
      await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth),
      id,
    ).toBeTruthy()
  }
  await page.screenshot({ path: info.outputPath('tutorial07-mobile.png'), fullPage: true })
  await chapter(page, 'tree')
  const editor = page.getByRole('textbox', { name: 'Editable Python experiment' })
  await editor.fill('print("before error")\nraise ValueError("visible error")')
  await runPython(page).click()
  await expect(page.getByRole('alert')).toContainText('ValueError: visible error')
  await editor.fill('print("recovered", X_train.shape, "X_test" in globals())')
  await runPython(page).click()
  await expect(page.getByLabel('Python output')).toContainText('recovered (360, 2) False')
  await expect(page.getByRole('alert')).toHaveCount(0)
})

test('generated data and runtime work from a static subdirectory', async ({ page }) => {
  test.setTimeout(180_000)
  const base = `http://127.0.0.1:${process.env.TEST_STATIC_PORT || '4174'}/dist/`
  const errors: string[] = []
  page.on('pageerror', (error) => errors.push(error.message))
  await page.goto(`${base}tutorials/tutorial07/kernels`)
  await expect(runPython(page)).toBeEnabled({ timeout: 60_000 })
  await page.getByRole('button', { name: 'Fit kernel SVM', exact: true }).click()
  await expect(
    page.getByRole('img', { name: 'SVM · rbf · decision boundary', exact: true }),
  ).toBeVisible({ timeout: 60_000 })
  const download = page.waitForEvent('download')
  await page.getByRole('link', { name: 'Notebook + data', exact: true }).click()
  expect(
    readFileSync((await (await download).path())!)
      .subarray(0, 2)
      .toString(),
  ).toBe('PK')
  expect(errors).toEqual([])
})
