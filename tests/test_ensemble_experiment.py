"""Regression checks for Tutorial08's scientific and evaluation contracts."""
import ast
import importlib.util
import json
from pathlib import Path
import unittest

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
FOLDER = ROOT / 'src/tutorials/tutorial08'
spec = importlib.util.spec_from_file_location('ensemble_experiment', FOLDER / 'experiment.py')
science = importlib.util.module_from_spec(spec)
spec.loader.exec_module(science)


def rows(dataset, split):
    return {tuple(row) for row in dataset[f'X_{split}']}


class EnsembleExperimentTests(unittest.TestCase):
    def setUp(self):
        self.lab = science.Experiment()

    def test_fixed_splits_are_stratified_disjoint_and_deterministic(self):
        result = self.lab.initialize()
        self.assertEqual([result['counts']['moons'][s]['total'] for s in ('train', 'val', 'test')],
                         [360, 120, 120])
        self.assertEqual([result['counts']['iris'][s]['total'] for s in ('train', 'val', 'test')],
                         [60, 20, 20])
        self.assertEqual([result['counts']['xor'][s]['total'] for s in ('train', 'val', 'test')],
                         [240, 80, 80])
        for name, data in self.lab.datasets.items():
            self.assertAlmostEqual(data['y_train'].mean(), .5, delta=.05)
            self.assertAlmostEqual(data['y_val'].mean(), .5, delta=.05)
            self.assertAlmostEqual(data['y_test'].mean(), .5, delta=.05)
            if name != 'iris':
                # Iris has repeated two-feature measurements; continuous data do not.
                train, validation, test = (rows(data, s) for s in ('train', 'val', 'test'))
                self.assertFalse(train & validation)
                self.assertFalse(train & test)
                self.assertFalse(validation & test)
                self.assertEqual(len(train) + len(validation) + len(test),
                                 len(train | validation | test))
        again = science.Experiment()
        for name in self.lab.datasets:
            for split in ('train', 'val', 'test'):
                np.testing.assert_array_equal(self.lab.datasets[name][f'X_{split}'],
                                              again.datasets[name][f'X_{split}'])
                np.testing.assert_array_equal(self.lab.datasets[name][f'y_{split}'],
                                              again.datasets[name][f'y_{split}'])

    def test_confusion_metrics_use_class_one_as_positive(self):
        result = science.metrics(np.array([0, 0, 1, 1]), np.array([0, 1, 0, 1]))
        self.assertEqual(result['confusion'], [[1, 1], [1, 1]])
        self.assertEqual(result['accuracy'], .5)
        self.assertEqual(result['precision'], .5)
        self.assertEqual(result['recall'], .5)
        self.assertEqual(result['f1'], .5)
        baseline = science.metrics(np.array([0, 1, 1]), np.zeros(3))
        self.assertEqual(baseline['confusion'], [[1, 0], [2, 0]])
        self.assertEqual(baseline['recall'], 0)
        self.assertEqual(baseline['precision'], 0)
        self.assertEqual(baseline['f1'], 0)

    def test_tree_grows_with_depth_and_returns_a_full_grid(self):
        shallow = self.lab.fit_tree({'depth': 1})
        deep = self.lab.fit_tree({'depth': None, 'min_leaf': 1})
        self.assertLess(shallow['leaves'], deep['leaves'])
        self.assertEqual(len(shallow['plot']['grid']['z']), 55)
        self.assertEqual(len(shallow['plot']['grid']['z'][0]), 55)
        self.assertEqual(len(shallow['plot']['points']), 480)
        self.assertTrue(shallow['rules'])
        self.assertEqual(len(shallow['importance']), 2)
        self.assertIn(shallow['validation']['accuracy'], [i / 120 for i in range(121)])
        self.assertGreaterEqual(deep['train']['accuracy'], shallow['train']['accuracy'])

    def test_bagging_and_forest_curves_match_tree_prefixes(self):
        for mode in ('bagging', 'forest'):
            row = self.lab.fit_forest({'mode': mode, 'n_estimators': 40})
            self.assertEqual(len(row['curve']['n']), 40)
            self.assertEqual(len(row['curve']['train']), 40)
            self.assertEqual(len(row['curve']['validation']), 40)
            self.assertTrue(0 <= row['oob'] <= 1)
            self.assertEqual(len(row['importance']), 2)
            self.assertEqual(len(row['plot']['points']), 480)
        forest = self.lab.fit_forest({'mode': 'forest', 'n_estimators': 40,
                                      'max_features': 'all'})
        self.assertEqual(forest['params']['max_features'], 'all')

    def test_boosting_staged_curve_and_best_tree(self):
        row = self.lab.fit_boosting({'mode': 'gradient', 'n_estimators': 30,
                                     'learning_rate': .1})
        self.assertEqual(len(row['curve']['n']), 30)
        self.assertEqual(len(row['curve']['validation']), 30)
        self.assertEqual(row['best_n'],
                         int(np.argmax(row['curve']['validation'])) + 1)
        self.assertEqual(row['params']['learning_rate'], .1)
        self.assertEqual(len(row['plot']['grid']['z']), 55)

    def test_linear_svm_reports_support_vectors_margins_and_metrics(self):
        row = self.lab.fit_margin({'C': 1})
        self.assertGreater(row['support_count'], 0)
        self.assertEqual(row['support_count'], len(row['plot']['support']))
        self.assertEqual([line['name'] for line in row['plot']['lines']],
                         ['boundary f=0', 'margin f=+1', 'margin f=-1'])
        self.assertGreater(row['validation']['accuracy'], .8)
        self.assertEqual(len(row['plot']['points']), 80)
        self.assertEqual(row['dataset'], 'Iris petals')

    def test_kernels_on_xor_show_the_linear_limitation(self):
        linear = self.lab.fit_kernel({'dataset': 'xor', 'kernel': 'linear', 'C': 1})
        rbf = self.lab.fit_kernel({'dataset': 'xor', 'kernel': 'rbf', 'C': 1, 'gamma': 1})
        self.assertGreater(rbf['validation']['accuracy'], linear['validation']['accuracy'])
        self.assertGreater(rbf['support_count'], 0)
        self.assertEqual(len(rbf['plot']['support']), rbf['support_count'])
        self.assertEqual(rbf['dataset'], 'XOR quadrants')
        poly = self.lab.fit_kernel({'dataset': 'moons', 'kernel': 'poly', 'C': 1,
                                    'gamma': 1, 'degree': 3})
        self.assertEqual(poly['params']['degree'], 3)

    def test_compare_inspect_and_final_test_are_frozen(self):
        comparison = self.lab.compare()
        self.assertEqual(len(comparison['rows']), 7)
        self.assertEqual(comparison['best'], comparison['rows'][0]['params']['key'])
        self.assertTrue(all(
            comparison['rows'][i]['validation']['accuracy']
            >= comparison['rows'][i + 1]['validation']['accuracy']
            for i in range(len(comparison['rows']) - 1)))
        key = comparison['best']
        detail = self.lab.inspect_candidate({'key': key})
        self.assertEqual(detail['metrics'], detail['row']['validation'])
        self.assertEqual(len(detail['plot']['points']), 480)
        with self.assertRaisesRegex(ValueError, 'Record why'):
            self.lab.final_test({'key': key, 'reason': ''})
        final = self.lab.final_test({'key': key, 'reason': 'Selected using validation.'})
        self.assertEqual(final['key'], key)
        self.assertEqual(sum(final['test']['confusion'][0] + final['test']['confusion'][1]), 120)
        self.assertEqual(final, self.lab.final_test({'key': key, 'reason': 'Already frozen.'}))
        other = next(row['params']['key'] for row in comparison['rows'] if row['params']['key'] != key)
        with self.assertRaisesRegex(ValueError, 'frozen'):
            self.lab.final_test({'key': other, 'reason': 'Different choice.'})
        with self.assertRaisesRegex(ValueError, 'frozen'):
            self.lab.fit_tree({'depth': 2})
        with self.assertRaisesRegex(ValueError, 'frozen'):
            self.lab.compare()

    def test_snippets_get_fresh_arrays_and_never_expose_test_rows(self):
        first = self.lab.execute({'code': 'print(X_train.shape, X_val.shape, "X_test" in globals(), "lab" in globals())\nX_train[:] = 0'})
        self.assertIsNone(first['error'])
        self.assertEqual(first['stdout'], '(360, 2) (120, 2) False False\n')
        second = self.lab.execute({'code': 'print(X_train.sum() != 0, X_iris_train.shape, X_xor_val.shape)'})
        self.assertEqual(second['stdout'], 'True (60, 2) (80, 2)\n')
        failure = self.lab.execute({'code': 'print("before")\nraise ValueError("visible failure")'})
        self.assertEqual(failure['stdout'], 'before\n')
        self.assertIn('ValueError: visible failure', failure['error'])
        self.assertNotIn('X_test', self.lab.execute({'code': 'print(globals().keys())'})['stdout'])

    def test_every_curriculum_starter_runs_in_its_own_experiment(self):
        curriculum = json.loads((FOLDER / 'curriculum.json').read_text())
        self.assertEqual([c['id'] for c in curriculum['chapters']],
                         ['data', 'tree', 'forest', 'boosting', 'margins', 'kernels', 'compare'])
        for chapter in curriculum['chapters']:
            with self.subTest(chapter=chapter['id']):
                result = science.Experiment().execute({'code': chapter['starter']})
                self.assertIsNone(result['error'], result['error'])
                self.assertTrue(result['stdout'])

    def test_notebook_functions_starters_and_figures_match_the_sources(self):
        functions = {n.name: ast.dump(n) for n in ast.parse((FOLDER / 'experiment.py').read_text()).body
                     if isinstance(n, ast.FunctionDef)}
        notebook = json.loads((FOLDER / 'tutorial08.ipynb').read_text())
        seen = set()
        code_cells = []
        for cell in notebook['cells']:
            if cell['cell_type'] != 'code':
                continue
            code_cells.append(''.join(cell['source']))
            for node in ast.parse(''.join(cell['source'])).body:
                if isinstance(node, ast.FunctionDef) and node.name in functions:
                    self.assertEqual(ast.dump(node), functions[node.name])
                    seen.add(node.name)
        self.assertEqual(seen, set(functions))
        self.assertGreaterEqual(sum(1 for cell in notebook['cells'] for output in cell.get('outputs', [])
                                    if 'image/png' in output.get('data', {})), 10)
        curriculum = json.loads((FOLDER / 'curriculum.json').read_text())
        markdown = '\n'.join(''.join(c['source']) for c in notebook['cells']
                             if c['cell_type'] == 'markdown')
        for chapter in curriculum['chapters']:
            self.assertIn(chapter['conceptTitle'], markdown)
            self.assertIn(chapter['pythonTitle'], markdown)
            self.assertIn(chapter['experiment'], markdown)
            self.assertEqual(code_cells.count(chapter['starter']), 1, chapter['id'])
            for symbol, _ in chapter['notation']:
                self.assertFalse(any(ord(char) < 32 for char in symbol), repr(symbol))
        self.assertIn("reason = ''", '\n'.join(code_cells))


if __name__ == '__main__':
    unittest.main()
