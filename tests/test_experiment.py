"""Scientific regression checks, kept out of the teaching material."""
import json
from pathlib import Path
import sys
import unittest

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src/tutorials/tutorial04'))
from experiment import Experiment, features, gradient, load_data, loss, step, train, transform, trace_step, convolution_map


class ExperimentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.path = ROOT / 'src/tutorials/tutorial04/data/mnist_3v8.npz'
        cls.data = load_data(cls.path)

    def test_split_is_balanced_disjoint_and_preserves_original_test(self):
        d = self.data
        self.assertEqual([len(d[s]) for s in ('train', 'validation', 'test')], [960, 240, 800])
        self.assertEqual(len(set(np.concatenate([d[s] for s in ('train', 'validation', 'test')]))), 2000)
        np.testing.assert_array_equal(d['test'], np.arange(1200, 2000))
        for split in ('train', 'validation', 'test'):
            self.assertEqual(float(d['labels'][d[split]].mean()), .5)

    def test_shift_pads_instead_of_wrapping(self):
        x = np.zeros((2, 28, 28)); x[:, 5, 0] = 1; x[:, 6, -1] = 1
        right = transform(x, 'shift', 1)
        self.assertEqual(right[:, :, 0].sum(), 0)
        self.assertEqual(right[:, 5, 1].sum(), 2)
        self.assertEqual(right.sum(), 2)
        self.assertEqual(transform(x, 'shift', -1).sum(), 2)
        np.testing.assert_array_equal(transform(x, 'shift', 0), x)

    def test_blur_never_mixes_examples(self):
        x = np.zeros((2, 28, 28)); x[1] = 1
        out = transform(x, 'blur')
        np.testing.assert_array_equal(out[0], 0)
        np.testing.assert_allclose(out[1], 1)

    def test_one_step_has_known_direction_and_batch_averaging(self):
        X, y, w = np.array([[2.0]]), np.array([1.0]), np.zeros(1)
        dw, db = gradient(w, 0., X, y)
        np.testing.assert_array_equal(dw, [-1.0]); self.assertEqual(db, -.5)
        w1, b1 = step(w, 0., X, y, .1)
        np.testing.assert_allclose(w1, [.1]); self.assertEqual(b1, .05)
        repeated = step(w, 0., np.repeat(X, 4, axis=0), np.repeat(y, 4), .1)
        np.testing.assert_allclose(repeated[0], w1); self.assertEqual(repeated[1], b1)
        self.assertLess(loss(w1, b1, X, y), loss(w, 0., X, y))

    def test_validation_labels_cannot_influence_parameters(self):
        d = self.data
        X = features(d['images'][d['train']]); y = d['labels'][d['train']]
        Xv = features(d['images'][d['validation']]); yv = d['labels'][d['validation']]
        a = train(X, y, Xv, yv, epochs=2)
        b = train(X, y, Xv, 1 - yv, epochs=2)
        np.testing.assert_array_equal(a['w'], b['w'])
        self.assertEqual(a['b'], b['b'])
        self.assertNotEqual(a['history'][-1]['validation']['accuracy'], b['history'][-1]['validation']['accuracy'])

    def test_web_boundary_and_notebook_baseline_agree(self):
        e = Experiment(self.path)
        result = e.fit({'epochs': 3})
        d = self.data
        reference = train(features(d['images'][d['train']]), d['labels'][d['train']],
                          features(d['images'][d['validation']]), d['labels'][d['validation']], epochs=3)
        np.testing.assert_allclose(result['weights'], reference['w'])
        self.assertEqual(result['history'], reference['history'])
        self.assertEqual(result['updates'], 90)
        json.dumps(result, allow_nan=False)

    def test_augmented_preprocessed_model_evaluates_consistently(self):
        e = Experiment(self.path)
        result = e.fit({'epochs': 2, 'representation': 'edges', 'augment': True})
        self.assertEqual(result['trainingSize'], 1920)
        self.assertEqual(result['updates'], 120)
        self.assertEqual(e.evaluate(result['id'])['accuracy'], result['history'][-1]['validation']['accuracy'])
        self.assertGreaterEqual(e.evaluate(result['id'], split='test', shift=-1)['accuracy'], 0)
        with self.assertRaises(ValueError):
            e.evaluate(result['id'], split='train')

    def test_invalid_settings_are_reported(self):
        e = Experiment(self.path)
        for settings in ({'epochs': 0}, {'batch': 0}, {'lr': float('nan')}):
            with self.assertRaises(ValueError):
                e.fit(settings)

    def test_trace_records_executed_lines_and_matches_the_training_step(self):
        X, y, w = np.array([[2., 0.]]), np.array([1.]), np.zeros(2)
        (w1, b1), trace = trace_step(w, 0., X, y, .1)
        np.testing.assert_allclose(w1, step(w, 0., X, y, .1)[0])
        self.assertEqual([row['line'] for row in trace], list(range(2, 10)))
        self.assertEqual(list(trace[0]['values']), ['z'])
        self.assertNotIn('w_new', trace[4]['values'])
        self.assertEqual(trace[-1]['values']['w_new'], [.1, 0.])
        self.assertEqual(trace[-1]['values']['b_new'], b1)
        self.assertIsNone(sys.gettrace())

    def test_convolution_window_is_the_feature_map_value(self):
        image = np.arange(16.).reshape(4, 4)
        kernel = np.array([[1., 2.], [0., -1.]])
        out = convolution_map(image, kernel)
        self.assertEqual(out.shape, (3, 3))
        for row in range(3):
            for col in range(3):
                self.assertEqual(out[row, col], float((image[row:row+2, col:col+2] * kernel).sum()))
        result = Experiment(self.path).convolution(row=25, col=25)
        self.assertAlmostEqual(result['value'], sum(map(sum, result['products'])))
        self.assertEqual(len(result['output']), 26 * 26)

    def test_student_code_uses_fresh_arrays_and_reports_errors(self):
        e = Experiment(self.path)
        self.assertIsNone(e.execute('X_train[:] = 0')['error'])
        self.assertIn('True', e.execute('print(X_train.max() > 0)')['stdout'])
        failed = e.execute('print("before error")\nraise ValueError("try again")')
        self.assertEqual(failed['stdout'], 'before error\n')
        self.assertEqual(failed['error'], 'ValueError: try again')
        self.assertIn('960', e.execute('print(len(y_train))')['stdout'])


if __name__ == '__main__':
    unittest.main()
