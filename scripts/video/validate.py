"""Validate completed Tutorial 04 artifacts without any paid API requests."""

import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess

from full import FOLDER, CHAPTERS, PRESENTATION_VERSION, verify_sources
from render import ffmpeg_binary


def probe(ffmpeg, path):
    result = subprocess.run([ffmpeg, '-hide_banner', '-i', str(path)],
                            capture_output=True, text=True)
    # FFmpeg exits nonzero when probing without output; inspect its stream metadata.
    match = re.search(r'Duration: (\d+):(\d+):(\d+\.\d+)', result.stderr)
    if not match:
        raise RuntimeError(f'Cannot probe {path}')
    duration = int(match[1]) * 3600 + int(match[2]) * 60 + float(match[3])
    if '1920x1080' not in result.stderr or 'h264' not in result.stderr or 'Audio: aac' not in result.stderr:
        raise RuntimeError(f'Unexpected codec/resolution: {path}')
    if 'Subtitle:' in result.stderr:
        raise RuntimeError('Embedded subtitle stream found; expected external-only SRT')
    return duration


def srt_time(text):
    hours, minutes, seconds = text.split(':')
    return int(hours) * 3600 + int(minutes) * 60 + float(seconds.replace(',', '.'))


def check_srt(path, duration):
    blocks = path.read_text().strip().split('\n\n')
    previous_start = -1
    count = 0
    for block in blocks:
        lines = block.splitlines()
        if len(lines) < 3:
            raise RuntimeError('Malformed SRT cue')
        start, end = map(srt_time, lines[1].split(' --> '))
        if not previous_start <= start < end <= duration + .15:
            raise RuntimeError(f'Subtitle timestamps outside video: {path}')
        previous_start = start
        count += 1
    return count


def check_presentation(folder):
    scenes = json.loads((folder / 'scenes.json').read_text())['scenes']
    static, interactive, moving = 0, 0, 0
    for scene in scenes:
        capture = json.loads((folder / (scene['id'] + '-frames/capture.json')).read_text())
        if capture.get('presentationVersion') != PRESENTATION_VERSION:
            raise RuntimeError(f'Old presentation frames: {scene["id"]}')
        layout = capture['layout']
        if not layout['pointerHidden'] or layout['ripples']:
            raise RuntimeError(f'Cursor/ripple covers the final hold: {scene["id"]}')
        focus = layout['focus']
        if not layout.get('context') or not focus:
            raise RuntimeError('Missing layout evidence')
        if layout.get('maskCount') != 0 or layout.get('mainTransform') != 'none' or float(layout['mainPaddingTop'].removesuffix('px')) > 100:
            raise RuntimeError(f'Blank-producing mask, transform or padding: {scene["id"]}')
        if focus['x'] < 40 or focus['y'] < 94 or focus['x'] + focus['width'] > 1880 or focus['y'] + focus['height'] > 1046:
            raise RuntimeError(f'Clipped focus box: {scene["id"]}')
        if scene['hasAction']:
            interactive += 1
            points = layout['motionSamples']
            if len(points) >= 5 and max(p['x'] for p in points) - min(p['x'] for p in points) + max(p['y'] for p in points) - min(p['y'] for p in points) > 50:
                moving += 1
        else:
            static += 1
    if moving < 50:
        raise RuntimeError('Too few interaction captures contain demonstrable cursor motion')
    return {'version': PRESENTATION_VERSION, 'cursor_free_holds': len(scenes),
            'unmasked_full_page_scenes': len(scenes), 'static_scenes': static,
            'interactive_scenes': interactive, 'moving_cursor_scenes': moving}


def main():
    global FOLDER
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', type=Path, default=FOLDER)
    FOLDER = parser.parse_args().output_dir.resolve()
    ffmpeg = ffmpeg_binary()
    summary = json.loads((FOLDER / 'summary.json').read_text())
    coverage = json.loads((FOLDER / 'coverage.json').read_text())
    verify_sources(coverage)
    presentation = check_presentation(FOLDER)
    previous_audio = FOLDER / 'previous-visuals/audio-hashes.json'
    audio_integrity = None
    if previous_audio.exists():
        expected = json.loads(previous_audio.read_text())
        actual = {file.name: hashlib.sha256(file.read_bytes()).hexdigest()
                  for file in (FOLDER / 'audio').iterdir() if file.is_file()}
        if actual != expected:
            raise RuntimeError('Existing audio cache changed during visual-only revision')
        audio_integrity = {'files': len(actual), 'byte_identical_to_previous_version': True}
    duration = probe(ffmpeg, FOLDER / 'tutorial04-complete.mp4')
    if abs(duration - summary['duration_seconds']) > .2:
        raise RuntimeError('Complete video duration drift exceeds 0.2 seconds')
    cues = check_srt(FOLDER / 'tutorial04-complete.srt', duration)
    chapters = []
    for chapter in summary['chapters']:
        actual = probe(ffmpeg, FOLDER / chapter['file'])
        if abs(actual - chapter['duration']) > .15:
            raise RuntimeError('Chapter duration drift exceeds 0.15 seconds')
        check_srt((FOLDER / chapter['file']).with_suffix('.srt'), actual)
        chapters.append({'file': chapter['file'], 'duration_seconds': actual})
    # Decode all video/audio packets, not just metadata or the first few seconds.
    result = subprocess.run([ffmpeg, '-v', 'error', '-threads', '4',
                             '-i', str(FOLDER / 'tutorial04-complete.mp4'),
                             '-f', 'null', '-'], capture_output=True, text=True)
    if result.returncode or result.stderr.strip():
        raise RuntimeError('Full audio/video decoding failed: ' + result.stderr)
    result = {
        'full_decode': 'passed', 'chapters': chapters, 'duration_seconds': duration,
        'subtitle_cues': cues, 'missing_teaching_texts': len(coverage['missingVerbatim']),
        'source_integrity': 'passed', 'subtitles': 'external only', 'presentation': presentation, 'audio_integrity': audio_integrity,
        'limitations': 'Automated integrity and coverage checks; not a human review of every spoken sentence.',
    }
    (FOLDER / 'validation.json').write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
