// Chromium compositor capture for the Tutorial 06 slide stage.
// Frames are timestamped; pointer and focus ring stay visible in the final hold.
import { mkdir, writeFile } from 'node:fs/promises'
import path from 'node:path'
import { performance } from 'node:perf_hooks'

export class SceneCapture {
  constructor(page) {
    this.page = page
  }

  async start(folder) {
    this.folder = folder
    await mkdir(folder, { recursive: true })
    this.frames = []
    this.writes = []
    this.startTime = performance.now()
    this.cdp = await this.page.context().newCDPSession(this.page)
    this.listener = ({ data, sessionId }) => {
      const index = this.frames.length
      const file = `frame-${String(index).padStart(5, '0')}.jpg`
      const time = index ? (performance.now() - this.startTime) / 1000 : 0
      this.frames.push({ file, time })
      this.writes.push(writeFile(path.join(folder, file), Buffer.from(data, 'base64')))
      this.cdp.send('Page.screencastFrameAck', { sessionId }).catch(() => {})
    }
    this.cdp.on('Page.screencastFrame', this.listener)
    await this.cdp.send('Page.startScreencast', {
      format: 'jpeg',
      quality: 92,
      maxWidth: 1920,
      maxHeight: 1080,
      everyNthFrame: 1,
    })
  }

  async stop() {
    await this.cdp.send('Page.stopScreencast')
    this.cdp.off('Page.screencastFrame', this.listener)
    await Promise.all(this.writes)
    const layout = await this.page.evaluate(() => {
      const box = (selector) => {
        const element = document.querySelector(selector)
        if (!element) return null
        const rect = element.getBoundingClientRect()
        return {
          x: rect.x,
          y: rect.y,
          width: rect.width,
          height: rect.height,
          opacity: getComputedStyle(element).opacity,
        }
      }
      return {
        focus: box('#focus'),
        pointer: box('#pointer'),
        pointerVisible: getComputedStyle(document.querySelector('#pointer')).display !== 'none',
        ripples: document.querySelectorAll('.video-ring').length,
      }
    })
    const file = 'final.jpg'
    await this.page.screenshot({ path: path.join(this.folder, file), type: 'jpeg', quality: 95 })
    const actionSeconds = (performance.now() - this.startTime) / 1000
    this.frames.push({ file, time: actionSeconds })
    await this.cdp.detach()
    const metadata = {
      frames: this.frames,
      actionSeconds,
      method: 'Chromium compositor screencast',
      captionsBurnedIn: false,
      presentationVersion: 'tutorial06-slides-v1',
      layout,
    }
    await writeFile(path.join(this.folder, 'capture.json'), JSON.stringify(metadata, null, 2))
    return metadata
  }
}
