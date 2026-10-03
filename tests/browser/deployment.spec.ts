import { test, expect } from '@playwright/test'
import { readFileSync } from 'node:fs'

// Exercise the production output on an ordinary static server, as Pages serves it.
const base = `http://127.0.0.1:${process.env.TEST_STATIC_PORT || '4174'}/dist/`

test('course outline, original demo URLs and 3D controls work without a CDN', async ({
  page,
  context,
}, info) => {
  const errors: string[] = []
  const external: string[] = []
  page.on('pageerror', (error) => errors.push(error.message))
  context.on('request', (request) => {
    if (/^https?:/.test(request.url()) && new URL(request.url()).hostname !== '127.0.0.1')
      external.push(request.url())
  })
  await context.route(/^https?:\/\/(?!127\.0\.0\.1)/, (route) => route.abort())
  await page.goto(base)
  await expect(page.getByRole('heading', { name: 'Tutorials', exact: true })).toBeVisible()
  await expect(page.getByRole('heading', { name: 'Demo', exact: true })).toBeVisible()
  await page.getByRole('link', { name: 'Demo', exact: true }).click()
  await expect(page).toHaveURL(`${base}#/demo`)
  expect(page.workers()).toHaveLength(0)
  await page.screenshot({ path: info.outputPath('course-outline.png'), fullPage: true })

  await page.getByRole('link', { name: /Gradient Descent Step by Step/ }).click()
  await expect(page).toHaveURL(`${base}gradient-descent-step-by-step.html`)
  await expect(page.getByRole('heading', { name: 'Gradient Descent Step by Step' })).toBeVisible()
  await page.getByRole('button', { name: 'Next step →', exact: true }).click()
  await expect(page.locator('#stepLabel')).toContainText('Step 2 of 6')
  await page.getByRole('button', { name: '2D · intercept + slope', exact: true }).click()
  await expect(page.locator('#loss3d canvas')).toBeVisible()
  await page.getByRole('link', { name: '← Course Demo', exact: true }).click()
  await expect(page).toHaveURL(`${base}#/demo`)

  await page.getByRole('link', { name: /GD vs SGD: Logistic Regression/ }).click()
  await expect(page).toHaveURL(`${base}gd-vs-sgd-logistic-regression.html`)
  await expect(page.locator('#loss3d canvas')).toBeVisible()
  await page.getByRole('button', { name: 'Next step →', exact: true }).click()
  await expect(page.locator('#stepLabel')).toContainText('Step 2 of 4')
  await page.getByRole('link', { name: '← Course Demo', exact: true }).click()

  await page.getByRole('link', { name: 'Demo overview →', exact: true }).click()
  await expect(page).toHaveURL(`${base}demo/`)
  await expect(page.getByRole('heading', { name: 'STAT3612 Interactive Demos' })).toBeVisible()
  await page.getByRole('link', { name: 'Open demo' }).first().click()
  await expect(page).toHaveURL(`${base}gradient-descent-step-by-step.html`)
  expect(errors).toEqual([])
  expect(external).toEqual([])
})

test('tutorial Python and notebook download work under the Pages subdirectory', async ({
  page,
}) => {
  await page.goto(`${base}#/tutorial04/update`)
  await expect(page.getByRole('status')).toContainText('Python ready', { timeout: 60_000 })
  await expect(page.getByRole('img', { name: 'Weights after one update' })).toBeVisible()
  const download = page.waitForEvent('download')
  await page.getByRole('link', { name: '↓ Notebook + data', exact: true }).click()
  expect(
    readFileSync((await (await download).path())!)
      .subarray(0, 2)
      .toString(),
  ).toBe('PK')
  await page.getByRole('link', { name: 'Demo', exact: true }).click()
  await expect(page).toHaveURL(`${base}#/demo`)
  await expect(page.getByRole('heading', { name: 'Demo', exact: true })).toBeVisible()
})

test('Demo navigation stays accessible on phones', async ({ page }, info) => {
  await page.setViewportSize({ width: 390, height: 844 })
  await page.goto(`${base}#/tutorial04/overview`)
  await page.getByRole('link', { name: 'Demo', exact: true }).click()
  await expect(page.getByRole('heading', { name: 'Demo', exact: true })).toBeVisible()
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBeTruthy()
  await page.screenshot({ path: info.outputPath('demo-mobile.png'), fullPage: true })
  await page.reload()
  await expect(page).toHaveTitle('Demo · STAT3612')
  await expect(page.getByRole('heading', { name: 'Demo', exact: true })).toBeInViewport()
  await page.getByRole('link', { name: 'All tutorials', exact: true }).click()
  await expect(page.getByRole('heading', { name: 'Tutorials', exact: true })).toBeInViewport()
})
