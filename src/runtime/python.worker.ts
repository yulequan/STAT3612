import type { PyodideInterface } from 'pyodide'

let python: PyodideInterface | undefined
let queue = Promise.resolve()

async function fetchOK(url: string) {
  const response = await fetch(url)
  if (!response.ok) throw new Error(`Could not load ${url}: HTTP ${response.status}`)
  return response
}

async function handle(data: { id: number; action: string; params: Record<string, unknown> }) {
  const { id, action, params } = data
  try {
    if (action === 'boot') {
      const base = String(params.base)
      const runtimeURL = new URL('python/', base).href
      const folder = new URL(`tutorials/${params.tutorial}/`, base).href
      const manifest = await fetchOK(`${folder}tutorial.json`).then((r) => r.json())
      const { loadPyodide } = await import(/* @vite-ignore */ `${runtimeURL}pyodide.mjs`)
      self.postMessage({ id, status: 'Starting Python…' })
      python = await loadPyodide({ indexURL: runtimeURL })
      if (!python) throw new Error('Python did not initialize.')
      self.postMessage({ id, status: 'Loading scientific packages…' })
      await python.loadPackage(manifest.python_packages)
      const source = await fetchOK(`${folder}${manifest.experiment}`).then((r) => r.text())
      python.FS.writeFile('/home/pyodide/experiment.py', source)
      if (manifest.dataset) {
        const dataset = await fetchOK(`${folder}${manifest.dataset}`).then((r) => r.arrayBuffer())
        python.FS.writeFile('/home/pyodide/data.npz', new Uint8Array(dataset))
      }
      await python.runPythonAsync(
        'import json\nfrom experiment import Experiment\nexperiment = Experiment("data.npz")',
      )
      const result = await python.runPythonAsync('experiment.dispatch("initialize", {})')
      self.postMessage({ id, result: JSON.parse(result) })
      return
    }
    if (!python) throw new Error('Python is still loading. Please wait.')
    python.globals.set('_request', JSON.stringify(params))
    python.globals.set('_action', action)
    python.globals.set('_progress', (row: string) =>
      self.postMessage({ id, progress: JSON.parse(row) }),
    )
    try {
      const result = await python.runPythonAsync(
        action === 'fit'
          ? 'json.dumps(experiment.fit(json.loads(_request), _progress))'
          : 'experiment.dispatch(_action, json.loads(_request))',
      )
      self.postMessage({ id, result: JSON.parse(result) })
    } finally {
      for (const name of ['_request', '_action', '_progress']) python.globals.delete(name)
    }
  } catch (error) {
    self.postMessage({ id, error: error instanceof Error ? error.message : String(error) })
  }
}

self.onmessage = ({ data }) => {
  queue = queue.then(() => handle(data))
}
