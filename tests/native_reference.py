"""Values for comparing the real browser WASM run against native Python."""
import json
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src/tutorials/tutorial04'))
from experiment import Experiment
experiment = Experiment(ROOT / 'src/tutorials/tutorial04/data/mnist_3v8.npz')
result = experiment.fit({})
print(json.dumps({'history': result['history'], 'test': experiment.evaluate(result['id'], split='test')}))
