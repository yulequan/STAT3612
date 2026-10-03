"""Offline checks for the TTS utility; never load real credentials or call the API."""

import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location(
    'minimax_tts', Path(__file__).resolve().parents[1] / 'scripts/minimax_tts.py'
)
tts = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tts)


class TtsTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.output = self.root / 'audio/sample.mp3'
        self.addCleanup(patch.stopall)
        patch.object(tts, 'ROOT', self.root).start()
        patch.dict(os.environ, {}, clear=True).start()
        patch.object(tts.sys, 'argv', ['minimax_tts', '--output', str(self.output)]).start()
        self.stdout = patch.object(tts.sys, 'stdout', io.StringIO()).start()
        self.stderr = patch.object(tts.sys, 'stderr', io.StringIO()).start()
        self.network = patch.object(tts.urllib.request, 'urlopen').start()

    def response(self, result):
        self.network.return_value = contextlib.nullcontext(io.StringIO(json.dumps(result)))

    def test_local_config_and_success(self):
        (self.root / '.env.local').write_text('MINIMAX_API_KEY=local-test-key\n')
        self.response({
            'base_resp': {'status_code': 0}, 'data': {'audio': '494433'},
            'extra_info': {'audio_length': 1000},
        })
        self.assertEqual(tts.main(), 0)
        self.assertEqual(self.output.read_bytes(), b'ID3')
        request = self.network.call_args.args[0]
        self.assertEqual(request.full_url, 'https://api.minimax.cn/v1/t2a_v2')
        payload = json.loads(request.data)
        self.assertEqual(payload['model'], 'speech-2.8-turbo')
        self.assertEqual(payload['language_boost'], 'English')
        metadata = self.output.with_suffix('.json').read_text()
        self.assertNotIn('local-test-key', metadata + self.stdout.getvalue())

    def test_environment_overrides_file(self):
        (self.root / '.env.local').write_text('MINIMAX_API_KEY=local-test-key\n')
        os.environ['MINIMAX_API_KEY'] = 'environment-test-key'
        self.response({'base_resp': {'status_code': 7, 'status_msg': 'quota exhausted'}})
        self.assertEqual(tts.main(), 1)
        request = self.network.call_args.args[0]
        self.assertEqual(request.get_header('Authorization'), 'Bearer environment-test-key')
        self.assertFalse(self.output.exists())
        self.network.assert_called_once()

    def test_missing_key(self):
        with self.assertRaises(SystemExit):
            tts.main()
        self.network.assert_not_called()

    def test_existing_output_never_calls_api(self):
        os.environ['MINIMAX_API_KEY'] = 'test-key'
        self.output.parent.mkdir()
        self.output.write_bytes(b'existing')
        with self.assertRaises(SystemExit):
            tts.main()
        self.assertEqual(self.output.read_bytes(), b'existing')
        self.network.assert_not_called()

    def test_untrusted_endpoint_never_receives_key(self):
        os.environ.update(MINIMAX_API_KEY='test-key', MINIMAX_API_BASE='https://example.org')
        with self.assertRaises(SystemExit):
            tts.main()
        self.network.assert_not_called()

    def test_invalid_audio_is_not_saved(self):
        os.environ['MINIMAX_API_KEY'] = 'test-key'
        self.response({'base_resp': {'status_code': 0}, 'data': {'audio': 'not-hex'}})
        self.assertEqual(tts.main(), 1)
        self.assertFalse(self.output.exists())

    def test_subtitles_download_without_credentials(self):
        os.environ['MINIMAX_API_KEY'] = 'test-key'
        response = {
            'base_resp': {'status_code': 0},
            'data': {'audio': '494433', 'subtitle_file': 'https://example.org/signed-subtitles'},
        }
        self.network.side_effect = [
            contextlib.nullcontext(io.StringIO(json.dumps(response))),
            contextlib.nullcontext(io.StringIO('[{"text":"Hello", "time_begin":0, "time_end":1000}]')),
        ]
        with patch.object(tts.sys, 'argv', ['minimax_tts', '--output', str(self.output), '--subtitles']):
            self.assertEqual(tts.main(), 0)
        self.assertEqual(self.network.call_args_list[1].args, ('https://example.org/signed-subtitles',))
        self.assertTrue(self.output.with_suffix('.subtitles.json').exists())

    def test_missing_subtitle_keeps_audio_without_retry(self):
        os.environ['MINIMAX_API_KEY'] = 'test-key'
        self.response({'base_resp': {'status_code': 0}, 'data': {'audio': '494433'}})
        with patch.object(tts.sys, 'argv', ['minimax_tts', '--output', str(self.output), '--subtitles']):
            self.assertEqual(tts.main(), 1)
        self.assertTrue(self.output.exists())
        self.network.assert_called_once()

    def test_length_limit(self):
        os.environ['MINIMAX_API_KEY'] = 'test-key'
        text = self.root / 'long.txt'
        text.write_text('a' * 10000)
        with patch.object(tts.sys, 'argv', ['minimax_tts', '--text-file', str(text)]):
            with self.assertRaises(SystemExit):
                tts.main()
        self.network.assert_not_called()


if __name__ == '__main__':
    unittest.main()
