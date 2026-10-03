// Inventory + record EVERY teaching block in the current built tutorial04.
// Fast production: record actual interactions; hold their final frame during narration.
// Credentials stay in Python, never in this browser process.
import { chromium, expect } from '@playwright/test'
import { mkdir, writeFile, readFile } from 'node:fs/promises'
import { SceneCapture } from './capture.mjs'
import { Presentation, PRESENTATION_VERSION } from './presentation.mjs'
import { createHash } from 'node:crypto'
import { readFileSync } from 'node:fs'
import { existsSync } from 'node:fs'
import { spawn } from 'node:child_process'
import path from 'node:path'

const output = path.resolve(process.argv[2] || '.cache/video/tutorial04-complete')
await mkdir(output, { recursive: true })
const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms))
const scenes = [],
  coverage = [],
  errors = [],
  inventory = []
const chapterNames = [
  'overview',
  'data',
  'prepare',
  'model',
  'loss',
  'update',
  'train',
  'evaluate',
  'beyond',
]
let currentChapter = 'overview'
let browser,
  page,
  recording = false,
  frameDir,
  capture,
  replaying = false,
  presentation,
  sceneInteractive = false
const lockedNarration = process.argv.includes('--reuse-narration')
const sourceFiles = [
  'src/tutorials/tutorial04/lesson.ts',
  'src/tutorials/tutorial04/learning.ts',
  'src/tutorials/tutorial04/Tutorial04.vue',
  'src/tutorials/tutorial04/BeyondLinear.vue',
  'src/tutorials/tutorial04/StepExplorer.vue',
  'src/tutorials/tutorial04/experiment.py',
  'src/components/TutorialOverview.vue',
  'src/App.vue',
  'src/style.css',
  'src/components/HomePage.vue',
  'src/components/PythonCode.vue',
  'src/components/PixelImage.vue',
  'src/components/PythonEditor.vue',
  'src/components/LineChart.vue',
  'src/tutorials/tutorial04/ChapterTheory.vue',
  'src/tutorials/tutorial04/PythonPractice.vue',
]
const sourceHashes = Object.fromEntries(
  sourceFiles.map((file) => [file, createHash('sha256').update(readFileSync(file)).digest('hex')]),
)
const previousCoverage = existsSync(path.join(output, 'coverage.json'))
  ? JSON.parse(await readFile(path.join(output, 'coverage.json')))
  : null
if (
  previousCoverage &&
  Object.entries(previousCoverage.sourceHashes).some(([file, hash]) => sourceHashes[file] !== hash)
)
  throw new Error(
    'Sources changed since capture. Use a new output directory to avoid mixing old and new scenes.',
  )
const cached = existsSync(path.join(output, 'scenes.json'))
  ? JSON.parse(await readFile(path.join(output, 'scenes.json'))).scenes
  : []
const server = spawn('npm', ['run', 'preview', '--', '--port', '4188', '--strictPort'], {
  stdio: ['ignore', 'ignore', 'pipe'],
  detached: true,
})
server.stderr.on('data', (data) => process.stderr.write(data))
const verbalize = (text) =>
  text
    .replace(/\.([A-Z])/g, '. $1')
    .replace(/\b(-?\d+\.\d{5,})\b/g, (value) => String(Number(Number(value).toFixed(4))))
    .replace(/↗|↓|→|←|●/g, ' ')
    .replace(/×/g, ' times ')
    .replace(/η/g, ' eta ')
    .replace(/∂/g, ' partial ')
    .replace(/σ/g, ' sigmoid ')
    .replace(/∇/g, ' gradient ')
    .replace(/≥/g, ' greater than or equal to ')
    .replace(/−/g, ' minus ')
    .replace(/…/g, ' to ')
    .replace(/§/g, 'section ')
    .replace(/\s+/g, ' ')
    .trim()

async function shot() {
  await sleep(120)
}
const labelControl = (label) =>
  page.locator('label').filter({ hasText: label }).locator('input, select, textarea').first()
async function move(x, y) {
  return presentation.move(x, y, recording && sceneInteractive && !replaying)
}
async function focus(locator) {
  await presentation.hidePointer()
  await presentation.frame(locator)
}
async function view(locator) {
  await focus(locator)
}
async function click(locator) {
  await view(locator)
  const box = await locator.boundingBox()
  await move(box.x + box.width / 2, box.y + box.height / 2)
  await presentation.pulse()
  await page.mouse.click(presentation.pointer.x, presentation.pointer.y)
  if (recording) await shot()
}
async function select(label, value) {
  const control = labelControl(label)
  await view(control)
  const b = await control.boundingBox()
  await move(b.x + b.width / 2, b.y + b.height / 2)
  await presentation.pulse()
  await control.selectOption(value)
  if (recording) await shot()
  await presentation.hidePointer()
}
async function slider(label, value) {
  const control = labelControl(label)
  await view(control)
  const b = await control.boundingBox()
  const limits = await control.evaluate((el) => ({ min: +el.min, max: +el.max, value: +el.value }))
  const x = (v) => b.x + 8 + ((b.width - 16) * (v - limits.min)) / (limits.max - limits.min)
  await move(x(limits.value), b.y + b.height / 2)
  await page.mouse.down()
  await move(x(value), b.y + b.height / 2)
  await page.mouse.up()
  // Ensure the requested value even if native thumb geometry rounds differently.
  await control.fill(String(value))
  await control.dispatchEvent('input')
  await sleep(200)
  await presentation.hidePointer()
}
async function stable() {
  if (await page.getByRole('status').count()) {
    await expect(page.getByRole('status')).toContainText('Python ready', { timeout: 60000 })
    await sleep(250)
    await expect(page.getByRole('status')).not.toContainText('updating', { timeout: 60000 })
  }
  await expect(page.getByRole('alert')).toHaveCount(0)
  if (errors.length) throw new Error(errors.join('\n'))
}
async function scene(id, text, target, action = null, covers = []) {
  const authored = cached.find((scene) => scene.id === id)
  if (lockedNarration && !authored) throw new Error(`Cannot reuse narration: new scene ${id}`)
  if (lockedNarration) text = authored.text
  sceneInteractive = Boolean(action) && !id.includes('-code-')
  const previous = cached.find((scene) => scene.id === id && scene.text === verbalize(text))
  const cachedCapture = path.join(output, id + '-frames/capture.json')
  if (
    previous &&
    existsSync(cachedCapture) &&
    JSON.parse(await readFile(cachedCapture)).presentationVersion === PRESENTATION_VERSION
  ) {
    replaying = true
    try {
      if (action) await action()
      await stable()
    } finally {
      replaying = false
    }
    scenes.push({ ...previous, hasAction: Boolean(action) && !id.includes('-code-') })
    coverage.push(...covers)
    console.log(`Reused capture ${id} (${scenes.length})`)
    return
  }
  if (!text.trim()) throw new Error(`Empty narration: ${id}`)
  frameDir = path.join(output, id + '-frames')
  await mkdir(frameDir, { recursive: true })
  await page.evaluate(
    (title) => {
      document.querySelector('#video-header small').textContent = title
      document.querySelector('#video-focus').style.display = 'none'
      window.__videoMotion = []
    },
    `${String(chapterNames.indexOf(currentChapter)).padStart(2, '0')} · ${currentChapter.toUpperCase()} · ${id.replaceAll('-', ' ')}`,
  )
  if (target) await view(target)
  await presentation.hidePointer()
  capture = new SceneCapture(page)
  await capture.start(frameDir)
  recording = true
  await shot()
  if (action) await action()
  await stable()
  if (target && !action) await view(target)
  // The final hold must never contain a parked cursor or click ripple.
  await presentation.hidePointer()
  await page.mouse.move(1918, 1078)
  await shot()
  recording = false
  await expect(page.locator('#video-caption')).toHaveCount(0)
  const { actionSeconds, frames } = await capture.stop(PRESENTATION_VERSION)
  await writeFile(path.join(frameDir, 'narration.txt'), verbalize(text))
  if (!frames.length) throw new Error(`No compositor frames: ${id}`)
  const box = await page.locator('#video-focus').boundingBox()
  if (!box || box.y < 68 || box.y + box.height > 1046 || box.width <= 0 || box.height <= 0)
    throw new Error(`Invalid focus viewport: ${id}`)
  scenes.push({
    id,
    chapter: currentChapter,
    text: verbalize(text),
    covers,
    actionSeconds,
    hasAction: Boolean(action) && !id.includes('-code-'),
  })
  coverage.push(...covers)
  await writeFile(
    path.join(output, 'scenes.json'),
    JSON.stringify({ title: 'Tutorial 04 - Complete walkthrough', scenes }, null, 2),
  )
  console.log(`Captured ${id} (${scenes.length}, ${frames.length} compositor frames)`)
}
async function blocks(prefix, selector, intro = '') {
  const locators = page.locator(selector)
  for (let i = 0; i < (await locators.count()); i++) {
    const target = locators.nth(i)
    if (!(await target.isVisible())) continue
    const text = (await target.innerText()).trim()
    if (!text) continue
    await scene(`${prefix}-${i + 1}`, (i === 0 ? intro : '') + text, target, null, [
      `${selector}[${i}]`,
    ])
  }
}
async function chapter(name) {
  currentChapter = name
  await click(page.getByRole('navigation').locator(`a[href="#/tutorial04/${name}"]`))
  await expect(page.locator('#concept h2')).toBeVisible()
  await expect(page.getByRole('status')).toContainText('Python ready', { timeout: 60000 })
  await stable()
  const teaching = await page
    .locator(
      '#concept h2, #concept p, #concept dd, #experiment p, #experiment h2, #experiment h3, #experiment .spaced-list li, #practice .practice-challenge, #practice .notebook-bridge h3, #practice .notebook-bridge p',
    )
    .allTextContents()
  inventory.push(...teaching.map((text) => ({ chapter: name, text: verbalize(text) })))
  await blocks(name + '-heading', '.chapter-heading h1')
  await blocks(
    name + '-theory',
    '#concept h2, #concept .theory-paragraphs p, #concept .notation-list dd, #concept .concept-note p',
  )
  await scene(name + '-equation', maths[name], page.locator('#concept .equation-card'), null, [
    `${name}:equation-and-notation`,
  ])
}
const maths = {
  data: 'The design matrix X has n rows and seven hundred and eighty four columns. Each row is one image. X sub i j is pixel j of example i. The labels are categories: zero for three, and one for eight.',
  prepare:
    'Divide each raw input value by two hundred and fifty five. Then apply the chosen feature transformation, phi. Use exactly the same transformation when evaluating the model.',
  model:
    'The score z is the sum of weight j times input j, plus bias b. The sigmoid is one divided by one plus the exponential of negative z. A probability at least one half means a score at least zero.',
  loss: 'The mean cross entropy is the negative average of y times log p, plus one minus y times log one minus p. A true eight contributes negative log p. A true three contributes negative log one minus p.',
  update:
    'By the chain rule, the loss derivative with respect to the score is p minus y. Multiply by input pixel j for the weight derivative. The new weight is the old weight minus eta times that derivative.',
  train:
    'At iteration t, subtract eta times the average gradient over minibatch B sub t. The number of updates per epoch is the ceiling of the number of training examples divided by batch size.',
  evaluate:
    'Accuracy is the average of the indicators that predicted class equals true class. The indicator is one when the condition is true and zero otherwise. Threshold probabilities to obtain predicted labels.',
  beyond:
    'Replace the original input by a learned representation phi theta, followed by an output weight vector v and intercept c. Theta, v and c are usually learned together from a training objective.',
}
const codeLessons = {
  load_data: [
    'Open the NumPy archive with a context manager. Reshape images into twenty eight by twenty eight arrays, convert to double precision, and divide by two hundred and fifty five. Read labels and the original training cutoff.',
    'Create a seeded random generator. For each class, shuffle only the original training indices. Reserve one fifth for validation and put the remaining indices into training. Finally sort the indices and keep all examples beyond the cutoff for test. This is a reproducible balanced split, not test leakage.',
  ],
  features: [
    'Apply transform to the batch and reshape to one row per image. Normalised inputs stay in zero to one units; disabling normalisation multiplies them by two hundred and fifty five. Representation and numerical scale are separate choices.',
  ],
  transform: [
    'Convert the input to a floating point array. Raw returns a copy. For blur, apply Gaussian smoothing only along the image axes, not across examples. Reflect boundary handling avoids introducing an artificial zero border.',
    'Edges combines horizontal and vertical Sobel derivatives with the Euclidean magnitude, divided by a fixed factor of four. Brightness adds an offset and clips to zero through one. These transformations preserve shape but not all information.',
    'For a horizontal shift, create an array of zeros. Copy the overlapping columns to the new positions. Positive offsets move right and negative offsets move left. Nothing wraps around. A shift larger than the width leaves all zeros. Unknown operations raise an error.',
  ],
  sigmoid: [
    'Convert the score to a floating point array. Compute the exponential of negative absolute score. Use separate expressions for positive and negative scores. This stable formulation avoids overflow for large negative inputs.',
  ],
  loss: [
    'Compute all scores with matrix multiplication and the bias. Log add exp of zero and z calculates log one plus exponential z stably. Subtract y times z and average. This implements cross entropy without directly taking logarithms of probabilities near zero or one.',
  ],
  step: [
    'First calculate scores, then probabilities, then residuals. Matrix transpose times residuals, divided by batch size, gives the weight gradient. The average residual gives the bias gradient.',
    'Subtract learning rate times each gradient. Return new weights and new bias. The gradients both use the original parameters. This is the same function used by the interactive trace and the actual training loop.',
  ],
  train_epochs: [
    'Start with zero weights and bias, and a seeded random generator. Loop from epoch zero through the requested final epoch. Yield training and validation metrics together with copies of the current parameters. Epoch zero is the untrained baseline.',
    'After each checkpoint except the last, draw a random permutation of training indices. Slice that order into batches. Call step on each batch. Validation never enters the parameter update. Epochs measure passes through data, not an equal update budget across batch sizes.',
  ],
  metrics: [
    'Compute probabilities and threshold at one half. Build a two by two confusion matrix by counting each actual and predicted class combination. Return mean loss, accuracy, and the matrix. Accuracy and loss measure different aspects of predictions.',
  ],
  convolution_map: [
    'Convert image and kernel to NumPy arrays. Sliding window view creates every valid image patch. Einstein summation multiplies each patch by the shared kernel and sums the two local axes. This is stride one cross correlation: the kernel is not flipped.',
  ],
}
async function python(ch) {
  if (ch !== 'update') {
    const panels = page.locator('#python .python-code')
    for (let i = 0; i < (await panels.count()); i++) {
      const panel = panels.nth(i)
      const title = await panel.innerText()
      const name = Object.keys(codeLessons).find((name) => title.includes(`${name}()`))
      if (!name) throw new Error(`Missing code narration: ${title}`)
      const lines = panel.locator('.code-line')
      const narration = codeLessons[name]
      for (let k = 0; k < narration.length; k++) {
        const from = Math.floor((k * (await lines.count())) / narration.length)
        const to = Math.floor(((k + 1) * (await lines.count())) / narration.length)
        const range = lines.nth(from)
        await range.evaluate((element, count) => {
          element.dataset.videoLineCount = String(count)
        }, to - from)
        await scene(
          `${ch}-code-${name}-${k + 1}`,
          narration[k],
          range,
          async () => {
            await view(range)
            await focus(range)
            // Keep long functions readable: scroll each explained portion into view.
            const b = await range.boundingBox()
            await move(b.x + 35, b.y + 15)
          },
          [`${ch}:code:${name}:lines:${from + 1}-${to}`],
        )
      }
    }
  }
  await blocks(ch + '-python-intro', '#python > h2, #python > p')
  await blocks(ch + '-practice', '#practice > h2, #practice > .practice-challenge')
  const editor = page.getByRole('textbox', { name: 'Editable Python experiment' })
  await scene(ch + '-starter-code', 'Here is the editable example. ' + practice[ch], editor, null, [
    `${ch}:practice:code-explanation`,
  ])
  await scene(
    ch + '-run-python',
    'Now run the example. Python executes locally in the browser with fresh training and validation arrays. Inspect the printed result before deciding what to change.',
    editor,
    async () => {
      await click(page.getByRole('button', { name: 'Run Python →', exact: true }))
      await expect(page.getByLabel('Python output')).not.toBeEmpty({ timeout: 60000 })
      await view(page.getByLabel('Python output'))
      await focus(page.getByLabel('Python output'))
    },
    [`${ch}:practice:starter-and-output`],
  )
  const summaries = {
    data: 'The printed image is twenty eight by twenty eight and its flattened row has seven hundred and eighty four entries. The flattened and two dimensional pixel accesses agree.',
    prepare:
      'The printed ranges and mean absolute change quantify the blur. The operation preserves array shape and input units, while changing local detail.',
    model:
      'With an active pixel value of one and weight two, the score is two, and sigmoid gives a probability of about zero point eight eight. The exact numerical output is shown here.',
    loss: 'For a true eight, the losses at probabilities zero point zero one, zero point four, zero point five one and zero point nine nine are approximately four point six zero five, zero point nine one six, zero point six seven three and zero point zero one. The last two predictions are both correct but differ in confidence.',
    update:
      'The eight gives positive new bias and positive weights on active pixels. The printed probability is now above one half. These calculations come from the same step function as the trace.',
    train:
      'The smaller batch performs three hundred updates in five epochs, versus forty for the larger batch. Compare the displayed validation loss and accuracy with that unequal update budget in mind. This is not proof that smaller batches always win.',
    evaluate:
      'The nearest centroid validation accuracy is printed here. This baseline has no SGD, so compare its measured validation performance rather than assuming gradient based fitting is always necessary.',
    beyond:
      'The constructed interaction rule predicts zero, one, one, zero, matching all four XOR targets. It is still a linear score in the expanded feature representation.',
  }
  await scene(ch + '-output', summaries[ch], page.getByLabel('Python output'), null, [
    `${ch}:practice:results`,
  ])
  const variants = {
    data: 'image = images[0]\nx = image.reshape(-1)\nj = int(np.argmin(x))\nrow, col = divmod(j, 28)\nprint("blank pixel:", j, row, col, x[j], image[row, col])',
    prepare:
      'image = images[0]\nfor sigma in [0.5, 1.0, 2.0]:\n    blurred = transform(image, "blur", sigma)\n    print("sigma:", sigma, "range:", blurred.min(), blurred.max(), "change:", np.abs(blurred-image).mean())',
    model:
      'x = X_train[0]\nj = int(np.argmax(x))\nfor bias in [0.0, 2.0]:\n    w = np.zeros(x.size)\n    w[j] = -2.0\n    z = x @ w + bias\n    print("bias:", bias, "score:", z, "p(8):", float(sigmoid(z)))',
    loss: 'y = 0\nfor p in [0.01, 0.4, 0.51, 0.99]:\n    cross_entropy = -y*np.log(p)-(1-y)*np.log(1-p)\n    print(f"p={p:.2f}, class={int(p >= .5)}, loss={cross_entropy:.3f}")',
    update:
      'i = int(np.flatnonzero(y_train == 0)[0])\nX, y = X_train[i:i+1], y_train[i:i+1]\nw_new, b_new = step(np.zeros(X.shape[1]), 0.0, X, y, lr=0.1)\nj = int(np.argmin(X[0]))\nprint("true 3; bias:", b_new)\nprint("blank pixel:", X[0,j], "new weight:", w_new[j])\nprint("new p(8):", sigmoid(X @ w_new + b_new))',
    train:
      'for batch, epochs in [(16, 2), (128, 15)]:\n    model = train(X_train, y_train, X_val, y_val, lr=0.1, epochs=epochs, batch=batch)\n    print("batch:", batch, "epochs:", epochs, "updates:", epochs*int(np.ceil(len(y_train)/batch)))\n    print("validation:", model["history"][-1]["validation"])',
    evaluate:
      'centres = np.stack([X_train[y_train == c].mean(axis=0) for c in [0,1]])\nw = 2*(centres[1]-centres[0])\nb = np.dot(centres[0],centres[0])-np.dot(centres[1],centres[1])\ndistance = ((X_val[:,None,:]-centres[None,:,:])**2).sum(axis=2)\nprint("linear rule agrees:", np.all((X_val @ w + b >= 0) == (distance.argmin(axis=1)==1)))',
    beyond:
      'i = int(np.flatnonzero(y_train == 0)[0])\nimage = images[i]\nkernel = np.ones((3,3))/9\na = convolution_map(image,kernel)\nprint("map shape:", a.shape)\nprint("window value:", a[10,10], "direct average:", image[10:13,10:13].mean())',
  }
  const variantSpeech = {
    data: 'Now find a blank pixel with arg min. Recover its row and column and verify that both accesses still agree. Reshaping preserves values, including zeros.',
    prepare:
      'Compare three blur strengths in one run. The printed changes quantify increasing smoothing; the same image and units are used for all three.',
    model:
      'Give an active pixel a negative weight and compare biases zero and two. The bias can cancel this example’s contribution, but a different image need not have the same active intensity.',
    loss: 'Flip the true label to three and run again. Confidence now works in the opposite direction. A probability near one for eight is confidently wrong.',
    update:
      'Change to a true three and inspect a blank pixel. The bias now decreases, and the blank pixel weight remains zero. That is the sign prediction we made earlier.',
    train:
      'Compare at equal updates instead: batch sixteen for two epochs and batch one hundred and twenty eight for fifteen epochs each gives one hundred and twenty updates. These are different data pass budgets. Report both epochs and updates when interpreting the result.',
    evaluate:
      'Expand the centroid distance difference into a weight vector and bias. This code checks that its thresholded linear score agrees with the nearest centroid predictions. It demonstrates why this rule has a linear decision boundary.',
    beyond:
      'Verify the local average convolution independently in Python. A three by three filter of one ninth gives a twenty six by twenty six map. Compare one map entry to the direct mean of its input patch.',
  }
  await scene(
    ch + '-modify-python',
    variantSpeech[ch],
    editor,
    async () => {
      await click(editor)
      await editor.fill(variants[ch])
      await focus(editor)
    },
    [`${ch}:practice:modified-code`],
  )
  await scene(
    ch + '-run-modified',
    'Run the modified experiment and check its printed evidence. ' + variantSpeech[ch],
    editor,
    async () => {
      const before = await page.getByLabel('Python output').innerText()
      await click(page.getByRole('button', { name: 'Run Python →', exact: true }))
      await expect(page.getByLabel('Python output')).not.toHaveText(before)
      await view(page.getByLabel('Python output'))
      await focus(page.getByLabel('Python output'))
    },
    [`${ch}:practice:modified-results`],
  )
  await scene(
    ch + '-variables',
    'The editable experiment provides fresh copies of training and validation arrays, not test data. ' +
      'Available functions and variables are listed here. Changes to these arrays do not change the classroom model.',
    page.locator('.available-variables'),
    async () => {
      if (!(await page.locator('.available-variables').evaluate((el) => el.hasAttribute('open'))))
        await click(page.locator('.available-variables summary'))
      await focus(page.locator('.available-variables'))
    },
    [`${ch}:available-variables`],
  )
  await blocks(ch + '-notebook', '#practice .notebook-bridge h3, #practice .notebook-bridge p')
  await scene(
    ch + '-reset',
    'Reset example restores the chapter starter code. Download the lab to keep a persistent notebook with the complete dataset and implementation.',
    page.locator('.editor-toolbar'),
    async () => {
      await click(page.getByRole('button', { name: 'Reset example', exact: true }))
    },
    [`${ch}:reset-and-notebook-download`],
  )
}
const practice = {
  data: 'Reshape the image, find the brightest flattened index, use divmod by twenty eight to recover its row and column, then verify that the two array accesses give the same value. Repeat with a blank pixel.',
  prepare:
    'Change sigma and compare minimum, maximum and mean absolute change. Larger Gaussian blur suppresses high frequency detail. It may remove useful differences between threes and eights; appearance alone is not evidence of better classification.',
  model:
    'Start at zero weights, choose an inked pixel, and assign weight two. The score is input dot weight plus bias. A bias change affects every example; a weight change only matters when that feature is active. Try a negative weight too.',
  loss: 'Evaluate four probabilities for a true eight, then repeat for a true three. Probabilities zero point five one and zero point nine nine have the same predicted class but different losses. Reversing the label reverses which confident predictions are rewarded.',
  update:
    'Select the first training eight and call step with learning rate zero point one. Inspect the new bias, brightest pixel weight, and probability. A true three reverses the bias update direction; a blank pixel has a zero weight gradient.',
  train:
    'Train five epochs with batch sizes sixteen and one hundred and twenty eight. There are sixty versus eight updates per epoch, so three hundred versus forty updates overall. Equal epochs do not mean equal optimisation budgets.',
  evaluate:
    'Average each class to form two centroids, compute squared distances for validation examples, and select the closer centroid. No gradient descent is needed. Expanding the difference between squared distances cancels the squared input term, leaving a linear decision boundary.',
  beyond:
    'For XOR, construct an interaction feature by multiplying the two inputs. The score uses both inputs minus twice their interaction, then subtracts one half and multiplies by four. Threshold the sigmoid. This is linear in expanded features but nonlinear in the original inputs.',
}

try {
  let online = false
  for (let i = 0; i < 100; i++) {
    if (server.exitCode !== null) throw new Error('Preview server exited')
    try {
      if ((await fetch('http://127.0.0.1:4188')).ok) {
        online = true
        break
      }
    } catch {}
    await sleep(100)
  }
  if (!online) throw new Error('Preview server unavailable')
  browser = await chromium.launch({
    executablePath:
      process.env.CHROME_BIN ||
      (existsSync('/usr/bin/google-chrome') ? '/usr/bin/google-chrome' : undefined),
    args: ['--no-sandbox'],
  })
  page = await browser.newPage({ viewport: { width: 1920, height: 1080 } })
  page.setDefaultTimeout(60000)
  page.on('pageerror', (e) => errors.push(e.message))
  await page.route(/^https?:\/\/(?!127\.0\.0\.1:4188\/)/, (r) => r.abort())
  await page.goto('http://127.0.0.1:4188/')
  presentation = new Presentation(page)
  await presentation.install()
  await scene(
    'course-home',
    'Hello everyone. Today we are working through Tutorial Four: From pixels to a classifier. We will cover the overview and all eight chapters, from preparing handwritten digits through a complete stochastic gradient descent experiment, and then the bridge to neural networks. Open Tutorial Four to begin.',
    page.locator('.course-index'),
    async () => {
      await click(page.locator('a[href="#/tutorial04/overview"]'))
      await focus(page.locator('.chapter-heading'))
    },
    ['course-index'],
  )
  inventory.push(
    ...(
      await page
        .locator(
          '.tutorial-overview h2, .tutorial-overview p, .tutorial-overview h3, .overview-objectives li',
        )
        .allTextContents()
    ).map((text) => ({ chapter: 'overview', text: verbalize(text) })),
  )
  await blocks(
    'overview',
    '.chapter-heading h1, .tutorial-overview h2, .overview-intro p, .overview-route h3, .overview-route p, .overview-objectives li, .tutorial-overview section > p, .overview-preparation p, .overview-format',
  )
  await scene(
    'overview-start',
    'The route connects data and preparation, prediction and learning, experiments and evaluation, then alternative models. The sidebar lets you jump to any chapter. Begin with Meet the data.',
    page.locator('.tutorial-overview > a'),
    null,
    ['overview:chapter-links-and-start'],
  )

  await chapter('data')
  await blocks(
    'data-explore',
    '#experiment .lede, #experiment h2, #experiment p:not(.lede), #experiment .split-list dd',
  )
  await scene(
    'data-question-answer',
    'If images and labels are shuffled independently, their pairings become incorrect. The model is then trained on wrong targets rather than digit identity. Always apply the same permutation to both.',
    page.locator('#experiment .question'),
    null,
    ['data:question-answer'],
  )
  await scene(
    'data-gallery',
    'There are twelve selectable training examples. The label convention is zero for three and one for eight. Click a different example, then hover over the image to inspect its row, column, flattened index and intensity.',
    page.locator('.gallery'),
    async () => {
      await click(page.getByRole('button', { name: /Inspect digit 8/ }).first())
      const image = page.getByRole('img', { name: 'One training image' })
      await view(image)
      const b = await image.boundingBox()
      await move(b.x + b.width * 0.45, b.y + b.height * 0.4)
    },
    ['data:gallery-and-pixel-hover'],
  )
  await scene(
    'data-splits',
    'Twenty eight times twenty eight gives seven hundred and eighty four features. Index j equals twenty eight times row plus column. There are nine hundred and sixty training images, two hundred and forty validation images, and eight hundred untouched test images. All splits are balanced and fixed.',
    page.locator('.split-list'),
    null,
    ['data:shapes-counts-labels'],
  )
  await python('data')

  await chapter('prepare')
  await blocks(
    'prepare-explore',
    '#experiment .lede, #experiment h2, #experiment p:not(.lede), #experiment .spaced-list li',
  )
  for (const [kind, text] of Object.entries({
    raw: 'Original preserves all input values.',
    blur: 'Gaussian blur smooths local detail. The amount control changes sigma.',
    edges:
      'Sobel edges measures local contrast. Fixed display clipping may hide values above one; the numerical array retains them.',
    shift:
      'Horizontal translation moves columns with zero padding. Labels should remain valid; there is no wraparound.',
    brightness: 'Brightness adds an offset and clips the result to zero through one.',
  })) {
    await scene(
      'prepare-' + kind,
      text +
        ' Compare the original and transformed image using the same display scale and inspect the numerical range.',
      page.locator('#experiment .panel').first(),
      async () => {
        await select('Image operation', kind)
        if (['blur', 'shift', 'brightness'].includes(kind))
          await slider('Amount:', kind === 'brightness' ? 0.2 : 2)
        await stable()
        await view(page.locator('#experiment .image-row'))
        await focus(page.locator('#experiment .image-row'))
      },
      [`prepare:operation:${kind}`],
    )
  }
  await scene(
    'prepare-normalize',
    'Toggle dividing intensities by two hundred and fifty five. This choice carries forward into training. It changes units and gradient magnitude, but does not retrain any model here.',
    page.getByLabel('Divide pixel intensities by 255'),
    async () => {
      await click(page.getByLabel('Divide pixel intensities by 255'))
      await click(page.getByLabel('Divide pixel intensities by 255'))
    },
    ['prepare:normalization'],
  )
  await scene(
    'prepare-question-answer',
    'Blur might help suppress irrelevant noise or remove the gaps that distinguish a three from an eight. Compare raw and blurred representations on the same validation split and controlled training settings, rather than deciding by visual neatness.',
    page.locator('#experiment .question'),
    null,
    ['prepare:question-answer'],
  )
  await python('prepare')

  await chapter('model')
  await blocks(
    'model-explore',
    '#experiment .lede, #experiment p:not(.lede), #experiment .takeaway',
  )
  await scene(
    'model-weights',
    'These are illustrative weights: the mean training eight minus the mean training three, not fitted SGD weights. Reverse the multiplier and the signed contributions reverse. Each map is independently scaled. Green is positive and orange is negative.',
    page.locator('#experiment .image-row'),
    async () => {
      await slider('Weight multiplier:', -1)
      await stable()
    },
    ['model:weights-and-contributions'],
  )
  await scene(
    'model-bias',
    'The bias shifts the score for all images. The panel reports score, probability, thresholded prediction, and actual label. The model has seven hundred and eighty four weights and one bias.',
    page.locator('#experiment .metrics'),
    async () => {
      await slider('Bias:', 3)
      await stable()
      await view(page.locator('#experiment .metrics'))
    },
    ['model:bias-and-metrics'],
  )
  await scene(
    'model-question-answer',
    'Reversing all weights reverses their pixel contributions. A large weight on a blank pixel still contributes zero, because the contribution is weight times input. Bias is the separate term that can shift every example.',
    page.locator('#experiment .question'),
    null,
    ['model:question-answer'],
  )
  await python('model')

  await chapter('loss')
  await blocks('loss-explore', '#experiment .lede, #experiment h2, #experiment p:not(.lede)')
  for (const [value, description] of [
    [0.51, 'a hesitant correct prediction'],
    [0.99, 'a confident correct prediction'],
    [0.01, 'a confidently wrong prediction'],
  ]) {
    await scene(
      'loss-probability-' + String(value).replace('.', ''),
      `For a true eight, probability ${value} is ${description}. Watch the cross entropy and correctness indicator.`,
      page.locator('#experiment .panel').first(),
      async () => {
        await slider('Predicted probability of 8:', value)
      },
      ['loss:confidence:' + value],
    )
  }
  await scene(
    'loss-flip-label',
    'Now select a true three. At the same small probability of eight, the prediction is correct and its loss is small. The plot shows negative log p for an eight and negative log one minus p for a three.',
    page.locator('#experiment .two-col'),
    async () => {
      await select('Actual digit', '0')
    },
    ['loss:labels-and-curves'],
  )
  await scene(
    'loss-question-answer',
    'For a true eight, probability zero point zero one costs much more than zero point four: the model is more confidently wrong. Correct or incorrect alone discards confidence and does not supply a smooth training signal.',
    page.locator('#experiment .question'),
    null,
    ['loss:question-answer'],
  )
  await python('loss')

  await chapter('update')
  await blocks(
    'update-explore',
    '#experiment .lede, #experiment p:not(.lede), #experiment .takeaway',
  )
  const imageSelect = labelControl('Learn from this image')
  const options = await imageSelect
    .locator('option')
    .evaluateAll((els) => els.map((el) => ({ value: el.value, label: el.textContent })))
  for (const digit of ['3', '8']) {
    await scene(
      'update-label-' + digit,
      `For a true ${digit}, compare the residual, probability before and after, loss, and new bias. A true three gives a positive residual, while a true eight gives a negative residual. Subtracting the gradient moves active pixel weights in the corresponding direction.`,
      page.locator('#experiment .panel'),
      async () => {
        await select(
          'Learn from this image',
          options.find((o) => o.label.trim().startsWith(digit)).value,
        )
      },
      ['update:label:' + digit],
    )
  }
  await scene(
    'update-rate',
    'Compare learning rates zero point zero one and zero point one. Every preview starts from zero weights; changing the rate is not taking another sequential training step. A larger rate makes a larger parameter change.',
    page.locator('#experiment .panel'),
    async () => {
      await select('Learning rate η', '0.01')
      await stable()
      await shot()
      await select('Learning rate η', '0.1')
    },
    ['update:learning-rate'],
  )
  await blocks(
    'update-trace-intro',
    '.step-explorer .section-caption h2, .step-explorer .section-caption p',
  )
  for (let line = 2; line <= 9; line++) {
    const button = page.getByRole('button', { name: `Inspect Python line ${line}`, exact: true })
    await click(button)
    const explanation = await page.locator('.step-observation > p').first().innerText()
    const titles = await page.locator('.step-observation h3').innerText()
    const formulas = {
      2: 'The scores are X times w plus b. Zero weights and bias give zero scores.',
      3: 'Apply sigmoid to the scores. Sigmoid of zero equals one half.',
      4: 'Subtract the targets from the probabilities. For this eight, one half minus one equals negative one half.',
      5: 'Transpose X, multiply by the residual vector, and divide by batch size. For one example this is input times residual.',
      6: 'Average the residuals for the bias gradient. Here it is negative one half.',
      7: 'Subtract eta times the weight gradient. Negative gradients therefore increase weights.',
      8: 'Subtract eta times the bias gradient. With eta zero point one, the new bias is positive zero point zero five.',
      9: 'Return new weights and bias. This completes a single update, not full model training.',
    }
    await scene(
      'update-trace-line-' + line,
      titles +
        '. ' +
        formulas[line] +
        ' ' +
        explanation +
        (line === 7
          ? ' The gradient and updated weights have opposite signs. Colour ranges are independently scaled; use numbers to compare magnitudes.'
          : ''),
      page.locator('.step-layout'),
      async () => {
        await click(button)
        await focus(page.locator('.step-observation'))
      },
      ['update:step-line:' + line],
    )
  }
  await scene(
    'update-trace-controls',
    'Previous step and Next step move through captured execution snapshots. This is a replayable trace of the actual Python step function, not a paused debugger. Values appear only after their line executes.',
    page.locator('.step-controls'),
    async () => {
      await click(page.getByRole('button', { name: '← Previous step' }))
      await click(page.getByRole('button', { name: 'Next step →' }))
    },
    ['update:trace-controls'],
  )
  await scene(
    'update-pixel',
    'Drag the pixel index slider. Compare the input intensity, weight gradient, and new weight for individual positions. A blank pixel contributes zero. The gradient and update maps use separate colour ranges.',
    page.locator('.feature-inspector'),
    async () => {
      await slider('Inspect pixel index j', 350)
      await focus(page.locator('.feature-inspector'))
    },
    ['update:pixel-gradient-weight-maps'],
  )
  await scene(
    'update-question-answer',
    'For a true eight, residual p minus y is negative. Inked pixels have positive intensities, so their gradients are negative. Subtracting a negative gradient increases their weights. Blank pixels do not move in this single-example update.',
    page.locator('#experiment .question'),
    null,
    ['update:question-answer'],
  )
  await python('update')

  await chapter('train')
  await blocks(
    'train-explore',
    '#experiment .lede, #experiment .takeaway, #experiment h2, #experiment h3, #experiment p:not(.lede)',
  )
  await scene(
    'train-stop-and-reset',
    'Long computations can be stopped without freezing the page. Start a deliberately long run, then use Stop and reset Python. This clears models in the current session and restarts the runtime. Export important experiments before resetting.',
    page.locator('.controls-panel'),
    async () => {
      await labelControl('Epochs').fill('100')
      await select('Batch size', '1')
      await click(page.getByRole('button', { name: 'Train classifier →', exact: true }))
      await click(page.getByRole('button', { name: 'Stop and reset Python', exact: true }))
      await expect(page.getByRole('status')).toContainText('Python ready', { timeout: 60000 })
      await labelControl('Epochs').fill('25')
      await select('Batch size', '32')
      await focus(page.locator('.controls-panel'))
    },
    ['train:stop-and-reset-runtime'],
  )
  await scene(
    'train-baseline',
    'Run the baseline: learning rate zero point one, twenty five epochs, batch size thirty two, raw normalised pixels, no augmentation. Watch training and validation mean cross entropy from epoch zero. A model is actually trained in browser Python.',
    page.locator('.controls-panel'),
    async () => {
      await click(page.getByRole('button', { name: 'Train classifier →', exact: true }))
      await expect(
        page.getByRole('button', { name: 'Train classifier →', exact: true }),
      ).toBeEnabled()
      await view(page.locator('.training-layout .panel').nth(1))
      await focus(page.locator('.training-layout .panel').nth(1))
    },
    ['train:baseline-and-loss-curves'],
  )
  await scene(
    'train-results',
    'Read the results of the baseline. ' +
      (await page.locator('.training-layout .metrics').innerText()) +
      '. Training accuracy is fit to training data; validation is evidence on held out examples. More epochs can improve training without improving validation.',
    page.locator('.training-layout .metrics'),
    null,
    ['train:baseline-results'],
  )
  await scene(
    'train-compare',
    'Change only the learning rate to zero point zero one and train again. Keep the split, seed, epochs and batch size fixed. Compare validation accuracy and loss, not just training accuracy. The run table stores the last eight experiments.',
    page.locator('.controls-panel'),
    async () => {
      await select('Learning rate', '0.01')
      await click(page.getByRole('button', { name: 'Train classifier →', exact: true }))
      await expect(
        page.getByRole('button', { name: 'Train classifier →', exact: true }),
      ).toBeEnabled()
      await view(page.locator('#experiment table'))
      await focus(page.locator('#experiment table'))
    },
    ['train:controlled-comparison-and-run-table'],
  )
  await blocks('train-post-results', '#experiment > .panel p, #experiment .question p')
  await scene(
    'train-augmentation',
    'Now restore the baseline rate and add copies shifted one pixel right. Augmentation doubles the training examples and updates per epoch. Keep the raw representation for this comparison; later compare original and shifted validation accuracy.',
    page.locator('.controls-panel'),
    async () => {
      await select('Learning rate', '0.1')
      await click(page.getByLabel('Add copies shifted 1 px right'))
      await click(page.getByRole('button', { name: 'Train classifier →', exact: true }))
      await expect(
        page.getByRole('button', { name: 'Train classifier →', exact: true }),
      ).toBeEnabled()
      await view(page.locator('#experiment table'))
      await focus(page.locator('#experiment table'))
    },
    ['train:augmentation'],
  )
  await scene(
    'train-settings',
    'All training controls are editable: learning rate, epochs, batch size, representation, input scale, and augmentation. Raw, blurred, or edge features change the input. Disabling scaling changes units. Full batch uses the complete training set. Change one decision at a time, and account for update cost.',
    page.locator('.controls-panel'),
    async () => {
      await select('Representation', 'blur')
      await select('Representation', 'edges')
      await select('Representation', 'raw')
      await select('Batch size', '1920')
      await select('Batch size', '32')
      await labelControl('Epochs').fill('25')
      await focus(page.locator('.controls-panel'))
    },
    ['train:all-settings'],
  )
  await scene(
    'train-export',
    'Export results downloads experiment settings, histories and selected run information. Reloading clears the session, so export anything you want to retain.',
    page.getByRole('button', { name: 'Export results ↓' }),
    async () => {
      const download = page.waitForEvent('download')
      await click(page.getByRole('button', { name: 'Export results ↓' }))
      await (await download).saveAs(path.join(output, 'training-results.json'))
    },
    ['train:export'],
  )
  await scene(
    'train-question-answer',
    'If loss barely changes, first inspect input scale and learning rate, then compare a controlled adjustment. If training improves while validation worsens, additional epochs may increase overfitting rather than help. Use validation evidence and keep a record of the change.',
    page.locator('#experiment .question'),
    null,
    ['train:question-answer'],
  )
  await python('train')

  await chapter('evaluate')
  await blocks(
    'evaluate-explore',
    '#experiment .lede, #experiment h2, #experiment h3, #experiment p:not(.lede)',
  )
  await scene(
    'evaluate-errors',
    'The learned weight map shows positive weights favouring eight. The confusion matrix has actual classes on rows and predictions on columns. Diagonal entries are correct. Inspect the most confident validation mistakes for ambiguity or a repeated failure pattern.',
    page.locator('#experiment > .panel').first(),
    async () => {
      await view(page.locator('.gallery.errors'))
      await focus(page.locator('.gallery.errors'))
    },
    ['evaluate:weights-confusion-and-mistakes'],
  )
  await scene(
    'evaluate-shift',
    'Evaluate the selected augmented model on validation images shifted one pixel right, without changing its weights. Compare its original and shifted accuracy. This is evidence about this particular transformation, not invariance to all shifts.',
    page.getByRole('button', { name: 'Evaluate shifted validation images' }),
    async () => {
      await click(page.getByRole('button', { name: 'Evaluate shifted validation images' }))
      await expect(page.getByText('Shifted 1 px right', { exact: true })).toBeVisible()
      await view(page.locator('#experiment .two-col .panel').first())
      await focus(page.locator('#experiment .two-col .panel').first())
    },
    ['evaluate:shifted-validation'],
  )
  await scene(
    'evaluate-baseline-robustness',
    'For a fair robustness comparison, return to training and select the original baseline run. Evaluate the same one pixel shift on the same validation split without retraining. Then restore the augmentation run. The augmentation cost is twice as many updates per epoch, so performance is not the only difference.',
    page.locator('#experiment .two-col .panel').first(),
    async () => {
      await click(page.locator('nav a[href="#/tutorial04/train"]'))
      await stable()
      await click(page.locator('#experiment tbody button').nth(0))
      await click(page.locator('nav a[href="#/tutorial04/evaluate"]'))
      await stable()
      await click(page.getByRole('button', { name: 'Evaluate shifted validation images' }))
      await expect(page.getByText('Shifted 1 px right', { exact: true })).toBeVisible()
      await view(page.locator('#experiment .two-col .panel').first())
      await focus(page.locator('#experiment .two-col .panel').first())
      await sleep(1000)
      await click(page.locator('nav a[href="#/tutorial04/train"]'))
      await stable()
      await click(page.locator('#experiment tbody button').nth(2))
      await click(page.locator('nav a[href="#/tutorial04/evaluate"]'))
      await stable()
      await click(page.getByRole('button', { name: 'Evaluate shifted validation images' }))
      await expect(page.getByText('Shifted 1 px right', { exact: true })).toBeVisible()
      await view(page.locator('#experiment .two-col .panel').first())
      await focus(page.locator('#experiment .two-col .panel').first())
    },
    ['evaluate:baseline-vs-augmented-robustness'],
  )
  await scene(
    'evaluate-decision',
    'Before testing, write a model selection rationale based only on validation evidence. Here we retain the augmentation experiment to investigate robustness. The test button is locked until a rationale is provided; test data is not used to pick hyperparameters.',
    page.getByLabel('Your model choice'),
    async () => {
      await labelControl('Your model choice').fill(
        'Selected the shifted-training experiment using original and shifted validation evidence; record both robustness and extra training cost.',
      )
      await focus(page.getByLabel('Your model choice'))
    },
    ['evaluate:selection-rationale'],
  )
  await scene(
    'evaluate-test',
    'Now evaluate once on the untouched eight hundred test images. The interface locks this decision after evaluation. Further tuning based on this result would make the test set no longer an independent final check.',
    page.getByRole('button', { name: 'Evaluate selected model on test set' }),
    async () => {
      await click(page.getByRole('button', { name: 'Evaluate selected model on test set' }))
      await expect(page.getByText('Final test accuracy')).toBeVisible()
      await view(page.locator('#experiment .two-col .panel').nth(1))
      await focus(page.locator('#experiment .two-col .panel').nth(1))
    },
    ['evaluate:final-test'],
  )
  await scene(
    'evaluate-final-results',
    'The held out test evaluation reports: ' +
      (await page.locator('#experiment .two-col .panel').nth(1).locator('.metrics').innerText()) +
      '. These results describe this fixed test set; they are not a guarantee for every handwriting distribution or every transformation.',
    page.locator('#experiment .two-col .panel').nth(1).locator('.metrics'),
    null,
    ['evaluate:actual-test-results'],
  )
  await scene(
    'evaluate-export',
    'Export the experiment and decision to keep your model choice, validation comparison and test result together.',
    page.getByRole('button', { name: 'Export experiment and decision ↓' }),
    async () => {
      const download = page.waitForEvent('download')
      await click(page.getByRole('button', { name: 'Export experiment and decision ↓' }))
      await (await download).saveAs(path.join(output, 'final-decision.json'))
    },
    ['evaluate:export'],
  )
  await python('evaluate')

  await chapter('beyond')
  await blocks(
    'beyond-explore',
    '.beyond-section > h2, .beyond-section > p, .beyond-section .concept-note p, .beyond-section .question p',
  )
  await blocks('beyond-linear-explanation', '.xor-layout p')
  for (const [mode, description] of Object.entries({
    linear:
      'This constructed straight line correctly classifies three of four XOR examples. No straight boundary can separate both pairs of opposite corners. More SGD cannot remove that limitation.',
    interaction:
      'Adding input one times input two changes the feature space. The constructed rule now classifies all four correctly. It is linear in these expanded features, not in the original inputs.',
    hidden:
      'Two ReLU units compute positive input differences in either direction. Their sum distinguishes unequal inputs. This tiny MLP has constructed weights; a learned MLP would update hidden and output weights by backpropagation.',
  })) {
    await scene(
      'beyond-xor-' + mode,
      description +
        ' Background colours show predicted regions and point colours show true labels. These are designed rules, not fitted training results.',
      page.locator('.xor-layout'),
      async () => {
        await select('Decision rule', mode)
        await view(page.locator('.xor-layout'))
        await focus(page.locator('.xor-layout'))
      },
      ['beyond:xor:' + mode],
    )
  }
  await blocks('beyond-xor-disclaimer', '.xor-layout p')
  for (const kind of ['vertical', 'horizontal', 'average']) {
    await scene(
      'beyond-filter-' + kind,
      `Choose the ${kind} filter. The same three by three kernel is applied at every position. Multiply corresponding patch and kernel entries and sum them to obtain one feature map value.`,
      page.locator('.convolution-layout'),
      async () => {
        await select('Example filter', kind)
        await stable()
        await view(page.locator('.convolution-layout'))
        await focus(page.locator('.convolution-layout'))
      },
      ['beyond:filter:' + kind],
    )
  }
  await scene(
    'beyond-window',
    'Drag the window row and column. The highlighted three by three input patch corresponds to one highlighted feature map position. Stride one with no padding gives twenty eight minus three plus one, or twenty six positions per axis.',
    page.locator('.convolution-layout'),
    async () => {
      await slider('Window row:', 0)
      await slider('Window column:', 0)
      await slider('Window row:', 10)
      await slider('Window column:', 10)
      await view(page.locator('.convolution-layout'))
      await focus(page.locator('.convolution-layout'))
    },
    ['beyond:convolution-window-and-equation'],
  )
  await blocks('beyond-convolution-notes', '.beyond-section .panel > p')
  await scene(
    'beyond-methods',
    'The next-method comparison has four directions. ' +
      (await page.locator('.beyond-section table').innerText()),
    page.locator('.beyond-section table'),
    null,
    ['beyond:all-method-table-rows'],
  )
  await scene(
    'beyond-reading',
    'Continue with the linked CS231n convolutional network notes and the PyTorch complete learning workflow. These external resources are further reading, not part of the local tutorial demonstration.',
    page.locator('.further-reading'),
    null,
    ['beyond:further-reading-links'],
  )
  await python('beyond')
  await scene(
    'notebook-download',
    'Download Notebook and data. The archive contains the complete offline lab. Keep your prediction, controlled experiment, validation comparison, chosen model and limitations in the notebook. That concludes all eight chapters and the overview.',
    page.locator('.notebook-bridge a'),
    async () => {
      const download = page.waitForEvent('download')
      await click(page.locator('.notebook-bridge a'))
      await (await download).saveAs(path.join(output, 'tutorial04-student.zip'))
    },
    ['notebook:download'],
  )
  await expect(page.locator('#video-caption')).toHaveCount(0)
  await writeFile(
    path.join(output, 'scenes.json'),
    JSON.stringify({ title: 'Tutorial 04 - Complete walkthrough', scenes }, null, 2),
  )
  const allNarration = scenes.map((scene) => scene.text).join(' ')
  const missing = inventory.filter((item) => item.text && !allNarration.includes(item.text))
  await writeFile(
    path.join(output, 'coverage.json'),
    JSON.stringify(
      {
        chapters: chapterNames,
        coverage,
        inventory,
        missingVerbatim: missing,
        sourceHashes,
        scenes: scenes.length,
        captionsBurnedIn: false,
      },
      null,
      2,
    ),
  )
  if (missing.length)
    throw new Error(
      `Coverage audit failed: ${missing.length} website teaching texts missing verbatim; review coverage.json`,
    )
  console.log(
    `Complete recording: ${scenes.length} scenes; all ${inventory.length} website teaching texts covered`,
  )
} finally {
  await browser?.close()
  try {
    process.kill(-server.pid, 'SIGTERM')
  } catch {}
}
