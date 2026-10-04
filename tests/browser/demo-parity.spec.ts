import { test, expect } from '@playwright/test'
import { readFileSync } from 'node:fs'
import { exerciseDemo } from './demo-scenarios.mjs'

for (const [kind, route] of [
  ['gradient', 'gradient-descent'],
  ['logistic', 'gd-vs-sgd'],
]) {
  test(`${kind} embedded controls match the original standalone demo`, async ({ page }) => {
    await page.emulateMedia({ reducedMotion: 'reduce' })
    await page.addInitScript(() => {
      Math.random = () => 0.37
    })
    await page.goto(`/demos/${route}`)
    await expect(page.frameLocator('iframe').locator('#nextButton')).toBeVisible()
    const frame = page.frames().find((frame) => frame.parentFrame())!
    const actual = await exerciseDemo(frame, kind)
    const expected = JSON.parse(readFileSync(`tests/fixtures/${kind}-demo.json`, 'utf8'))
    expect(actual).toEqual(expected)
  })
}
