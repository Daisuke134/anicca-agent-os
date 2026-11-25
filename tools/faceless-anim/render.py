#!/usr/bin/env python3
"""Faceless animation renderer — built from Mau Baron's published system
(X article 2123034992485847041, 2026-11-18): PIL only + ffmpeg.
Style: pure black bg, two smooth white faceless figures (thick rounded
capsules, dark rim, soft glow, faint floor reflection), spaced capital
labels above figures, winner turns yellow + raises arms at second 9.
Templates: WALL / STAIRS / DOORS. One mp4 per scene from scenes.json.
"""
import json, math, os, subprocess, sys
from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H, FPS, DUR = 1080, 1920, 30, 11
FLOOR = 1560
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
WHITE = (245, 245, 245)
YELLOW = (255, 204, 0)
DARKRIM = (40, 40, 40)

def font(sz):
    return ImageFont.truetype(FONT, sz)

def spaced(s):
    return " ".join(list(s.replace(" ", "  ")))

def draw_label(d, cx, y, text, color, maxw=470):
    t = spaced(text)
    sz = 52
    while sz > 20:
        f = font(sz)
        if d.textlength(t, font=f) <= maxw:
            break
        sz -= 4
    f = font(sz)
    tw = d.textlength(t, font=f)
    d.text((cx - tw / 2, y), t, font=f, fill=color)

def capsule(d, x0, y0, x1, y1, wdt, fill, rim=DARKRIM):
    d.line([x0, y0, x1, y1], fill=rim, width=wdt + 6)
    d.line([x0, y0, x1, y1], fill=fill, width=wdt)
    r = wdt // 2
    for (px, py) in [(x0, y0), (x1, y1)]:
        d.ellipse([px - r, py - r, px + r, py + r], fill=fill)

def figure(d, cx, feet_y, color, pose="stand", t=0.0, win=False):
    """Draw one figure. feet_y = ground contact. Height ~430 standing."""
    hip_y = feet_y - 190
    sh_y = feet_y - 330
    head_r = 52
    if pose == "kneel":
        hip_y = feet_y - 110
        sh_y = feet_y - 250
        capsule(d, cx - 10, hip_y, cx - 55, feet_y - 6, 44, color)   # back leg folded
        capsule(d, cx + 6, hip_y, cx + 60, feet_y - 70, 44, color)   # front leg bent
        capsule(d, cx + 55, feet_y - 70, cx + 58, feet_y - 4, 44, color)
    else:
        step = 10 * math.sin(t * 4) if pose == "walk" else 0
        capsule(d, cx - 8, hip_y, cx - 34, feet_y - 2 + step, 46, color)
        capsule(d, cx + 8, hip_y, cx + 34, feet_y - 2 - step, 46, color)
    capsule(d, cx, hip_y + 10, cx, sh_y, 62, color)  # torso
    # arms
    if win:
        capsule(d, cx - 14, sh_y + 16, cx - 95, sh_y - 95, 40, color)
        capsule(d, cx + 14, sh_y + 16, cx + 95, sh_y - 95, 40, color)
    elif pose == "kneel":
        capsule(d, cx + 10, sh_y + 16, cx + 105, sh_y + 105, 38, color)  # reaching to brick
        capsule(d, cx - 10, sh_y + 16, cx - 60, sh_y + 90, 38, color)
    elif pose == "think":
        capsule(d, cx + 10, sh_y + 16, cx + 62, sh_y - 78, 38, color)  # hand to chin
        capsule(d, cx - 10, sh_y + 16, cx - 70, sh_y + 80, 38, color)
    elif pose == "knock":
        capsule(d, cx + 10, sh_y + 16, cx + 100, sh_y - 30, 38, color)
        capsule(d, cx - 10, sh_y + 16, cx - 66, sh_y + 84, 38, color)
    else:
        capsule(d, cx - 12, sh_y + 16, cx - 72, sh_y + 96, 40, color)
        capsule(d, cx + 12, sh_y + 16, cx + 72, sh_y + 96, 40, color)
    hy = sh_y - head_r - 16
    d.ellipse([cx - head_r - 3, hy - head_r - 3, cx + head_r + 3, hy + head_r + 3], fill=DARKRIM)
    d.ellipse([cx - head_r, hy - head_r, cx + head_r, hy + head_r], fill=color)
    return hy

def brick(d, x, y, bw=118, bh=52, fill=(168, 74, 52)):
    d.rounded_rectangle([x, y, x + bw, y + bh], radius=8, fill=fill, outline=(90, 40, 28), width=3)
    d.rectangle([x, y, x + bw, y + 10], fill=(196, 96, 66))

def render_scene(scene, outdir):
    tpl = scene["template"]
    frames = FPS * DUR
    tmp = os.path.join(outdir, f"frames_{scene['id']}")
    os.makedirs(tmp, exist_ok=True)
    for fi in range(frames):
        t = fi / FPS
        win = t >= 9.0
        rc = YELLOW if win else WHITE
        img = Image.new("RGB", (W, H), (0, 0, 0))
        glow = Image.new("RGB", (W, H), (0, 0, 0))
        gd = ImageDraw.Draw(glow)
        main = Image.new("RGB", (W, H), (0, 0, 0))
        d = ImageDraw.Draw(main)

        lx, rx = 272, 808
        if tpl == "WALL":
            # left: one brick, kneeling, red tool jitter
            brick(d, lx - 58, FLOOR - 52)
            jx = 8 * math.sin(t * 6)
            d.polygon([(lx + 96 + jx, FLOOR - 130), (lx + 128 + jx, FLOOR - 108), (lx + 100 + jx, FLOOR - 92)], fill=(220, 40, 40))
            figure(d, lx - 30, FLOOR, WHITE, pose="kneel", t=t)
            # right: wall grows row by row for 7s (5 rows x 3), then figure climbs
            rows = 5
            built = min(rows * 3, int((t / 7.0) * rows * 3) + (1 if t > 0 else 0))
            for i in range(built):
                r, c = divmod(i, 3)
                brick(d, rx - 177 + c * 118 + (59 if r % 2 else 0) - (59 if r % 2 else 0), FLOOR - 52 - (r + 1) * 52 + 52, fill=(150, 66, 46))
            wall_top = FLOOR - rows * 52
            if t < 7:
                figure(d, rx + 130, FLOOR, rc, pose="stand", t=t)
            else:
                k = min(1.0, (t - 7) / 2.0)
                fx = (rx + 130) + (rx - (rx + 130)) * k
                fy = FLOOR - (FLOOR - wall_top) * k
                figure(d, fx, fy - 52 if k >= 1 else fy, rc, pose="stand", t=t, win=win)
            figure(gd, lx - 30, FLOOR, (60, 60, 60), pose="kneel", t=t)
        elif tpl == "STAIRS":
            steps = 7
            for i in range(steps):
                x0 = 430 + i * 70
                y0 = FLOOR - (i + 1) * 62
                d.rectangle([x0, y0, x0 + 70, FLOOR], fill=(52, 52, 56), outline=(90, 90, 96))
            figure(d, lx, FLOOR, WHITE, pose="think", t=t)
            k = min(steps, int(t) + 0)
            fx = 430 + k * 70 + 8 if k > 0 else 400
            fy = FLOOR - k * 62
            if t < 1:
                fx, fy = 400, FLOOR
            figure(d, fx, fy, rc, pose="walk" if not win else "stand", t=t, win=win)
            figure(gd, lx, FLOOR, (60, 60, 60), pose="think", t=t)
        elif tpl == "DOORS":
            # left door (never opens) + left figure
            d.rectangle([lx - 95, FLOOR - 470, lx + 95, FLOOR], fill=(34, 34, 38), outline=(110, 110, 116), width=4)
            figure(d, lx - 190, FLOOR, WHITE, pose="stand", t=t)
            # right: 4 doors in a row behind/right, figure walks door to door
            doors_x = [560, 690, 820, 950]
            cur = min(3, int(t / 2.2))
            for i, dx in enumerate(doors_x):
                open_yellow = (i == 3 and t >= 8.0)
                fillc = (255, 204, 0) if open_yellow else (34, 34, 38)
                d.rectangle([dx - 52, FLOOR - 470, dx + 52, FLOOR], fill=fillc, outline=(110, 110, 116), width=4)
            fx = doors_x[cur] - 105
            figure(d, fx, FLOOR, rc, pose="knock" if not win else "stand", t=t, win=win)
            figure(gd, lx - 190, FLOOR, (60, 60, 60), pose="stand", t=t)

        # labels (winner label turns yellow with figure)
        draw_label(d, lx if tpl != "DOORS" else 285, 300, scene["left"], WHITE)
        draw_label(d, rx if tpl != "DOORS" else 800, 300, scene["right"], rc)
        # watermark
        wf = font(30)
        d.text((W / 2 - d.textlength("ANICCA", font=wf) / 2, H - 90), "ANICCA", font=wf, fill=(90, 90, 90))
        # glow composite + reflection
        glow = glow.filter(ImageFilter.GaussianBlur(18))
        img = Image.blend(img, glow, 0.35)
        refl = main.transpose(Image.FLIP_TOP_BOTTOM).crop((0, H - FLOOR, W, H))
        base = Image.new("RGB", (W, H), (0, 0, 0))
        base.paste(refl, (0, FLOOR))
        base = base.point(lambda p: int(p * 0.16))
        img = Image.blend(img, base, 0.5)
        img.paste(main, (0, 0), main.convert("L").point(lambda p: 255 if p > 12 else 0))
        img.save(os.path.join(tmp, f"f{fi:04d}.png"))
    out = os.path.join(outdir, f"{scene['id']:02d}-{tpl.lower()}.mp4")
    subprocess.run(["ffmpeg", "-y", "-framerate", str(FPS), "-i", os.path.join(tmp, "f%04d.png"),
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20", out],
                   check=True, capture_output=True)
    subprocess.run(["rm", "-rf", tmp])
    return out

if __name__ == "__main__":
    scenes = json.load(open(os.path.join(os.path.dirname(__file__), "scenes.json")))
    outdir = os.path.join(os.path.dirname(__file__), "out")
    os.makedirs(outdir, exist_ok=True)
    only = int(sys.argv[1]) if len(sys.argv) > 1 else None
    for s in scenes:
        if only and s["id"] != only:
            continue
        p = render_scene(s, outdir)
        print("rendered", p, os.path.getsize(p))
    with open(os.path.join(outdir, "captions.txt"), "w") as f:
        for s in scenes:
            f.write(f"{s['id']:02d} [{s['template']}] {s['caption']}\n")
    print("done")
