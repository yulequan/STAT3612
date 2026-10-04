#!/usr/bin/env python3
"""Run the actual packaged notebook in an isolated extracted directory."""
import argparse
import ast
from pathlib import Path
import tempfile
from zipfile import ZipFile

import nbformat
from nbclient import NotebookClient
from package_student import package

ROOT = Path(__file__).resolve().parents[1]
folders = sorted((ROOT / 'src/tutorials').glob('tutorial*'))
parser = argparse.ArgumentParser()
parser.add_argument('tutorial', nargs='?', choices=[p.name for p in folders])
args = parser.parse_args()
for folder in folders:
    if args.tutorial and folder.name != args.tutorial:
        continue
    path = folder / f'{folder.name}.ipynb'
    if not path.exists():
        continue
    source = ast.parse((folder / 'experiment.py').read_text())
    functions = {n.name: ast.dump(n) for n in source.body if isinstance(n, ast.FunctionDef)}
    notebook = nbformat.read(path, as_version=4)
    for cell in notebook.cells:
        if cell.cell_type != 'code':
            continue
        for node in ast.parse(cell.source).body:
            if isinstance(node, ast.FunctionDef) and node.name in functions:
                assert ast.dump(node) == functions[node.name], f'Stale notebook function: {folder.name}/{node.name}'
    with tempfile.TemporaryDirectory(prefix='stat3612-notebook-') as temporary:
        with ZipFile(package(folder)) as archive:
            archive.extractall(temporary)
        nb = nbformat.read(Path(temporary) / path.name, as_version=4)
        # Exercise the opt-in final evaluation using the already-selected baseline.
        for cell in nb.cells:
            if cell.cell_type == 'code' and "reason = ''" in cell.source:
                cell.source = cell.source.replace("reason = ''", "reason = 'Baseline selected for package verification'")
        NotebookClient(nb, timeout=600, resources={'metadata': {'path': temporary}}).execute()
        print(f'{folder.name}: {len(nb.cells)} packaged cells executed, including final test evaluation.')
