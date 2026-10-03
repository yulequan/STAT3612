"""Complete tutorial04 production: current-site capture, rate-limited parallel TTS,
parallel encoding, external subtitles, chapter videos and YouTube chapter markers.

python3 scripts/video/full.py [--skip-capture] [--audio-workers 3] [--encode-workers 3]
Requires npm dependencies, Chrome, and FFmpeg (see scripts/NARRATION.md).
"""

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import json
import math
from pathlib import Path
import subprocess
import sys
import threading
import time
import textwrap

from render import ROOT, ffmpeg_binary, encode, timestamp

FOLDER = ROOT / '.cache/video/tutorial04-complete'
PRESENTATION_VERSION = 'full-page-v3'
CHAPTERS = [
    ('overview', '00 Overview'), ('data', '01 Meet the data'),
    ('prepare', '02 Prepare the inputs'), ('model', '03 Make a prediction'),
    ('loss', '04 Define the objective'), ('update', '05 Take one step'),
    ('train', '06 Train the classifier'), ('evaluate', '07 Evaluate and improve'),
    ('beyond', '08 Beyond a linear model'),
]


class RateGate:
    """At most one new request per 3.4s (~17.6 RPM; provider default is 20)."""
    def __init__(self, interval=3.4):
        self.interval = interval
        self.lock = threading.Lock()
        self.next_start = 0

    def wait(self):
        with self.lock:
            now = time.monotonic()
            delay = max(0, self.next_start - now)
            self.next_start = max(now, self.next_start) + self.interval
        if delay:
            time.sleep(delay)


def audio_key(text):
    # Include explicit voice/model/speed; shell overrides are not permitted for full production.
    return hashlib.sha256(('speech-2.8-turbo|English_Insightful_Speaker|0.95|' + text).encode()).hexdigest()[:20]


def load_cache(audio, text):
    if not audio.exists():
        return None
    sidecar, subtitles = audio.with_suffix('.json'), audio.with_suffix('.subtitles.json')
    if not sidecar.exists() or not subtitles.exists():
        raise RuntimeError(f'Incomplete paid audio cache: {audio}. Recover files before retrying.')
    meta = json.loads(sidecar.read_text())
    if meta['text'] != text or meta['model'] != 'speech-2.8-turbo' or meta['voice'] != 'English_Insightful_Speaker':
        raise RuntimeError('Audio cache configuration mismatch')
    if not json.loads(subtitles.read_text()):
        raise RuntimeError('Empty provider subtitles')
    return meta


def generate_audio(folder, scenes, workers, reuse_only=False):
    import os
    env = {**os.environ, 'MINIMAX_TTS_MODEL': 'speech-2.8-turbo',
           'MINIMAX_TTS_VOICE': 'English_Insightful_Speaker'}
    audio_dir = folder / 'audio'
    audio_dir.mkdir(exist_ok=True)
    unique = {audio_key(scene['text']): scene['text'] for scene in scenes}
    if reuse_only:
        for key, text in unique.items():
            if not load_cache(audio_dir / (key + '.mp3'), text):
                raise RuntimeError(f'Audio-only reuse requested but cache is missing: {key}')
        print(f'Reused all {len(unique)} audio files; TTS disabled.', flush=True)
        return []
    gate = RateGate()
    generated = []

    def task(item):
        key, text = item
        audio = audio_dir / (key + '.mp3')
        if load_cache(audio, text):
            return key, False
        gate.wait()
        source = audio.with_suffix('.txt'); source.write_text(text)
        result = subprocess.run([
            sys.executable, str(ROOT / 'scripts/minimax_tts.py'), '--subtitles',
            '--text-file', str(source), '--output', str(audio),
        ], cwd=ROOT, env=env, capture_output=True, text=True)
        if result.returncode:
            # No paid retries. All in-flight tasks finish and save their successful results.
            raise RuntimeError(f'TTS failed for {key}: {result.stderr.strip()}')
        load_cache(audio, text)
        return key, True

    failed = []
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(task, item): item[0] for item in unique.items()}
        for number, future in enumerate(as_completed(futures), 1):
            try:
                key, fresh = future.result()
                if fresh: generated.append(key)
                print(f'Audio {number}/{len(unique)}: {key} ({"generated" if fresh else "cached"})', flush=True)
            except Exception as error:
                failed.append(str(error))
                # Cancel queued work, but do not interrupt already-billable in-flight requests.
                for other in futures: other.cancel()
                break
    if failed:
        raise RuntimeError('\n'.join(failed))
    return generated


def timeline_for(folder, scenes):
    result = []
    offset = 0
    for scene in scenes:
        key = audio_key(scene['text'])
        audio = folder / 'audio' / (key + '.mp3')
        meta = load_cache(audio, scene['text'])
        duration = meta['extra_info']['audio_length'] / 1000
        capture = json.loads((folder / (scene['id'] + '-frames/capture.json')).read_text())
        if capture.get('captionsBurnedIn') is not False or capture.get('method') != 'Chromium compositor screencast':
            raise RuntimeError('Old capture method / subtitle layer detected')
        if capture.get('presentationVersion') != PRESENTATION_VERSION:
            raise RuntimeError('Outdated presentation capture; recapture with current framing/cursor rules')
        if not capture.get('layout', {}).get('pointerHidden') or capture['layout'].get('ripples'):
            raise RuntimeError('Final hold contains a cursor or click overlay')
        action = capture['actionSeconds']
        dynamic = scene.get('hasAction', True)
        lead = .35 if dynamic else .15
        total = math.ceil(max(lead + duration + .4, action + .4 if dynamic else 0) * 60) / 60
        # Quantise scene length to whole video frames, so SRT offsets match concatenation.
        item = {**scene, 'audio_key': key, 'duration': duration, 'total': total,
                'lead': lead, 'offset': offset, 'actionSeconds': action}
        result.append(item)
        offset += total
    return result


def subtitle_cues(subtitle):
    """Use provider character/word times, never interpolate word times uniformly.

    MiniMax may return subword tokens, so group them using source character spans.
    Old sentence-only cached audio retains its provider cue without guessed splits.
    """
    import re
    words = subtitle.get('timestamped_words') or []
    text = subtitle['text']
    if not words:
        return [(subtitle['time_begin'] / 1000, subtitle['time_end'] / 1000, text)]
    source_begin = subtitle.get('text_begin', 0)
    chunks = []
    start = 0
    while start < len(text):
        candidates = [m.end() for m in re.finditer(r'\s+', text[start:start + 79])]
        length = candidates[-1] if candidates and len(text) - start > 78 else min(78, len(text) - start)
        end = start + length
        matching = [word for word in words if word['word_end'] > source_begin + start and word['word_begin'] < source_begin + end]
        if matching and text[start:end].strip():
            chunks.append((matching[0]['time_begin'] / 1000,
                           matching[-1]['time_end'] / 1000, text[start:end].strip()))
        start = end
    if not chunks:
        raise RuntimeError('Word subtitle timing does not match source text')
    return chunks


def srt_for(folder, timeline, base=0):
    entries = []
    for scene in timeline:
        subs = json.loads((folder / 'audio' / (scene['audio_key'] + '.subtitles.json')).read_text())
        for subtitle in subs:
            for begin, end, cue_text in subtitle_cues(subtitle):
                if not 0 <= begin < end <= scene['duration'] + .5:
                    raise RuntimeError(f'Invalid subtitle timestamps: {scene["id"]}')
                start = scene['offset'] - base + scene['lead'] + begin
                stop = scene['offset'] - base + scene['lead'] + min(end, scene['duration'])
                text = '\n'.join(textwrap.wrap(cue_text, width=42))
                entries.append(f'{len(entries) + 1}\n{timestamp(start)} --> {timestamp(stop)}\n{text}')
    return '\n\n'.join(entries) + '\n'


def encode_scene(ffmpeg, folder, scene):
    destination = folder / 'clips' / (scene['id'] + '.mp4')
    stamp = destination.with_suffix('.json')
    frame_dir = folder / (scene['id'] + '-frames')
    capture = json.loads((frame_dir / 'capture.json').read_text())
    fingerprint = hashlib.sha256(('compositor-v3-centered-stage|' + json.dumps({k: v for k, v in scene.items() if k != 'offset'}, sort_keys=True) +
        (frame_dir / 'capture.json').read_text()).encode()).hexdigest()
    if destination.exists() and stamp.exists() and json.loads(stamp.read_text()).get('fingerprint') == fingerprint:
        return
    frames = capture['frames']
    if not frames:
        raise RuntimeError('Empty capture')
    if scene.get('hasAction', True):
        if frames[-1]['time'] > scene['total']:
            raise RuntimeError('Invalid capture duration')
    else:
        # Keep the highlighted final state; do not move the cursor on every paragraph.
        frames = [{**frames[-1], 'time': 0}]
    lines = []
    for i, frame in enumerate(frames):
        end = frames[i + 1]['time'] if i + 1 < len(frames) else scene['total']
        lines.extend([f"file '{frame['file']}'", 'option framerate 60', f'duration {max(.001, end - frame["time"]):.6f}'])
    lines.extend([f"file '{frames[-1]['file']}'", 'option framerate 60'])
    (frame_dir / 'frames.txt').write_text('\n'.join(lines) + '\n')
    temp = destination.with_suffix('.tmp.mp4')
    encode(ffmpeg, [
        '-threads', '2', '-f', 'concat', '-safe', '0', '-i', str(frame_dir / 'frames.txt'),
        '-i', str(folder / 'audio' / (scene['audio_key'] + '.mp3')),
        '-map', '0:v:0', '-map', '1:a:0', '-vf', 'fps=60,format=yuv420p',
        '-af', f'adelay={round(scene["lead"]*1000)}:all=1,apad',
        '-t', f'{scene["total"]:.6f}', '-c:v', 'libx264', '-threads', '2',
        '-preset', 'veryfast', '-crf', '18', '-g', '120',
        '-c:a', 'aac', '-b:a', '128k', '-ar', '48000', '-ac', '1',
        '-video_track_timescale', '60000', str(temp),
    ])
    temp.replace(destination)
    stamp.write_text(json.dumps({'fingerprint': fingerprint}))


def concatenate(ffmpeg, folder, timeline, filename):
    # AAC is decoded/re-encoded once per deliverable for a continuous clock;
    # the scene MP4 audio packet durations can differ slightly from video duration.
    listing = folder / (filename + '.concat.txt')
    listing.write_text('\n'.join(
        f"file 'clips/{scene['id']}.mp4'\nduration {scene['total']:.9f}" for scene in timeline
    ) + '\n')
    destination = folder / (filename + '.mp4')
    temp = folder / (filename + '.tmp.mp4')
    encode(ffmpeg, [
        '-f', 'concat', '-safe', '0', '-i', str(listing),
        '-c:v', 'copy', '-c:a', 'aac', '-b:a', '128k', '-ar', '48000',
        '-af', 'aresample=async=1:first_pts=0', '-movflags', '+faststart',
        '-metadata', 'title=STAT3612 Tutorial 04 - ' + filename, str(temp),
    ])
    temp.replace(destination)


def verify_sources(coverage):
    for relative, expected in coverage['sourceHashes'].items():
        if hashlib.sha256((ROOT / relative).read_bytes()).hexdigest() != expected:
            raise RuntimeError(f'Website changed since capture: {relative}. Rebuild and recapture.')
    if coverage['missingVerbatim']:
        raise RuntimeError('Coverage audit contains unaddressed teaching text')
    if coverage['chapters'] != [key for key, _ in CHAPTERS]:
        raise RuntimeError('Incomplete chapter coverage')


def main():
    global FOLDER
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--skip-capture', action='store_true')
    parser.add_argument('--reuse-audio-only', action='store_true', help='Never call TTS; fail if any audio cache is missing')
    parser.add_argument('--output-dir', type=Path, default=FOLDER)
    parser.add_argument('--audio-workers', type=int, default=3, choices=range(1, 5))
    parser.add_argument('--encode-workers', type=int, default=3, choices=range(1, 5))
    args = parser.parse_args()
    FOLDER = args.output_dir.resolve()
    ffmpeg = ffmpeg_binary()
    if not args.skip_capture:
        subprocess.run(['npm', 'run', 'build'], cwd=ROOT, check=True)
        command = ['node', 'scripts/video/complete.mjs', str(FOLDER)]
        if args.reuse_audio_only:
            command.append('--reuse-narration')
        subprocess.run(command, cwd=ROOT, check=True)
    coverage = json.loads((FOLDER / 'coverage.json').read_text())
    verify_sources(coverage)
    scenes = json.loads((FOLDER / 'scenes.json').read_text())['scenes']
    if len({scene['id'] for scene in scenes}) != len(scenes):
        raise RuntimeError('Duplicate scene ID')
    estimate = sum(len(text) for text in {scene['text'] for scene in scenes}) * 2 / 10000
    print(f'{len(scenes)} scenes; estimated unique TTS input cost ~CNY {estimate:.2f}', flush=True)
    generated = generate_audio(FOLDER, scenes, args.audio_workers, args.reuse_audio_only)
    timeline = timeline_for(FOLDER, scenes)
    (FOLDER / 'timeline.json').write_text(json.dumps(timeline, indent=2))
    (FOLDER / 'tutorial04-complete.srt').write_text(srt_for(FOLDER, timeline))
    (FOLDER / 'clips').mkdir(exist_ok=True)
    with ThreadPoolExecutor(max_workers=args.encode_workers) as pool:
        futures = {pool.submit(encode_scene, ffmpeg, FOLDER, scene): scene for scene in timeline}
        for number, future in enumerate(as_completed(futures), 1):
            future.result()
            print(f'Encoded {number}/{len(timeline)}: {futures[future]["id"]}', flush=True)
    concatenate(ffmpeg, FOLDER, timeline, 'tutorial04-complete')
    chapters = []
    for number, (key, title) in enumerate(CHAPTERS):
        selected = [scene for scene in timeline if scene['chapter'] == key]
        filename = f'{number:02}-{key}'
        concatenate(ffmpeg, FOLDER, selected, filename)
        (FOLDER / (filename + '.srt')).write_text(srt_for(FOLDER, selected, selected[0]['offset']))
        chapters.append({'title': title, 'start': selected[0]['offset'],
                         'duration': sum(scene['total'] for scene in selected), 'file': filename + '.mp4'})
    (FOLDER / 'youtube-chapters.txt').write_text('\n'.join(
        f'{int(ch["start"])//60:02}:{int(ch["start"])%60:02} {ch["title"]}' for ch in chapters
    ) + '\n')
    unique = {scene['audio_key'] for scene in timeline}
    usage = sum(json.loads((FOLDER / 'audio' / (key + '.json')).read_text())['extra_info']['usage_characters'] for key in unique)
    summary = {
        'video': str(FOLDER / 'tutorial04-complete.mp4'), 'chapters': chapters,
        'scenes': len(scenes), 'width': 1920, 'height': 1080, 'output_fps': 60,
        'capture': 'complete webpage without masks or translations; scroll-only framing; interaction-only cursor',
        'audio_reuse_only': args.reuse_audio_only,
        'subtitles': 'external SRT only; no burned-in subtitles or caption area',
        'duration_seconds': sum(scene['total'] for scene in timeline),
        'unique_audio_characters': usage, 'estimated_tts_cny': round(usage * 2 / 10000, 4),
        'new_api_requests_this_run': len(generated), 'sourceHashes': coverage['sourceHashes'],
    }
    # Catch source changes made during a long production job as well.
    verify_sources(coverage)
    (FOLDER / 'summary.json').write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
