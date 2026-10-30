import { defineConfig } from '@playwright/test'
import { existsSync } from 'node:fs'

const previewPort = process.env.TEST_PREVIEW_PORT || '4173'
const staticPort = process.env.TEST_STATIC_PORT || '4174'
const devPort = process.env.TEST_DEV_PORT || '4175'

export default defineConfig({
  testDir: './tests/browser',
  timeout: 120_000,
  expect: { timeout: 15_000 },
  // Every Python test boots a browser Pyodide worker, so a full run is minutes of
  // real computation. Parallel files keep local runs short; CI shards the same
  // files across separate runners instead, where one worker per runner is fastest.
  workers: process.env.CI ? 1 : 4,
  use: {
    actionTimeout: 15_000,
    baseURL: `http://127.0.0.1:${previewPort}`,
    viewport: { width: 1440, height: 1000 },
    launchOptions: {
      executablePath:
        process.env.CHROME_BIN ||
        (existsSync('/usr/bin/google-chrome') ? '/usr/bin/google-chrome' : undefined),
      args: ['--no-sandbox'],
    },
    screenshot: 'only-on-failure',
    trace: 'retain-on-failure',
  },
  webServer: [
    {
      command: `npx vite --host 127.0.0.1 --port ${devPort} --strictPort`,
      url: `http://127.0.0.1:${devPort}`,
      // Reuse a server left over from the previous local run instead of failing.
      reuseExistingServer: !process.env.CI,
    },
    {
      command: `npm run preview -- --port ${previewPort} --strictPort`,
      url: `http://127.0.0.1:${previewPort}`,
      reuseExistingServer: !process.env.CI,
    },
    {
      // Serve the built site at /dist/ to verify subdirectory deployment with
      // an ordinary static server, independently of Vite's development behavior.
      command: `python3 -m http.server ${staticPort} --bind 127.0.0.1`,
      url: `http://127.0.0.1:${staticPort}/dist/`,
      reuseExistingServer: !process.env.CI,
      stderr: 'ignore',
    },
  ],
})
