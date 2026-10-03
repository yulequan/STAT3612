#!/usr/bin/env python3
"""Package the editable notebook, shared Python code and data; preserve data paths."""
import argparse
import json
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

ROOT = Path(__file__).resolve().parents[1]


def package(folder):
    spec = json.loads((folder / 'tutorial.json').read_text())
    output = ROOT / '.cache/packages' / f"{spec['id']}-student.zip"
    output.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(output, 'w', ZIP_DEFLATED) as archive:
        for relative in spec['student_files']:
            path = Path(relative)
            archive.write(folder / relative, str(path))
    return output


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('tutorial', nargs='?', default='tutorial04')
    args = parser.parse_args()
    print(package(ROOT / 'src/tutorials' / args.tutorial))
