"""Regression checks for the spam lesson's scientific and evaluation contracts."""
import ast
import hashlib
import importlib.util
import json
import sys
from pathlib import Path
import tempfile
import unittest
import xml.etree.ElementTree as ET
from unittest.mock import patch

import numpy as np
from scipy import sparse

ROOT = Path(__file__).resolve().parents[1]
FOLDER = ROOT / 'src/tutorials/tutorial05'
spec = importlib.util.spec_from_file_location('spam_experiment', FOLDER / 'experiment.py')
science = importlib.util.module_from_spec(spec)
spec.loader.exec_module(science)


class SpamExperimentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.path = FOLDER / 'data/SMSSpamCollection.txt'
        cls.lab = science.Experiment(cls.path)

    def test_original_source_checksum_audit_and_disjoint_identity_splits(self):
        self.assertEqual(hashlib.sha256(self.path.read_bytes()).hexdigest(),
                         '7d039a24a6083ed9ef0f806ebad56bbb976e3aeb8de05669173bfdc4996c239d')
        result = self.lab.initialize()
        self.assertEqual([result[k] for k in ('raw', 'excluded', 'duplicates', 'unique')], [5574, 0, 415, 5159])
        self.assertEqual([result['counts'][k]['total'] for k in ('train', 'validation', 'test')], [3095, 1032, 1032])
        identities = [{ ' '.join(s.lower().split()) for s in self.lab.messages[ix] }
                      for ix in self.lab.splits.values()]
        for i in range(3):
            for j in range(i + 1, 3):
                self.assertFalse(identities[i] & identities[j])
        self.assertEqual(sum(map(len, identities)), len(self.lab.messages))
        for ix in self.lab.splits.values():
            self.assertAlmostEqual(self.lab.labels[ix].mean(), self.lab.labels.mean(), delta=.002)
        again = science.Experiment(self.path)
        for split in self.lab.splits:
            np.testing.assert_array_equal(self.lab.splits[split], again.splits[split])

    def test_conflicting_normalized_identity_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'messages.txt'
            path.write_text('ham\tAre you FREE?\nspam\t are   you free? \n')
            with self.assertRaisesRegex(ValueError, 'Conflicting labels'):
                science.load_data(path)

    def test_threshold_confusion_conventions(self):
        result = science.metrics(np.array([0, 0, 1, 1]), [.1, .6, .4, .9], .5)
        self.assertEqual(result['confusion'], [[1, 1], [1, 1]])
        self.assertEqual(result['precision'], .5)
        self.assertEqual(result['recall'], .5)
        higher = science.metrics(np.array([0, 0, 1, 1]), [.1, .6, .4, .9], .8)
        self.assertEqual(higher['confusion'], [[2, 0], [1, 1]])
        baseline = science.metrics(self.lab.y_val, np.zeros(len(self.lab.y_val)))
        self.assertEqual(baseline['recall'], 0)
        self.assertAlmostEqual(baseline['average_precision'], self.lab.y_val.mean())

    def test_slider_summaries_match_actual_python_decisions(self):
        lab = science.Experiment(self.path)
        row = lab.fit({})
        self.assertEqual(len(row['thresholds']), 101)
        for i in [0, 20, 50, 80, 100]:
            actual = lab.evaluate({'id': row['id'], 'threshold': i / 100})['metrics']
            for key, value in row['thresholds'][i].items():
                self.assertEqual(value, actual[key])

    def test_text_pipelines_remain_sparse_and_unknown_words_do_not_change_columns(self):
        for representation in ('count', 'tfidf'):
            model = science.build_model(representation=representation)
            model.fit(self.lab.X_train, self.lab.y_train)
            vectorizer = model.named_steps['vectorizer']
            vector = model[:-1].transform(['totallyunseenword3612'])
            self.assertTrue(sparse.issparse(vector))
            self.assertEqual(vector.shape[1], len(vectorizer.vocabulary_))
            self.assertEqual(vector.nnz, 0)
            self.assertNotIn('totallyunseenword3612', vectorizer.vocabulary_)
            self.assertLessEqual(vector.shape[1], 2500)
            if representation == 'tfidf':
                count = science.text_vectorizer('count', vocabulary=vectorizer.vocabulary_).fit_transform(self.lab.X_train)
                df = np.asarray((count > 0).sum(axis=0)).ravel()
                np.testing.assert_allclose(vectorizer.idf_, np.log((1 + len(self.lab.X_train)) / (1 + df)) + 1)

    def test_nltk_tokenization_is_shared_with_vectorizers(self):
        text = 'Congratulations! Claim your FREE prize now!'
        result = self.lab.tokenize({'text': text})
        self.assertEqual(result['raw_tokens'], ['congratulations', '!', 'claim', 'your', 'free', 'prize', 'now', '!'])
        self.assertEqual(result['tokens'], ['congratulations', 'claim', 'your', 'free', 'prize', 'now'])
        vectorizer = science.text_vectorizer()
        self.assertEqual(vectorizer.build_analyzer()(text), result['tokens'])

    def test_worked_tfidf_values_df_counts_and_zero_rows_match_sklearn(self):
        documents = ['claim your prize', 'check your timetable', 'send your notes']
        result = self.lab.vectorize({'documents': documents, 'representation': 'tfidf', 'text': 'unknown3612'})
        your, prize = map(result['vocabulary'].index, ['your', 'prize'])
        self.assertEqual([result['df'][your], result['df'][prize]], [3, 1])
        self.assertAlmostEqual(result['idf'][your], 1)
        self.assertAlmostEqual(result['idf'][prize], np.log(2) + 1)
        self.assertAlmostEqual(result['norms'][0], np.sqrt(2 * (1 + np.log(2)) ** 2 + 1))
        manual = np.asarray(result['weighted']) / np.asarray(result['norms'])[:, None]
        np.testing.assert_allclose(manual, result['matrix'])
        self.assertFalse(np.any(result['transformed']))
        repeated = self.lab.vectorize({'documents': ['prize prize', 'prize'], 'representation': 'tfidf'})
        self.assertEqual(repeated['df'], [2])
        self.assertEqual(repeated['counts'], [[2], [1]])

    def test_naive_bayes_hand_calculation_and_real_evidence(self):
        messages = ['meet after class', 'meet for lunch', 'claim your prize', 'win your prize']
        vectorizer = science.text_vectorizer()
        matrix = vectorizer.fit_transform(messages)
        classifier = science.MultinomialNB(alpha=1).fit(matrix, [0, 0, 1, 1])
        self.assertEqual(matrix.shape[1], 9)
        np.testing.assert_array_equal(classifier.feature_count_.sum(axis=1), [6, 6])
        self.assertAlmostEqual(classifier.predict_proba(vectorizer.transform(['claim prize']))[0, 1], 6 / 7)
        lab = science.Experiment(self.path)
        for representation in ('count', 'tfidf'):
            row = lab.fit({'kind': 'nb', 'representation': representation, 'alpha': .5})
            model = lab.runs[row['id']]['model']
            result = lab.explain({'id': row['id'], 'text': 'Claim your free prize now!'})
            log_p = model.predict_log_proba([result['text']])[0]
            self.assertAlmostEqual(result['score'], log_p[1] - log_p[0])
            self.assertAlmostEqual(result['bias'] + sum(item['contribution'] for item in result['evidence']), result['score'])
            self.assertAlmostEqual(result['probability'], model.predict_proba([result['text']])[0, 1])
            empty = lab.explain({'id': row['id'], 'text': 'unknown3612'})
            self.assertEqual(empty['evidence'], [])
            self.assertAlmostEqual(empty['probability'], lab.y_train.mean())
        with self.assertRaisesRegex(ValueError, 'nonnegative'):
            science.build_model(kind='nb', representation='numeric')

    def test_core_starters_work_without_running_extensions(self):
        curriculum = json.loads((FOLDER / 'curriculum.json').read_text())
        lab = science.Experiment(self.path)
        for chapter in curriculum['chapters']:
            if not chapter['extension']:
                with self.subTest(chapter=chapter['id']):
                    # Other tutorials also have an experiment.py; mirror this
                    # lesson's isolated worker/module when importing helpers.
                    with patch.dict(sys.modules, {'experiment': science}):
                        result = lab.execute({'code': chapter['starter']})
                    self.assertIsNone(result['error'], result['error'])
                    if chapter['focus']:
                        lines = chapter['starter'].splitlines()
                        excerpt = '\n'.join(line for start, end in chapter['focus']['ranges'] for line in lines[start:end])
                        with patch.dict(sys.modules, {'experiment': science}):
                            focused = lab.execute({'code': excerpt})
                        self.assertIsNone(focused['error'], focused['error'])
        self.assertEqual(lab.runs, {})  # Snippet examples do not register UI candidates.

    def test_cv_refits_every_pipeline_without_heldout_inputs(self):
        messages = np.array([f'class{label} shared uniquetoken{i}' for i in range(30) for label in [0, 1]])
        labels = np.tile([0, 1], 30)
        actual_builder = science.build_model
        fitted = []
        def builder(**kwargs):
            model = actual_builder(**kwargs)
            original_fit = model.fit
            def fit(X, y):
                result = original_fit(X, y)
                vocabulary = set(model.named_steps['vectorizer'].vocabulary_)
                self.assertEqual(len(X), 48)
                seen_tokens = {t for s in X for t in science.tokens(s)}
                self.assertTrue(vocabulary <= seen_tokens)
                absent = {t for s in messages for t in science.tokens(s)} - seen_tokens
                self.assertFalse(vocabulary & absent)
                fitted.append(model)
                return result
            model.fit = fit
            return model
        with patch.object(science, 'build_model', side_effect=builder):
            result = science.cross_validate(messages, labels, values=(.1, 1.))
        self.assertEqual(len(fitted), 10)
        self.assertEqual(len({id(model) for model in fitted}), 10)
        self.assertEqual([len(row['folds']) for row in result], [5, 5])

    def test_contributions_equal_actual_decision_function(self):
        lab = science.Experiment(self.path)
        for kind, representation in [('logistic', 'count'), ('logistic', 'tfidf'), ('logistic', 'numeric'), ('lda', 'numeric'), ('gam', 'numeric')]:
            row = lab.fit({'kind': kind, 'representation': representation})
            text = 'Congratulations! Claim £1000 at https://example.org now!!!'
            explanation = lab.explain({'id': row['id'], 'text': text})
            model = lab.runs[row['id']]['model']
            score = model.decision_function([text])[0]
            self.assertAlmostEqual(explanation['score'], score, places=9)
            self.assertAlmostEqual(explanation['bias'] + sum(r['value'] for r in explanation['contributions']), score, places=9)
            self.assertAlmostEqual(explanation['probability'], 1 / (1 + np.exp(-score)), places=9)

    def test_knn_vote_matches_neighbor_labels(self):
        lab = science.Experiment(self.path)
        for representation in ('numeric', 'tfidf'):
            row = lab.fit({'kind': 'knn', 'representation': representation, 'k': 5})
            result = lab.explain({'id': row['id'], 'text': 'Claim a prize now'})
            self.assertEqual(len(result['neighbors']), 5)
            self.assertEqual(result['probability'], sum(n['label'] for n in result['neighbors']) / 5)
            self.assertEqual([n['distance'] for n in result['neighbors']], sorted(n['distance'] for n in result['neighbors']))

    def test_additive_curves_center_at_reference_and_have_no_interactions(self):
        lab = science.Experiment(self.path)
        result = lab.gam({})
        model = lab.runs[result['run']['id']]['model']
        raw = np.asarray(result['reference']).reshape(1, -1)
        def score(values):
            return model[1:].decision_function(values)[0]
        base = score(raw)
        a = raw.copy(); a[0, 0] += 20
        b = raw.copy(); b[0, 3] += 3
        both = a.copy(); both[0, 3] = b[0, 3]
        self.assertAlmostEqual(score(both) - base, (score(a) - base) + (score(b) - base), places=10)
        for j, curve in enumerate(result['curves']):
            for i in [0, 20, 59]:
                values = raw.copy(); values[0, j] = curve['x'][i]
                self.assertAlmostEqual(curve['effect'][i], score(values) - base, places=10)

    def test_test_set_not_used_during_fitting_and_decision_freezes(self):
        a, b = science.Experiment(self.path), science.Experiment(self.path)
        b.labels[b.splits['test']] = 1 - b.labels[b.splits['test']]
        ra, rb = a.fit({}), b.fit({})
        np.testing.assert_allclose(a.runs[ra['id']]['model'].named_steps['classifier'].coef_, b.runs[rb['id']]['model'].named_steps['classifier'].coef_)
        self.assertEqual(ra['validation'], rb['validation'])
        with self.assertRaisesRegex(ValueError, 'Record why'):
            a.final_test({'id': ra['id'], 'reason': ''})
        final = a.final_test({'id': ra['id'], 'threshold': .7, 'reason': 'Validation supports fewer ham false alarms.'})
        self.assertEqual(final, a.final_test({'id': ra['id'], 'threshold': .7, 'reason': 'Already frozen.'}))
        with self.assertRaisesRegex(ValueError, 'frozen'):
            a.final_test({'id': ra['id'], 'threshold': .5, 'reason': 'Different threshold'})
        with self.assertRaisesRegex(ValueError, 'Final test'):
            a.fit({})
        with self.assertRaises(ValueError):
            a.cv({})
        json.dumps(final, allow_nan=False)

    def test_snippets_are_fresh_report_errors_and_omit_test_arrays(self):
        result = self.lab.execute({'code': 'print("X_test" in globals(), "y_test" in globals())\nX_train[:] = "changed"'})
        self.assertEqual(result['stdout'], 'False False\n')
        result = self.lab.execute({'code': 'print(X_train[0] != "changed")\nraise ValueError("visible failure")'})
        self.assertIn('True', result['stdout'])
        self.assertIn('ValueError: visible failure', result['error'])

    def test_notebook_functions_and_chapters_match_sources(self):
        functions = {n.name: ast.dump(n) for n in ast.parse((FOLDER / 'experiment.py').read_text()).body if isinstance(n, ast.FunctionDef)}
        notebook = json.loads((FOLDER / 'tutorial05.ipynb').read_text())
        seen = set()
        for cell in notebook['cells']:
            if cell['cell_type'] != 'code':
                continue
            for node in ast.parse(''.join(cell['source'])).body:
                if isinstance(node, ast.FunctionDef) and node.name in functions:
                    self.assertEqual(ast.dump(node), functions[node.name])
                    seen.add(node.name)
        self.assertEqual(seen, set(functions))
        curriculum = json.loads((FOLDER / 'curriculum.json').read_text())
        markdown = '\n'.join(''.join(c['source']) for c in notebook['cells'] if c['cell_type'] == 'markdown')
        code_cells = [''.join(c['source']) for c in notebook['cells'] if c['cell_type'] == 'code']
        for c in curriculum['chapters']:
            for symbol, _ in c['notation']:
                self.assertFalse(any(ord(char) < 32 for char in symbol), repr(symbol))
            self.assertIn(c['conceptTitle'], markdown)
            self.assertIn(c['pythonTitle'], markdown)
            self.assertIn(c['experiment'], markdown)
            self.assertEqual(code_cells.count(c['starter']), 1, c['id'])
            if c['focus']:
                lines = c['starter'].splitlines()
                excerpt = '\n'.join(line for start, end in c['focus']['ranges'] for line in lines[start:end])
                self.assertIn('```python\n' + excerpt + '\n```', markdown)

    def test_notebook_diagrams_use_actual_audit_and_code_typography(self):
        notebook = json.loads((FOLDER / 'tutorial05.ipynb').read_text())
        figures = [ET.fromstring(''.join(output['data']['image/svg+xml']))
                   for cell in notebook['cells'] for output in cell.get('outputs', [])
                   if 'image/svg+xml' in output.get('data', {})]
        ns = {'svg': 'http://www.w3.org/2000/svg'}
        by_title = {f.find('svg:title', ns).text: f for f in figures}
        curriculum = json.loads((FOLDER / 'curriculum.json').read_text())
        for chapter in curriculum['chapters']:
            if chapter['flow']:
                self.assertIn(chapter['flow']['title'], by_title)
        data = by_title['Raw messages → deduplication → data splits']
        text = ' '.join(data.itertext())
        initial = self.lab.initialize()
        for value in [initial['raw'], initial['duplicates'], initial['unique'],
                      *(split['total'] for split in initial['counts'].values())]:
            self.assertIn(f'{value:,}', text)
        self.assertNotRegex(text, r'\{(?:counts\.|raw|unique|duplicates)')
        tokenization = by_title['Follow one message through preprocessing']
        code = tokenization.findall(".//svg:text[@class='code']", ns)
        literal = ' '.join(node.text for node in code)
        self.assertIn('Congratulations! Claim your FREE prize now!', literal)
        self.assertIn('["congratulations", "!", "claim",', literal)
        self.assertIn('font-family:Consolas,monospace', ''.join(tokenization.itertext()))


if __name__ == '__main__':
    unittest.main()
