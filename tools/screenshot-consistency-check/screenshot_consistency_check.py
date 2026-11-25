#!/usr/bin/env python3
"""Screenshot Consistency Gate — App Store スクリーンショット全ロケール一貫性判定器.

全ロケールのスクリーンショットセットについて、決定的に PASS/FAIL を出す:
  Gate A 枚数: 全セットでファイル数が一致すること
  Gate B 解像度: 全画像の (width, height) が完全一致すること
  Gate C バンド高さ: 見出しバンドの高さ (px) が全画像で中央値 ±2px 以内
  Gate D 部品高さ: 見出しの部品高さ (px) がロケール別に中央値 ±3px 以内
    (2026-11-17 改訂。旧定義は「見出し行ランの最大高さを全画像の中央値 ±3px」)

定義:
  - 背景色 = 各画像の (5,5) ピクセル (見出しバンドの地色)
  - インク行 = 背景色との差分 (RGB 各チャンネル絶対差の合計 > 60) のピクセルが
    2px 間引きサンプルで 4 個以上ある行
  - 見出し行ラン = バンド領域内のインク行の連続。アプリ画面本体は高さ 250px 以上の
    ランとして検出し、その開始行をバンド高さとする
  - グリフ高さ (画像単位・参考値) = その画像の見出し行ランの最大高さ
    (ascender から descender までを含む行が代表値になる)
  - 部品高さ (画像単位・Gate D の対象) = バンド領域 (バンド高さより上の行) の
    インク画素について連結成分 (8近傍) を求め、その最大成分の高さ
    (成分の最下行 - 最上行 + 1)。1グリフの実描画高さであり、行の文字構成
    (ディセンダやアクセントの有無) や書体系統差 (CJK は字面いっぱいに描かれ
    Latin より行エクステントが系統的に大きい) の影響を受けない。
    そのため Gate D は全体中央値ではなくロケール別の中央値で判定する

使い方:
  python3 screenshot_consistency_check.py \
      --set en=/path/to/en --set ja=/path/to/ja --set es=/path/to/es \
      [--out report.json]
終了コード: 0 = PASS, 1 = FAIL, 2 = 入力エラー
依存: Python 標準ライブラリのみ (PNG デコーダ内蔵)
"""

import argparse
import json
import statistics
import struct
import sys
import zlib
from pathlib import Path

# --- 許容差 (ゲート仕様の正本は anicca-ops files/screenshot-consistency-gate-2026-11-17.md)
BAND_TOL_PX = 2        # Gate C: バンド高さの許容差 (全体中央値 ±)
COMPONENT_TOL_PX = 3   # Gate D: 部品高さの許容差 (ロケール別中央値 ±)
SCAN_ROWS = 1400       # バンド検出のために読む最大行数
CONTENT_RUN_MIN = 250  # これ以上の高さのランはアプリ画面本体とみなす
MIN_LINE_ROWS = 4      # これ未満のランはノイズとして見出し行に数えない
INK_DIFF_SUM = 60      # 背景色との差分閾値 (RGB 絶対差の合計)
INK_MIN_SAMPLES = 4    # インク行とみなす最小サンプル数 (2px 間引き)


# ---------------------------------------------------------------- PNG decoder
def read_png_rgb(path: Path, max_rows: int):
    """PNG を読み、(width, height, rows) を返す。rows は RGB bytes のリスト (先頭 max_rows 行)。
    対応: bit depth 8, color type 0/2/3/4/6, 非インターレース。"""
    data = path.read_bytes()
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError(f"not a PNG: {path}")
    pos = 8
    idat = bytearray()
    plte = None
    width = height = bitdepth = colortype = interlace = None
    while pos < len(data):
        (length,) = struct.unpack(">I", data[pos:pos + 4])
        ctype = data[pos + 4:pos + 8]
        chunk = data[pos + 8:pos + 8 + length]
        if ctype == b"IHDR":
            width, height, bitdepth, colortype, _comp, _filt, interlace = struct.unpack(
                ">IIBBBBB", chunk)
        elif ctype == b"PLTE":
            plte = chunk
        elif ctype == b"IDAT":
            idat.extend(chunk)
        elif ctype == b"IEND":
            break
        pos += 12 + length
    if bitdepth != 8 or interlace != 0:
        raise ValueError(f"unsupported PNG (bitdepth={bitdepth}, interlace={interlace}): {path}")
    channels = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}[colortype]
    stride = width * channels
    want_rows = min(max_rows, height)
    want_bytes = want_rows * (stride + 1)
    dobj = zlib.decompressobj()
    raw = dobj.decompress(bytes(idat), want_bytes + stride + 1)
    rows = []
    prev = bytearray(stride)
    off = 0
    for _ in range(want_rows):
        if off + stride + 1 > len(raw):
            break
        ftype = raw[off]
        line = bytearray(raw[off + 1:off + 1 + stride])
        off += stride + 1
        if ftype == 1:  # Sub
            for i in range(channels, stride):
                line[i] = (line[i] + line[i - channels]) & 0xFF
        elif ftype == 2:  # Up
            for i in range(stride):
                line[i] = (line[i] + prev[i]) & 0xFF
        elif ftype == 3:  # Average
            for i in range(stride):
                left = line[i - channels] if i >= channels else 0
                line[i] = (line[i] + ((left + prev[i]) >> 1)) & 0xFF
        elif ftype == 4:  # Paeth
            for i in range(stride):
                a = line[i - channels] if i >= channels else 0
                b = prev[i]
                c = prev[i - channels] if i >= channels else 0
                p = a + b - c
                pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
                pred = a if (pa <= pb and pa <= pc) else (b if pb <= pc else c)
                line[i] = (line[i] + pred) & 0xFF
        elif ftype != 0:
            raise ValueError(f"unsupported filter {ftype}: {path}")
        # RGB へ正規化
        if colortype == 2:
            rows.append(bytes(line))
        elif colortype == 6:
            rgb = bytearray(width * 3)
            rgb[0::3] = line[0::4]
            rgb[1::3] = line[1::4]
            rgb[2::3] = line[2::4]
            rows.append(bytes(rgb))
        elif colortype == 0:
            rgb = bytearray(width * 3)
            rgb[0::3] = line
            rgb[1::3] = line
            rgb[2::3] = line
            rows.append(bytes(rgb))
        elif colortype == 3:
            rgb = bytearray(width * 3)
            for x in range(width):
                idx = line[x] * 3
                rgb[x * 3:x * 3 + 3] = plte[idx:idx + 3]
            rows.append(bytes(rgb))
        elif colortype == 4:
            rgb = bytearray(width * 3)
            rgb[0::3] = line[0::2]
            rgb[1::3] = line[0::2]
            rgb[2::3] = line[0::2]
            rows.append(bytes(rgb))
        prev = line
    return width, height, rows


def png_size(path: Path):
    """IHDR だけ読んで (width, height) を返す。"""
    with path.open("rb") as f:
        head = f.read(33)
    if head[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError(f"not a PNG: {path}")
    width, height = struct.unpack(">II", head[16:24])
    return width, height


# ------------------------------------------------------------------- analysis
def max_component_height(rows, width, bg_rgb, y_limit):
    """バンド領域 (y < y_limit) のインク画素の連結成分 (8近傍) のうち最大の高さを返す。
    インクの定義は行判定と同じ (背景色との RGB 絶対差の合計 > INK_DIFF_SUM)。
    インクが無い・領域が空なら 0。"""
    br, bgc, bb = bg_rgb
    n_rows = min(y_limit, len(rows))
    if n_rows <= 0:
        return 0
    ink_rows = []
    for y in range(n_rows):
        row = rows[y]
        xs = set()
        for x in range(width):
            i = x * 3
            if (abs(row[i] - br) + abs(row[i + 1] - bgc) + abs(row[i + 2] - bb)) > INK_DIFF_SUM:
                xs.add(x)
        ink_rows.append(xs)
    visited = [set() for _ in ink_rows]
    best = 0
    for y in range(n_rows):
        for x in ink_rows[y]:
            if x in visited[y]:
                continue
            stack = [(x, y)]
            visited[y].add(x)
            min_y = max_y = y
            while stack:
                cx, cy = stack.pop()
                if cy < min_y:
                    min_y = cy
                if cy > max_y:
                    max_y = cy
                for dy in (-1, 0, 1):
                    ny = cy + dy
                    if ny < 0 or ny >= n_rows or not ink_rows[ny]:
                        continue
                    for dx in (-1, 0, 1):
                        nx = cx + dx
                        if nx in ink_rows[ny] and nx not in visited[ny]:
                            visited[ny].add(nx)
                            stack.append((nx, ny))
            h = max_y - min_y + 1
            if h > best:
                best = h
    return best


def analyze_image(path: Path):
    width, height, rows = read_png_rgb(path, SCAN_ROWS)
    bg = rows[5][15:18]  # pixel (5,5)
    br, bgc, bb = bg[0], bg[1], bg[2]

    def is_ink_row(row: bytes) -> bool:
        cnt = 0
        # 2px 間引き: x = 0,2,4,...
        for i in range(0, width * 3, 6):
            if (abs(row[i] - br) + abs(row[i + 1] - bgc) + abs(row[i + 2] - bb)) > INK_DIFF_SUM:
                cnt += 1
                if cnt >= INK_MIN_SAMPLES:
                    return True
        return False

    runs = []
    start = None
    for y, row in enumerate(rows):
        if is_ink_row(row):
            if start is None:
                start = y
        else:
            if start is not None:
                runs.append((start, y - 1))
                start = None
    if start is not None:
        runs.append((start, len(rows) - 1))

    band_height = None
    lines = []
    for (s, e) in runs:
        h = e - s + 1
        if h >= CONTENT_RUN_MIN:
            band_height = s
            break
        if h >= MIN_LINE_ROWS:
            lines.append({"start": s, "end": e, "height": h})
    glyph = max((ln["height"] for ln in lines), default=0)
    if band_height is None:
        component = 0
    else:
        component = max_component_height(rows, width, (br, bgc, bb), band_height)
    return {
        "file": path.name,
        "width": width,
        "height": height,
        "band_height": band_height,
        "lines": lines,
        "glyph_height": glyph,
        "component_height": component,
    }


# ----------------------------------------------------------------------- main
def main(argv=None):
    ap = argparse.ArgumentParser(description="Screenshot Consistency Gate")
    ap.add_argument("--set", action="append", required=True, metavar="NAME=DIR",
                    help="ロケール名=スクリーンショットフォルダ (複数指定)")
    ap.add_argument("--out", metavar="JSON", help="結果 JSON の出力先")
    args = ap.parse_args(argv)

    sets = {}
    for spec in args.set:
        if "=" not in spec:
            print(f"error: --set は NAME=DIR 形式: {spec}", file=sys.stderr)
            return 2
        name, d = spec.split("=", 1)
        dpath = Path(d).expanduser()
        if not dpath.is_dir():
            print(f"error: フォルダが無い: {dpath}", file=sys.stderr)
            return 2
        files = sorted(p for p in dpath.iterdir()
                       if p.is_file() and p.suffix.lower() == ".png")
        sets[name] = files

    results = {}
    all_images = []
    for name, files in sets.items():
        imgs = []
        for p in files:
            info = analyze_image(p)
            info["set"] = name
            imgs.append(info)
            all_images.append(info)
        results[name] = imgs

    gates = []

    # Gate A: 枚数
    counts = {name: len(files) for name, files in sets.items()}
    a_ok = len(set(counts.values())) == 1
    gates.append(("A count", a_ok, f"counts={counts}"))

    # Gate B: 解像度
    sizes = {(im["width"], im["height"]) for im in all_images}
    b_ok = len(sizes) == 1
    gates.append(("B resolution", b_ok, f"sizes={sorted(sizes)}"))

    # Gate C: バンド高さ
    bands = [im["band_height"] for im in all_images]
    if any(b is None for b in bands):
        gates.append(("C band_height", False, "band not detected in some image"))
        band_median = None
    else:
        band_median = statistics.median(bands)
        bad = [(im["set"], im["file"], im["band_height"]) for im in all_images
               if abs(im["band_height"] - band_median) > BAND_TOL_PX]
        gates.append(("C band_height", not bad,
                      f"median={band_median}px tol=±{BAND_TOL_PX}px outliers={bad}"))

    # Gate D: 部品高さ (ロケール別中央値 ±3px)
    # 書体系統差 (CJK は字面いっぱいに描かれる) を吸収するため、全体中央値ではなく
    # ロケールごとの中央値で判定する。対象は行エクステントではなく部品高さ。
    component_medians = {}
    d_bad = []
    d_missing = []
    for name, imgs in results.items():
        vals = [im["component_height"] for im in imgs]
        if any(v == 0 for v in vals):
            component_medians[name] = None
            d_missing.extend((name, im["file"]) for im in imgs
                             if im["component_height"] == 0)
            continue
        med = statistics.median(vals)
        component_medians[name] = med
        d_bad.extend((name, im["file"], im["component_height"]) for im in imgs
                     if abs(im["component_height"] - med) > COMPONENT_TOL_PX)
    d_ok = not d_bad and not d_missing
    gates.append(("D component_height (per-locale)", d_ok,
                  f"medians={component_medians} tol=±{COMPONENT_TOL_PX}px "
                  f"outliers={d_bad} missing={d_missing}"))

    overall = all(ok for _n, ok, _d in gates)

    # ---- レポート出力
    print("=== Screenshot Consistency Gate ===")
    for name in sets:
        print(f"[{name}] {counts[name]} files")
        for im in results[name]:
            line_hs = [ln["height"] for ln in im["lines"]]
            print(f"  {im['file']}: {im['width']}x{im['height']} "
                  f"band={im['band_height']} glyph={im['glyph_height']} "
                  f"comp={im['component_height']} lines={line_hs}")
    for gname, ok, detail in gates:
        print(f"Gate {gname}: {'PASS' if ok else 'FAIL'} ({detail})")
    print(f"OVERALL: {'PASS' if overall else 'FAIL'}")

    if args.out:
        report = {
            "overall": "PASS" if overall else "FAIL",
            "tolerances": {"band_px": BAND_TOL_PX, "component_px": COMPONENT_TOL_PX},
            "band_median": band_median,
            "component_medians": component_medians,
            "gates": [{"gate": n, "pass": ok, "detail": d} for n, ok, d in gates],
            "sets": {name: [{k: v for k, v in im.items() if k != "set"}
                            for im in imgs] for name, imgs in results.items()},
        }
        Path(args.out).write_text(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if overall else 1


if __name__ == "__main__":
    sys.exit(main())
