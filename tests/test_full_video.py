"""Offline checks for the complete video pipeline. Never call the paid API."""

import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

VIDEO = Path(__file__).resolve().parents[1] / 'scripts/video'
sys.path.insert(0, str(VIDEO))
import full
sys.path.pop(0)


class FullVideoTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name)
        (self.folder / 'audio').mkdir()

    def cache(self, text='Hello', words=None):
        key = full.audio_key(text)
        audio = self.folder / 'audio' / (key + '.mp3')
        audio.write_bytes(b'ID3')
        audio.with_suffix('.json').write_text(json.dumps({
            'text': text, 'model': 'speech-2.8-turbo', 'voice': 'English_Insightful_Speaker',
            'extra_info': {'audio_length': 1000},
        }))
        audio.with_suffix('.subtitles.json').write_text(json.dumps([{
            'text': text, 'time_begin': 0, 'time_end': 1000,
            'timestamped_words': words,
        }]))
        return audio

    def capture(self, id='hello', burned=False):
        folder = self.folder / (id + '-frames')
        folder.mkdir()
        (folder / 'capture.json').write_text(json.dumps({
            'frames': [{'file': 'final.jpg', 'time': 1.2}], 'actionSeconds': 1.2,
            'method': 'Chromium compositor screencast', 'captionsBurnedIn': burned,
            'presentationVersion': full.PRESENTATION_VERSION,
            'layout': {'pointerHidden': True, 'ripples': 0},
        }))

    def test_dedupe_and_cache_no_paid_calls(self):
        self.cache()
        with patch.object(full.subprocess, 'run') as paid:
            generated = full.generate_audio(self.folder, [{'text': 'Hello'}, {'text': 'Hello'}], 2)
            self.assertEqual(generated, [])
            paid.assert_not_called()

    def test_incomplete_cache_is_not_regenerated(self):
        audio = self.cache()
        audio.with_suffix('.subtitles.json').unlink()
        with self.assertRaises(RuntimeError):
            full.load_cache(audio, 'Hello')

    def test_configuration_changes_are_rejected(self):
        audio = self.cache()
        with self.assertRaises(RuntimeError):
            full.load_cache(audio, 'Other text')

    def test_reuse_only_missing_audio_never_calls_api(self):
        with patch.object(full.subprocess, 'run') as paid:
            with self.assertRaises(RuntimeError):
                full.generate_audio(self.folder, [{'text': 'Missing'}], 3, reuse_only=True)
            paid.assert_not_called()

    def test_reuse_only_uses_existing_audio_without_api(self):
        self.cache()
        with patch.object(full.subprocess, 'run') as paid:
            self.assertEqual(full.generate_audio(self.folder, [{'text': 'Hello'}], 3, reuse_only=True), [])
            paid.assert_not_called()

    def test_parked_cursor_is_rejected(self):
        self.cache(); self.capture()
        path = self.folder / 'hello-frames/capture.json'
        metadata = json.loads(path.read_text())
        metadata['layout']['pointerHidden'] = False
        path.write_text(json.dumps(metadata))
        with self.assertRaises(RuntimeError):
            full.timeline_for(self.folder, [{'id': 'hello', 'text': 'Hello'}])

    def test_old_visual_capture_is_rejected(self):
        self.cache(); self.capture()
        path = self.folder / 'hello-frames/capture.json'
        metadata = json.loads(path.read_text())
        metadata['presentationVersion'] = 'old'
        path.write_text(json.dumps(metadata))
        with self.assertRaises(RuntimeError):
            full.timeline_for(self.folder, [{'id': 'hello', 'text': 'Hello'}])

    def test_timeline_quantizes_to_frames(self):
        self.cache(); self.capture()
        timeline = full.timeline_for(self.folder, [{'id': 'hello', 'text': 'Hello', 'hasAction': True}])
        self.assertAlmostEqual(timeline[0]['total'] * 60, round(timeline[0]['total'] * 60))
        self.assertGreater(timeline[0]['total'], 1.2)

    def test_burned_in_capture_rejected(self):
        self.cache(); self.capture(burned=True)
        with self.assertRaises(RuntimeError):
            full.timeline_for(self.folder, [{'id': 'hello', 'text': 'Hello'}])

    def test_word_cues_use_provider_times_and_preserve_text(self):
        text = 'A natural explanation with carefully aligned words. ' * 4
        words = []
        position = 0
        for number, word in enumerate(text.split(' ')):
            if not word: continue
            words.append({'word': word, 'word_begin': position, 'word_end': position + len(word),
                          'time_begin': number * 100, 'time_end': number * 100 + 75})
            position += len(word) + 1
        cues = full.subtitle_cues({'text': text, 'text_begin': 0, 'timestamped_words': words})
        self.assertEqual(' '.join(c[2] for c in cues), text.strip())
        self.assertGreater(len(cues), 1)
        valid_begin = {w['time_begin'] / 1000 for w in words}
        valid_end = {w['time_end'] / 1000 for w in words}
        self.assertTrue(all(c[0] in valid_begin and c[1] in valid_end for c in cues))

    def test_old_sentence_only_cache_never_gets_fake_word_times(self):
        cues = full.subtitle_cues({'text': 'A whole sentence.', 'time_begin': 20, 'time_end': 950})
        self.assertEqual(cues, [(.02, .95, 'A whole sentence.')])

    def test_source_changes_and_missing_content_are_rejected(self):
        coverage = {
            'sourceHashes': {'scripts/video/full.py': 'incorrect-hash'},
            'missingVerbatim': [], 'chapters': [key for key, _ in full.CHAPTERS],
        }
        with self.assertRaises(RuntimeError):
            full.verify_sources(coverage)
        coverage['sourceHashes'] = {}
        coverage['missingVerbatim'] = [{'text': 'Uncovered teaching block'}]
        with self.assertRaises(RuntimeError):
            full.verify_sources(coverage)

    def test_encode_is_cached_and_has_no_subtitle_filter(self):
        self.cache(); self.capture(); (self.folder / 'clips').mkdir()
        scene = full.timeline_for(self.folder, [{'id': 'hello', 'text': 'Hello', 'hasAction': False}])[0]
        calls = []
        def fake_encode(ffmpeg, arguments):
            calls.append(arguments)
            Path(arguments[-1]).write_bytes(b'video')
        with patch.object(full, 'encode', side_effect=fake_encode):
            full.encode_scene('ffmpeg', self.folder, scene)
            full.encode_scene('ffmpeg', self.folder, {**scene, 'offset': 500})
        self.assertEqual(len(calls), 1)
        self.assertNotIn('subtitles', str(calls[0]))
        self.assertIn('fps=60,format=yuv420p', calls[0])
        self.assertIn('option framerate 60', (self.folder / 'hello-frames/frames.txt').read_text())


if __name__ == '__main__':
    unittest.main()
