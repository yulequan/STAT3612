import { test, expect } from '@playwright/test'
import { readFileSync } from 'node:fs'

const base = `http://127.0.0.1:${process.env.TEST_STATIC_PORT || '4174'}/dist/`
const tutorial = `${base}tutorials/tutorial07/`
const deck = 'midterm_review_slides.pdf'

test('Tutorial 07 is discoverable and offers the deck as its only material', async ({ page }) => {
  await page.goto(base)
  await page
    .getByRole('main')
    .getByRole('link', { name: /Tutorial 07/ })
    .click()
  await expect(page).toHaveURL(`${tutorial}overview`)
  await expect(page.getByRole('heading', { name: 'Midterm Review', exact: true })).toBeVisible()
  await expect(page.locator('.tutorial-overview')).toContainText('Practice Paper 1')
  const materials = page.getByRole('region', { name: 'Tutorial materials' })
  await expect(materials.locator('a[download]')).toHaveCount(1)
  await expect(materials.getByRole('link', { name: 'Slides (PDF)' })).toHaveAttribute(
    'href',
    `/dist/tutorials/tutorial07/${deck}`,
  )
  const downloaded = page.waitForEvent('download')
  await materials.getByRole('link', { name: 'Slides (PDF)' }).click()
  const download = await downloaded
  expect(download.suggestedFilename()).toBe(deck)
  expect(
    readFileSync((await download.path())!)
      .subarray(0, 5)
      .toString(),
  ).toBe('%PDF-')
  // Slides only: no notebook, README or ZIP package.
  await expect(page.locator('a[href$="student.zip"]')).toHaveCount(0)
  expect(page.workers()).toHaveLength(0)
  await page.goto(`${base}tutorials`)
  await expect(page.getByRole('main').getByRole('link', { name: /Tutorial 07/ })).toBeVisible()
})

test('the slide-only deck embeds on a direct static subdirectory visit', async ({
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
  const pdfLoaded = page.waitForResponse(`${tutorial}${deck}`)
  await page.goto(`${tutorial}slides`)
  expect((await pdfLoaded).status()).toBe(200)
  await expect(page.locator('iframe')).toHaveAttribute(
    'src',
    `${new URL(tutorial).pathname}${deck}#view=FitH&pagemode=none`,
  )
  await expect(page.locator('iframe')).toHaveAttribute(
    'title',
    'Tutorial 07: Midterm review slides',
  )
  await expect(page.locator('iframe')).toBeVisible()
  const pdf = await request.get(`${tutorial}${deck}`)
  expect(pdf.headers()['content-type']).toContain('application/pdf')
  expect((await pdf.body()).subarray(0, 5).toString()).toBe('%PDF-')
  const standalone = page.getByRole('link', { name: 'Open PDF in a new tab' })
  await expect(standalone).toHaveAttribute('href', `${new URL(tutorial).pathname}${deck}`)
  await expect(standalone).toHaveAttribute('target', '_blank')
  await expect(page.locator('.review-materials')).toContainText('69 PDF pages')
  await expect(page.locator('.sidebar-bottom a[download]')).toHaveAttribute(
    'href',
    `/dist/tutorials/tutorial07/${deck}`,
  )
  const downloaded = page.waitForEvent('download')
  await page.getByRole('main').getByRole('link', { name: 'Download slides (PDF)' }).click()
  expect((await downloaded).suggestedFilename()).toBe(deck)
  await expect(page.locator('a[href$="student.zip"]')).toHaveCount(0)
  await page.reload()
  await expect(page).toHaveURL(`${tutorial}slides`)
  await expect(page).toHaveTitle('Review slides · STAT3612')
  expect(page.workers()).toHaveLength(0)
  expect(errors).toEqual([])
  expect(external).toEqual([])
  await page.screenshot({ path: info.outputPath('tutorial07-slides.png'), fullPage: true })
})

test('Tutorial 07 fits phones and is searchable through the mobile menu', async ({
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
  await page.screenshot({ path: info.outputPath('tutorial07-mobile.png'), fullPage: true })
  await page.goto(base)
  await page.getByRole('button', { name: 'Open course menu' }).click()
  await page.getByLabel('Find course content').fill('midterm review')
  await page
    .getByRole('navigation')
    .getByRole('link', { name: /Tutorial 07/ })
    .click()
  await expect(page).toHaveURL(`${tutorial}overview`)
  await expect(page.getByRole('button', { name: 'Open course menu' })).toHaveAttribute(
    'aria-expanded',
    'false',
  )
  await page.getByRole('button', { name: 'Open course menu' }).click()
  await expect(
    page.locator('.sidebar-bottom').getByRole('link', { name: 'Slides (PDF)' }),
  ).toBeVisible()
  await expect(page.locator('.sidebar-bottom a[download]')).toHaveCount(1)
})
