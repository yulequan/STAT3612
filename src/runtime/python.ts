import { ref } from 'vue'

export function createPython(tutorial: string) {
  const ready = ref(false)
  const status = ref('Preparing the experiment…')
  const error = ref('')
  let serial = 0
  let worker: Worker | undefined
  const pending = new Map<
    number,
    {
      resolve: (value: unknown) => void
      reject: (error: Error) => void
      progress?: (value: unknown) => void
    }
  >()

  function request<T>(
    action: string,
    params: Record<string, unknown> = {},
    progress?: (value: unknown) => void,
  ): Promise<T> {
    return new Promise((resolve, reject) => {
      if (!worker) return reject(new Error('Python is not running.'))
      const id = ++serial
      pending.set(id, { resolve: (value) => resolve(value as T), reject, progress })
      worker.postMessage({ id, action, params })
    })
  }

  function dispose() {
    if (worker) {
      worker.onmessage = null
      worker.onerror = null
    }
    worker?.terminate()
    worker = undefined
    ready.value = false
    for (const item of pending.values()) item.reject(new Error('Python session restarted.'))
    pending.clear()
  }

  async function start<T>() {
    dispose()
    error.value = ''
    status.value = 'Starting Python…'
    worker = new Worker(new URL('./python.worker.ts', import.meta.url), { type: 'module' })
    const sessionWorker = worker
    worker.onmessage = ({ data }) => {
      const item = pending.get(data.id)
      if (!item) return
      if (data.status) {
        status.value = data.status
        return
      }
      if (data.progress) {
        item.progress?.(data.progress)
        return
      }
      pending.delete(data.id)
      if (data.error) item.reject(new Error(data.error))
      else item.resolve(data.result)
    }
    worker.onerror = (event) => {
      status.value = 'Python stopped'
      error.value = event.message || 'The Python worker stopped. Restart the experiment.'
      ready.value = false
      for (const item of pending.values()) item.reject(new Error(error.value))
      pending.clear()
    }
    try {
      const result = await request<T>('boot', {
        tutorial,
        base: new URL(import.meta.env.BASE_URL, window.location.href).href,
      })
      if (worker === sessionWorker) {
        ready.value = true
        status.value = 'Python ready · runs on this device'
      }
      return result
    } catch (e) {
      if (worker === sessionWorker) {
        error.value = String(e)
        status.value = 'Python could not start'
      }
      throw e
    }
  }
  return { ready, status, error, request, start, dispose }
}
