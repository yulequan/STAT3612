// These interactions are also used to capture the pre-migration reference values.
export async function exerciseDemo(page, kind) {
  const snapshots = {}
  // An update schedules its first animation frame before disabling Next. Wait for
  // that frame to run before checking completion, including with reduced motion.
  const settle = async () => {
    await page.evaluate(
      () =>
        new Promise((resolve) => {
          requestAnimationFrame(() => requestAnimationFrame(resolve))
        }),
    )
    await page.waitForFunction(() => !document.querySelector('#nextButton').disabled)
  }
  const capture = async (name) => {
    await page.locator('#nextButton').waitFor({ state: 'visible' })
    await settle()
    snapshots[name] = await page.evaluate(() => {
      const selectors =
        '.metrics strong, .iteration-badge strong, .narration [id], .bridge-note [id], output, #modelEquation, #lossValue'
      return Object.fromEntries(
        [...document.querySelectorAll(selectors)]
          .filter((el) => el.id)
          .map((el) => [el.id, el.textContent]),
      )
    })
  }
  const click = async (id) => {
    await page.locator(`#${id}`).click()
    await settle()
  }
  const slider = async (id, value) => {
    await page.locator(`#${id}`).fill(String(value))
    await page.locator(`#${id}`).dispatchEvent('input')
  }
  await capture('initial')
  if (kind === 'gradient') {
    for (const mode of ['1d', '2d']) {
      await click(`mode${mode}`)
      for (const preset of ['origin', 'low', 'high', 'reverse', 'near', 'random']) {
        await page.locator('#initialCase').selectOption(preset)
        await capture(`${mode}/${preset}/initial`)
        for (let step = 0; step < 5; step++) await click('nextButton')
        await capture(`${mode}/${preset}/updated`)
        await click('backButton')
        await capture(`${mode}/${preset}/back`)
      }
      await click('randomButton')
      await capture(`${mode}/new-random`)
      await page.locator('#initialCase').selectOption('origin')
      for (let i = 0; i < 4; i++) {
        await click('samplePlus')
        await capture(`${mode}/samples/${i}`)
      }
      for (let i = 0; i < 4; i++) await click('sampleMinus')
      await slider('learningRate', mode === '1d' ? 0.8 : 0.275)
      await capture(`${mode}/high-rate`)
      await slider('speed', 5)
      await capture(`${mode}/speed`)
      await page.locator('.step-chip[data-step="5"]').click()
      await capture(`${mode}/jump-update`)
      await click('resetButton')
      await capture(`${mode}/reset`)
    }
  } else {
    for (const count of [20, 100, 200]) {
      await slider('sampleCount', count)
      for (const batch of [1, 4, count]) {
        await slider('batchSize', batch)
        await capture(`${count}/${batch}/initial`)
        for (let step = 0; step < 5; step++) {
          await click('nextButton')
          await capture(`${count}/${batch}/step${step + 1}`)
        }
        await click('backButton')
        await capture(`${count}/${batch}/back`)
        await click('resetButton')
      }
    }
    await slider('sampleCount', 20)
    await capture('batch-clamped')
    await slider('learningRate', 0.8)
    await slider('speed', 20)
    await capture('rate-and-speed')
    await click('nextButton')
    await click('nextButton')
    await capture('high-rate-update')
    await click('resetButton')
    await capture('reset')
  }
  return snapshots
}
