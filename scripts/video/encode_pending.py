"""Optional encoder sidecar: encode cached scenes while rate-limited TTS is running.
It never calls the API. Main full.py also skips matching encoded clips.
"""

from concurrent.futures import ThreadPoolExecutor, as_completed
import argparse
from pathlib import Path
import json
import time

from full import FOLDER, audio_key, encode_scene, ffmpeg_binary, timeline_for


def main():
    global FOLDER
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', type=Path, default=FOLDER)
    FOLDER = parser.parse_args().output_dir.resolve()
    ffmpeg = ffmpeg_binary()
    scenes = json.loads((FOLDER / 'scenes.json').read_text())['scenes']
    done = set()
    with ThreadPoolExecutor(max_workers=3) as pool:
        while len(done) < len(scenes):
            ready = [scene for scene in scenes if scene['id'] not in done and
                     (FOLDER / 'audio' / (audio_key(scene['text']) + '.subtitles.json')).exists()]
            if not ready:
                time.sleep(5)
                continue
            futures = {pool.submit(encode_scene, ffmpeg, FOLDER,
                                    timeline_for(FOLDER, [scene])[0]): scene for scene in ready}
            for future in as_completed(futures):
                future.result()
                scene = futures[future]
                done.add(scene['id'])
                print(f'Pre-encoded {len(done)}/{len(scenes)}: {scene["id"]}', flush=True)


if __name__ == '__main__':
    main()
