# Assets — 素材の置き場と取得手順

このスキルの素材は「実際に伸びたアカウントで証明された型」の実物である。
利用者は素材を自分で作らなくてよい。必要なのは、正本から取得して、文面とフックだけを変えること。

## 1. 勝者の背景写真セット・全スライド（正本）

- 正本: GitHub `Daisuke134/anicca-ops` の `files/winner-images-2026-11-15/`
  - ローカルクローン: `~/workspace/anicca-ops/files/winner-images-2026-11-15/`
  - 取得: `cd ~/workspace/anicca-ops && git pull`（47ファイル、約11MB）
- 命名規則: `<アカウント>_<投稿ID>_slideNN.jpg`、表紙は `<アカウント>_<投稿ID>_cover.webp`
- 収録済みの勝者（2026-11-15 時点）:
  - `aniccaaffirmation_7624115204804267272_*` — 英語面の勝者カルーセル（再生253,737）。実写ライフスタイル写真セット。
  - `anicca.jp_7621795876935355655_*` — 日本語面の勝者「メンタルが強い人の口癖５選」（再生75,490）。夕焼け写真セット。
  - `anicca.jp4_7649736101048962322_*` — @anicca.jp4 自身の勝ち投稿（再生24,802）。
  - `anicca.jp_loser_purple-starry_tj11_*` — 敗者形式の記録（紫星空＋一文。使うなという証拠として保存）。
- 新しい勝者を固定したら、同じ命名でこのフォルダへ追加し、リンク＋実測数字を勝者マップ（anicca-ops `files/winner-posts-master-2026-11-15.md`）に記録する。

## 2. ビルダーの型（このフォルダに同梱）

- `scripts/rebuild.py` — 勝者実物からの作り直し型。背景の焼き込み文字を OpenCV の inpaint で除去してクリーン背景を作り、勝者と同型のレイアウトで新しい文面を描く。依存: `~/workspace/tools/cv2-lib`（cv2）、Pillow。
- `scripts/build_hr3.py` — テキストフィット（自動縮小）型。長い文面でも画面内に収める。端切れ防止の正本実装。
- `scripts/build_hv2fix.py` — 端切れ欠陥（HV2-1 slide03）の修正型。既存パックの直し方として使う。
- 制作物の置き場の実例: goal ワークスペース `hidden_files/dist-production-2026-11-15-1015-rebuild/`（パックごとのフォルダ＋ manifest.json ＋ pixelmatch-results.txt）。

## 3. フォント

- 英語面: Fredoka（`~/workspace/tools/fonts/Fredoka.ttf`、太字・黒縁＋白文字が勝者の型）
- 日本語面（リスト型）: ゴシック系。勝者実物に合わせる。
- 日本語面（名言型）: NotoSerifCJK（明朝）`/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc`
- TikTok ネイティブ風: TikTok Sans は併用スキル `tiktok-slideshow-skill/fonts/TikTokSans.ttf` に同梱されている。

## 4. 道具

- 計測: `~/workspace/tools/tikwm/tikwm <投稿URL>`（再生・いいね・コメント・共有・保存）
- ピクセル比較: `~/workspace/tools/pixeldiff/`（`python3 prep.py` で 540x960 に正規化 → `node diff.js a.png b.png ラベル`）
- 公開: Postiz CLI（`~/.local/bin/postiz`、予約は QUEUE へバルク登録）

## 5. レイアウト仕様（勝者実物から）

- 画角: TikTok 写真投稿は勝者の実物寸法に合わせる（検証時は 540x960 に正規化して比較）。
- 英語勝者型: 実写写真フルブリード＋白太字テキスト＋黒縁。文字は写真の余白部に置く。
- 日本語勝者型: 全スライド同じ写真＋白文字。1枚目がフック（タイトル）、以降が項目。
- Honne 勝者型: 7枚組。表紙＋セリフ5選＋締め。背景は勝者表紙スライドの文字除去済み実物を再利用する。
