# -*- coding: utf-8 -*-
"""@honne_reveal 用 HR3 パック (2026-11-15 本人確定: 日本語面・@honnevideo 勝者形式).
ビルダーは dist-production-2026-11-15-1015-rebuild/rebuild.py の hv_pack と同一.
背景 = 勝者スライドから文字除去済みの clean_backgrounds/hv_cover_bg.jpg を再利用.
変えるのは文面とフックだけ. 旧勝者 @sentimental.texting の iMessage 型は使わない.
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

HR3 = {
 'hr3-1': ("両想いのサイン", "両想い確定\nセリフ5選",
   ["「今、同じこと考えてた」", "「気が合うって、こういうこと」", "「言わなくても伝わるね」", "「偶然じゃなくて必然だね」", "「二人だと時間が早い」"],
   ["同じタイミングは、心が同期している証拠。", "合う感覚は、無理に作れない。", "以心伝心は、距離が近い証拠。", "必然と感じるのは、特別な相手だけ。", "時間の感覚が変わるのは、夢中の証拠。"],
   ["両想いは、", "小さな一致に宿る。"]),
 'hr3-2': ("独占欲のサイン", "独占欲確定\nセリフ5選",
   ["「他の人と話すの、やだな」", "「一番近くにいたい」", "「取られたくないんだ」", "「休みの日、空いてる？」", "「返信、早い方だと思う」"],
   ["嫉妬を隠さないのは、本気の証拠。", "一番の位置を望むのは、特別な証拠。", "素直な独占欲は、好意の裏返し。", "予定を押さえに来るのは、優先の証拠。", "返信の速さは、意識の表れ。"],
   ["独占欲は、", "本気の裏側にある。"]),
 'hr3-3': ("甘えのサイン", "甘え確定\nセリフ5選",
   ["「今日、声聞きたかった」", "「そばにいていい？」", "「元気、分けてもらった」", "「素でいられるの、あなただけ」", "「もう少しだけ、ここにいたい」"],
   ["声を求めるのは、心の拠り所の証拠。", "そばを求めるのは、安心の証拠。", "元気の出どころは、特別な人。", "素を見せられる相手は、限られている。", "離れがたさは、いちばん正直な気持ち。"],
   ["甘えるのは、", "心を許した証拠。"]),
 'hr3-4': ("照れのサイン", "照れ確定\nセリフ5選",
   ["「目、合わせられない」", "「褒められると弱いんだ」", "「顔、赤くなってない？」", "「そういうの、ずるい」", "「意識しちゃうじゃん」"],
   ["視線を逸らすのは、意識の証拠。", "褒め言葉に弱いのは、嬉しい証拠。", "自分で気づくほど、動揺している。", "ずるいと言うのは、効いている証拠。", "意識の言葉は、好意の入口。"],
   ["照れは、", "気持ちの漏れ出し。"]),
 'hr3-5': ("懐きのサイン", "懐いてる確定\nセリフ5選",
   ["「あなたにだけ、弱音を吐く」", "「いちばんに報告したかった」", "「相談相手は、あなたがいい」", "「近くにいると落ち着く」", "「離れたくないな」"],
   ["弱音の宛先は、いちばん信頼する人。", "一番の報告は、一番の存在の証拠。", "相談相手に選ぶのは、信頼の形。", "落ち着ける場所は、心の帰る場所。", "離れがたさは、懐いた証拠。"],
   ["懐くのは、", "心が帰る場所だから。"]),
 'hr3-6': ("守りたいのサイン", "守りたい確定\nセリフ5選",
   ["「何かあったら、すぐ呼んで」", "「送っていくよ」", "「無事が一番大事」", "「困ったら頼ってね」", "「そばで見守ってる」"],
   ["呼ばれる前提で待つのは、守る側の証拠。", "送る申し出は、心配の表れ。", "無事を願うのは、大事な人だけ。", "頼る先に名乗り出るのは、本気の証拠。", "見守る姿勢は、静かな愛情。"],
   ["守りたいは、", "行動に先に出る。"]),
 'hr3-7': ("未来のサイン", "未来確定\nセリフ5選",
   ["「来年も一緒にいたい」", "「二人で行きたい場所、ある」", "「将来、想像できるんだ」", "「予定は二人で決めたい」", "「先の話、していい？」"],
   ["来年の話は、未来にあなたがいる証拠。", "行きたい場所に二人を置いている。", "想像の中にいるのは、特別な証拠。", "予定を共有するのは、人生の共有。", "先の話の許可を求めるのは、慎重な本気。"],
   ["未来の話は、", "本気の人にだけする。"]),
 'hr3-8': ("本命のサイン", "本命確定\nセリフ5選",
   ["「あなたが本命だよ」", "「他とは比べられない」", "「気持ちは決まってる」", "「選ぶなら、あなただけ」", "「真剣に向き合いたい」"],
   ["本命と口にするのは、覚悟の証拠。", "比べられない存在は、一人だけ。", "決まった気持ちは、迷いがない証拠。", "選択肢が一人なのは、本気の形。", "真剣の言葉は、軽くは言えない。"],
   ["本命は、", "言葉と行動が一致する。"]),
}

if __name__ == '__main__':
    for pack, (upper, title, items, comments, closing) in HR3.items():
        hv_pack(pack, upper, title, items, comments, closing)
    (OUT/'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=1))
    print(json.dumps({k: len(v) for k, v in manifest.items()}, ensure_ascii=False))
