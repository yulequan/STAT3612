import { test, expect } from '@playwright/test'
import { readFileSync } from 'node:fs'

const base = `http://127.0.0.1:${process.env.TEST_STATIC_PORT || '4174'}/dist/`

test('two-level course outline collapses independently and keeps navigation state', async ({
  page,
}, info) => {
  await page.goto(base)
  const main = page.getByRole('main')
  const outline = page.getByRole('navigation', { name: 'Course outline' })
  await expect(
    main.getByRole('heading', { name: 'Statistical Machine Learning', exact: true }),
  ).toBeVisible()
  await expect(main.getByText('Prof. Lequan Yu', { exact: true })).toBeVisible()
  await expect(page.locator('.header-links a')).toHaveCount(0)
  await expect(page.locator('iframe')).toHaveCount(0)
  expect(page.workers()).toHaveLength(0)
  for (const name of ['Lectures', 'Tutorials', 'Demos']) {
    await expect(outline.getByRole('button', { name, exact: true })).toHaveAttribute(
      'aria-expanded',
      'true',
    )
  }
  for (const href of [
    '#/tutorials/tutorial04/overview',
    '#/demos/gradient-descent',
    '#/demos/gd-vs-sgd',
  ]) {
    await expect(main.locator(`a[href="${href}"]`)).toBeVisible()
    await expect(outline.locator(`a[href="${href}"]`)).toBeVisible()
  }
  await expect(main.locator('a[href="#/tutorials/tutorial04/update"]')).toHaveCount(0)
  await expect(outline.locator('a[href="#/tutorials/tutorial04/update"]')).toHaveCount(0)
  await page.screenshot({ path: info.outputPath('course-home.png'), fullPage: true })
  await outline.getByRole('button', { name: 'Demos', exact: true }).click()
  await expect(
    outline.getByRole('link', { name: 'Gradient Descent Step by Step', exact: true }),
  ).toBeHidden()
  await expect(outline.getByRole('link', { name: /Tutorial 04/ })).toBeVisible()
  await outline.getByRole('button', { name: 'Tutorials', exact: true }).focus()
  await page.keyboard.press('Space')
  await expect(outline.getByRole('button', { name: 'Tutorials', exact: true })).toHaveAttribute(
    'aria-expanded',
    'false',
  )
  await outline.getByRole('button', { name: 'Demos', exact: true }).click()
  await outline.getByRole('link', { name: 'Gradient Descent Step by Step', exact: true }).click()
  await expect(page).toHaveURL(`${base}#/demos/gradient-descent`)
  await expect(outline.getByRole('button', { name: 'Tutorials', exact: true })).toHaveAttribute(
    'aria-expanded',
    'false',
  )
  await expect(
    outline.getByRole('link', { name: 'Gradient Descent Step by Step', exact: true }),
  ).toHaveAttribute('aria-current', 'page')
  await outline.getByRole('button', { name: 'Tutorials', exact: true }).click()
  await outline.getByRole('link', { name: /Tutorial 04/ }).click()
  await expect(page).toHaveURL(`${base}#/tutorials/tutorial04/overview`)
  await expect(page.locator('.tutorial-overview > :first-child')).toContainText(
    'Tutor: Yinghao Zhu',
  )
  await expect(page.getByRole('link', { name: 'yhzhu99@connect.hku.hk' })).toHaveAttribute(
    'href',
    'mailto:yhzhu99@connect.hku.hk',
  )
  await expect(page.locator('a[download][href$="student.zip"]')).toHaveCount(1)
  await expect(page.locator('.sidebar-bottom a[download]')).toBeVisible()
  await expect(page.getByLabel('Tutorial chapter')).toHaveValue('overview')
  await page.screenshot({ path: info.outputPath('tutorial-overview.png'), fullPage: true })
  await page.getByLabel('Tutorial chapter').selectOption('beyond')
  await expect(page).toHaveURL(`${base}#/tutorials/tutorial04/beyond`)
  await expect(outline.getByRole('link', { name: /Tutorial 04/ })).toHaveAttribute(
    'aria-current',
    'page',
  )
  await expect(page.getByRole('status')).toContainText('Python ready', { timeout: 60_000 })
  await expect(page.locator('a[download][href$="student.zip"]')).toHaveCount(1)
  await expect(page.getByRole('main').locator('a[download][href$="student.zip"]')).toHaveCount(0)
  await page.goBack()
  await expect(page.getByLabel('Tutorial chapter')).toHaveValue('overview')
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
    .getByRole('link', { name: 'Gradient Descent Step by Step', exact: true })
    .click()
  await expect(page.getByRole('button', { name: 'Course menu +' })).toHaveAttribute(
    'aria-expanded',
    'false',
  )
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
