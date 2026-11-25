# ReelClaw import — inventory (fetched from Mac mini 2026-11-03)

## Source on Mac
- Skill body (only real copy): `/Users/anicca/.openclaw/workspace/skills/reelclaw/`
  - `~/.openclaw/skills/reelclaw` is a symlink to it.
  - `~/.kiro/skills/reelclaw` is a dangling symlink (target `~/.agents/skills/reelclaw` does not exist).
- No SKILL.md — the skill is a bash script suite (deterministic orchestrators, no LLM).

## What it does
- Lanes: widget-ja/en, card-ja/en, honne-ja/en (+honne-fresh-ja) — affirmation "widget/card" reels and Honne face/POV-style reels.
- Orchestrators (`skill/scripts/run-*.sh`): pick a hook text (LRU rotation from hook JSON), pick a random base-video variant from `reelclaw-assets/videos/<lane>/v*.mp4`, mux BGM with ffmpeg when the base is silent, then post.
- Posting route: **Postiz Public API** (`https://api.postiz.com/public/v1`) for all three platforms:
  - `post-video-to-instagram.sh` (instagram-standalone, post_type=post)
  - `post-video-to-tiktok.sh` (`__type: tiktok`, DIRECT_POST; warmup lanes post as draft UPLOAD per `state/postiz-integrations.json`; `video_made_with_ai: true`, autoAddMusic)
  - `post-video-to-youtube.sh` (YouTube Short, public, not made for kids)
- Older/alternate creation pipeline `create-ugc-reel.sh`: mcporter → DanSUGC MCP (search/purchase UGC reaction clips) + ffmpeg + node-canvas overlay. A 2026-03-17 run folder (`~/reelclaw-ja-20260317-1330/`, error JSON kept in `evidence/`) shows it failing with "Unknown MCP server 'dansugc'".
- On the Mac it is driven by launchd (`ai.anicca.reelclaw-*` plists in `~/profitable-claude/launchd/plists/`, one sample in `launchd/`) and workspace runner scripts (one sample in `runners/`).

## Copied here
- `skill/` — complete skill (14 scripts + hookPool-ja.txt), sizes verified against Mac.
- `tests/` — `~/.openclaw/tests/reelclaw` (3 pytest files).
- `specs/` — hook source-of-truth fix spec (39,851 B).
- `state/postiz-integrations.json` — Postiz integration registry (IDs + warmup phases; operational config, not a credential).
- `hooks/` — only honne-hooks-en.json / honne-hooks-ja.json (from `~/.openclaw/workspace/honne-ai/`).
- `ASSETS-README.md`, `assets-manifest.txt` — asset tree documentation/manifest.
- `launchd/`, `runners/`, `evidence/` — samples/evidence.

## NOT copied / gaps to run it on the VM
1. **Base videos not copied**: `~/.openclaw/workspace/reelclaw-assets/` = 163 MB, 25 files (v1–v4 mp4 per lane + `music/anicca-bgm.mp3`). Link is slow (~112 KB per 20 s); manifest is in `assets-manifest.txt`. Copy on demand before running lanes.
2. **4 of 6 hook JSONs are missing on the Mac itself** (dangling symlinks in `reelclaw-assets/hooks/`): `tiktok-marketing/hooks-en.json`, `hooks-ja.json`, `reelclaw-widget-hooks-en.json`, `reelclaw-widget-hooks-ja.json` do not exist. Card/widget lanes have no hook source until these are restored/regenerated. Only honne hooks exist.
3. **POSTIZ_API_KEY**: scripts read it from env; on the Mac it lives in `~/.openclaw/.env` (key present — value never read or copied). The VM needs its own Postiz key + the integration IDs from `state/postiz-integrations.json` (those IDs belong to the Mac-side Postiz org; verify they match the VM's Postiz connection before use).
4. **Runtime deps**: bash, ffmpeg/ffprobe, python3; UGC pipeline additionally needs mcporter + DanSUGC MCP + node-canvas + `skills/larry` scripts + font `~/Library/Fonts/TikTokSansDisplayBold.ttf`.
5. Scripts hardcode Mac paths (`$HOME/.openclaw/workspace/...`) — path remap needed on the VM.
6. BGM file referenced by runners: `~/.openclaw/workspace/tiktok-marketing/music/bgm-cta.mp3` (inside the un-copied asset tree).

Note: SSH from this VM must pass `-i /home/hatch/.ssh/id_ed25519` explicitly — OpenSSH resolves `~` in the config's IdentityFile to /root (process runs as root with HOME=/home/hatch), so the plain `mac-mini` alias offers no key. scp must run serially; parallel connections through the proxy are closed.
