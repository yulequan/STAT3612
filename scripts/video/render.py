"""Generate, record and assemble the tutorial04 update sample.

Run from the project root:
  python3 scripts/video/render.py
Use --skip-record to reassemble existing browser frames without recording again.
Requires npm dependencies, built site, and FFmpeg (FFMPEG_BIN or PATH).
Alternatively installs can live entirely in the ignored .cache/video-tools venv;
see scripts/NARRATION.md. Existing matching audio is reused without API charges.
"""

import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
SPEC = ROOT / 'scripts/video/tutorial04-update.json'
OUTPUT = ROOT / '.cache/video/tutorial04-update'


def ffmpeg_binary():
    configured = os.environ.get('FFMPEG_BIN') or shutil.which('ffmpeg')
    if configured:
        return configured
    python = ROOT / '.cache/video-tools/bin/python'
    if python.exists():
        return subprocess.check_output(
            [str(python), '-c', 'import imageio_ffmpeg; print(imageio_ffmpeg.get_ffmpeg_exe())'],
            text=True,
        ).strip()
    raise RuntimeError('FFmpeg not found. Set FFMPEG_BIN or follow scripts/NARRATION.md.')


def timestamp(seconds):
    ms = round(seconds * 1000)
    hours, ms = divmod(ms, 3600000)
    minutes, ms = divmod(ms, 60000)
    seconds, ms = divmod(ms, 1000)
    return f'{hours:02}:{minutes:02}:{seconds:02},{ms:03}'


def subtitle_entries(timeline, folder):
    offset = 0
    result = []
    for scene in timeline:
        subtitles = json.loads((folder / (scene['id'] + '.subtitles.json')).read_text())
        for subtitle in subtitles:
            begin = subtitle['time_begin'] / 1000
            end = subtitle['time_end'] / 1000
            if not 0 <= begin < end <= scene['duration'] + .5:
                raise ValueError(f"Invalid provider subtitle time in {scene['id']}")
            result.append((offset + scene['lead'] + begin,
                           offset + scene['lead'] + min(end, scene['duration']),
                           subtitle['text']))
        offset += scene['total']
    return result


def check_external_subtitles(folder, timeline):
    """Refuse old captures that still contain a subtitle layer/background."""
    for scene in timeline:
        layout = folder / (scene['id'] + '-frames/layout.json')
        if not layout.exists():
            raise RuntimeError('Capture lacks subtitle-layer checks. Record again without --skip-record.')
        recorded = json.loads(layout.read_text())
        if '#video-caption' in recorded:
            raise RuntimeError('Old burned-in subtitle capture detected. Record again without --skip-record.')


def prepare_audio(folder, scenes):
    folder.mkdir(parents=True, exist_ok=True)
    for scene in scenes:
        audio = folder / (scene['id'] + '.mp3')
        meta = audio.with_suffix('.json')
        subtitles = audio.with_suffix('.subtitles.json')
        if audio.exists():
            if not meta.exists() or not subtitles.exists():
                raise RuntimeError(f'{audio}: incomplete cache. Recover missing files or choose a new output directory.')
            if json.loads(meta.read_text())['text'] != scene['text']:
                raise RuntimeError(f'{audio}: script changed. Choose a new output directory to regenerate deliberately.')
            print(f'Reusing audio: {scene["id"]}', flush=True)
            continue
        text = audio.with_suffix('.txt')
        text.write_text(scene['text'])
        subprocess.run([
            sys.executable, str(ROOT / 'scripts/minimax_tts.py'),
            '--text-file', str(text), '--output', str(audio), '--subtitles',
        ], check=True, cwd=ROOT)


def encode(ffmpeg, arguments):
    result = subprocess.run([ffmpeg, '-hide_banner', '-loglevel', 'error', '-y', *arguments],
                            capture_output=True, text=True)
    if result.returncode:
        raise RuntimeError(f'FFmpeg failed:\n{result.stderr}')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--skip-record', action='store_true')
    parser.add_argument('--output-dir', type=Path, default=OUTPUT)
    args = parser.parse_args()
    folder = args.output_dir.resolve()
    ffmpeg = ffmpeg_binary()  # Fail before any paid requests if the encoder is missing.
    scenes = json.loads(SPEC.read_text())['scenes']
    prepare_audio(folder, scenes)
    if not args.skip_record:
        if not (ROOT / 'dist/index.html').exists():
            raise RuntimeError('Run npm run build before recording.')
        subprocess.run(['node', str(ROOT / 'scripts/video/record.mjs'), str(folder)],
                       cwd=ROOT, check=True)
    timeline = json.loads((folder / 'timeline.json').read_text())
    if [scene['id'] for scene in timeline] != [scene['id'] for scene in scenes]:
        raise RuntimeError('Timeline does not match the scene specification.')
    check_external_subtitles(folder, timeline)
    srt = '\n\n'.join(
        f'{i}\n{timestamp(begin)} --> {timestamp(end)}\n{text}'
        for i, (begin, end, text) in enumerate(subtitle_entries(timeline, folder), 1)
    ) + '\n'
    (folder / 'tutorial04-update.srt').write_text(srt)
    for scene in timeline:
        print(f'Encoding: {scene["id"]}', flush=True)
        encode(ffmpeg, [
            '-f', 'concat', '-safe', '0', '-i', str(folder / (scene['id'] + '-frames/frames.txt')),
            '-i', str(folder / (scene['id'] + '.mp3')),
            '-map', '0:v:0', '-map', '1:a:0',
            '-vf', 'fps=30,format=yuv420p',
            '-af', f'adelay={round(scene["lead"] * 1000)}:all=1,apad',
            '-t', str(scene['total']), '-c:v', 'libx264', '-preset', 'fast', '-crf', '20',
            '-c:a', 'aac', '-b:a', '128k', '-ar', '48000', '-ac', '1',
            str(folder / (scene['id'] + '.mp4')),
        ])
    # Restrict clip names via the fixed spec above; quote resolved paths for FFmpeg.
    clips = '\n'.join(f"file '{scene['id']}.mp4'" for scene in timeline) + '\n'
    (folder / 'clips.txt').write_text(clips)
    final = folder / 'tutorial04-update.mp4'
    encode(ffmpeg, [
        '-f', 'concat', '-safe', '0', '-i', str(folder / 'clips.txt'),
        '-c', 'copy', '-movflags', '+faststart', '-metadata',
        'title=STAT3612 Tutorial 04 - One gradient update', str(final),
    ])
    usage = sum(json.loads((folder / (scene['id'] + '.json')).read_text())
                ['extra_info']['usage_characters'] for scene in scenes)
    summary = {
        'video': str(final), 'width': 1920, 'height': 1080, 'fps': 30,
        'subtitles': 'external SRT only; no burned-in captions or background',
        'planned_duration_seconds': sum(scene['total'] for scene in timeline),
        'narration_seconds': sum(scene['duration'] for scene in timeline),
        'usage_characters': usage,
        'estimated_tts_cny_at_turbo_rate': round(usage * 2 / 10000, 4),
        'note': 'Cost estimate applies to turbo at 2 CNY / 10,000 characters, excluding retries.',
    }
    (folder / 'summary.json').write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
