#!/usr/bin/env python3
"""Prepare local Python runtime and tutorial assets. Network needed only on first build."""
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
from package_student import package

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / '.cache/public'
RUNTIME = ROOT / 'node_modules/pyodide'


def main():
    if not RUNTIME.exists():
        raise SystemExit('Run npm ci first.')
    # Rebuild the generated public tree, including the authored standalone demos.
    # Only this cache is disposable; public/ and src/ remain the source of truth.
    shutil.rmtree(PUBLIC, ignore_errors=True)
    shutil.copytree(ROOT / 'public', PUBLIC)
    vendor = PUBLIC / 'vendor'
    vendor.mkdir(parents=True, exist_ok=True)
    three = ROOT / 'node_modules/three'
    shutil.copy2(three / 'build/three.min.js', vendor / 'three.min.js')
    shutil.copy2(three / 'LICENSE', vendor / 'three-LICENSE.txt')
    version = json.loads((RUNTIME / 'package.json').read_text())['version']
    lock = json.loads((RUNTIME / 'pyodide-lock.json').read_text())
    target = PUBLIC / 'python'
    target.mkdir(parents=True, exist_ok=True)
    for name in ('pyodide.mjs', 'pyodide.asm.js', 'pyodide.asm.wasm',
                 'python_stdlib.zip', 'pyodide-lock.json'):
        shutil.copy2(RUNTIME / name, target / name)

    dependencies = set()

    def include(name):
        if name in dependencies:
            return
        dependencies.add(name)
        for dep in lock['packages'][name]['depends']:
            include(dep)

    manifests = sorted((ROOT / 'src/tutorials').glob('tutorial*/tutorial.json'))
    for manifest in manifests:
        for name in json.loads(manifest.read_text())['python_packages']:
            include(name)

    cache = ROOT / '.cache/pyodide' / version
    cache.mkdir(parents=True, exist_ok=True)

    def download(name):
        spec = lock['packages'][name]
        path = cache / spec['file_name']

        def valid():
            return path.exists() and hashlib.sha256(path.read_bytes()).hexdigest() == spec['sha256']

        if not valid():
            temporary = path.with_suffix('.download')
            url = f"https://cdn.jsdelivr.net/pyodide/v{version}/full/{spec['file_name']}"
            subprocess.run(['curl', '--fail', '--silent', '--show-error', '--location',
                            '--retry', '3', '--retry-all-errors', '--max-time', '180', url, '-o', str(temporary)], check=True)
            temporary.replace(path)
            if not valid():
                path.unlink()
                raise RuntimeError(f'Checksum mismatch: {name}')
        shutil.copy2(path, target / path.name)
        return f"{name} {spec['version']}"

    with ThreadPoolExecutor(max_workers=3) as pool:
        for result in pool.map(download, sorted(dependencies)):
            print(result)
    for manifest in manifests:
        folder = manifest.parent
        spec = json.loads(manifest.read_text())
        destination = PUBLIC / 'tutorials' / spec['id']
        destination.mkdir(parents=True, exist_ok=True)
        shutil.copy2(manifest, destination / 'tutorial.json')
        for relative in spec['web_assets']:
            src, out = folder / relative, destination / relative
            out.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, out)
        shutil.copy2(package(folder), destination / 'student.zip')
    print(f'Local runtime ready: Pyodide {version}; no CDN requests in class.')


if __name__ == '__main__':
    main()
