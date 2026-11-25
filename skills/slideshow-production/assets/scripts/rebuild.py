# -*- coding: utf-8 -*-
"""勝者のダウンロード済み実物から作り直す (2026-11-15 本人指示).
背景 = anicca-ops files/winner-images-2026-11-15/ の勝者スライドそのもの (文字を inpaint で除去).
レイアウト・文字の置き方 = 勝者と同型. 変えるのは文面とフックだけ.
"""
import sys, json, pathlib
sys.path.insert(0, '/home/hatch/workspace/tools/cv2-lib')
import cv2, numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = pathlib.Path('/home/hatch/workspace')
WIN = ROOT/'anicca-ops/files/winner-images-2026-11-15'
OUT = pathlib.Path(__file__).parent
BGD = OUT/'clean_backgrounds'; BGD.mkdir(exist_ok=True)
FONTS = ROOT/'tools/fonts'
SERIF = '/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc'
SERIF_R = '/usr/share/fonts/opentype/noto/NotoSerifCJK-Regular.ttc'

def fredoka(size, weight=600):
    f = ImageFont.truetype(str(FONTS/'Fredoka.ttf'), size)
    try: f.set_variation_by_axes([weight, 100])
    except Exception: pass
    return f
def tiktok(size):
    """EN 面の勝者フォント: TikTok Sans Bold (2026-11-15 本人指摘で Fredoka から切替).
    実測根拠 (勝者 photo/7624115204804267272 vs 本日版 photo/7708235355358563604, digit "5" 同高57px):
    勝者 stem 8px / stroke 6px に対し Fredoka 600 は stem 11px / stroke 8px で太すぎた.
    TikTok Sans Bold は stem 9px で勝者に一致する."""
    f = ImageFont.truetype(str(FONTS/'TikTokSans.ttf'), size)
    try: f.set_variation_by_name('Bold')
    except Exception: pass
    return f
def maru(size):
    return ImageFont.truetype(str(FONTS/'ZenMaruGothic-Bold.ttf'), size)
def serif(size, bold=True):
    return ImageFont.truetype(SERIF if bold else SERIF_R, size)

# ---------- clean backgrounds (remove baked text via inpainting) ----------
def clean(img_path, out_name, white_thr=235, black_thr=None, row_thr=25, dilate=8, radius=7):
    img = cv2.imread(str(img_path))
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    h, w = gray.shape
    white = (gray > white_thr).astype(np.uint8)
    rowcount = white[:, int(w*0.06):int(w*0.94)].sum(axis=1)
    rows = np.where(rowcount > row_thr)[0]
    mask = np.zeros((h, w), np.uint8)
    if len(rows):
        # group contiguous row zones
        zones, start, prev = [], rows[0], rows[0]
        for r in rows[1:]:
            if r - prev > 30:
                zones.append((start, prev)); start = r
            prev = r
        zones.append((start, prev))
        for (a, b) in zones:
            a2, b2 = max(0, a-28), min(h, b+28)
            band = np.zeros((h, w), np.uint8)
            m = (gray[a2:b2] > white_thr)
            if black_thr is not None:
                m = m | (gray[a2:b2] < black_thr)
            band[a2:b2][m] = 255
            mask = cv2.bitwise_or(mask, band)
    mask = cv2.dilate(mask, np.ones((dilate, dilate), np.uint8))
    out = cv2.inpaint(img, mask, radius, cv2.INPAINT_TELEA)
    cv2.imwrite(str(BGD/out_name), out, [cv2.IMWRITE_JPEG_QUALITY, 92])
    return BGD/out_name

EN_BG, JP_BG, HV_BG = [], None, None
def make_backgrounds():
    global JP_BG, HV_BG
    for i in range(1, 6):
        EN_BG.append(clean(WIN/f'aniccaaffirmation_7624115204804267272_slide0{i}.jpg',
                           f'en_bg{i}.jpg', white_thr=243, black_thr=38, row_thr=25, dilate=4, radius=4))
    JP_BG = clean(WIN/'anicca.jp_7621795876935355655_slide01.jpg', 'jp_bg.jpg',
                  white_thr=240, black_thr=None, row_thr=25, dilate=7, radius=8)
    HV_BG = clean(WIN/'honnevideo_7705265545704197428_slide01.jpg', 'hv_cover_bg.jpg',
                  white_thr=236, black_thr=None, row_thr=12, dilate=7, radius=6)

# ---------- text helpers ----------
def wrap_en(text, font, max_w, draw):
    words = text.split()
    lines, cur = [], ''
    for wd in words:
        t = (cur + ' ' + wd).strip()
        if draw.textlength(t, font=font) <= max_w or not cur:
            cur = t
        else:
            lines.append(cur); cur = wd
    if cur: lines.append(cur)
    # balance 2 lines
    if len(lines) == 2 and abs(len(lines[0]) - len(lines[1])) > 12:
        words = text.split(); best = None
        for i in range(1, len(words)):
            l1, l2 = ' '.join(words[:i]), ' '.join(words[i:])
            if draw.textlength(l1, font=font) <= max_w and draw.textlength(l2, font=font) <= max_w:
                d = abs(draw.textlength(l1, font=font) - draw.textlength(l2, font=font))
                if best is None or d < best[0]: best = (d, [l1, l2])
        if best: lines = best[1]
    return lines

def en_text(img, text, cy_ratio=0.47, hook=False):
    """勝者同型: 白太字+黒縁+薄い影, 中央, 小文字."""
    d = ImageDraw.Draw(img)
    W, H = img.size
    t = text.lower()
    if hook and not t.endswith('...'): t += '...'
    if not hook and t.endswith('.'): t = t[:-1]
    size = 100 if hook else 92
    while size > 40:
        f = tiktok(size)
        lines = wrap_en(t, f, 940, d)
        if len(lines) <= 2 and all(d.textlength(l, font=f) <= 940 for l in lines): break
        size -= 6
    f = tiktok(size)
    lines = wrap_en(t, f, 940, d)
    sw = max(3, round(size * 0.075))  # 勝者実測の stroke 比 (digit 高57pxで6px). 旧: 固定8pxで太すぎた
    lh = int(size * 1.22)
    total = lh * len(lines)
    y = int(H * cy_ratio) - total // 2
    # soft shadow layer
    sh = Image.new('RGBA', img.size, (0, 0, 0, 0))
    ds = ImageDraw.Draw(sh)
    for l in lines:
        w = d.textlength(l, font=f)
        ds.text(((W - w) / 2 + 3, y + 5), l, font=f, fill=(0, 0, 0, 110), stroke_width=sw, stroke_fill=(0, 0, 0, 110))
        y += lh
    sh = sh.filter(ImageFilter.GaussianBlur(4))
    img.paste(Image.alpha_composite(img.convert('RGBA'), sh).convert('RGB'), (0, 0))
    d = ImageDraw.Draw(img)
    y = int(H * cy_ratio) - total // 2
    for l in lines:
        w = d.textlength(l, font=f)
        d.text(((W - w) / 2, y), l, font=f, fill=(255, 255, 255), stroke_width=sw, stroke_fill=(10, 10, 10))
        y += lh
    return img

def jp_text(img, text, cy_ratio=0.47, size=88):
    """勝者同型: 白い丸ゴシック, 中央, 縁なし."""
    d = ImageDraw.Draw(img)
    W, H = img.size
    lines = text.split('\n')
    while size > 40:
        f = maru(size)
        if all(d.textlength(l, font=f) <= 940 for l in lines): break
        size -= 6
    f = maru(size)
    lh = int(size * 1.55)
    total = lh * len(lines) - int(size * 0.4)
    y = int(H * cy_ratio) - total // 2
    for l in lines:
        w = d.textlength(l, font=f)
        d.text(((W - w) / 2, y), l, font=f, fill=(255, 255, 255))
        y += lh
    return img

def jp_split(phrase):
    """フレーズを勝者のように2行へ割る (助詞・読点の近くで)."""
    p = phrase.replace('「', '').replace('」', '')
    if len(p) <= 8: return p
    mids = [i for i, c in enumerate(p) if c in 'はがをにへとも、' and 3 <= i <= len(p) - 3]
    if mids:
        i = min(mids, key=lambda x: abs(x + 1 - len(p) / 2)) + 1
        return p[:i] + '\n' + p[i:]
    i = len(p) // 2
    return p[:i] + '\n' + p[i:]

def save(img, pack, name):
    pdir = OUT/pack; pdir.mkdir(exist_ok=True)
    p = pdir/name
    img.save(p, quality=92)
    return str(p)

manifest = {}

def en_pack(pack, hook, affs):
    files = []
    bgs = [EN_BG[0], EN_BG[1], EN_BG[2], EN_BG[3], EN_BG[4]]
    img = Image.open(bgs[0]).convert('RGB')
    files.append(save(en_text(img, hook, 0.485, hook=True), pack, 'slide01.jpg'))
    for i, a in enumerate(affs[:4]):
        img = Image.open(bgs[i + 1]).convert('RGB')
        files.append(save(en_text(img, a, 0.47), pack, f'slide{i + 2:02d}.jpg'))
    manifest[pack] = files

def jp_pack(pack, title, items):
    files = []
    img = Image.open(JP_BG).convert('RGB')
    files.append(save(jp_text(img, title, 0.47, 92), pack, 'slide01.jpg'))
    for i, it in enumerate(items[:4]):
        img = Image.open(JP_BG).convert('RGB')
        files.append(save(jp_text(img, jp_split(it), 0.47, 86), pack, f'slide{i + 2:02d}.jpg'))
    manifest[pack] = files

# ---------- Honne ----------
def sample_color(path, xy):
    im = Image.open(path).convert('RGB')
    return im.getpixel(xy)

def hv_pack(pack, upper, title, items, comments, closing_big):
    W, H = 1080, 1920
    beige = sample_color(WIN/'honnevideo_7705265545704197428_slide02.jpg', (60, 600))
    green = sample_color(WIN/'honnevideo_7705265545704197428_slide02.jpg', (540, 430))
    files = []
    # cover
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
    # items
    for i, (s, c) in enumerate(zip(items, comments)):
        img = Image.new('RGB', (W, H), beige)
        d = ImageDraw.Draw(img)
        d.line([(90, 150), (990, 150)], fill=green, width=4)
        f_n = serif(175)
        tw = d.textlength(str(i + 1), font=f_n)
        d.text(((W - tw) / 2, int(H * 0.175)), str(i + 1), font=f_n, fill=green)
        f_s = serif(94)
        tw = d.textlength(s, font=f_s)
        d.text(((W - tw) / 2, int(H * 0.475)), s, font=f_s, fill=(30, 28, 25))
        f_c = serif(55, bold=False)
        tw = d.textlength(c, font=f_c)
        d.text(((W - tw) / 2, int(H * 0.565)), c, font=f_c, fill=(105, 98, 88))
        f_a2 = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf', 52)
        tw = d.textlength('Anicca', font=f_a2)
        d.text(((W - tw) / 2, int(H * 0.945)), 'Anicca', font=f_a2, fill=green)
        files.append(save(img, pack, f'slide{i + 2:02d}.jpg'))
    # closing
    img = Image.new('RGB', (W, H), beige)
    d = ImageDraw.Draw(img)
    d.line([(90, 150), (990, 150)], fill=green, width=4)
    f_g = serif(58)
    t = '保存して、見返してね'
    tw = d.textlength(t, font=f_g)
    d.text(((W - tw) / 2, int(H * 0.385)), t, font=f_g, fill=green)
    y = int(H * 0.455)
    for l in closing_big:
        f_b = serif(118)
        tw = d.textlength(l, font=f_b)
        d.text(((W - tw) / 2, y), l, font=f_b, fill=(30, 28, 25))
        y += 160
    f_a2 = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf', 52)
    tw = d.textlength('Anicca', font=f_a2)
    d.text(((W - tw) / 2, int(H * 0.945)), 'Anicca', font=f_a2, fill=green)
    files.append(save(img, pack, 'slide07.jpg'))
    manifest[pack] = files

# ---------- data ----------
TA2 = {
 'ta2-1': ("5 affirmations to tell yourself in a quiet moment",
   ["Peace lives within me. I return to it whenever I need.", "I am safe in this moment. I am safe in this breath.", "Stillness is my home. Quiet is my native language.", "I am here, now. That is enough.", "This breath is enough. This moment is enough."]),
 'ta2-2': ("5 affirmations to tell yourself to come back to now",
   ["I am awake to the small wonders of my day.", "I do not need to chase. The moment finds me.", "I let this moment be exactly as it is.", "I return to my breath. I return to myself.", "I am present in this body, this place, this hour."]),
 'ta2-3': ("5 affirmations to tell yourself with gratitude",
   ["I am grateful for the breath I take, right this second.", "I am grateful for the body that carries me through today.", "Today, I notice what is good, and I let it grow.", "I am happy, healthy, and centered in myself.", "I have everything I need, exactly when I need it."]),
 'ta2-4': ("5 affirmations to tell yourself when you need to trust",
   ["I trust that life is unfolding as it needs to.", "I surrender my grip and let life meet me halfway.", "I trust the ground to hold me, even when I cannot see it.", "I do not have to know the whole path to take the next step.", "I trust that what I need will find me in time."]),
}
TS2 = {
 'ts2-1': ("5 affirmations to tell yourself when life feels hard",
   ["I have weathered hard days before, and I will weather this one too.", "I bend with the storm, and I do not break.", "Difficulty passes through me; it does not define me.", "I am still standing, and that is its own quiet victory.", "Every hardship has taught me something I needed to know."]),
 'ts2-2': ("5 affirmations to tell yourself to keep rising",
   ["I meet this challenge with steady, open hands.", "I am more resilient than my hardest moment.", "What is heavy today will be lighter tomorrow.", "I let difficulty soften me, not harden me.", "I rise, gently and surely, as many times as I need to."]),
 'ts2-3': ("5 affirmations to tell yourself to let go",
   ["I release what I cannot control, and I keep my peace.", "I let go of the need to have it all figured out.", "I loosen my grip, and I feel myself breathe again.", "What is meant to leave, I let leave.", "I set down the weight I was never meant to carry."]),
 'ts2-4': ("5 affirmations to tell yourself to make peace",
   ["I make peace with endings, and with what comes after.", "I release old stories that no longer serve me.", "I allow life to be uncertain, and I stay soft inside it.", "I let the river carry what is no longer mine.", "I open my hands, and I let the moment be free."]),
}
HE = {
 'he-1': ("心が軽くなる\n朝の口癖5選", ["まあ、なんとかなる", "今日は今日の私でいい", "比べるのは昨日の私だけ", "深呼吸してから決める", "小さな良いことを数える"]),
 'he-2': ("自分を責めない\n朝の言葉5選", ["失敗は、私の全部じゃない", "今日の私は、今日のままでいい", "責めるより、認めることから", "うまくいかない日も、進んでいる", "私は、私の味方でいる"]),
 'he-3': ("不安が和らぐ\n昼の言葉5選", ["不安は、波のように過ぎていく", "今できることは、ひとつだけ", "深呼吸。まず、それでいい", "最悪の想像は、まだ起きていない", "今日を乗り切れば、それで十分"]),
 'he-4': ("比べない心を作る\n言葉5選", ["あの人の速さは、私の速さじゃない", "昨日の私より、少しだけ前に", "比べる時間は、自分を育てる時間に", "私の歩幅で、ちゃんと進んでいる", "花は、隣と比べずに咲く"]),
}
OBOU = {
 'obou-1': ("心が静まる\n夜の口癖5選", ["今日もよくやった", "明日は明日の私に任せる", "比べた分だけ、深呼吸する", "できなかったことより、できたこと", "眠る前に、自分へありがとう"]),
 'obou-2': ("朝が軽くなる\n言葉5選", ["今日は、軽やかに始めよう", "朝の光は、私の味方", "昨日の重さは、置いていく", "まず一杯の水と、深呼吸", "今日の私に、期待していい"]),
 'obou-3': ("自分を許す\n夜の言葉5選", ["できなかった私も、許していい", "後悔は、学びに変えて手放す", "謝る勇気も、許す勇気も、私のもの", "完璧じゃなくても、愛される資格はある", "今夜は、自分に優しく閉じよう"]),
 'obou-4': ("不安な日に唱える\n言葉5選", ["不安な日は、無理に元気を出さない", "怖いのは、大事に思っている証拠", "今は嵐の中。でも、嵐は過ぎる", "支えてくれる人は、ちゃんといる", "今日は、生き延びるだけで花丸"]),
}
BUD2 = {
 'bud2-1': ("心が整う\n名言5選", ["焦る心は、深呼吸ひとつで整う", "静けさは、心の本来の場所", "整えるのは、環境より先に呼吸", "心の波は、眺めれば静まる", "今ここに戻れば、心は整う"]),
 'bud2-2': ("前を向ける\n言葉5選", ["下を向く日があっても、道は前にある", "昨日の涙は、今日の肥料", "一歩前へ。それだけで景色は変わる", "顔を上げれば、空はいつもそこにある", "前を向く勇気は、小さくていい"]),
 'bud2-3': ("自分を信じる\n名言5選", ["信じる力は、静かに育つ", "私の歩みは、私だけの正解", "迷いは、信じる心の途中経過", "自分を信じる人は、最後まで歩ける", "根拠のない自信も、始まりには十分"]),
 'bud2-4': ("不安が和らぐ\n言葉5選", ["不安は、未来からの借りもの", "まだ起きていないことに、怯えなくていい", "心配の9割は、現実にならない", "不安な夜も、朝は必ず来る", "息を吐くたび、不安も出ていく"]),
}
JPNEW = {
 'jp-1': ("心が整う\n朝の口癖5選", ["今日も、なんとかなる", "深呼吸してから、始める", "比べる相手は、昨日の私", "小さな一歩で、十分", "朝の光を、味方にする"]),
 'jp-2': ("気持ちが落ち着く\n昼の口癖5選", ["ひと息ついてから、返事する", "今は、今できることだけ", "気持ちは、天気と同じ", "焦る日は、空を見る", "大丈夫、ペースは自分で決める"]),
 'jp-3': ("自分を大切にする\n夜の口癖5選", ["今日の私に、ありがとう", "休むことは、前に進むこと", "私の気持ちも、大事な気持ち", "比べない夜を、自分にあげる", "明日の私に、優しく渡す"]),
 'jp-4': ("前を向ける\n朝の言葉5選", ["顔を上げれば、空がある", "昨日の涙は、今日の肥料", "一歩前へ、景色が変わる", "私の歩幅で、進んでいく", "今日も、私を生きる"]),
}
HV = {
 'hv2-1': ("脈ありサイン", "嬉しい確定\nセリフ5選",
   ["「今日も話せて嬉しい」", "「もっとあなたのこと知りたい」", "「次はいつ会える？」", "「帰ったら連絡してね」", "「あなたといると落ち着く」"],
   ["日常の報告が、あなた宛てになっている。", "知りたい気持ちは、好意の入口。", "次の約束を、自分から取りに来ている。", "無事を気にかけるのは、大事な人だけ。", "素でいられる相手は、限られている。"],
   ["言葉より、", "その後の行動を見て。"]),
 'hv2-2': ("距離が縮まるサイン", "また会いたい確定\nセリフ5選",
   ["「今度は二人で行きたい」", "「声聞くと安心する」", "「予定、空けておくね」", "「夢に出てきたよ」", "「もうちょっと一緒にいたい」"],
   ["二人きりを望むのは、距離を縮める合図。", "声が安心材料になるのは、特別な証拠。", "予定を先に押さえるのは、本気の準備。", "夢の話をするのは、口実を作っている。", "帰りたくないは、いちばん素直な言葉。"],
   ["また会いたいは、", "行動で伝わる。"]),
 'hv2-3': ("本音のサイン", "好き確定\nセリフ5選",
   ["「あなたの声、好きだな」", "「会うと元気出る」", "「ずっと話していたい」", "「今度、誘ってもいい？」", "「あなたは特別だよ」"],
   ["声への好意は、感情が動いている証拠。", "元気の理由にされるのは、特別な位置。", "時間を伸ばしたがるのは、好意の形。", "許可を求めるのは、慎重な本気。", "特別という言葉は、軽くは使わない。"],
   ["本音は、", "ふとした言葉に宿る。"]),
 'hv2-4': ("特別扱いのサイン", "特別確定\nセリフ5選",
   ["「あなたにだけ話すね」", "「他の人とは違うんだ」", "「秘密、共有したい」", "「あなたなら分かってくれる」", "「一番に連絡したよ」"],
   ["限定公開は、信頼のいちばん強い形。", "違いを言葉にするのは、意識している証拠。", "秘密の共有は、心の距離が近い証拠。", "理解者として選ばれている。", "一番の報告先は、いちばん大事な人。"],
   ["特別扱いは、", "隠しきれない。"]),
}

if __name__ == '__main__':
    import os
    if os.environ.get('EN_ONLY'):
        for i in range(1, 6):
            p = clean(WIN/f'aniccaaffirmation_7624115204804267272_slide0{i}.jpg',
                      f'en_bg{i}.jpg', white_thr=232, black_thr=48, row_thr=25, dilate=9, radius=7)
            img = cv2.imread(str(p)).astype(np.float32)
            blur = cv2.GaussianBlur(img, (0, 0), 6)
            h, w = img.shape[:2]
            band = np.zeros((h, w), np.float32)
            band[int(h*0.36):int(h*0.64), :] = 0.45
            band = cv2.GaussianBlur(band, (0, 0), 25)[..., None]
            out = (img * (1 - band) + blur * band).astype(np.uint8)
            cv2.imwrite(str(p), out, [cv2.IMWRITE_JPEG_QUALITY, 92])
            EN_BG.append(p)
        for pack, (hook, affs) in {**TA2, **TS2}.items():
            en_pack(pack, hook, affs)
        (OUT/'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=1))
        print('EN redone')
        sys.exit(0)
    make_backgrounds()
    for pack, (hook, affs) in {**TA2, **TS2}.items():
        en_pack(pack, hook, affs)
    for pack, (title, items) in {**HE, **OBOU, **BUD2, **JPNEW}.items():
        jp_pack(pack, title, items)
    for pack, (upper, title, items, comments, closing) in HV.items():
        hv_pack(pack, upper, title, items, comments, closing)
    (OUT/'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=1))
    print(json.dumps({k: len(v) for k, v in manifest.items()}, ensure_ascii=False))
    print('packs:', len(manifest))
