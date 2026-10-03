import { test, expect } from '@playwright/test'
import { readFileSync } from 'node:fs'

const base = `http://127.0.0.1:${process.env.TEST_STATIC_PORT || '4174'}/dist/`

test('home and sidebar expose all materials and keep the full outline open on navigation', async ({
  page,
}, info) => {
  await page.goto(base)
  await expect(
    page.getByRole('heading', { name: 'Statistical Machine Learning', exact: true }),
  ).toBeVisible()
  await expect(page.locator('iframe')).toHaveCount(0)
  expect(page.workers()).toHaveLength(0)
  await page.screenshot({ path: info.outputPath('course-home.png'), fullPage: true })
  const outline = page.getByRole('navigation', { name: 'Course outline' })
  const hrefs = () =>
    outline.locator('a').evaluateAll((links) => links.map((link) => link.getAttribute('href')))
  const expandedLinks = await hrefs()
  for (const href of [
    '#/tutorials/tutorial04/overview',
    '#/tutorials/tutorial04/update',
    '#/demos/gradient-descent',
    '#/demos/gd-vs-sgd',
  ]) {
    await expect(page.getByRole('main').locator(`a[href="${href}"]`).first()).toBeVisible()
    await expect(outline.locator(`a[href="${href}"]`).first()).toBeVisible()
  }
  for (const name of ['Lectures', 'Tutorials', 'Demos']) {
    await outline.getByRole('link', { name, exact: true }).click()
    await expect(page).toHaveURL(`${base}#/${name.toLowerCase()}`)
    await expect(page.getByRole('heading', { name, exact: true })).toBeVisible()
    await expect(outline.getByRole('link', { name, exact: true })).toHaveAttribute(
      'aria-current',
      'page',
    )
    if (name === 'Lectures')
      await expect(page.getByText('Lecture materials are coming soon.')).toBeVisible()
    expect(await hrefs()).toEqual(expandedLinks)
  }
  await page.reload()
  await expect(page).toHaveTitle('Demos · STAT3612')
  await page
    .getByRole('main')
    .getByRole('link', { name: /Gradient Descent Step by Step/ })
    .click()
  await expect(page).toHaveURL(`${base}#/demos/gradient-descent`)
  expect(await hrefs()).toEqual(expandedLinks)
  await outline.getByRole('link', { name: 'Overview', exact: true }).click()
  await expect(page).toHaveURL(`${base}#/tutorials/tutorial04/overview`)
  expect(await hrefs()).toEqual(expandedLinks)
  await outline.getByRole('link', { name: 'Gradient Descent Step by Step', exact: true }).click()
  await expect(
    outline.getByRole('link', { name: 'Gradient Descent Step by Step', exact: true }),
  ).toHaveAttribute('aria-current', 'page')
  await page.goBack()
  await expect(
    page.getByRole('heading', { name: 'Learning objectives', exact: true }),
  ).toBeVisible()
  await page.goForward()
  await expect(page.locator('iframe')).toHaveCount(1)
})

test('embedded demos retain 3D, playback and standalone links without external requests', async ({
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
  await page.goto(`${base}#/demos/gradient-descent`)
  const frame = page.frameLocator('iframe')
  await expect(frame.getByRole('heading', { name: 'Gradient Descent Step by Step' })).toBeVisible()
  await frame.locator('#mode2d').click()
  await expect(frame.locator('#loss3d canvas')).toBeVisible()
  await frame.locator('#nextButton').click()
  await expect(frame.locator('#stepLabel')).toContainText('Step 2 of 6')
  await page.screenshot({ path: info.outputPath('embedded-gradient.png'), fullPage: true })
  await page
    .getByRole('navigation', { name: 'Course outline' })
    .getByRole('link', { name: 'GD vs SGD: Logistic Regression', exact: true })
    .click()
  await expect(page).toHaveURL(`${base}#/demos/gd-vs-sgd`)
  await expect(page.locator('iframe')).toHaveCount(1)
  await expect(frame.locator('#loss3d canvas')).toBeVisible()
  await frame.locator('#speed').fill('20')
  await frame.locator('#speed').dispatchEvent('input')
  await frame.locator('#playButton').click()
  await expect(frame.locator('#iterationValue')).not.toHaveText('0')
  await frame.locator('#playButton').click()
  await expect(frame.locator('#playButton')).toHaveText('▶ Auto play')
  await expect(frame.locator('#nextButton')).toBeEnabled()
  // Drag and zoom the live 3D surface; neither interaction should navigate the host.
  const canvas = frame.locator('#loss3d canvas')
  await canvas.scrollIntoViewIfNeeded()
  const box = (await canvas.boundingBox())!
  await page.mouse.move(box.x + box.width / 2, box.y + box.height / 2)
  await page.mouse.down()
  await page.mouse.move(box.x + box.width / 2 + 60, box.y + box.height / 2 + 30)
  await page.mouse.up()
  await page.mouse.wheel(0, 100)
  await expect(page).toHaveURL(`${base}#/demos/gd-vs-sgd`)
  await page.screenshot({ path: info.outputPath('embedded-logistic.png'), fullPage: true })
  const popup = page.waitForEvent('popup')
  await page.getByRole('link', { name: 'Open standalone ↗' }).click()
  const standalone = await popup
  await expect(standalone).toHaveURL(`${base}gd-vs-sgd-logistic-regression.html`)
  await standalone.close()
  // The iframe's course link must navigate the top page, never nest the SPA inside itself.
  await frame.getByRole('link', { name: '← Course Demos' }).click()
  await expect(page).toHaveURL(`${base}#/demos`)
  await expect(page.locator('iframe')).toHaveCount(0)
  expect(errors).toEqual([])
  expect(external).toEqual([])
})

test('tutorial Python, downloads and old links work under a Pages subdirectory', async ({
  page,
}) => {
  await page.goto(`${base}#/tutorial04/update`)
  await expect(page).toHaveURL(`${base}#/tutorials/tutorial04/update`)
  await expect(page.getByRole('status')).toContainText('Python ready', { timeout: 60_000 })
  await expect(page.getByRole('img', { name: 'Weights after one update' })).toBeVisible()
  const download = page.waitForEvent('download')
  await page.getByRole('link', { name: '↓ Notebook + data', exact: true }).click()
  expect(
    readFileSync((await (await download).path())!)
      .subarray(0, 2)
      .toString(),
  ).toBe('PK')
  await page.goto(`${base}#/demo`)
  await expect(page).toHaveURL(`${base}#/demos`)
  await expect(page.getByRole('heading', { name: 'Demos', exact: true })).toBeVisible()
  for (const file of ['gradient-descent-step-by-step', 'gd-vs-sgd-logistic-regression']) {
    await page.goto(`${base}${file}.html`)
    await expect(page.locator('#nextButton')).toBeVisible()
  }
  await page.goto(`${base}demo/`)
  await expect(page.getByRole('heading', { name: 'STAT3612 Interactive Demos' })).toBeVisible()
})

test('phone navigation and embedded demos fit the viewport', async ({ page }, info) => {
  await page.setViewportSize({ width: 390, height: 844 })
  await page.goto(base)
  await page.getByRole('button', { name: 'Course menu +' }).click()
  await page
    .getByRole('navigation', { name: 'Course outline' })
    .getByRole('link', { name: 'Demos', exact: true })
    .click()
  await expect(page.getByRole('button', { name: 'Course menu +' })).toHaveAttribute(
    'aria-expanded',
    'false',
  )
  await page
    .getByRole('main')
    .getByRole('link', { name: /Gradient Descent Step by Step/ })
    .click()
  const frame = page.frameLocator('iframe')
  await frame.locator('#mode2d').click()
  await expect(frame.locator('#loss3d canvas')).toBeVisible()
  await expect
    .poll(() =>
      page.locator('iframe').evaluate((el: HTMLIFrameElement) => {
        const doc = el.contentDocument!
        return doc.documentElement.scrollHeight <= el.clientHeight + 2
      }),
    )
    .toBeTruthy()
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBeTruthy()
  expect(
    await frame.locator('body').evaluate(() => document.documentElement.scrollWidth <= innerWidth),
  ).toBeTruthy()
  await page.screenshot({ path: info.outputPath('embedded-mobile.png'), fullPage: true })
  await page.getByRole('button', { name: 'Course menu +' }).click()
  await page
    .getByRole('navigation', { name: 'Course outline' })
    .getByRole('link', { name: 'Course home', exact: true })
    .click()
  await expect(page.locator('iframe')).toHaveCount(0)
  await expect(page.getByRole('heading', { name: 'Statistical Machine Learning' })).toBeVisible()
})
