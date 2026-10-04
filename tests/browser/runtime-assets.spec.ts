import { test, expect } from '@playwright/test'
import { execFile } from 'node:child_process'
import { promisify } from 'node:util'

test('asset preparation preserves Python assets on a running development server', async ({
  page,
  request,
}) => {
  const base = `http://127.0.0.1:${process.env.TEST_DEV_PORT || '4175'}`
  const manifestURL = `${base}/tutorials/tutorial04/tutorial.json`
  expect((await (await request.get(manifestURL)).json()).id).toBe('tutorial04')
  await page.goto(`${base}/tutorials/tutorial04/data`)
  await expect(page.getByRole('button', { name: 'Run Python →', exact: true })).toBeEnabled({
    timeout: 60_000,
  })
  // This used to remove Vite's watched directory, making JSON requests return index.html.
  await promisify(execFile)('python3', ['scripts/prepare_web.py'])
  const response = await request.get(manifestURL)
  expect(response.headers()['content-type']).toContain('application/json')
  expect((await response.json()).id).toBe('tutorial04')
  await page.reload()
  await expect(page.getByRole('button', { name: 'Run Python →', exact: true })).toBeEnabled({
    timeout: 60_000,
  })
  await page.getByRole('button', { name: 'Run Python →', exact: true }).click()
  await expect(page.getByLabel('Python output')).toContainText('same value:')
  await expect(page.getByRole('alert')).toHaveCount(0)
  await expect(page.getByRole('status')).toHaveCount(0)
  await expect(page.getByText('Python ready', { exact: false })).toHaveCount(0)
  await expect(page.getByLabel('Learning sections')).toHaveCount(0)
})

test('HTML returned for the tutorial manifest reports the URL and retry recovers', async ({
  page,
  context,
}) => {
  await context.route('**/tutorials/tutorial04/tutorial.json', (route) =>
    route.fulfill({
      status: 200,
      contentType: 'text/html',
      body: '<!doctype html><html><body>App fallback</body></html>',
    }),
  )
  await page.goto('/tutorials/tutorial04/data')
  await expect(page.getByRole('alert')).toContainText('HTML instead of tutorial JSON')
  await expect(page.getByRole('alert')).toContainText('/tutorials/tutorial04/tutorial.json')
  await context.unroute('**/tutorials/tutorial04/tutorial.json')
  await page.getByRole('button', { name: 'Restart Python', exact: true }).click()
  await expect(page.getByRole('button', { name: 'Run Python →', exact: true })).toBeEnabled({
    timeout: 60_000,
  })
  await expect(page.getByRole('alert')).toHaveCount(0)
  await expect(page.getByRole('status')).toHaveCount(0)
  await expect(page.getByText('Python ready', { exact: false })).toHaveCount(0)
  await expect(page.getByLabel('Learning sections')).toHaveCount(0)
})
