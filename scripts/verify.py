#!/usr/bin/env python3
"""Verify scientific behavior, extracted notebook execution, production build and browser UI."""
import argparse
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def run(*command):
    print('\nRunning:', ' '.join(map(str, command)), flush=True)
    subprocess.run(list(map(str, command)), cwd=ROOT, check=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('tutorial', nargs='?', default='tutorial04', choices=['tutorial04'])
    parser.parse_args()
    python = ROOT / '.venv/bin/python'
    if not python.exists():
        python = Path(sys.executable)
    run(python, '-m', 'unittest', 'discover', '-s', 'tests', '-v')
    run(python, 'scripts/check_notebook.py')
    run('npm', 'run', 'build')
    run('npm', 'run', 'test:web')
    print('\nAll checks passed.')


if __name__ == '__main__':
    main()
