#!/usr/bin/env bash
set -euo pipefail
export PATH=/opt/homebrew/bin:/usr/local/bin:$PATH
source /Users/anicca/.openclaw/.env >/dev/null 2>&1 || true
WORK=/Users/anicca/.openclaw/workspace/reelclaw-widget-ja-$(date +%Y%m%d-%H%M%S)
mkdir -p "$WORK"
HOOK_SRC=/Users/anicca/.openclaw/workspace/tiktok-marketing/ugc-library/hooks/Woman_Reacts_with_Amazement_and_Joy.mp4
DEMO_SRC=/Users/anicca/anicca-project/assets/reelclaw/ja-widget-videos/self-hatred-affirmatino.MP4
HOOK_TEXT1='なんで誰も'
HOOK_TEXT2='教えてくれなかったの...'
FONT_JA='/System/Library/Fonts/ヒラギノ角ゴシック W6.ttc'
BGM='/Users/anicca/.openclaw/workspace/tiktok-marketing/music/bgm-cta.mp3'
OUT="$WORK/reel-final.mp4"
SILENT="$WORK/reel-text.mp4"

ffmpeg -y -hide_banner -loglevel error -ss 0 -t 3 -i "$HOOK_SRC" -vf "scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2:color=black,setsar=1,fps=30" -an -c:v libx264 -preset fast -crf 18 -movflags +faststart "$WORK/hook.mp4"
ffmpeg -y -hide_banner -loglevel error -i "$WORK/hook.mp4" -i "$DEMO_SRC" -filter_complex "[0:v]scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2,setsar=1,fps=30[v0];[1:v]scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2,setsar=1,fps=30[v1];[v0][v1]concat=n=2:v=1:a=0[outv]" -map "[outv]" -an -c:v libx264 -preset fast -crf 18 -movflags +faststart "$SILENT"
ffmpeg -y -hide_banner -loglevel error -i "$SILENT" -vf "drawtext=text='${HOOK_TEXT1}':fontfile=${FONT_JA}:fontsize=44:fontcolor=white:borderw=4:bordercolor=black:x=(60+(900-text_w)/2):y=320:enable='between(t,0,3)',drawtext=text='${HOOK_TEXT2}':fontfile=${FONT_JA}:fontsize=44:fontcolor=white:borderw=4:bordercolor=black:x=(60+(900-text_w)/2):y=380:enable='between(t,0,3)'" -c:v libx264 -preset fast -crf 18 -movflags +faststart "$SILENT.tmp.mp4"
mv "$SILENT.tmp.mp4" "$SILENT"
DUR=$(ffprobe -v quiet -show_entries format=duration -of csv=p=0 "$SILENT" | cut -d. -f1)
FADE=$((DUR-1)); [ "$FADE" -lt 0 ] && FADE=0
ffmpeg -y -hide_banner -loglevel error -i "$SILENT" -i "$BGM" -map 0:v -map 1:a -af "afade=t=in:st=0:d=0.5,afade=t=out:st=${FADE}:d=1,volume=0.8" -c:v copy -c:a aac -b:a 128k -shortest -movflags +faststart "$OUT"
ffprobe -v quiet -show_entries format=duration -of csv=p=0 "$OUT"
python3 - <<'PY'
import json, pathlib, os
path = pathlib.Path('/Users/anicca/.openclaw/workspace/tiktok-marketing/reelclaw-widget-rotation.json')
data = json.loads(path.read_text())
data['lastUsed']['W11'] = '2026-05-12'
data['lastUsed']['reelclaw-anicca-ja-widget-2'] = 'W11'
data['lastVideoByCron']['reelclaw-anicca-ja-widget-2'] = 'self-hatred-affirmatino.MP4'
data['history'].append({'date':'2026-05-12','cron':'reelclaw-anicca-ja-widget-2','hookId':'W11','demoVideo':'self-hatred-affirmatino.MP4'})
tmp = path.with_suffix(path.suffix + '.tmp')
tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')
os.replace(tmp, path)
json.loads(path.read_text())
print('rotation updated')
PY
python3 - <<'PY'
import os, json, urllib.request
api=os.environ.get('POSTIZ_API_KEY')
if not api:
    raise SystemExit('POSTIZ_API_KEY missing')
video='/Users/anicca/.openclaw/workspace/reelclaw-widget-ja-' + os.listdir('/Users/anicca/.openclaw/workspace')[-1] if False else None
PY
