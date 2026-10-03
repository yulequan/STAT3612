# MiniMax English narration smoke test

The backend-only TTS utility uses Python's standard library and the China
pay-as-you-go API. A browser recording pipeline produces the update sample below.

## Configure

Copy `.env.example` to `.env.local`, insert your key, and restrict its permissions:

```bash
cp .env.example .env.local
chmod 600 .env.local
```

The script reads `.env.local`; already exported environment variables take precedence.
This does not globally export variables in your shell. Both `.env.local` and generated
files under `.cache/` are ignored by Git. Never put secrets in `VITE_*` variables.
Rotate any key shared in chat, screenshots, or logs.

Defaults:

- `MINIMAX_API_BASE=https://api.minimax.cn`
- `MINIMAX_TTS_MODEL=speech-2.8-turbo`
- `MINIMAX_TTS_VOICE=English_Insightful_Speaker` (existing system voice)
- English language boost, speed 0.95, mono MP3, 32 kHz / 128 kbps.

## Generate

```bash
python3 scripts/minimax_tts.py
# Custom narration; choose a new output path:
python3 scripts/minimax_tts.py --text-file lesson.txt --output .cache/narration/lesson.mp3
# Optional HD comparison (a separate billable request):
MINIMAX_TTS_MODEL=speech-2.8-hd python3 scripts/minimax_tts.py \
  --output .cache/narration/minimax-hd.mp3
```

Each successful run saves an MP3 and a JSON sidecar containing text, model, voice,
trace ID, and provider usage/duration metadata. `audio_length` is milliseconds.
Play the MP3 locally to assess pronunciation and teaching style. Request success
and valid file headers do not establish subjective voice quality.

The script refuses to overwrite existing audio, limits text to fewer than 10,000
characters, restricts credential transmission to the official default China API
host, uses normal TLS certificate verification, and never automatically retries
billable requests. Check the provider console if a timeout occurs before retrying.

## Model choice and price

At the time of setup, official China pay-as-you-go docs list:

| Model | CNY / 10,000 input characters |
| --- | ---: |
| speech-2.8-turbo | 2.00 |
| speech-2.8-hd | 3.50 |
| speech-2.6-turbo / speech-02-turbo | 2.00 |
| speech-2.6-hd / speech-02-hd | 3.50 |

Choose 2.8-turbo for the initial cost-effective test; older turbo models have no
listed price advantage. English letters, spaces, punctuation and newlines each
count as one character; a Chinese character counts as two. Use the API's
`usage_characters` and the console billing record for actual accounting. System
voices avoid creating a clone/designed voice (which has separate fees).
Prices can change; verify before larger batches.

Official references:

- https://platform.minimax.cn/docs/guides/speech-t2a-websocket
- https://platform.minimax.cn/docs/api-reference/speech-t2a-http
- https://platform.minimax.cn/docs/guides/pricing-paygo

## Offline tests

```bash
python3 -m unittest discover -s tests -p 'test_minimax_tts.py' -v
```

Tests mock HTTP and use dummy credentials; they never call the paid API.

## Browser video sample: overview + one gradient update

This is a short sample, NOT the complete eight-chapter course.

Install FFmpeg in an ignored environment if it is not available on PATH:

```bash
uv venv .cache/video-tools
uv pip install --python .cache/video-tools/bin/python imageio-ffmpeg==0.6.0
```

Then build the current website and generate the sample:

```bash
npm run build
python3 scripts/video/render.py
# Reassemble checked, caption-free frames without recording again:
python3 scripts/video/render.py --skip-record
```

The script uses the existing Playwright dependency and Chrome (or a Playwright
browser). Set `CHROME_BIN` or `FFMPEG_BIN` if needed. Port 4188 must be available.
Audio and its provider sentence timestamps are cached by scene; matching audio is
reused. Changed text or missing sidecars fail instead of automatically charging
again. `--subtitles` on the TTS utility requests timestamped subtitle JSON; signed
subtitle downloads never receive the API Authorization header.

Outputs under `.cache/video/tutorial04-update/`:

- `tutorial04-update.mp4`: H.264/AAC 1920 × 1080 sample with narration, visible
  cursor, click ripples, highlights, slider dragging, and real Python execution.
- `tutorial04-update.srt`: separately uploadable English subtitles, based on
  MiniMax timestamps plus scene offsets. **No subtitles or subtitle background
  are drawn into the video.** Old caption-layer captures are rejected.
- `summary.json`, `timeline.json`: timing and usage metadata.
- Scene audio, timestamped screenshot frames, and viewport checks for diagnostics.

Screenshots are sampled at approximately 10 fps and encoded at 30 fps; this does
not create 30 unique frames per second. Frame timestamps preserve wall-clock
interaction timing. It is a prototype, not a claim of professional 60-fps capture.
Rebuild after website changes: recording deliberately reads local `dist/`, not a
possibly stale external website. The scene spec is `scripts/video/tutorial04-update.json`.

### YouTube subtitles

Upload the MP4 first. In YouTube Studio select the video under **Subtitles**,
choose **English**, then **Add / Upload file / With timing**, and upload the SRT.
Review and publish the track. Viewers can toggle captions; translated tracks can
be uploaded separately. English automatic captions are also available when the
video is eligible, but may be delayed or misrecognise mathematical terminology.
The supplied SRT is preferable to relying solely on automatic recognition.
YouTube upload is not automated by these scripts.

Additional offline video tests:

```bash
python3 -m unittest discover -s tests -p 'test_*video*.py' -v
```

## Complete Tutorial 04: 00–08

```bash
python3 scripts/video/full.py
# Existing verified captures; reuse matching narration and encoded clips:
python3 scripts/video/full.py --skip-capture
# Re-record visuals while locking the existing narration; NEVER call TTS:
python3 scripts/video/full.py --reuse-audio-only
# Re-encode newly recorded visuals, with TTS strictly disabled:
python3 scripts/video/full.py --skip-capture --reuse-audio-only
# Full decoding, chapter durations, subtitle bounds and content/source audit:
python3 scripts/video/validate.py
# After website changes, use a fresh directory to avoid incompatible visual caches:
python3 scripts/video/full.py --output-dir .cache/video/tutorial04-v2
```

The complete pipeline rebuilds the current website, captures the course index,
Overview and every chapter, then uses up to three TTS workers and three encoding
workers. API starts are spaced at least 3.4 seconds apart: the official default
China TTS limit for prepaid users is 20 RPM. Higher concurrency does not bypass
that limit. Repeated identical narration is generated only once. There are no
automatic retries of paid requests. Completed audio survives failed runs.

For advanced use, `python3 scripts/video/encode_pending.py` is an optional local
encoder sidecar that consumes completed audio while TTS is running. **Do not run
the sidecar and main encoding stage simultaneously**: let the sidecar finish
before invoking `full.py --skip-capture` for assembly.

Outputs under `.cache/video/tutorial04-complete/`:

- `tutorial04-complete.mp4` and `tutorial04-complete.srt`.
- `00-overview.mp4` / `.srt` through `08-beyond.mp4` / `.srt` for separate uploads.
- `youtube-chapters.txt`: timestamp markers to paste into the description.
- `coverage.json`: all teaching text inventory, content/interaction coverage,
  zero missing verbatim inventoried teaching blocks, and SHA-256 hashes of website sources.
- `scenes.json`, `timeline.json`, `summary.json`: narration, timings and usage.
- Actual training-results JSON, final model-decision JSON and student ZIP downloads.

Complete recordings use Chromium compositor JPEG frames instead of blocking
screenshot loops. Cursor motion is animated using `requestAnimationFrame`; real
mouse events drive clicks and slider drags. Frame timestamps and a 60 Hz input
image timebase preserve movement in the 60-fps output. Capture is still dependent
on browser/load performance, not a promise of 60 unique frames at all times.
Static teaching scenes hold their final highlighted image **without a cursor**.
The cursor is only visible while clicking, selecting or dragging; it and click
ripples are removed before the final hold is captured. Interactive scenes retain
the motion frames then hold that clean final image. No synthetic results or
generated webpage images are substituted for Python output.

`presentation.mjs` preserves the **complete webpage**, including the sidebar,
columns and surrounding teaching content. It only scrolls to make the current
card, formula, code range or output readable within the 1920 × 1080 viewport.
There is **no outside matte, cropping mask, horizontal translation or artificial
blank padding**. A transparent focus border sits outside the active target; it
does not hide the rest of the page. Short blocks use the upper-middle viewport,
while taller panels use the available height, subject to natural scroll limits.
These changes are injected only into recording; the deployed website is unchanged.
The presentation version invalidates old captures and clip fingerprints.

`--reuse-audio-only` locks scene narration to the previous `scenes.json` during
recapture, then verifies every audio cache exists. It fails on missing audio
instead of calling MiniMax. Browser presentation tests also check positioning,
context, cursor motion, and cursor-free final holds:

```bash
node --test tests/video/presentation.test.mjs
```

The validator checks all final hold cursor/ripple states, absence of masks,
horizontal transforms and blank padding, and focus boundaries, in addition to
decoding and subtitle timestamps. Browser tests check that framing leaves
horizontal positions unchanged and the sidebar unobscured. Automated geometry
tests do not replace a human visual review of the final video.

The course covers all website teaching text, mathematical notation, source
functions, controls, question prompts and answers, original and modified Python
exercises, model comparison, test evaluation, exports and notebook handoff. It
does not enumerate every possible slider value, open external further-reading
sites, or execute the companion notebook outside the browser. Capture runs in
one browser session so training and model choices remain consistent. The audit
refuses missing chapters or teaching text; rendering refuses modified sources
and captures with burned-in captions. Website changes require recapture in a
new output directory rather than mixing incompatible cached scenes.

Subtitle cues use provider word/subword times where available, grouped into
readable chunks using character spans, rather than guessing uniform word
positions. Older sentence-only cache remains at its original provider timing.
Captions are always external; the video has no subtitle background strip.

`full.py` deduplicates audio by text + model + voice + speed, and encodes only
changed scenes. Encoded clip outputs are atomic. The complete output deliberately
has a different filename from the short `tutorial04-update` sample.
