"""Offline checks for the Tutorial 06 slide-video sample. Never calls MiniMax."""

import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    'tutorial06_sample', ROOT / 'scripts/video/tutorial06/build.py'
)
sample = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sample)


class Tutorial06SampleTest(unittest.TestCase):
    def test_focus_boxes_stay_inside_the_pdf_page(self):
        for scene in sample.ALL_SCENES:
            for cue in scene['cues']:
                x0, y0, x1, y1 = cue['box']
                self.assertLess(x0, x1)
                self.assertLess(y0, y1)
                self.assertGreaterEqual(x0, 0)
                self.assertGreaterEqual(y0, 0)
                self.assertLessEqual(x1, sample.PDF_WIDTH)
                self.assertLessEqual(y1, sample.PDF_HEIGHT)

    def test_phrase_time_uses_global_provider_word_offsets(self):
        subtitles = [{
            'text': 'Hello world. Next part.',
            'text_begin': 100,
            'time_begin': 0,
            'time_end': 2000,
            'timestamped_words': [
                {'word': 'Hello', 'word_begin': 100, 'word_end': 105,
                 'time_begin': 0, 'time_end': 400},
                {'word': 'world.', 'word_begin': 106, 'word_end': 112,
                 'time_begin': 400, 'time_end': 900},
                {'word': 'Next', 'word_begin': 113, 'word_end': 117,
                 'time_begin': 1000, 'time_end': 1400},
            ],
        }]
        self.assertAlmostEqual(sample.phrase_time(subtitles, 'Next part'), 1.0)

    def test_srt_offsets_and_sentence_spacing(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary)
            (output / 'audio').mkdir()
            (output / 'audio/01.subtitles.json').write_text(json.dumps([{
                'text': 'Hello.Next sentence.',
                'text_begin': 0,
                'time_begin': 0,
                'time_end': 1000,
                'timestamped_words': [
                    {'word': 'Hello.', 'word_begin': 0, 'word_end': 6,
                     'time_begin': 0, 'time_end': 500},
                    {'word': 'Next', 'word_begin': 6, 'word_end': 10,
                     'time_begin': 500, 'time_end': 700},
                    {'word': 'sentence.', 'word_begin': 11, 'word_end': 20,
                     'time_begin': 700, 'time_end': 1000},
                ],
            }]))
            sample.write_srt(output, {
                'scenes': [{'page': 1, 'offset': 0, 'lead': 0.45, 'duration': 1.0}]
            })
            subtitles = (output / 'tutorial06-sample.srt').read_text()
            self.assertIn('Hello. Next sentence.', subtitles)
            self.assertIn('00:00:00,450 --> 00:00:01,450', subtitles)


    def test_all_34_slides_have_ordered_spoken_cues(self):
        self.assertEqual([scene['page'] for scene in sample.ALL_SCENES], list(range(1, 35)))
        import csv
        import re
        with open(ROOT / 'scripts/video/tutorial06/narration.csv', newline='') as handle:
            scripts = {
                int(row['page']): row['script_en']
                for row in csv.DictReader(handle)
            }
        for scene in sample.ALL_SCENES:
            script = re.sub(r'\s+', ' ', scripts[scene['page']].lower())
            self.assertGreaterEqual(len(scene['cues']), 1)
            for cue in scene['cues']:
                self.assertIn(re.sub(r'\s+', ' ', cue['phrase'].lower()), script)

    def test_page_selection(self):
        self.assertEqual([scene['page'] for scene in sample.select_scenes('1-4')], [1, 2, 3, 4])
        self.assertEqual(len(sample.select_scenes('all')), 34)


if __name__ == '__main__':
    unittest.main()
