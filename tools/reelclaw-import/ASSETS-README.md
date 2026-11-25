# reelclaw-assets — canonical location for ALL reelclaw video posting assets

**Authority**: Dais 2026-06-08 — "no Desktop / Downloads / external dirs ever. internal only, simple."
**Total size**: ~371 MB (as of 2026-06-08)
**Source of moves**: ~/Desktop/honne/, ~/Desktop/FINAL-*.mp4, ~/anicca-iam-feed/work/, ~/.openclaw/workspace/honne-ai/, ~/.openclaw/workspace/reelclaw-bootstrap/

## ★ HARD RULE ★

★ All reelclaw scripts (run-card-en/ja, run-widget-en/ja, run-honne-en/ja) MUST point to paths under `~/.openclaw/workspace/reelclaw-assets/` ★. Never reference Desktop, Downloads, anicca-iam-feed, or any external location.

## Structure

```
reelclaw-assets/
├── README.md                      (this file)
├── music/
│   └── anicca-bgm.mp3             (= STATIC BGM used across all reelclaw video posts; ffmpeg attach via build_reel.sh pattern)
├── hooks/                         (= symlinks to live hook JSONs; caption text rotation source)
│   ├── card-en.json    →  ~/.openclaw/workspace/tiktok-marketing/hooks-en.json (filter family=reelclaw-card)
│   ├── card-ja.json    →  ~/.openclaw/workspace/tiktok-marketing/hooks-ja.json (same)
│   ├── widget-en.json  →  ~/.openclaw/workspace/tiktok-marketing/reelclaw-widget-hooks-en.json
│   ├── widget-ja.json  →  ~/.openclaw/workspace/tiktok-marketing/reelclaw-widget-hooks-ja.json
│   ├── honne-en.json   →  ~/.openclaw/workspace/honne-ai/honne-hooks-en.json
│   └── honne-ja.json   →  ~/.openclaw/workspace/honne-ai/honne-hooks-ja.json
└── videos/                        (= pre-baked hook+demo+BGM .mp4 variants; scripts pick random each fire)
    ├── card-en/                   (= 3 variants: v1=en-card-1, v2=FINAL-card-en-v3, v3=FINAL-card-en-v4)
    │   ├── v1.mp4
    │   ├── v2.mp4
    │   └── v3.mp4
    ├── card-ja/                   (= 3 variants: v1=reelclaw-ja-2, v3, v4)
    ├── widget-en/                 (= 7 variants: v0=FINAL-widget-en, v1=iam-feed backup, v2..v6)
    ├── widget-ja/                 (= 4 variants: v1=bootstrap, v2..v4)
    ├── honne-en/
    │   ├── v1.mp4                 (= honne-en-sample-v1-with-bgm — for IG/YT or TT)
    │   ├── v2.mp4                 (= sample-v2-with-bgm — alt)
    │   ├── v3-silent.mp4          (= silent track — DON'T USE for TT, no music)
    │   └── demos-raw/             (= 27 raw demo clips for future variety builder, hook+demo combo generator)
    └── honne-ja/                  (= 5 variants: v1=honne-ai reel-final + v1-v4 FINAL baked)
```

## Hook counts (= caption rotation source)

| family | hook count | source JSON |
|---|---|---|
| card-en | 144 (filter family=reelclaw-card) | hooks-en.json |
| card-ja | 182 (filter family=reelclaw-card) | hooks-ja.json |
| widget-en | 12 | reelclaw-widget-hooks-en.json |
| widget-ja | 12 | reelclaw-widget-hooks-ja.json |
| honne-en | 25 | honne-hooks-en.json |
| honne-ja | 0 (empty in file — check honne-mapping.json fallback) | honne-hooks-ja.json |

## Music — single static file

All reelclaw video posts use `~/.openclaw/workspace/reelclaw-assets/music/anicca-bgm.mp3` (= 1 canonical file, same music every post). Embedded via ffmpeg at video build time.

Reference pattern (run-honne-ja `build_reel.sh`):
```
ffmpeg -i $REEL_NOTEXT -i music/anicca-bgm.mp3 -map 0:v -map 1:a -af "afade=in/out" -c:v copy -c:a aac ...
```

## NOT for OSS / Capafy distribution

★ UGC hook video assets owned by Dais personally (Dan UGC licensed) ★ — cannot be redistributed via Capafy, OSS, or external skill sale. reelclaw skill = internal use only.

## How hooks/demos imported per cron run

- ★ Hooks ★: read locally from `hooks/<family>.json` at cron fire time (= no API call, no MCP)
- ★ Videos ★: read locally from `videos/<family>/v*.mp4` (= no per-cron import from Dan UGC API)
- ★ Music ★: read locally from `music/anicca-bgm.mp3`

= all local, no external dependency per cron. Re-stock = manual Dais update when new UGC clips arrive (= `cp newvideo.mp4 ~/.openclaw/workspace/reelclaw-assets/videos/<family>/vN.mp4`).


## BAKE STATUS (= 2026-06-08 M1 complete)

All 25 video variants now have BGM baked throughout (verified via ffmpeg volumedetect at 0s, mid, end-1s):

| family | variants | mean_vol range |
|---|---|---|
| card-en | 3 (v1, v2, v3) | -12 to -26 dB ✓ |
| card-ja | 3 (v1, v3, v4) | -12 to -24 dB ✓ |
| widget-en | 7 (v0..v6) | -12 to -24 dB ✓ |
| widget-ja | 4 (v1..v4) | -12 to -24 dB ✓ |
| honne-en | 3 (v1, v2, v3) | -16 to -24 dB ✓ |
| honne-ja | 5 (v1, v1-final..v4-final) | -12 to -38 dB ✓ |

★ Re-bake any new variant added in the future via:
```
ffmpeg -i <new>.mp4 -i music/anicca-bgm.mp3 -map 0:v -map 1:a -af "afade=t=in:st=0:d=0.5,afade=t=out:st=$((DUR-1)):d=1,volume=0.8" -c:v copy -c:a aac -b:a 128k -shortest <new>-bgm.mp4
```
