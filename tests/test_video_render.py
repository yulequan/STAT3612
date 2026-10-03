"""Offline tests for video narration caching and subtitle timing."""

import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location(
    'video_render', Path(__file__).resolve().parents[1] / 'scripts/video/render.py'
)
render = importlib.util.module_from_spec(spec)
spec.loader.exec_module(render)


class VideoTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name)

    def test_old_caption_capture_is_rejected(self):
        folder = self.folder / 'a-frames'
        folder.mkdir()
        (folder / 'layout.json').write_text('{"#video-caption": null}')
        with self.assertRaises(RuntimeError):
            render.check_external_subtitles(self.folder, [{'id': 'a'}])
        (folder / 'layout.json').write_text('{"#video-focus": {"y": 140}}')
        render.check_external_subtitles(self.folder, [{'id': 'a'}])

    def test_timestamp_rounding(self):
        self.assertEqual(render.timestamp(59.9996), '00:01:00,000')
        self.assertEqual(render.timestamp(3661.025), '01:01:01,025')

    def test_subtitle_offsets(self):
        rows = [{'text': 'Hello', 'time_begin': 100, 'time_end': 900}]
        for name in ['a', 'b']:
            (self.folder / (name + '.subtitles.json')).write_text(json.dumps(rows))
        timeline = [
            {'id': 'a', 'lead': 2, 'duration': 1, 'total': 4},
            {'id': 'b', 'lead': 2, 'duration': 1, 'total': 4},
        ]
        entries = render.subtitle_entries(timeline, self.folder)
        self.assertEqual(entries, [(2.1, 2.9, 'Hello'), (6.1, 6.9, 'Hello')])

    def test_audio_cache_never_regenerates_paid_audio(self):
        audio = self.folder / 'a.mp3'
        audio.write_bytes(b'ID3')
        audio.with_suffix('.json').write_text(json.dumps({'text': 'Hello'}))
        audio.with_suffix('.subtitles.json').write_text('[]')
        with patch.object(render.subprocess, 'run') as request:
            render.prepare_audio(self.folder, [{'id': 'a', 'text': 'Hello'}])
            request.assert_not_called()
            with self.assertRaises(RuntimeError):
                render.prepare_audio(self.folder, [{'id': 'a', 'text': 'Changed'}])
            request.assert_not_called()

    def test_incomplete_cache_does_not_trigger_paid_retry(self):
        (self.folder / 'a.mp3').write_bytes(b'ID3')
        with patch.object(render.subprocess, 'run') as request:
            with self.assertRaises(RuntimeError):
                render.prepare_audio(self.folder, [{'id': 'a', 'text': 'Hello'}])
            request.assert_not_called()


if __name__ == '__main__':
    unittest.main()
