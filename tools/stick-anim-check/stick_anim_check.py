#!/usr/bin/env python3
"""stick-anim-check — edge-clipping + format gate for faceless stick animations.

Winner format (Mau Baron article 2026-11-18, Step 6 check): both figures on
screen and acting by second 1, labels readable, NOTHING BROKEN — a figure or
arm leaving the frame is a break. This checker makes that rule mechanical:

  * mp4: ffprobe must show h264, 1080x1920, 30fps, ~11s.
  * frames at 1s and 10s (extracted to a temp dir, deleted after): no bright
    pixel (any channel > 100) may touch the outer 6px band on left or right.
    Figures/labels/app-name are bright on pure black, so any bright pixel in
    the band means something is clipped by the frame edge.
  * png: the same edge test on the single image.

Usage: stick_anim_check.py <file.mp4|file.png> [...]
Exit 0 = PASS (all files), 1 = FAIL. Free: Python stdlib + PIL + ffmpeg only.
"""
import json, os, shutil, subprocess, sys, tempfile
from PIL import Image

EDGE = 6
BRIGHT = 100

def edge_counts(path):
    im = Image.open(path).convert("RGB")
    w, h = im.size
    px = im.load()
    left = right = 0
    for y in range(h):
        for x in range(EDGE):
            if max(px[x, y]) > BRIGHT:
                left += 1
        for x in range(w - EDGE, w):
            if max(px[x, y]) > BRIGHT:
                right += 1
    return left, right

def check_png(path):
    l, r = edge_counts(path)
    ok = (l == 0 and r == 0)
    print(f"{'PASS' if ok else 'FAIL'} png {os.path.basename(path)} edge_bright left={l} right={r}")
    return ok

def check_mp4(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0",
                          "-show_entries", "stream=codec_name,width,height,r_frame_rate",
                          "-show_entries", "format=duration", "-of", "json", path],
                         capture_output=True, text=True)
    try:
        info = json.loads(out.stdout)
        st = info["streams"][0]
        dur = float(info["format"]["duration"])
        spec_ok = (st["codec_name"] == "h264" and st["width"] == 1080 and st["height"] == 1920
                   and st["r_frame_rate"].startswith("30/") and 10.5 <= dur <= 11.5)
    except Exception as e:
        print(f"FAIL mp4 {os.path.basename(path)} ffprobe: {e}")
        return False
    tmp = tempfile.mkdtemp(prefix="stickcheck-")
    ok = spec_ok
    try:
        for sec in (1, 10):
            fp = os.path.join(tmp, f"f{sec}.png")
            subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", str(sec), "-i", path,
                            "-frames:v", "1", fp], check=True, capture_output=True)
            l, r = edge_counts(fp)
            frame_ok = (l == 0 and r == 0)
            ok = ok and frame_ok
            print(f"  frame {sec}s edge_bright left={l} right={r} {'ok' if frame_ok else 'CLIPPED'}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print(f"{'PASS' if ok else 'FAIL'} mp4 {os.path.basename(path)} spec_ok={spec_ok}")
    return ok

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__); sys.exit(2)
    results = []
    for p in sys.argv[1:]:
        results.append(check_png(p) if p.lower().endswith(".png") else check_mp4(p))
    print(f"TOTAL {'PASS' if all(results) else 'FAIL'} {sum(results)}/{len(results)}")
    sys.exit(0 if all(results) else 1)
