# Video Caption Fix — Burned-in Subtitles That Fit the Frame

Use this skill whenever you burn captions/subtitles into a vertical video
(1080×1920) before it is posted anywhere (YouTube / LinkedIn / X / TikTok).
It exists because of a real defect that shipped. Do not burn an SRT directly
into a video without going through this skill.

## The defect pattern (what went wrong, 2026-11-18, SF Naïve hackathon videos)

- The source SRT cues were up to ~12 seconds long and contained full
  sentences (sometimes several sentences in one cue).
- Those SRTs were burned in directly with ffmpeg's `subtitles` filter.
  An SRT carries no script resolution, so libass falls back to its default
  PlayRes (384×288) and scales the font up to the real 1080×1920 frame.
- Result: caption text rendered huge, wrapped into many lines, overflowed
  both sides of the frame (words clipped at the edges, not fully readable),
  and covered most of the picture including the speaker's face.
- Affected as posted: IMG_1398, IMG_1399 (and the first IMG_1436 encode).
  The user rejected them on sight: "it's not fitting inside the screen,
  it's not following the scales — I can't even see the whole text."

Root cause in one line: long cues + wrong PlayRes scaling. Fixing only the
font size is not enough; the cues themselves must be re-segmented, and the
subtitle script must declare the real frame size.

## The exact fix

### 1. Re-segment the SRT into short cues and emit ASS

Tool: `~/workspace/sf-naive/fix_captions.py`
(for other projects, copy this script — it is the canonical implementation).

```bash
python3 ~/workspace/sf-naive/fix_captions.py <input.srt> <output.ass>
# prints: cues: <N>
```

Re-segmentation rules implemented by the script (do not weaken them):

- Max **8 words** per cue and max **58 characters** per cue.
- Timing inside an original cue is split **proportionally to word count**
  of each chunk, with a minimum chunk duration of 1.0s, never extending
  past the original cue end.
- Each cue is wrapped to **at most 2 balanced lines**: texts of ≤30 chars
  stay on one line; longer texts are split at the word boundary that makes
  the two lines closest in length (`\N` line break in ASS).

### 2. ASS style — the frame must be declared, and these values are fixed

The generated ASS header is part of the fix. Verify it is present verbatim
in every fixed file:

```
[Script Info]
PlayResX: 1080
PlayResY: 1920
WrapStyle: 0

Style: Cap,DejaVu Sans,64,&H00FFFFFF,&H000000FF,&H00000000,&H64000000,-1,0,0,0,100,100,0,0,1,3,0,2,70,70,300,1
```

That is:

- `PlayResX=1080`, `PlayResY=1920` — matches the output frame exactly, so
  libass does no extra scaling. This is the single most important value.
- `FontSize=64` (at 1080 wide ≈ 64px cap height — readable, not dominant)
- Font: DejaVu Sans, Bold
- `Outline=3`, `Shadow=0`, white primary, black outline
- `Alignment=2` (bottom-center)
- `MarginL=70`, `MarginR=70` — no caption line can reach the frame edges
- `MarginV=300` — captions sit 300px above the bottom edge, clear of
  platform UI overlays at the bottom of 1080×1920 players

Programmatic pre-check before encoding (all must pass):

- Header contains `PlayResX: 1080` and `PlayResY: 1920`.
- Every `Dialogue:` line contains at most one `\N` (max 2 lines).
- No caption line exceeds ~31 characters (observed max on the verified
  2026-11-18 fixed set: 30–31 chars/line).

### 3. Encode with the ASS (never the raw SRT)

```bash
ffmpeg -i <input> \
  -vf "scale=1080:1920,subtitles=<fixed>.ass" \
  -c:v libx264 -preset veryfast -crf 20 \
  -c:a aac -b:a 160k -movflags +faststart <output>.mp4
```

- Burn the **ASS**, not the SRT.
- Output geometry is 1080×1920. (The SF source MOVs carry rotation=-90
  metadata and ffmpeg applies it automatically; do not add a transpose
  filter and do not "correct" the stored 1920×1080 stream dimensions
  by hand.)
- Verify the finished file with ffprobe (1080×1920, has an audio stream)
  on the final file only — probing a file that is still being written
  gives false "moov atom not found" errors.

## Mandatory verification gate — before any posting, no exceptions

A video that fails any check below **must not be posted**. Fix and
re-verify. "The encode finished" and "ffprobe looks right" are not
verification.

1. Extract **at least 3 frames per video** — early, middle, and late —
   choosing timestamps where a caption is actually on screen:

   ```bash
   ffmpeg -y -ss <seconds> -i <output>.mp4 -frames:v 1 qa_<video>_<t>.jpg
   ```

2. **Read every extracted frame with your own eyes** (open the image;
   do not rely on file size, pixel-diff numbers, or the encode log).
3. Confirm all of the following on every frame:
   - (a) Every caption line is **fully inside the frame** with visible
     margin on both sides — no clipped words at either edge.
   - (b) Captions are **max 2 lines** at any moment.
   - (c) Text height is roughly **64px at 1080 wide** — clearly readable
     but not covering the speaker's face or dominating the picture.
   - (d) Frames with no speech show **no caption** — do not misread a
     silent frame as a caption failure, and do not let a caption linger
     into a silent stretch.
4. Record the QA: which timestamps you extracted, and pass/fail per check
   (a)–(d), next to the video's production record.
5. **Show the user the actual artifact video before posting it**
   (standing user instruction, 2026-11-18). Posting first and showing
   later is a violation of this gate, for every video, every platform
   (X, LinkedIn, YouTube alike).

## Prepared fixed caption files (SF Naïve set, 2026-11-18)

Produced by `fix_captions.py` in `~/workspace/sf-naive/transcripts/`:

| Video | Fixed ASS | Cues |
|---|---|---|
| IMG_1398 | fixed-1398.ass | 67 |
| IMG_1399 | fixed-1399.ass | 59 |
| IMG_1436 | fixed-1436.ass | 101 |
| IMG_1413 | fixed-1413.ass | 207 |
| IMG_1494 | fixed-1494.ass | 253 |
| IMG_1495 | fixed-1495.ass | 207 |
| IMG_1496 | fixed-1496.ass | 212 |
| IMG_1504 | fixed-1504.ass | 204 |

All 8 files pass the programmatic pre-check: PlayRes 1080×1920,
max 2 lines per cue, max 31 chars per line.

## Rules that never bend

- Never burn a raw SRT with cues longer than 8 words / 58 chars.
- Never burn subtitles without a PlayRes that matches the output frame.
- Never post a captioned video whose frames you have not looked at.
- Never delete an already-posted (even defective) video to "fix" it —
  remake and repost; deletion only when the user explicitly names it.
