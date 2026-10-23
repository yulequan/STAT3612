"""Build the narrated Tutorial 06 slide video.

Usage:
  python3 scripts/video/tutorial06/build.py --pages all          # all 34 slides
  python3 scripts/video/tutorial06/build.py --pages 1-4 --output-dir .cache/video/tutorial06-sample --pointer
  python3 scripts/video/tutorial06/build.py --pages all --skip-tts --skip-record
"""

import argparse
import csv
import json
import math
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import textwrap
import time

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
SPEC = ROOT / 'src/tutorials/tutorial06/time_series_slides.pdf'
CSV = HERE / 'narration.csv'
DEFAULT_OUTPUT = ROOT / '.cache/video/tutorial06-complete'
PDF_WIDTH = 453.54
PDF_HEIGHT = 255.12
WIDTH = 1920
HEIGHT = 1080
FPS = 30
CHAPTERS = [
    ('Opening & roadmap', 1),
    ('Data structures & tasks', 3),
    ('Patterns & features', 6),
    ('Preprocessing & leakage', 11),
    ('Models: simple to sequence', 16),
    ('Forecasting with ARIMA', 22),
    ('Validation & evaluation', 25),
    ('Summary & group project', 30),
]

sys.path.insert(0, str(HERE))
from scenes import SCENES as ALL_SCENES, SAMPLE_PAGES  # noqa: E402

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


def run(arguments, **kwargs):
    result = subprocess.run(arguments, capture_output=True, text=True, **kwargs)
    if result.returncode:
        raise RuntimeError(
            f'Command failed: {" ".join(str(value) for value in arguments)}\n{result.stderr}'
        )
    return result


def timestamp(seconds):
    milliseconds = round(seconds * 1000)
    hours, milliseconds = divmod(milliseconds, 3600000)
    minutes, milliseconds = divmod(milliseconds, 60000)
    seconds, milliseconds = divmod(milliseconds, 1000)
    return f'{hours:02}:{minutes:02}:{seconds:02},{milliseconds:03}'


def normalized(text):
    return re.sub(r'\s+', ' ', text.lower())


def phrase_time(subtitles, phrase):
    """Return the first provider word time covering a spoken phrase."""
    target = normalized(phrase)
    for segment in subtitles:
        text = segment['text']
        chars = []
        offsets = []
        for index, character in enumerate(text):
            if character.isspace():
                if chars and chars[-1] != ' ':
                    chars.append(' ')
                    offsets.append(index)
            else:
                chars.append(character.lower())
                offsets.append(index)
        position = ''.join(chars).find(target)
        if position < 0:
            continue
        local_start = offsets[position]
        global_start = segment.get('text_begin', 0) + local_start
        for word in segment['timestamped_words']:
            if word['word_begin'] <= global_start < word['word_end']:
                return word['time_begin'] / 1000
        for word in segment['timestamped_words']:
            if word['word_begin'] >= global_start:
                return word['time_begin'] / 1000
    raise RuntimeError(f'Cue phrase not found in MiniMax subtitles: {phrase!r}')


def load_scripts():
    with open(CSV, newline='') as handle:
        return {int(row['page']): row['script_en'] for row in csv.DictReader(handle)}


def ensure_audio(output, scripts, scenes, skip_tts=False):
    audio_dir = output / 'audio'
    audio_dir.mkdir(parents=True, exist_ok=True)
    generated = False
    last_request = 0.0
    for scene in scenes:
        page = scene['page']
        audio = audio_dir / f'{page:02d}.mp3'
        sidecar = audio.with_suffix('.json')
        subtitles = audio.with_suffix('.subtitles.json')
        source = audio.with_suffix('.txt')
        if audio.exists():
            if not sidecar.exists() or not subtitles.exists():
                raise RuntimeError(f'Incomplete audio cache: {audio}')
            if json.loads(sidecar.read_text())['text'].strip() != scripts[page].strip():
                raise RuntimeError(f'Script changed for page {page}; use a new output directory')
            continue
        if skip_tts:
            raise RuntimeError(f'Audio is missing for page {page}: {audio}')
        wait = max(0.0, last_request + 3.4 - time.monotonic())
        if wait:
            time.sleep(wait)
        last_request = time.monotonic()
        source.write_text(scripts[page])
        run([
            sys.executable, str(ROOT / 'scripts/minimax_tts.py'), '--subtitles',
            '--text-file', str(source), '--output', str(audio),
        ], cwd=ROOT)
        generated = True
        print(f'Generated audio for page {page}', flush=True)
    if not generated:
        print('Reused all lesson audio; no TTS request was made.', flush=True)


def ensure_pages(output, scenes):
    page_dir = output / 'pages'
    page_dir.mkdir(parents=True, exist_ok=True)
    wanted = {scene['page'] for scene in scenes}
    missing = [page for page in wanted if not (page_dir / f'{page:02d}.png').exists()]
    if not missing:
        return
    first, last = min(missing), max(missing)
    run([
        'pdftoppm', '-f', str(first), '-l', str(last), '-png',
        '-scale-to-x', str(WIDTH), '-scale-to-y', str(HEIGHT),
        str(SPEC), str(page_dir / 'page'),
    ])
    for page in missing:
        source = page_dir / f'page-{page:02d}.png'
        if not source.exists():
            raise RuntimeError(f'Missing rendered PDF page: {source}')
        source.replace(page_dir / f'{page:02d}.png')


def write_record(output, scripts, lesson_scenes, show_pointer=False):
    timeline_scenes = []
    offset = 0.0
    for scene in lesson_scenes:
        page = scene['page']
        audio = output / 'audio' / f'{page:02d}.mp3'
        meta = json.loads(audio.with_suffix('.json').read_text())
        subtitles = json.loads(audio.with_suffix('.subtitles.json').read_text())
        duration = meta['extra_info']['audio_length'] / 1000
        cues = []
        for cue in scene['cues']:
            time = phrase_time(subtitles, cue['phrase'])
            cues.append({'time': round(time, 3), 'box': cue['box'], 'phrase': cue['phrase']})
        cues.sort(key=lambda item: item['time'])
        lead = 0.45
        tail = 0.55
        total = math.ceil((lead + duration + tail) * FPS) / FPS
        timeline_scenes.append({
            'id': scene['id'],
            'page': page,
            'image': f'pages/{page:02d}.png',
            'audio': f'audio/{page:02d}.mp3',
            'text': scripts[page],
            'duration': duration,
            'lead': lead,
            'tail': tail,
            'total': total,
            'cues': cues,
            'showPointer': show_pointer,
            'offset': offset,
        })
        offset += total
    record = {
        'title': 'Tutorial 06 · ' + ('complete' if len(lesson_scenes) == 34 else 'sample'),
        'scenes': timeline_scenes,
    }
    (output / 'record.json').write_text(json.dumps(record, indent=2))
    return record


def prepare_stage(output):
    shutil.copy2(HERE / 'stage.html', output / 'stage.html')


def run_record(output):
    run(['node', str(HERE / 'record.mjs'), str(output)], cwd=ROOT)


def frames_file(folder, total):
    capture = json.loads((folder / 'capture.json').read_text())
    if capture.get('captionsBurnedIn') is not False:
        raise RuntimeError('Capture reported burned-in captions')
    frames = capture['frames']
    if not frames:
        raise RuntimeError('Capture has no frames')
    lines = ['ffconcat version 1.0']
    for index, frame in enumerate(frames):
        next_time = frames[index + 1]['time'] if index + 1 < len(frames) else total
        duration = max(0.001, next_time - frame['time'])
        lines.append(f"file '{frame['file']}'")
        lines.append(f'duration {duration:.6f}')
    (folder / 'frames.txt').write_text('\n'.join(lines) + '\n')


def encode_scene(ffmpeg, output, scene):
    folder = output / (scene['id'] + '-frames')
    frames_file(folder, scene['total'])
    destination = output / 'clips' / (scene['id'] + '.mp4')
    destination.parent.mkdir(parents=True, exist_ok=True)
    audio = output / scene['audio']
    run([
        ffmpeg, '-hide_banner', '-loglevel', 'error', '-y',
        '-f', 'concat', '-safe', '0', '-i', str(folder / 'frames.txt'),
        '-i', str(audio),
        '-map', '0:v:0', '-map', '1:a:0',
        '-vf', f'fps={FPS},format=yuv420p',
        '-af', f'adelay={round(scene["lead"] * 1000)}:all=1,apad',
        '-t', f'{scene["total"]:.3f}',
        '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '20',
        '-c:a', 'aac', '-b:a', '128k', '-ar', '48000', '-ac', '1',
        '-movflags', '+faststart',
        str(destination),
    ])


def subtitle_cues(subtitle):
    """Use provider word times, grouped into readable character spans."""
    words = subtitle.get('timestamped_words') or []
    text = subtitle['text']
    if not words:
        return [(subtitle['time_begin'] / 1000, subtitle['time_end'] / 1000, text)]
    source_begin = subtitle.get('text_begin', 0)
    chunks = []
    start = 0
    while start < len(text):
        candidates = [match.end() for match in re.finditer(r'\s+', text[start:start + 79])]
        length = candidates[-1] if candidates and len(text) - start > 78 else min(78, len(text) - start)
        end = start + length
        matching = [
            word for word in words
            if word['word_end'] > source_begin + start and word['word_begin'] < source_begin + end
        ]
        if matching and text[start:end].strip():
            chunks.append((
                matching[0]['time_begin'] / 1000,
                matching[-1]['time_end'] / 1000,
                text[start:end].strip(),
            ))
        start = end
    if not chunks:
        raise RuntimeError('Word subtitle timing does not match source text')
    return chunks


def write_srt(output, timeline, filename='tutorial06-sample.srt'):
    entries = []
    for scene in timeline['scenes']:
        subtitles = json.loads(
            (output / 'audio' / f'{scene["page"]:02d}.subtitles.json').read_text()
        )
        for subtitle in subtitles:
            for begin, end, cue_text in subtitle_cues(subtitle):
                if not 0 <= begin < end <= scene['duration'] + 0.5:
                    raise RuntimeError(f'Invalid subtitle timestamps on page {scene["page"]}')
                start = scene['offset'] + scene['lead'] + begin
                stop = scene['offset'] + scene['lead'] + min(end, scene['duration'])
                cue_text = re.sub(r'([.!?])(?=[A-Za-z])', r'\1 ', cue_text)
                text = '\n'.join(textwrap.wrap(cue_text, width=42))
                entries.append(f'{len(entries) + 1}\n{timestamp(start)} --> {timestamp(stop)}\n{text}')
    (output / filename).write_text('\n\n'.join(entries) + '\n')


def select_scenes(value):
    if value == 'all':
        return ALL_SCENES
    pages = set()
    for part in value.split(','):
        part = part.strip()
        if '-' in part:
            first, last = (int(number) for number in part.split('-', 1))
            pages.update(range(first, last + 1))
        elif part:
            pages.add(int(part))
    selected = [scene for scene in ALL_SCENES if scene['page'] in pages]
    if not selected:
        raise ValueError(f'No slides selected by --pages {value!r}')
    return selected


def write_chapters(output, timeline):
    by_page = {scene['page']: scene for scene in timeline['scenes']}
    lines = []
    for name, page in CHAPTERS:
        start = by_page[page]['offset']
        lines.append(f'{int(start // 60):02d}:{int(start % 60):02d} {name}')
    (output / 'youtube-chapters.txt').write_text('\n'.join(lines) + '\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument('--pages', default='all', help='all, 1-4, or a comma-separated list')
    parser.add_argument('--pointer', action='store_true', help='draw the arrow pointer (sample only)')
    parser.add_argument('--skip-tts', action='store_true')
    parser.add_argument('--skip-record', action='store_true')
    parser.add_argument('--skip-encode', action='store_true')
    args = parser.parse_args()
    output = args.output_dir.resolve()
    output.mkdir(parents=True, exist_ok=True)
    ffmpeg = ffmpeg_binary()  # Fail before paid TTS if the encoder is unavailable.
    scripts = load_scripts()
    scenes = select_scenes(args.pages)
    label = 'sample' if {scene['page'] for scene in scenes} <= SAMPLE_PAGES else 'complete'
    ensure_audio(output, scripts, scenes, skip_tts=args.skip_tts)
    ensure_pages(output, scenes)
    timeline = write_record(output, scripts, scenes, show_pointer=args.pointer)
    prepare_stage(output)
    if not args.skip_record:
        run_record(output)
    if args.skip_encode:
        print(f'Prepared {output}; capture requested={not args.skip_record}')
        return
    for scene in timeline['scenes']:
        print(f'Encoding {scene["id"]}', flush=True)
        encode_scene(ffmpeg, output, scene)
    clips = '\n'.join(f"file 'clips/{scene['id']}.mp4'" for scene in timeline['scenes']) + '\n'
    (output / 'clips.txt').write_text(clips)
    final = output / f'tutorial06-{label}.mp4'
    run([
        ffmpeg, '-hide_banner', '-loglevel', 'error', '-y',
        '-f', 'concat', '-safe', '0', '-i', str(output / 'clips.txt'),
        '-c', 'copy', '-movflags', '+faststart',
        '-metadata', f'title=STAT3612 Tutorial 06 - {label}', str(final),
    ])
    write_srt(output, timeline, f'tutorial06-{label}.srt')
    write_chapters(output, timeline)
    usage = sum(
        json.loads((output / 'audio' / f'{scene["page"]:02d}.json').read_text())
        ['extra_info']['usage_characters']
        for scene in timeline['scenes']
    )
    summary = {
        'video': str(final),
        'width': WIDTH,
        'height': HEIGHT,
        'fps': FPS,
        'pages': [scene['page'] for scene in timeline['scenes']],
        'duration_seconds': round(sum(scene['total'] for scene in timeline['scenes']), 3),
        'narration_seconds': round(sum(scene['duration'] for scene in timeline['scenes']), 3),
        'usage_characters': usage,
        'estimated_tts_cny_at_turbo_rate': round(usage * 2 / 10000, 4),
        'subtitles': 'external SRT only; no burned-in captions or background',
        'pointer': args.pointer,
        'note': 'Sample.' if label == 'sample' else 'Complete Tutorial 06, pages 1-34.',
    }
    (output / 'summary.json').write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
