"""Generate a small English narration sample using MiniMax's China API.

Usage: python3 scripts/minimax_tts.py [--text-file path] [--output path]
Credentials: environment variables or the gitignored project .env.local.
No third-party dependencies; no automatic retries of billable requests.
"""

import argparse
import json
import os
from pathlib import Path
import sys
import urllib.error
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
SAMPLE = (
    "Let's take one training example and see how it changes the model. "
    "First, we calculate a score. Then, the sigmoid function turns that score "
    "into a probability. Notice that the probability is close to one half. "
    "The model is still uncertain. Now click Next step. "
    "The difference between the prediction and the true label determines "
    "how we update the weights."
)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--text-file', type=Path)
    parser.add_argument('--subtitles', action='store_true', help='Fetch provider sentence timestamps')
    parser.add_argument('--output', type=Path, default=ROOT / '.cache/narration/minimax-sample.mp3')
    args = parser.parse_args()
    env_file = ROOT / '.env.local'
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            if line.strip() and not line.lstrip().startswith('#'):
                key, separator, value = line.partition('=')
                if separator:
                    os.environ.setdefault(key.strip(), value.strip())
    key = os.environ.get('MINIMAX_API_KEY')
    if not key:
        parser.error('Set MINIMAX_API_KEY in the environment or .env.local')
    if args.output.exists():
        parser.error('Output already exists; choose another path to avoid accidental charges')
    text = args.text_file.read_text() if args.text_file else SAMPLE
    if not text.strip() or len(text) >= 10000:
        parser.error('Text must contain 1–9999 characters')
    payload = {
        'model': os.environ.get('MINIMAX_TTS_MODEL', 'speech-2.8-turbo'),
        'text': text,
        'stream': False,
        'subtitle_enable': args.subtitles,
        'subtitle_type': 'word' if args.subtitles else 'sentence',
        'language_boost': 'English',
        'voice_setting': {
            'voice_id': os.environ.get('MINIMAX_TTS_VOICE', 'English_Insightful_Speaker'),
            'speed': 0.95, 'vol': 1, 'pitch': 0,
        },
        'audio_setting': {
            'sample_rate': 32000, 'bitrate': 128000, 'format': 'mp3', 'channel': 1,
        },
    }
    base = os.environ.get('MINIMAX_API_BASE', 'https://api.minimax.cn').rstrip('/')
    if base != 'https://api.minimax.cn':
        parser.error('This script only sends credentials to https://api.minimax.cn')
    request = urllib.request.Request(
        base + '/v1/t2a_v2', data=json.dumps(payload).encode(),
        headers={'Authorization': 'Bearer ' + key, 'Content-Type': 'application/json'},
    )
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            result = json.load(response)
    except urllib.error.HTTPError as error:
        print(f'HTTP {error.code}; check credentials, quota, and API availability.', file=sys.stderr)
        return 1
    except (urllib.error.URLError, TimeoutError, ValueError):
        print('Request failed or returned invalid JSON; not retried automatically.', file=sys.stderr)
        return 1
    status = result.get('base_resp', {})
    if status.get('status_code') != 0:
        print(f"MiniMax error {status.get('status_code')}: {status.get('status_msg')}", file=sys.stderr)
        return 1
    audio = result.get('data', {}).get('audio')
    if not audio:
        print('MiniMax returned no audio.', file=sys.stderr)
        return 1
    try:
        decoded = bytes.fromhex(audio)
    except ValueError:
        print('MiniMax returned invalid audio encoding.', file=sys.stderr)
        return 1
    if not decoded:
        print('MiniMax returned empty audio.', file=sys.stderr)
        return 1
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(decoded)
    metadata = {
        'model': payload['model'], 'voice': payload['voice_setting']['voice_id'],
        'text': text, 'extra_info': result.get('extra_info', {}),
        'trace_id': result.get('trace_id'),
    }
    args.output.with_suffix('.json').write_text(json.dumps(metadata, indent=2))
    subtitle_url = result.get('data', {}).get('subtitle_file')
    if args.subtitles and subtitle_url:
        # This is a signed public download: never forward the API Authorization header.
        if not subtitle_url.startswith('https://'):
            print('Unsafe subtitle URL; audio saved, subtitles not downloaded.', file=sys.stderr)
            return 1
        try:
            with urllib.request.urlopen(subtitle_url, timeout=30) as response:
                subtitles = json.load(response)
            args.output.with_suffix('.subtitles.json').write_text(json.dumps(subtitles, indent=2))
        except (urllib.error.URLError, TimeoutError, ValueError):
            print('Audio saved; subtitle download failed. Do not regenerate blindly.', file=sys.stderr)
            return 1
    elif args.subtitles:
        print('Audio saved; API returned no subtitle file.', file=sys.stderr)
        return 1
    print(f'Audio: {args.output}')
    print(json.dumps(metadata['extra_info'], indent=2))
    return 0


if __name__ == '__main__':
    sys.exit(main())
