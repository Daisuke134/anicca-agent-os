# -*- coding: utf-8 -*-
"""@honnevideo HV2-1〜4 の端切れ修正版 (2026-11-15 緊急修正).
ビルダーは dist-production-2026-11-15-hr3-reveal/build_hr3.py の hv_pack と同一
(自動縮小 fit() 入り). 文面データは dist-production-2026-11-15-1015-rebuild/rebuild.py
の HV と同一 (hv_data.json). 欠陥版は固定サイズで長文セリフが両端切れしていた.
コピー元: @honnevideo 自社勝者「大好き確定セリフ5選」
https://www.tiktok.com/@honnevideo/photo/7705265545704197428
"""
import json, pathlib
from PIL import Image, ImageDraw, ImageFont

ROOT = pathlib.Path('/home/hatch/workspace')
WIN = ROOT/'anicca-ops/files/winner-images-2026-11-15'
REBUILD = ROOT/'goals/anicca-revenue-growth-as-life-manager/hidden_files/dist-production-2026-11-15-1015-rebuild'
HV_BG = REBUILD/'clean_backgrounds/hv_cover_bg.jpg'
OUT = pathlib.Path(__file__).parent
SERIF = '/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc'
SERIF_R = '/usr/share/fonts/opentype/noto/NotoSerifCJK-Regular.ttc'

def serif(size, bold=True):
    return ImageFont.truetype(SERIF if bold else SERIF_R, size)

def sample_color(path, xy):
    return Image.open(path).convert('RGB').getpixel(xy)

def save(img, pack, name):
    pdir = OUT/pack; pdir.mkdir(exist_ok=True)
    p = pdir/name
    img.save(p, quality=92)
    return str(p)

manifest = {}

def fit(draw, text, max_size, bold=True, limit=1000):
    """勝者の余白に合わせて、はみ出す場合だけサイズを下げる (HV2-1 slide03 の文字切れ対策)."""
    size = max_size
    while size > 30:
        f = serif(size, bold)
        if draw.textlength(text, font=f) <= limit: return f
        size -= 4
    return serif(size, bold)

def hv_pack(pack, upper, title, items, comments, closing_big):
    W, H = 1080, 1920
    beige = sample_color(WIN/'honnevideo_7705265545704197428_slide02.jpg', (60, 600))
    green = sample_color(WIN/'honnevideo_7705265545704197428_slide02.jpg', (540, 430))
    files = []
    img = Image.open(HV_BG).convert('RGB')
    d = ImageDraw.Draw(img)
    f_up = serif(56)
    tw = d.textlength(upper, font=f_up)
    d.text(((W - tw) / 2, int(H * 0.535)), upper, font=f_up, fill=(255, 255, 255))
    y = int(H * 0.605)
    for l in title.split('\n'):
        f_t = serif(124)
        tw = d.textlength(l, font=f_t)
        d.text(((W - tw) / 2, y), l, font=f_t, fill=(255, 255, 255))
        y += 165
    f_a = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf', 46)
    tw = d.textlength('Anicca', font=f_a)
    d.text(((W - tw) / 2, int(H * 0.945)), 'Anicca', font=f_a, fill=(255, 255, 255))
    files.append(save(img, pack, 'slide01.jpg'))
    for i, (s, c) in enumerate(zip(items, comments)):
        img = Image.new('RGB', (W, H), beige)
        d = ImageDraw.Draw(img)
        d.line([(90, 150), (990, 150)], fill=green, width=4)
        f_n = serif(175)
        tw = d.textlength(str(i + 1), font=f_n)
        d.text(((W - tw) / 2, int(H * 0.175)), str(i + 1), font=f_n, fill=green)
        f_s = fit(d, s, 94)
        tw = d.textlength(s, font=f_s)
        d.text(((W - tw) / 2, int(H * 0.475)), s, font=f_s, fill=(30, 28, 25))
        f_c = fit(d, c, 55, bold=False)
        tw = d.textlength(c, font=f_c)
        d.text(((W - tw) / 2, int(H * 0.565)), c, font=f_c, fill=(105, 98, 88))
        f_a2 = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf', 52)
        tw = d.textlength('Anicca', font=f_a2)
        d.text(((W - tw) / 2, int(H * 0.945)), 'Anicca', font=f_a2, fill=green)
        files.append(save(img, pack, f'slide{i + 2:02d}.jpg'))
    img = Image.new('RGB', (W, H), beige)
    d = ImageDraw.Draw(img)
    d.line([(90, 150), (990, 150)], fill=green, width=4)
    f_g = serif(58)
    t = '保存して、見返してね'
    tw = d.textlength(t, font=f_g)
    d.text(((W - tw) / 2, int(H * 0.385)), t, font=f_g, fill=green)
    y = int(H * 0.455)
    for l in closing_big:
        f_b = fit(d, l, 118)
        tw = d.textlength(l, font=f_b)
        d.text(((W - tw) / 2, y), l, font=f_b, fill=(30, 28, 25))
        y += 160
    f_a2 = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf', 52)
    tw = d.textlength('Anicca', font=f_a2)
    d.text(((W - tw) / 2, int(H * 0.945)), 'Anicca', font=f_a2, fill=green)
    files.append(save(img, pack, 'slide07.jpg'))
    manifest[pack] = files

if __name__ == '__main__':
    HV = json.loads((OUT/'hv_data.json').read_text())
    for pack, (upper, title, items, comments, closing) in HV.items():
        hv_pack(pack, upper, title, items, comments, closing)
    (OUT/'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=1))
    print(json.dumps({k: len(v) for k, v in manifest.items()}, ensure_ascii=False))
