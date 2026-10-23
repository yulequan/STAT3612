import { test, expect } from '@playwright/test'
import { readFileSync } from 'node:fs'

const base = `http://127.0.0.1:${process.env.TEST_STATIC_PORT || '4174'}/dist/`
const tutorial = `${base}tutorials/tutorial06/`

test('Tutorial 06 is discoverable with one ZIP download and no Python runtime', async ({
  page,
}) => {
  await page.goto(base)
  await page
    .getByRole('main')
    .getByRole('link', { name: /Tutorial 06/ })
    .click()
  await expect(page).toHaveURL(`${tutorial}overview`)
  await expect(
    page.getByRole('heading', { name: 'Machine Learning for Time Series Data', exact: true }),
  ).toBeVisible()
  const materials = page.getByRole('region', { name: 'Tutorial materials' })
  await expect(materials.locator('a[download]')).toHaveCount(1)
  await expect(materials.getByRole('link', { name: 'Notebook + setup (ZIP)' })).toHaveAttribute(
    'href',
    '/dist/tutorials/tutorial06/student.zip',
  )
  await expect(page.locator('a[href$=".ipynb"]')).toHaveCount(0)
  const downloaded = page.waitForEvent('download')
  await materials.getByRole('link', { name: 'Notebook + setup (ZIP)' }).click()
  const download = await downloaded
  expect(download.suggestedFilename()).toBe('student.zip')
  expect(
    readFileSync((await download.path())!)
      .subarray(0, 2)
      .toString(),
  ).toBe('PK')
  expect(page.workers()).toHaveLength(0)
  await page.goto(`${base}tutorials`)
  await expect(page.getByRole('main').getByRole('link', { name: /Tutorial 06/ })).toBeVisible()
})

test('PDF, notebook and setup package work on a direct static subdirectory visit', async ({
  page,
  request,
  context,
}, info) => {
  const errors: string[] = []
  const external: string[] = []
  page.on('pageerror', (error) => errors.push(error.message))
  context.on('request', (req) => {
    if (/^https?:/.test(req.url()) && new URL(req.url()).hostname !== '127.0.0.1')
      external.push(req.url())
  })
  const pdfLoaded = page.waitForResponse(`${tutorial}time_series_slides.pdf`)
  await page.goto(`${tutorial}slides`)
  expect((await pdfLoaded).status()).toBe(200)
  await expect(page.locator('iframe')).toHaveAttribute(
    'src',
    `${new URL(tutorial).pathname}time_series_slides.pdf#view=FitH&pagemode=none`,
  )
  await expect(page.locator('iframe')).toHaveAttribute('title', 'Tutorial 06: Time-series slides')
  await expect(page.locator('iframe')).toBeVisible()
  const pdf = await request.get(`${tutorial}time_series_slides.pdf`)
  expect(pdf.headers()['content-type']).toContain('application/pdf')
  expect((await pdf.body()).subarray(0, 5).toString()).toBe('%PDF-')
  const standalone = page.getByRole('link', { name: 'Open PDF in a new tab' })
  await expect(standalone).toHaveAttribute(
    'href',
    `${new URL(tutorial).pathname}time_series_slides.pdf`,
  )
  await expect(standalone).toHaveAttribute('target', '_blank')
  await expect(page.getByRole('main').locator('a[download]')).toHaveCount(1)
  await expect(page.locator('a[href$=".ipynb"]')).toHaveCount(0)
  await expect(page.getByRole('main')).toContainText(
    'The ZIP includes requirements.txt and README.md',
  )
  const downloaded = page.waitForEvent('download')
  await page.getByRole('main').getByRole('link', { name: 'Notebook + setup (ZIP)' }).click()
  expect(
    readFileSync((await (await downloaded).path())!)
      .subarray(0, 2)
      .toString(),
  ).toBe('PK')
  await page.reload()
  await expect(page).toHaveURL(`${tutorial}slides`)
  await expect(page).toHaveTitle('Slides & notebook · STAT3612')
  expect(page.workers()).toHaveLength(0)
  expect(errors).toEqual([])
  expect(external).toEqual([])
  await page.screenshot({ path: info.outputPath('tutorial06-slides.png'), fullPage: true })
})

test('Tutorial 06 fits phones and is searchable through the mobile menu', async ({
  page,
}, info) => {
  await page.goto(`${tutorial}slides`)
  for (const width of [320, 390, 768, 1440]) {
    await page.setViewportSize({ width, height: 900 })
    expect(
      await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth),
      `${width}px`,
    ).toBeTruthy()
  }
  await page.setViewportSize({ width: 390, height: 844 })
  await page.screenshot({ path: info.outputPath('tutorial06-mobile.png'), fullPage: true })
  await page.goto(base)
  await page.getByRole('button', { name: 'Open course menu' }).click()
  await page.getByLabel('Find course content').fill('time series')
  await page
    .getByRole('navigation')
    .getByRole('link', { name: /Tutorial 06/ })
    .click()
  await expect(page).toHaveURL(`${tutorial}overview`)
  await expect(page.getByRole('button', { name: 'Open course menu' })).toHaveAttribute(
    'aria-expanded',
    'false',
  )
  await page.getByRole('button', { name: 'Open course menu' }).click()
  await expect(
    page.locator('.sidebar-bottom').getByRole('link', { name: 'Notebook + setup (ZIP)' }),
  ).toBeVisible()
  await expect(page.locator('.sidebar-bottom a[download]')).toHaveCount(1)
  await expect(page.locator('a[href$=".ipynb"]')).toHaveCount(0)
})
