// Video-only art direction. Does not change the tutorial app or its data.
export const PRESENTATION_VERSION = 'full-page-v3'

export class Presentation {
  constructor(page) {
    this.page = page
    this.pointer = { x: 1780, y: 960 }
  }

  async install() {
    await this.page.addStyleTag({
      content: `
      html { scroll-behavior: auto !important; }
      body { overflow-x: hidden; }
      .content { max-width: 1450px; }
      .python-code pre, .python-code code { font-size: 18px; }
      .step-layout .python-code { position: static; }
      /* Browser/native cursors never appear in screenshots; ours is interaction-only. */
      * { cursor: none !important; }
      #video-header { position: fixed; inset: 0 0 auto; height: 68px; z-index: 2147483600;
        background: #172a30; color: white; padding: 0 35px; display: flex; align-items: center;
        justify-content: space-between; font: 24px system-ui; pointer-events: none; }
      #video-header small { font-size: 16px; color: #b8d1c6; }
      #video-pointer { position: fixed; width: 23px; height: 30px; display: none;
        z-index: 2147483640; pointer-events: none; filter: drop-shadow(0 2px 2px #0005); }
      #video-focus { position: fixed; border: 2px solid #c88b2f; border-radius: 6px;
        z-index: 2147483599; pointer-events: none; background: transparent; }
      .video-ring { position: fixed; width: 16px; height: 16px; border: 3px solid #e59425;
        border-radius: 50%; z-index: 2147483641; pointer-events: none;
        animation: video-click .55s ease-out forwards; }
      @keyframes video-click { from { transform: translate(-50%,-50%) scale(.5); opacity: 1; }
        to { transform: translate(-50%,-50%) scale(2.8); opacity: 0; } }
    `,
    })
    await this.page.evaluate(() => {
      for (const id of ['video-header', 'video-pointer', 'video-focus']) {
        const el = document.createElement('div')
        el.id = id
        document.body.append(el)
      }
      document.querySelector('#video-header').innerHTML =
        '<span>STAT3612 · Tutorial 04 · Complete walkthrough</span><small></small>'
      document.querySelector('#video-pointer').innerHTML =
        '<svg width="23" height="30" viewBox="0 0 30 38"><path d="M3 2 L3 29 L10 23 L16 35 L22 32 L16 21 L27 21 Z" fill="white" stroke="#18322d" stroke-width="2"/></svg>'
      document.querySelector('#video-focus').style.display = 'none'
    })
  }

  async hidePointer() {
    this.pointer = { x: 1780, y: 960 }
    await this.page.evaluate(() => {
      document.querySelector('#video-pointer').style.display = 'none'
      document.querySelectorAll('.video-ring').forEach((el) => el.remove())
    })
  }

  async frame(locator) {
    // Context = a real containing card/section, not an isolated line at the top.
    return locator.evaluate((element) => {
      const main = document.querySelector('main')
      const isFixed = (el) => {
        for (let p = el; p; p = p.parentElement)
          if (getComputedStyle(p).position === 'fixed') return true
        return false
      }
      const rect = (el) => {
        if (el.dataset.videoLineCount) {
          const lines = [...el.parentElement.children]
          const index = lines.indexOf(el)
          const boxes = lines
            .slice(index, index + +el.dataset.videoLineCount)
            .map((line) => line.getBoundingClientRect())
          const x = Math.min(...boxes.map((b) => b.left)),
            y = Math.min(...boxes.map((b) => b.top))
          return {
            x,
            y,
            width: Math.max(...boxes.map((b) => b.right)) - x,
            height: Math.max(...boxes.map((b) => b.bottom)) - y,
          }
        }
        const b = el.getBoundingClientRect()
        return { x: b.x, y: b.y, width: b.width, height: b.height }
      }
      let context = element
      // Avoid unnecessarily huge panels; keep the relevant paragraph AND its heading.
      const preferred =
        '.equation-card, .concept-note, .question, .takeaway, .python-output, .python-editor, .feature-inspector, .step-observation, .image-row, .xor-layout, .convolution-layout, .notebook-bridge, .overview-intro, .overview-route > li, .overview-preparation > div, .panel, .python-code, .theory-paragraphs, .chapter-heading, .course-index'
      let candidate = element.closest(preferred)
      const composite =
        element.closest('.step-layout') ||
        (element.matches('.image-row') ? element.closest('.panel') : null)
      if (composite && rect(composite).height <= 750) candidate = composite
      if (candidate && !element.dataset.videoLineCount) {
        const b = rect(candidate)
        if (b.height <= 750 && b.width <= 1660) context = candidate
      }
      if (/^(H2|H3)$/.test(element.tagName) && context === element) {
        const parent = element.parentElement,
          b = rect(parent)
        if (b.height <= 650 && b.width <= 1660 && parent.id !== 'concept') context = parent
      }
      const fixed = isFixed(element)
      let box = rect(context)
      const oversized = box.height > 810
      // Large composite views remain readable: frame an explicit viewport portion.
      if (!fixed) {
        // Scroll only. Preserve the website's sidebar, columns and surrounding content.
        // Short blocks sit in the upper-middle with useful context above and below;
        // tall panels use the available viewport. Never fabricate blank page padding.
        const desiredY = oversized
          ? 110
          : Math.max(100, Math.min(300, (1080 + 68 - box.height) / 2))
        window.scrollTo({ top: scrollY + box.y - desiredY, behavior: 'instant' })
        box = rect(context)
      }
      const focus = rect(element)
      const top = Math.max(98, focus.y - 6),
        left = Math.max(46, focus.x - 6)
      Object.assign(document.querySelector('#video-focus').style, {
        display: 'block',
        left: `${left}px`,
        top: `${top}px`,
        width: `${Math.min(1874, focus.x + focus.width + 6) - left}px`,
        height: `${Math.min(1040, focus.y + focus.height + 6) - top}px`,
      })
      return {
        context: rect(context),
        target: focus,
        fixed,
        oversized,
        viewport: { width: 1920, height: 1080 },
        pointerVisible:
          getComputedStyle(document.querySelector('#video-pointer')).display !== 'none',
      }
    })
  }

  async move(x, y, visible = true) {
    if (!visible) {
      await this.page.mouse.move(x, y)
      this.pointer = { x, y }
      return
    }
    // The animation and the native drag use the SAME clock and easing, not two
    // independently timed loops (which previously left the cursor parked on text).
    const from = { ...this.pointer }
    const begin = await this.page.evaluate(
      ({ from }) => {
        const cursor = document.querySelector('#video-pointer')
        Object.assign(cursor.style, { display: 'block', left: `${from.x}px`, top: `${from.y}px` })
        return performance.now()
      },
      { from },
    )
    await this.page.evaluate(
      ({ begin, from, x, y }) => {
        const cursor = document.querySelector('#video-pointer')
        window.__videoMotion = []
        window.__videoMotionDone = new Promise((resolve) => {
          function frame(now) {
            const t = Math.min(1, (now - begin) / 650),
              e = t * t * (3 - 2 * t)
            const point = { x: from.x + (x - from.x) * e, y: from.y + (y - from.y) * e }
            Object.assign(cursor.style, { left: `${point.x}px`, top: `${point.y}px` })
            window.__videoMotion.push(point)
            if (t < 1) requestAnimationFrame(frame)
            else resolve()
          }
          requestAnimationFrame(frame)
        })
      },
      { begin, from, x, y },
    )
    while (true) {
      const t = await this.page.evaluate(
        (begin) => Math.min(1, (performance.now() - begin) / 650),
        begin,
      )
      const e = t * t * (3 - 2 * t)
      await this.page.mouse.move(from.x + (x - from.x) * e, from.y + (y - from.y) * e)
      if (t === 1) break
      await this.page.waitForTimeout(16)
    }
    await this.page.evaluate(() => window.__videoMotionDone)
    this.pointer = { x, y }
  }

  async pulse() {
    await this.page.evaluate(({ x, y }) => {
      const ring = document.createElement('div')
      ring.className = 'video-ring'
      ring.style.left = `${x}px`
      ring.style.top = `${y}px`
      document.body.append(ring)
      setTimeout(() => ring.remove(), 600)
    }, this.pointer)
  }
}
