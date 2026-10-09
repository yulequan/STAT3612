import { test, expect, type Page } from '@playwright/test'
import { readFileSync } from 'node:fs'
const curriculum = JSON.parse(readFileSync('src/tutorials/tutorial05/curriculum.json', 'utf8')) as {
  chapters: {
    id: string
    title: string
    conceptTitle: string
    activityTitle: string
    pythonTitle: string
    points: string[]
    focus: { title: string } | null
  }[]
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

test('overview motivates the complete case study without starting Python', async ({ page }) => {
  await page.goto('/tutorials/tutorial05/overview')
  await expect(
    page.getByRole('heading', { name: 'Learning objectives', exact: true }),
  ).toBeVisible()
  await expect(page.locator('.tutorial-overview')).toContainText('SMS Spam Collection')
  await expect(page.locator('.tutorial-overview')).toContainText('LDA')
  await expect(page.locator('.tutorial-overview')).toContainText('additive spline')
  expect(page.workers()).toHaveLength(0)
  await expect(page.getByRole('link', { name: '↓ Notebook + data', exact: true })).toBeVisible()
})

test('every chapter connects guided explanations, explicit Python and an executable experiment', async ({
  page,
}) => {
  test.setTimeout(240_000)
  const errors: string[] = [],
    external: string[] = []
  page.on('pageerror', (e) => errors.push(e.message))
  page.on('request', (r) => {
    if (/^https?:/.test(r.url()) && new URL(r.url()).hostname !== '127.0.0.1')
      external.push(r.url())
  })
  await page.goto('/tutorials/tutorial05/inbox')
  await expect(runPython(page)).toBeEnabled({ timeout: 60_000 })
  const outputs: Record<string, string> = {
    inbox: 'Keyword prediction:',
    data: 'Always-ham recall:',
    tokenize: 'NLTK tokens:',
    text: 'Vocabulary:',
    tfidf: 'IDF:',
    naive: 'NB representation comparison:',
    logistic: 'LR prediction:',
    neighbors: 'Spam vote:',
    regularization: 'weight norm=',
    validation: 'Selected C:',
    features: 'Numerical baseline AP:',
    lda: 'lda validation AP:',
    gam: 'gam validation AP:',
    decision: 'Classifier:',
  }
  for (const section of curriculum.chapters) {
    await chapter(page, section.id)
    await expect(page.locator('.chapter-heading h1')).toHaveText(section.title)
    await expect(page.locator('#concept h2')).toHaveText(section.conceptTitle)
    await expect(page.locator('#python h2')).toHaveText(section.pythonTitle)
    await expect(page.getByRole('textbox', { name: 'Editable Python experiment' })).toHaveCount(1)
    if (['tfidf', 'naive'].includes(section.id))
      await expect(page.locator('#concept .katex').first()).toBeVisible()
    if (section.points.length)
      await expect(page.locator('#concept .key-points li').first()).toBeVisible()
    await expect(page.locator('.katex-error')).toHaveCount(0)
    await expect(page.locator('#python .cm-line').first()).toBeVisible()
    await expect(page.locator('#python .python-code:visible')).toHaveCount(0)
    await expect(page.locator('#concept .python-code')).toHaveCount(section.focus ? 1 : 0)
    if (section.focus) {
      await expect(page.locator('#concept .code-toolbar')).toContainText(section.focus.title)
      await expect(page.locator('#concept .hljs-keyword').first()).toBeVisible()
    }
    await runPython(page).click()
    await expect(page.getByLabel('Python output')).toContainText(outputs[section.id]!, {
      timeout: 90_000,
    })
    await expect(page.getByRole('alert')).toHaveCount(0)
  }
  expect(errors).toEqual([])
  expect(external).toEqual([])
})

test('interactive representations, learned models, CV and frozen test decision form one workflow', async ({
  page,
}, info) => {
  test.setTimeout(240_000)
  await page.goto('/tutorials/tutorial05/inbox')
  await expect(runPython(page)).toBeEnabled({ timeout: 60_000 })
  await expect(page.getByRole('table', { name: 'One keyword is not enough' })).toBeVisible()
  await expect(page.getByRole('button', { name: 'Apply keyword rule' })).toHaveCount(0)
  await chapter(page, 'data')
  const dataFlow = page.getByRole('figure', { name: 'Raw messages → deduplication → data splits' })
  await expect(dataFlow).toContainText('5,574 SMS messages')
  await expect(dataFlow).toContainText('5,159 unique messages')
  await expect(dataFlow).toContainText('415 repeats removed')
  await expect(dataFlow).toContainText('Train · 3,095')
  await expect(dataFlow).toContainText('Validation · 1,032')
  await expect(dataFlow).toContainText('Test · 1,032')
  await expect(dataFlow).toContainText('Learn vocabulary, IDF and model')
  await expect(page.locator('.audit, .split-row')).toHaveCount(0)
  await expect(page.locator('#concept table')).toHaveCount(0)
  await page.screenshot({ path: info.outputPath('data-flow.png'), fullPage: true })
  await expect(page.getByLabel('First lines of the raw data file')).toContainText('Go until jurong')
  await page.getByLabel('Search messages').fill('prize')
  await page.getByRole('combobox', { name: 'Label', exact: true }).selectOption('1')
  await expect(page.locator('.data-table tbody mark').first()).toHaveText(/prize/i)
  await expect(page.locator('.data-table tbody .tag.ham')).toHaveCount(0)
  await chapter(page, 'tokenize')
  const tokenFlow = page.getByRole('figure', { name: 'Follow one message through preprocessing' })
  await expect(tokenFlow.locator('code')).toHaveCount(4)
  await expect(tokenFlow.locator('code').first()).toHaveText(
    'Congratulations! Claim your FREE prize now!',
  )
  await expect(tokenFlow.locator('code').last()).toHaveText(
    '["congratulations", "claim", "your", "free", "prize", "now"]',
  )
  await expect(page.locator('.key-points code').first()).toHaveText('TreebankWordTokenizer')
  await page.getByLabel('Message to tokenize').fill('FREE prize!!!')
  await page.getByRole('button', { name: 'Tokenize message', exact: true }).click()
  await expect(tokenFlow.locator('.flow-code').nth(2)).toHaveText(
    '["free", "prize", "!", "!", "!"]',
  )
  await expect(tokenFlow.locator('.flow-code').last()).toHaveText('["free", "prize"]')
  await expect(page.locator('.teaching-flow')).toHaveCount(1)
  await expect(tokenFlow.locator('.flow-code').first()).toHaveText('FREE prize!!!')
  await page.screenshot({ path: info.outputPath('token-flow.png'), fullPage: true })
  await chapter(page, 'features')
  await page.getByLabel('Message to measure').fill('free 123!!!')
  await page.getByRole('button', { name: 'Measure message features' }).click()
  await expect(page.locator('.spam-metrics')).toContainText('11')
  await chapter(page, 'text')
  await page.getByLabel('New message to transform').fill('free newword3612')
  await page.getByRole('button', { name: 'Build and transform toy vectors' }).click()
  await expect(page.getByText('Ignored unknown words:')).toContainText('newword3612')
  await page.getByRole('button', { name: 'prize', exact: true }).click()
  await expect(page.locator('.spam-table th.highlight').first()).toHaveText('prize')
  await chapter(page, 'tfidf')
  await page.getByRole('button', { name: 'your', exact: true }).click()
  await expect(page.getByRole('table', { name: 'TF–IDF calculation' })).toContainText('0.385')
  await page.getByRole('button', { name: 'prize', exact: true }).click()
  await expect(page.getByRole('table', { name: 'TF–IDF calculation' })).toContainText('1.693')
  await page.getByRole('button', { name: 'Build and transform toy vectors' }).click()
  await expect(page.getByRole('rowheader', { name: 'Training IDF', exact: true })).toBeVisible()
  await page.screenshot({ path: info.outputPath('text-vectors.png'), fullPage: true })
  await chapter(page, 'naive')
  await page.getByRole('button', { name: 'Fit Naive Bayes classifier', exact: true }).click()
  await expect(page.getByRole('table', { name: 'Naive Bayes word evidence' })).toContainText(
    'prize',
    { timeout: 60_000 },
  )
  await page.getByLabel('Message for Naive Bayes').fill('unknown3612')
  await page.getByRole('button', { name: 'Inspect Naive Bayes evidence' }).click()
  await expect(page.getByText('No known words remain.', { exact: false })).toBeVisible()
  await page.screenshot({ path: info.outputPath('naive-bayes.png'), fullPage: true })
  await chapter(page, 'logistic')
  await page.getByRole('button', { name: 'Fit logistic classifier', exact: true }).click()
  await expect(
    page.getByRole('heading', { name: 'Message-specific contributions wⱼxⱼ' }),
  ).toBeVisible({ timeout: 60_000 })
  await page.getByText('Recall the score-to-probability mapping', { exact: true }).click()
  await expect(
    page.getByRole('img', { name: 'Linear score mapped through the sigmoid' }),
  ).toBeVisible()
  await chapter(page, 'regularization')
  await page.getByRole('button', { name: 'Fit regularization path' }).click()
  await page.getByText('Exact results and coefficient norms', { exact: true }).click()
  await expect(page.getByRole('img', { name: 'Coefficient magnitude along the path' })).toBeVisible(
    { timeout: 90_000 },
  )
  await expect(
    page.getByRole('img', { name: 'Word weights shrink as the penalty grows' }),
  ).toBeVisible()
  await chapter(page, 'validation')
  await page.getByRole('combobox', { name: 'Held-out fold', exact: true }).selectOption('2')
  await expect(page.locator('.folds .heldout')).toContainText('Fold 3')
  await page.getByRole('button', { name: 'Run five-fold cross-validation' }).click()
  await expect(page.getByRole('img', { name: 'Training-only five-fold CV' })).toBeVisible({
    timeout: 90_000,
  })
  await expect(page.getByText('Vocabulary sizes across folds:')).toBeVisible()
  await chapter(page, 'lda')
  await page.getByRole('button', { name: 'Fit LDA classifier' }).click()
  await expect(
    page.getByRole('img', { name: 'LDA · two-feature marginal of the fitted distributions' }),
  ).toBeVisible({ timeout: 60_000 })
  await chapter(page, 'gam')
  await page.getByRole('button', { name: 'Fit additive spline classifier' }).click()
  await expect(page.getByRole('img', { name: 'Additive effect of Characters' })).toBeVisible({
    timeout: 60_000,
  })
  await expect(page.getByRole('img', { name: 'Additive effect of Digits' })).toBeVisible()
  await page.screenshot({ path: info.outputPath('additive-effects.png'), fullPage: true })
  await chapter(page, 'neighbors')
  await page
    .getByRole('combobox', { name: 'Model representation', exact: true })
    .selectOption('tfidf')
  await page.getByRole('button', { name: 'Fit KNN classifier' }).click()
  await expect(page.getByRole('heading', { name: 'The neighbours that voted' })).toBeVisible({
    timeout: 60_000,
  })
  await expect(page.locator('.mail-card')).toHaveCount(5)
  await chapter(page, 'decision')
  await expect(
    page.getByRole('img', { name: 'Validation score histograms with the threshold' }),
  ).toBeVisible()
  await page.getByRole('button', { name: 'Inspect validation errors and curves' }).click()
  await expect(page.getByRole('img', { name: 'Validation precision–recall curve' })).toBeVisible()
  const matrixBefore = await page
    .getByRole('table', { name: 'Validation confusion matrix' })
    .innerText()
  await page
    .getByRole('slider', { name: /Validation decision threshold/ })
    .evaluate((element: HTMLInputElement) => {
      element.value = '0.8'
      element.dispatchEvent(new Event('input', { bubbles: true }))
      element.dispatchEvent(new Event('change', { bubbles: true }))
    })
  await expect
    .poll(() => page.getByRole('table', { name: 'Validation confusion matrix' }).innerText())
    .not.toBe(matrixBefore)
  await expect(runPython(page)).toBeEnabled()
  const finalButton = page.getByRole('button', { name: 'Freeze decision and evaluate test set' })
  await expect(finalButton).toBeDisabled()
  await page
    .getByLabel('Model and threshold rationale')
    .fill(
      'Selected using validation; prioritize avoiding legitimate messages blocked. Historical English SMS does not establish modern email performance.',
    )
  await finalButton.click()
  await expect(
    page.getByRole('heading', { name: 'Final test result · decision frozen' }),
  ).toBeVisible()
  await expect(
    page.getByRole('combobox', { name: 'Selected candidate', exact: true }),
  ).toBeDisabled()
  await expect(finalButton).toBeDisabled()
  await page.screenshot({ path: info.outputPath('final-decision.png'), fullPage: true })
  const exported = page.waitForEvent('download')
  await page.getByRole('button', { name: 'Export experiment record' }).click()
  const record = JSON.parse(readFileSync((await (await exported).path())!, 'utf8'))
  expect(record.runs.map((r: { kind: string }) => r.kind)).toEqual(
    expect.arrayContaining(['nb', 'logistic', 'knn', 'lda', 'gam']),
  )
  expect(record.final.threshold).toBe(0.8)
  expect(record.final.test.confusion.flat().reduce((a: number, b: number) => a + b, 0)).toBe(1032)
  const downloaded = page.waitForEvent('download')
  await page.getByRole('link', { name: '↓ Notebook + data' }).click()
  expect(
    readFileSync((await (await downloaded).path())!)
      .subarray(0, 2)
      .toString(),
  ).toBe('PK')
  await expect(page.getByRole('alert')).toHaveCount(0)
})

test('mobile layout, edited snippets and cancellation preserve a usable lesson', async ({
  page,
}, info) => {
  await page.setViewportSize({ width: 390, height: 844 })
  await page.goto('/tutorials/tutorial05/text')
  await expect(runPython(page)).toBeEnabled({ timeout: 60_000 })
  for (const id of [
    'inbox',
    'text',
    'tfidf',
    'tokenize',
    'naive',
    'data',
    'validation',
    'gam',
    'decision',
  ]) {
    await chapter(page, id)
    expect(
      await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth),
      id,
    ).toBeTruthy()
    const diagram = page.locator('.teaching-flow')
    if (await diagram.count()) {
      expect(await diagram.evaluate((el) => el.scrollWidth <= el.clientWidth), id).toBeTruthy()
      await page.screenshot({ path: info.outputPath(`${id}-mobile.png`), fullPage: true })
    }
  }
  const editor = page.getByRole('textbox', { name: 'Editable Python experiment' })
  await editor.fill('print("before error")\nraise ValueError("visible error")')
  await runPython(page).click()
  await expect(page.getByRole('alert')).toContainText('ValueError: visible error')
  await editor.fill('print("recovered", len(X_train), "X_test" in globals())')
  await runPython(page).click()
  await expect(page.getByLabel('Python output')).toContainText('recovered 3095 False')
  await expect(page.getByRole('alert')).toHaveCount(0)
  await editor.fill('while True:\n    pass')
  await runPython(page).click()
  await page.getByRole('button', { name: 'Stop and reset Python', exact: true }).click()
  await expect(runPython(page)).toBeEnabled({ timeout: 60_000 })
  await editor.fill('print("after restart")')
  await runPython(page).click()
  await expect(page.getByLabel('Python output')).toContainText('after restart')
  await page.screenshot({ path: info.outputPath('mobile.png'), fullPage: true })
})

test('original SMS file and sklearn run under a static subdirectory; loading failure can recover', async ({
  page,
  context,
}) => {
  const base = `http://127.0.0.1:${process.env.TEST_STATIC_PORT || '4174'}/dist/`
  await context.route('**/tutorials/tutorial05/SMSSpamCollection.txt', (route) => route.abort())
  await context.route('**/tutorials/tutorial05/data/SMSSpamCollection.txt', (route) =>
    route.abort(),
  )
  await page.goto(`${base}tutorials/tutorial05/data`)
  await expect(page.getByRole('alert')).toBeVisible()
  await context.unroute('**/tutorials/tutorial05/data/SMSSpamCollection.txt')
  await page.getByRole('button', { name: 'Restart Python' }).click()
  await expect(runPython(page)).toBeEnabled({ timeout: 60_000 })
  await runPython(page).click()
  await expect(page.getByLabel('Python output')).toContainText('Always-ham recall:')
  await expect(page.getByRole('alert')).toHaveCount(0)
})

test('core comparison and test evaluation work without visiting extension chapters', async ({
  page,
}, info) => {
  test.setTimeout(180_000)
  await page.goto('/tutorials/tutorial05/decision')
  await expect(runPython(page)).toBeEnabled({ timeout: 60_000 })
  await page.getByRole('button', { name: 'Compare BoW and TF–IDF with NB', exact: true }).click()
  await expect(page.locator('.chapter-experiment .spam-table tbody tr')).toHaveCount(2, {
    timeout: 60_000,
  })
  await page
    .getByRole('button', { name: 'Compare NB, LR and KNN with TF–IDF', exact: true })
    .click()
  await expect(page.locator('.chapter-experiment .spam-table tbody tr')).toHaveCount(5, {
    timeout: 60_000,
  })
  const rows = await page.locator('.chapter-experiment .spam-table tbody').innerText()
  expect(rows).toContain('NB')
  expect(rows).toContain('LOGISTIC')
  expect(rows).toContain('KNN')
  await page
    .getByRole('combobox', { name: 'Comparison group', exact: true })
    .selectOption('numeric')
  await expect(page.locator('.chapter-experiment .spam-table tbody tr')).toHaveCount(0)
  await page.getByRole('combobox', { name: 'Comparison group', exact: true }).selectOption('text')
  await page
    .getByLabel('Model and threshold rationale')
    .fill(
      'Compared text representations with NB fixed and models with TF–IDF fixed on validation. Avoid false alarms; English SMS has limited scope.',
    )
  await page
    .getByRole('button', { name: 'Freeze decision and evaluate test set', exact: true })
    .click()
  await expect(
    page.getByRole('heading', { name: 'Final test result · decision frozen' }),
  ).toBeVisible()
  await page.screenshot({ path: info.outputPath('core-comparison.png'), fullPage: true })
})
