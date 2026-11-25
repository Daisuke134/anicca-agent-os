# ReelClaw / Honne Hook Source of Truth Fix Spec

Date: 2026-04-09
Status: PATCH READY
Owner: Anicca

## Goal

Fix hook source confusion across ReelClaw card, ReelClaw widget, and Honne ReelClaw families.

Primary problems:
1. Hook sources are split across SKILL.md, spec markdown, jobs.json payload text, and runtime JSON files.
2. Different cron families use different hook pools, but that is not expressed cleanly in one source of truth.
3. 3-line hooks are visually weak for widget/reel formats.
4. Honne JA stores hook text inside video mapping, which makes data model evolution harder.
5. Widget W1-W12 and planned Honne H1-H10 live only in spec markdown, not machine-readable files.

---

## Current Source of Truth by Cron Family

### Source of Truth Matrix

| Family | Cron IDs | Hook Source | Mapping Source | Rotation Source | Status |
|---|---|---|---|---|---|
| Card ReelClaw JA | reelclaw-ja-1, reelclaw-ja-2 | /Users/anicca/.openclaw/workspace/tiktok-marketing/hooks-ja.json | demos mapping in tiktok-marketing assets | not yet fully normalized | runtime existing |
| Card ReelClaw EN | reelclaw-en-1, reelclaw-en-2 | /Users/anicca/.openclaw/workspace/tiktok-marketing/hooks-en.json | demos mapping in tiktok-marketing assets | not yet fully normalized | runtime existing |
| Widget ReelClaw JA | reelclaw-anicca-ja-widget-1, reelclaw-anicca-ja-widget-2 | /Users/anicca/.openclaw/workspace/tiktok-marketing/reelclaw-widget-hooks-ja.json | /Users/anicca/anicca-project/assets/reelclaw/ja-widget-videos/ | /Users/anicca/.openclaw/workspace/tiktok-marketing/reelclaw-widget-rotation.json | source-managed |
| Widget ReelClaw EN | reelclaw-anicca-en-widget-1, reelclaw-anicca-en-widget-2 | /Users/anicca/.openclaw/workspace/tiktok-marketing/reelclaw-widget-hooks-en.json | /Users/anicca/anicca-project/assets/reelclaw/en-widget-videos/ | /Users/anicca/.openclaw/workspace/tiktok-marketing/reelclaw-widget-rotation.json | source-managed |
| Honne ReelClaw JA | reelclaw-honne-ja-1, reelclaw-honne-ja-2, reelclaw-honne-ja-3 | /Users/anicca/.openclaw/workspace/honne-ai/honne-hooks-ja.json | /Users/anicca/.openclaw/workspace/honne-ai/honne-mapping.json | /Users/anicca/.openclaw/workspace/honne-ai/honne-rotation.json | source-managed |
| Honne ReelClaw EN | honne-en-morning, honne-en-afternoon, honne-en-evening | /Users/anicca/.openclaw/workspace/honne-ai/honne-hooks-en.json | planned Honne EN mapping | planned Honne EN rotation | planned |
| Empathy Hooks | optional shared family | /Users/anicca/.openclaw/workspace/tiktok-marketing/reelclaw-empathy-hooks.json | none | none | optional |

### 1. Anicca card ReelClaw (runtime existing)
Crons:
- reelclaw-ja-1
- reelclaw-ja-2
- reelclaw-en-1
- reelclaw-en-2

Current hook source:
- /Users/anicca/.openclaw/workspace/tiktok-marketing/hooks-ja.json
- /Users/anicca/.openclaw/workspace/tiktok-marketing/hooks-en.json

### 2. Anicca widget ReelClaw (source-managed)
Crons:
- reelclaw-anicca-ja-widget-1
- reelclaw-anicca-ja-widget-2
- reelclaw-anicca-en-widget-1
- reelclaw-anicca-en-widget-2

Current hook source:
- W1-W12 JA in /Users/anicca/anicca-project/.cursor/plans/ios/1.8.3/10k-mrr-growth-spec.md
- W1-W12 EN in /Users/anicca/anicca-project/.cursor/plans/ios/1.8.3/10k-mrr-growth-spec.md
- Referenced from /Users/anicca/anicca-project/.cursor/plans/ios/1.8.3/cron-patches.md
- Referenced from /Users/anicca/anicca-project/openclaw-skills/jobs.json as "Widget hooks W1-W12 JA/EN from spec"

### 3. Honne JA ReelClaw (source-managed)
Crons:
- reelclaw-honne-ja-1
- reelclaw-honne-ja-2
- reelclaw-honne-ja-3

Current hook source:
- /Users/anicca/.openclaw/workspace/honne-ai/honne-mapping.json
- hook source is videos[].hooks[]

### 4. Honne EN ReelClaw (planned only)
Planned crons:
- honne-en-morning
- honne-en-afternoon
- honne-en-evening

Current hook source:
- H1-H10 EN in /Users/anicca/anicca-project/.cursor/plans/ios/1.8.3/10k-mrr-growth-spec.md

### 5. Anicca empathy hook pool (spec only)
Current source:
- E1-E5 EN/JA in /Users/anicca/anicca-project/.cursor/plans/ios/1.8.3/10k-mrr-growth-spec.md

---

## Problems to Solve

### Problem A: Hook source is not machine-readable for widget and Honne EN families
W1-W12 and H1-H10 live in markdown only. Runtime payloads reference them verbally.

Why this matters:
- The agent can drift from the intended list.
- Rotation logic cannot safely use markdown as a data store.
- jobs.json payload text becomes long, fragile, and harder to audit.

### Problem B: Hook family boundaries are unclear
Card ReelClaw, widget ReelClaw, Honne JA, Honne EN, and empathy hooks are distinct families, but the current system does not enforce that cleanly.

Why this matters:
- Wrong hook family may be used in the wrong cron.
- Reviewers can misread the source of truth.
- Future updates risk silent drift.

### Problem C: 3-line hooks reduce visual quality
Widget/Reel short-form overlays should prioritize instant readability.

Why this matters:
- The first frame must be understandable at a glance.
- 3-line and 4-line overlays increase cognitive load.
- Existing good outputs are already closer to 1-line or 2-line hooks.

### Problem D: Honne JA mixes video mapping and hook content in one file
honne-mapping.json currently contains both video metadata and hook text.

Why this matters:
- Rotation state and copy inventory are different concerns.
- Future Honne EN parity becomes harder.
- Hook editing becomes risky because it touches mapping logic too.

### Problem E: jobs.json references prose, not exact JSON files
Current jobs.json lines say things like "Widget hooks W1-W12 EN from spec".

Why this matters:
- Runtime instructions are less precise than they should be.
- The exact source of truth is not explicit enough.
- Auditing gets harder because the payload does not point to a concrete data file.

---

## Target Design

### Hook content should live in JSON, not markdown prose
Create exact machine-readable files:
- /Users/anicca/.openclaw/workspace/tiktok-marketing/reelclaw-widget-hooks-ja.json
- /Users/anicca/.openclaw/workspace/tiktok-marketing/reelclaw-widget-hooks-en.json
- /Users/anicca/.openclaw/workspace/honne-ai/honne-hooks-ja.json
- /Users/anicca/.openclaw/workspace/honne-ai/honne-hooks-en.json
- /Users/anicca/.openclaw/workspace/tiktok-marketing/reelclaw-empathy-hooks.json

### Family separation
- Card ReelClaw keeps using hooks-ja.json / hooks-en.json
- Widget ReelClaw uses reelclaw-widget-hooks-ja.json / reelclaw-widget-hooks-en.json
- Honne JA uses honne-hooks-ja.json
- Honne EN uses honne-hooks-en.json
- Empathy hooks remain a separate optional family

### Visual rule
- Widget ReelClaw: 1 line preferred, 2 lines max
- Honne ReelClaw: 2 lines preferred, 2 lines max
- 3 lines forbidden for widget and honne reel families

### Mapping rule
- honne-mapping.json should become mapping + rotation only
- hook inventory should move out into honne-hooks-ja.json and honne-hooks-en.json

### jobs.json rule
Every cron payload should reference an exact JSON path, not "from spec" wording.

---

## Full TODO List

### 1. Hook source of truth fixes

| ID | TODO | File / Target | Why |
|---|---|---|---|
| T1 | Widget JA hook JSON を作る | /Users/anicca/.openclaw/workspace/tiktok-marketing/reelclaw-widget-hooks-ja.json | W1-W12 JA を spec/prose 依存から脱却 |
| T2 | Widget EN hook JSON を作る | /Users/anicca/.openclaw/workspace/tiktok-marketing/reelclaw-widget-hooks-en.json | W1-W12 EN を exact path 参照にする |
| T3 | Honne JA hook JSON を作る | /Users/anicca/.openclaw/workspace/honne-ai/honne-hooks-ja.json | honne-mapping.json videos[].hooks[] の混在を解消 |
| T4 | Honne EN hook JSON を作る | /Users/anicca/.openclaw/workspace/honne-ai/honne-hooks-en.json | planned-only から runtime-ready にする |
| T5 | Empathy hook JSON を作る | /Users/anicca/.openclaw/workspace/tiktok-marketing/reelclaw-empathy-hooks.json | E1-E5 を family として独立管理する |
| T6 | Card ReelClaw JA hook inventory を整理 | /Users/anicca/.openclaw/workspace/tiktok-marketing/hooks-ja.json | 長文・多行・drift を是正 |
| T7 | Card ReelClaw EN hook inventory を整理 | /Users/anicca/.openclaw/workspace/tiktok-marketing/hooks-en.json | 同上 |
| T8 | family ごとの hook schema を固定 | current spec + new JSONs | field drift 防止 |
| T9 | hook object に id/status/maxLines/tags/lastUsed を統一 | all hook JSONs | validation と運用を楽にする |

### 2. Rotation / state separation

Status:
- DONE: T10, T11, T12, T13, T14, T15

Implemented state split:
- Widget rotation state lives in /Users/anicca/.openclaw/workspace/tiktok-marketing/reelclaw-widget-rotation.json
- Honne rotation state lives in /Users/anicca/.openclaw/workspace/honne-ai/honne-rotation.json
- Honne mapping file now points to rotationSource instead of embedding rotation
- Hook inventories keep lastUsed as null and rotation state is treated as separate state data

| ID | TODO | File / Target | Why |
|---|---|---|---|
| T10 | Widget rotation file を作る | /Users/anicca/.openclaw/workspace/tiktok-marketing/reelclaw-widget-rotation.json | same-day repeat 防止 |
| T11 | Honne rotation file を作る | /Users/anicca/.openclaw/workspace/honne-ai/honne-rotation.json | state 分離 |
| T12 | honne-mapping.json を mapping 専用化 | /Users/anicca/.openclaw/workspace/honne-ai/honne-mapping.json | hooks / rotation / posting の混在を減らす |
| T13 | Widget lastUsed を rotation file に移す | widget family | hook data を clean に保つ |
| T14 | Honne lastUsed を rotation file に移す | honne family | 同上 |
| T15 | hook file と rotation file の責務を文書化 | spec | future drift 防止 |

### 3. Runtime payload / jobs fixes

| ID | TODO | File / Target | Why |
|---|---|---|---|
| T16 | Widget cron の hook source を exact path 化 | /Users/anicca/anicca-project/openclaw-skills/jobs.json | from spec を廃止 |
| T17 | Honne JA cron の hook source を exact path 化 | /Users/anicca/anicca-project/openclaw-skills/jobs.json | prose 参照を廃止 |
| T18 | Honne cron の video mapping source を明記 | /Users/anicca/anicca-project/openclaw-skills/jobs.json | hook と demo の責務を分離 |
| T19 | Card cron の hook source も exact path を明示 | /Users/anicca/anicca-project/openclaw-skills/jobs.json | audit を楽にする |
| T20 | family ごとに rotation source path を payload に書く | /Users/anicca/anicca-project/openclaw-skills/jobs.json | repeat guard を明確化 |
| T21 | title / caption / CTA source path も payload に寄せる | /Users/anicca/anicca-project/openclaw-skills/jobs.json | prose drift 防止 |
| T22 | Widget JA/EN cron IDs と source paths の整合確認 | /Users/anicca/anicca-project/openclaw-skills/jobs.json | misbinding 防止 |
| T23 | Honne JA cron IDs と source paths の整合確認 | /Users/anicca/anicca-project/openclaw-skills/jobs.json | 同上 |
| T24 | planned Honne EN cron に備えて payload schema を先に決める | jobs.json / spec | 後戻り防止 |

### 4. Spec / docs updates

| ID | TODO | File / Target | Why |
|---|---|---|---|
| T25 | 2026-04-09 spec に full TODO を反映 | /Users/anicca/.openclaw/workspace/specs/2026-04-09-reelclaw-hook-source-of-truth-fix.md | doc completeness |
| T26 | current source-of-truth matrix を spec に入れる | same spec | family ごとの差を一目化 |
| T27 | folder tree を spec に追加 | same spec | path 理解を容易にする |
| T28 | platform behavior matrix を spec に追加 | same spec | TT/IG/YT の投稿モードを整理 |
| T29 | acceptance criteria を preview 前提で追加 | same spec | 完了条件を厳密化 |
| T30 | 1.8.3 patch doc を更新 | 1.8.3 Cron Patches | source-managed docs の整合 |
| T31 | 10k-mrr-growth-spec.md を更新 | /Users/anicca/anicca-project/.cursor/plans/ios/1.8.3/10k-mrr-growth-spec.md | docs drift 解消 |
| T32 | card/widget/honne family の違いを spec で明文化 | all related specs | confusion 防止 |
| T33 | 3-line hooks are weak を spec に rule として書く | same spec | design rule 固定 |

### 5. Line-break / text rendering fixes

Status:
- DONE: T34, T35, T36, T38, T39, T40, T41, T42
- PARTIAL: T43, T44, T45
- TODO: T37, T46

Implemented files:
- /Users/anicca/.openclaw/workspace/tiktok-marketing/add-overlay-cli.js
- /Users/anicca/.openclaw/workspace/tiktok-marketing/reelclaw-render-rules.json

Implemented rules:
- widget maxLines = 2
- honne maxLines = 2
- empathy maxLines = 2
- card maxLines = 3
- safe text box width = 760px equivalent
- center alignment is hardcoded
- literal /n is rejected
- | is normalized to \n for Honne compatibility
- renderer throws when computed line count exceeds family maxLines

| ID | TODO | File / Target | Why |
|---|---|---|---|
| T34 | Widget family を 2 lines max に固定 | renderer + hook JSON | one-liner overflow 防止 |
| T35 | Honne family を 2 lines fixed に固定 | renderer + hook JSON | setup/reveal 安定化 |
| T36 | Empathy family を 2 lines max に固定 | renderer + hook JSON | social proof 見切れ防止 |
| T37 | Card family を原則 3 lines max に圧縮 | card hooks | ugly 4-line 超を削減 |
| T38 | safe text box width 760px を固定 | renderer | 左右見切れ防止 |
| T39 | center align を固定 | renderer | first frame quality 向上 |
| T40 | /n literal を reject | renderer | 改行事故防止 |
| T41 | | -> \n 互換変換を追加 | Honne migration | 既存 data 互換 |
| T42 | maxLines validator を追加 | validator | family rule enforcement |
| T43 | language-aware width guard を追加 | validator | JA/EN の横幅事故防止 |
| T44 | 1行が長すぎる hook は fail | validator | ugly one-liner を未然防止 |
| T45 | auto-wrap ではなく rewrite required 判定を追加 | validator or preflight | 長文放置防止 |
| T46 | line-break preview を自動生成 | preview pipeline | 目視検証を楽にする |

### 6. Hook rewrite / normalization work

Status:
- DONE: T47, T48, T49, T50, T51, T52, T55, T56, T57
- PARTIAL: T53, T54

Implemented normalization:
- Widget JA/EN final 2-line display-safe wording written into widget hook JSON files
- Empathy EN/JA final 2-line wording written into empathy JSON
- Honne JA punctuation and line-break normalization applied in honne-hooks-ja.json
- Honne EN final 2-line wording preserved in honne-hooks-en.json
- High-priority card JA/EN long hooks were compressed where they directly affect visual quality or sales messaging

| ID | TODO | File / Target | Why |
|---|---|---|---|
| T47 | Widget EN W1-W12 を 2行安全版に更新 | widget EN JSON | 画面はみ出し防止 |
| T48 | Widget JA W1-W12 を 2行安全版に更新 | widget JA JSON | 同上 |
| T49 | Empathy EN E1-E5 を 2行安全版に更新 | empathy JSON | 同上 |
| T50 | Empathy JA E1-E5 を 2行安全版に更新 | empathy JSON | 同上 |
| T51 | Honne JA 8 videos × 3 hooks を 2行安全版に更新 | honne JA JSON | 同上 |
| T52 | Honne EN H1-H10 を 2行安全版に更新 | honne EN JSON | 同上 |
| T53 | Card JA hooks 全件を review して圧縮 | hooks-ja.json | 4行超の削減 |
| T54 | Card EN hooks 全件を review して圧縮 | hooks-en.json | 同上 |
| T55 | セルフケアアプリ100個… 系 hook を card safe version に修正 | hooks-ja.json | high-priority sales copy 修正 |
| T56 | why did nobody tell me… 系 hook を widget safe version に固定 | widget EN/JA | key conversion hook quality 向上 |
| T57 | 休んでいいよ / 生活費は誰が払う 系長文を短文化 | card JA | readability 改善 |

### 7. Media / demo path / asset hygiene

Status:
- DONE: T60, T61, T62, T64, T65
- PARTIAL: T58, T63
- TODO: T59

Implemented file:
- /Users/anicca/.openclaw/workspace/tiktok-marketing/reelclaw-media-sources.json

Implemented inventory:
- Widget JA demo list fixed in reelclaw-media-sources.json
- Widget EN demo list fixed in reelclaw-media-sources.json
- Card demo source directories recorded
- Honne JA demo source directory and files recorded
- Honne EN source remains planned/null
- UGC hook source directory recorded
- CTA exact paths recorded

Known media risk:
- Widget EN still includes rumnation.mov, so mixed container risk remains until explicit compatibility validation passes or file is converted to .mp4

| ID | TODO | File / Target | Why |
|---|---|---|---|
| T58 | Widget EN demo .mov の互換性検証 | /Users/anicca/anicca-project/assets/reelclaw/en-widget-videos/ | concat/upload 事故防止 |
| T59 | 必要なら .mp4 に統一 | same path | media stability |
| T60 | Widget JA demo list を固定 | /Users/anicca/anicca-project/assets/reelclaw/ja-widget-videos/ | rotation reproducibility |
| T61 | Widget EN demo list を固定 | /Users/anicca/anicca-project/assets/reelclaw/en-widget-videos/ | 同上 |
| T62 | Card demo trim list を固定 | /Users/anicca/.openclaw/workspace/tiktok-marketing/assets/demos/ja/trimmed/ and /Users/anicca/.openclaw/workspace/tiktok-marketing/assets/demos/en/trimmed/ | cron reproducibility |
| T63 | Honne EN demo path を決める | Honne assets | planned only 解消 |
| T64 | UGC hook clip inventory を一覧化 | /Users/anicca/.openclaw/workspace/tiktok-marketing/ugc-library/hooks/ | creative reproducibility |
| T65 | CTA asset source を exact path 化 | CTA assets | drift 防止 |

### 8. Title / caption / CTA normalization

Status:
- DONE: T66, T67, T68, T69, T70, T71, T72, T73, T74, T75

Implemented file:
- /Users/anicca/.openclaw/workspace/tiktok-marketing/reelclaw-copy-rules.json

Implemented normalization:
- Widget JA/EN exact title and caption rules fixed
- Honne JA/EN title rotations fixed
- Card JA/EN default title/caption templates fixed
- CTA path is source-managed per family/language
- hashtag policy is explicit per family/language

| ID | TODO | File / Target | Why |
|---|---|---|---|
| T66 | family ごとの title rule を決める | spec / payload | TT first impression を統一 |
| T67 | family ごとの caption rule を決める | spec / payload | platform copy drift 防止 |
| T68 | family ごとの CTA rule を決める | spec / assets | ending drift 防止 |
| T69 | Widget JA title を exact phrases に固定 | widget family | clean feature sell |
| T70 | Widget EN title を exact phrases に固定 | widget family | 同上 |
| T71 | Honne JA title を exact phrases に固定 | honne family | decode angle 明確化 |
| T72 | Honne EN title を exact phrases に固定 | honne family | 同上 |
| T73 | Card JA title/caption を整理 | card family | emotional lane の一貫性 |
| T74 | Card EN title/caption を整理 | card family | 同上 |
| T75 | hashtag policy を family ごとに決める | captions | random drift 防止 |

### 9. Posting policy / platform behavior verification

Status:
- DONE: T79, T81, T82
- PARTIAL: T76, T77, T78, T80

Implemented file:
- /Users/anicca/.openclaw/workspace/tiktok-marketing/reelclaw-platform-rules.json

Verified truths:
- Honne JA is runtime-verified as TikTok draft only, SELF_ONLY + UPLOAD, no audio
- Widget source-managed crons specify TikTok draft, Instagram direct, YouTube direct
- Postiz result files confirm EN test outputs existed for TikTok, Instagram, and YouTube integrations

Still not fully verified:
- Card family exact runtime draft/direct mode per cron
- Widget runtime behavior beyond source-managed payload text
- Honne EN platform behavior because EN family is still planned

| ID | TODO | File / Target | Why |
|---|---|---|---|
| T76 | 各 cron の TikTok 投稿モードを確認 | runtime + spec | draft/direct ambiguity 解消 |
| T77 | 各 cron の Instagram 投稿モードを確認 | runtime + spec | same |
| T78 | 各 cron の YouTube Shorts 投稿モードを確認 | runtime + spec | same |
| T79 | Honne JA の draft only を docs に反映 | spec/docs | runtime truth 反映 |
| T80 | Widget/Card family の TT draft policy を runtime で照合 | runtime | 全部 draft? 問題の確定 |
| T81 | family別 platform matrix を確定版にする | spec | confusion 終了 |
| T82 | Postiz payload の title/caption/platform fields を実検証 | runtime logs/results | docs と実挙動の差を消す |

### 10. Preview / QA / verification

Status:
- DONE: T88, T90
- PARTIAL: T83, T84
- TODO: T85, T86, T87, T89

Implemented file:
- /Users/anicca/.openclaw/workspace/tiktok-marketing/reelclaw-qa-rules.json

Implemented directories:
- /Users/anicca/.openclaw/workspace/tiktok-marketing/previews/
- /Users/anicca/.openclaw/workspace/tiktok-marketing/previews/line-breaks/

Implemented QA rules:
- first-frame visibility checklist
- line-break regression checklist
- demo overlay absence check
- CTA overlap check
- family-based preview targets
- fallback policy for overflow, missing media, unknown platform mode, title/caption mismatch

| ID | TODO | File / Target | Why |
|---|---|---|---|
| T83 | 各 family の first-frame preview を保存 | preview outputs | 視覚 QA |
| T84 | 全 hook の line-break preview を保存 | registry / preview dir | regression 防止 |
| T85 | Widget JA/EN を TikTok draft preview で目視確認 | TikTok drafts | overflow 最終確認 |
| T86 | Honne JA を TikTok draft preview で目視確認 | TikTok drafts | same |
| T87 | Card JA/EN を TT preview で目視確認 | TikTok drafts or preview images | same |
| T88 | CTA の位置・被り確認 | preview outputs | final frame QA |
| T89 | title/caption 実表示確認 | Postiz/TikTok UI | prose drift 検知 |
| T90 | failure cases の fallback を決める | pipeline | bad hook 自動停止 |

### 11. Open uncertainty cleanup

Status:
- DONE: uncertainty registry created
- OPEN: T91, T92, T93, T94, T95, T96, T97, T98

Implemented file:
- /Users/anicca/.openclaw/workspace/tiktok-marketing/reelclaw-open-questions.json

Principle:
- runtime-verified truths are separated from source-managed intent and from still-planned items
- unresolved items remain explicitly open instead of being guessed

| ID | TODO | Target | Why |
|---|---|---|---|
| T91 | Card runtime exact TT draft/direct を確定 | runtime jobs | 現時点で未確定 |
| T92 | Widget runtime exact TT draft/direct を確定 | runtime jobs | source spec と runtime の差を確認 |
| T93 | Honne JA の IG/YT mode を確定 | runtime/docs | draft only の範囲確認 |
| T94 | Honne EN demo assets の所在を確定 | filesystem/spec | planned only 解消 |
| T95 | empathy hooks をどの cron が使うか確定 | spec/payload | orphan family 防止 |
| T96 | title rotation state をどこに持つか決定 | state design | prose drift 防止 |
| T97 | card family の old long hooks を全て残すか削るか決定 | hook governance | inventory cleanup |
| T98 | central safe-zone の exact font size / line height を確定 | renderer | pixel-level overflow 防止 |

### 12. Final done criteria

| ID | DONE 条件 |
|---|---|
| D1 | family ごとの hook source of truth が全て JSON 化されている |
| D2 | jobs.json が exact path 参照のみになる |
| D3 | widget/honne/empathy が 2行以内で固定される |
| D4 | card hooks が原則3行以内に圧縮される |
| D5 | TikTok first-frame preview で左右見切れゼロ |
| D6 | family ごとの TT/IG/YT posting mode が文書と runtime で一致 |
| D7 | Honne が ReelClaw family として同じ骨格に揃う |
| D8 | user が どこで何が正本か を 1画面で理解できる |
---

## Folder Tree

```text
/Users/anicca/.openclaw/workspace/
├── tiktok-marketing/
│   ├── hooks-ja.json
│   ├── hooks-en.json
│   ├── reelclaw-widget-hooks-ja.json
│   ├── reelclaw-widget-hooks-en.json
│   ├── reelclaw-empathy-hooks.json
│   ├── reelclaw-widget-rotation.json
│   ├── ugc-library/
│   │   └── hooks/
│   └── assets/
│       └── demos/
│           ├── ja/trimmed/
│           └── en/trimmed/
├── honne-ai/
│   ├── honne-mapping.json
│   ├── honne-hooks-ja.json
│   ├── honne-hooks-en.json
│   ├── honne-rotation.json
│   ├── demos/
│   └── output/
└── mau-tiktok/
    ├── cta_ja_final.mp4
    └── cta_en_final.mp4

/Users/anicca/anicca-project/
└── assets/
    └── reelclaw/
        ├── ja-widget-videos/
        └── en-widget-videos/
```

## Platform Behavior Matrix

| Family | TikTok | Instagram | YouTube Shorts |
|---|---|---|---|
| Card ReelClaw JA/EN | verify exact runtime mode per cron | likely direct in source-managed docs, verify runtime | likely direct in source-managed docs, verify runtime |
| Widget ReelClaw JA/EN | draft in source-managed payloads | direct in source-managed payloads | direct in source-managed payloads |
| Honne ReelClaw JA | draft only, SELF_ONLY, no audio | not confirmed | not confirmed |
| Honne ReelClaw EN | planned | planned | planned |

## Family Differences

| Family | What it sells | Visual style | Hook rule |
|---|---|---|---|
| Card ReelClaw | emotional self-care / nudge value | broader emotional overlays | target max 3 lines |
| Widget ReelClaw | lockscreen/widget feature desire | clean feature-first short overlays | 1 line preferred, 2 max |
| Honne ReelClaw | hidden meaning / relationship decode | drama + reveal | 2 semantic lines fixed |
| Empathy | social proof / save-me angle | short emotional proof | 2 max |

## 3-Line Hooks Are Weak Rule

Rule:
- Widget ReelClaw: 3-line hooks are forbidden.
- Honne ReelClaw: 3-line hooks are forbidden.
- Empathy family: 3-line hooks are forbidden.
- Card family: 3-line hooks are tolerated only when readability remains high, but target is still 3 max and compression is preferred.

Reason:
- Widget and Honne first frames must be readable at a glance.
- 3-line overlays reduce beauty, shrink font size, and increase horizontal overflow risk.

## Acceptance Criteria

| ID | Acceptance check |
|---|---|
| A1 | Every cron family has one explicit hook source path |
| A2 | Widget and Honne families no longer rely on prose-only hook sources |
| A3 | Rotation state is stored outside hook inventories |
| A4 | jobs.json payload text points to exact JSON paths |
| A5 | Spec includes source-of-truth matrix, folder tree, and platform behavior matrix |
| A6 | Widget/Honne line-break target is documented as hard rule |
| A7 | Reviewer can identify where hook text, mapping, rotation, CTA, and demo source live without reading runtime code |

## To-Be Flow After Fix

### 1. Card ReelClaw flow
1. cron fires for reelclaw-ja-1 / reelclaw-ja-2 / reelclaw-en-1 / reelclaw-en-2
2. runtime reads hooks-ja.json or hooks-en.json
3. select hook from card family pool
4. select UGC hook video
5. select trimmed demo from demos-mapping.json
6. render overlay using card rules
7. build reel
8. post to TikTok / Instagram / YouTube
9. update card family rotation state

Why this is better:
- Card family stays stable and separate.
- No accidental use of widget or honne hooks.

### 2. Widget ReelClaw flow
1. cron fires for reelclaw-anicca-ja-widget-1 / 2 or EN equivalents
2. runtime reads reelclaw-widget-hooks-ja.json or reelclaw-widget-hooks-en.json
3. validator checks maxLines <= 2
4. select widget demo video from exact widget video folder
5. select UGC hook video
6. render short clean overlay, 1-2 lines only
7. build reel with CTA and BGM
8. post to configured platforms
9. update widget family rotation state

Why this is better:
- W1-W12 becomes a real production hook pool.
- No confusion with old SKILL.md fixed lines.
- Visual quality becomes enforceable.

### 3. Honne JA ReelClaw flow
1. cron fires for reelclaw-honne-ja-1 / 2 / 3
2. runtime reads honne-mapping.json for demo/video rotation only
3. runtime reads honne-hooks-ja.json for hook text only
4. validator checks maxLines <= 2
5. select matching hook family and demo pair
6. build honne reel
7. post to TikTok draft flow
8. update honne rotation state

Why this is better:
- Hook inventory and mapping stop fighting each other.
- Honne copy can evolve without risking video mapping.

### 4. Honne EN ReelClaw flow
1. cron fires for honne-en-morning / afternoon / evening when implemented
2. runtime reads honne-hooks-en.json
3. runtime uses honne EN demo source
4. validator checks line count and family
5. build reel
6. post
7. update EN honne rotation state

Why this is better:
- Planned EN family becomes implementation-ready, not just spec-only.

---

## JSON Schema

### 1. Widget hook schema

```json
{
  "family": "reelclaw-widget",
  "language": "en",
  "version": 1,
  "hooks": [
    {
      "id": "W1",
      "text": "You're telling me I never knew you could put affirmations on your lockscreen?",
      "status": "active",
      "maxLines": 2,
      "tags": ["widget", "lockscreen", "affirmation"],
      "lastUsed": null
    }
  ]
}
```

### 2. Honne hook schema

```json
{
  "family": "honne-reelclaw",
  "language": "ja",
  "version": 1,
  "hooksByVideo": {
    "boss-imnotmad.MP4": [
      {
        "id": "HJ-boss-imnotmad-1",
        "text": "上司の『怒ってないよ』→|絶対怒ってる",
        "status": "active",
        "maxLines": 2,
        "tags": ["boss", "anger"],
        "lastUsed": null
      }
    ]
  }
}
```

### 3. Rotation schema

```json
{
  "family": "reelclaw-widget",
  "version": 1,
  "lastUsed": {
    "reelclaw-anicca-en-widget-1": {
      "hookId": "W1",
      "video": "anger.MP4",
      "date": "2026-04-09T09:30:00+09:00"
    }
  }
}
```

---

## Exact File Contents

### A. /Users/anicca/.openclaw/workspace/tiktok-marketing/reelclaw-widget-hooks-en.json

```json
{
  "family": "reelclaw-widget",
  "language": "en",
  "version": 1,
  "hooks": [
    {"id": "W1", "text": "You're telling me I never knew you could put affirmations on your lockscreen?", "status": "active", "maxLines": 2, "tags": ["widget","lockscreen","affirmation"], "lastUsed": null},
    {"id": "W2", "text": "Since you're always on your phone", "status": "active", "maxLines": 2, "tags": ["widget","phone"], "lastUsed": null},
    {"id": "W3", "text": "You're telling me I could've been watching affirmations this whole time?", "status": "active", "maxLines": 2, "tags": ["widget","affirmation"], "lastUsed": null},
    {"id": "W4", "text": "How to put affirmation words on your lockscreen (it changes everyday)", "status": "active", "maxLines": 2, "tags": ["widget","howto"], "lastUsed": null},
    {"id": "W5", "text": "How to add positive affirmations on ur lockscreen (it changes everyday)", "status": "active", "maxLines": 2, "tags": ["widget","howto"], "lastUsed": null},
    {"id": "W6", "text": "POV: you need those affirmations on your lockscreen bc you don't chase, you attract", "status": "active", "maxLines": 2, "tags": ["widget","pov"], "lastUsed": null},
    {"id": "W7", "text": "POV: you found an app that gives you new affirmations every hour", "status": "active", "maxLines": 2, "tags": ["widget","pov"], "lastUsed": null},
    {"id": "W8", "text": "How to put affirmations on your lock screen 🥺", "status": "active", "maxLines": 2, "tags": ["widget","howto"], "lastUsed": null},
    {"id": "W9", "text": "POV: your phone reminds you to be grateful", "status": "active", "maxLines": 2, "tags": ["widget","gratitude"], "lastUsed": null},
    {"id": "W10", "text": "The first thing I see every morning", "status": "active", "maxLines": 2, "tags": ["widget","morning"], "lastUsed": null},
    {"id": "W11", "text": "Why did nobody tell me about this...", "status": "active", "maxLines": 2, "tags": ["widget","discovery"], "lastUsed": null},
    {"id": "W12", "text": "4 years dealing with anxiety and I just find this!?", "status": "active", "maxLines": 2, "tags": ["widget","anxiety"], "lastUsed": null}
  ]
}
```

### B. /Users/anicca/.openclaw/workspace/tiktok-marketing/reelclaw-widget-hooks-ja.json

```json
{
  "family": "reelclaw-widget",
  "language": "ja",
  "version": 1,
  "hooks": [
    {"id": "W1", "text": "ロック画面にアファメーション置けるの知らなかったんだけど？", "status": "active", "maxLines": 2, "tags": ["widget","lockscreen","affirmation"], "lastUsed": null},
    {"id": "W2", "text": "どうせずっとスマホ見てるんだから", "status": "active", "maxLines": 2, "tags": ["widget","phone"], "lastUsed": null},
    {"id": "W3", "text": "え、ずっとアファメーション見れたってこと？", "status": "active", "maxLines": 2, "tags": ["widget","affirmation"], "lastUsed": null},
    {"id": "W4", "text": "ロック画面にアファメーションを設定する方法（毎日変わる）", "status": "active", "maxLines": 2, "tags": ["widget","howto"], "lastUsed": null},
    {"id": "W5", "text": "ポジティブなアファメーションをロック画面に追加する方法（毎日変わる）", "status": "active", "maxLines": 2, "tags": ["widget","howto"], "lastUsed": null},
    {"id": "W6", "text": "POV: ロック画面にアファメーション必要。追いかけない、引き寄せる", "status": "active", "maxLines": 2, "tags": ["widget","pov"], "lastUsed": null},
    {"id": "W7", "text": "POV: 毎時間新しいアファメーションくれるアプリ見つけた", "status": "active", "maxLines": 2, "tags": ["widget","pov"], "lastUsed": null},
    {"id": "W8", "text": "ロック画面にアファメーションを設定する方法 🥺", "status": "active", "maxLines": 2, "tags": ["widget","howto"], "lastUsed": null},
    {"id": "W9", "text": "POV: スマホが感謝を思い出させてくれた", "status": "active", "maxLines": 2, "tags": ["widget","gratitude"], "lastUsed": null},
    {"id": "W10", "text": "毎朝、最初に目に入る言葉", "status": "active", "maxLines": 2, "tags": ["widget","morning"], "lastUsed": null},
    {"id": "W11", "text": "なんで誰も教えてくれなかったの...", "status": "active", "maxLines": 2, "tags": ["widget","discovery"], "lastUsed": null},
    {"id": "W12", "text": "4年間不安と戦ってて今これ見つけたんだけど！？", "status": "active", "maxLines": 2, "tags": ["widget","anxiety"], "lastUsed": null}
  ]
}
```

### C. /Users/anicca/.openclaw/workspace/honne-ai/honne-hooks-en.json

```json
{
  "family": "honne-reelclaw",
  "language": "en",
  "version": 1,
  "hooks": [
    {"id": "H1", "text": "I asked AI what my boyfriend ACTUALLY meant by 'I'm fine' 😳", "status": "active", "maxLines": 2, "tags": ["relationship","decode"], "lastUsed": null},
    {"id": "H2", "text": "He left me on read. AI told me why. I wasn't ready 💔", "status": "active", "maxLines": 2, "tags": ["read","relationship"], "lastUsed": null},
    {"id": "H3", "text": "My mom said 'do whatever you want.' AI said that's NOT what she meant", "status": "active", "maxLines": 2, "tags": ["family","decode"], "lastUsed": null},
    {"id": "H4", "text": "Clap if you're against people who say 'I'm fine' when they're NOT 👏", "status": "active", "maxLines": 2, "tags": ["fine","emotion"], "lastUsed": null},
    {"id": "H5", "text": "POV: AI decoded what your boss REALLY thinks of you", "status": "active", "maxLines": 2, "tags": ["boss","pov"], "lastUsed": null},
    {"id": "H6", "text": "AI wrote the PERFECT reply to my crush's confusing text", "status": "active", "maxLines": 2, "tags": ["reply","crush"], "lastUsed": null},
    {"id": "H7", "text": "Why did nobody tell me about this app...", "status": "active", "maxLines": 2, "tags": ["discovery"], "lastUsed": null},
    {"id": "H8", "text": "3 years into my relationship and I just found this!?", "status": "active", "maxLines": 2, "tags": ["relationship"], "lastUsed": null},
    {"id": "H9", "text": "I showed AI my ex's last text. The truth hit different.", "status": "active", "maxLines": 2, "tags": ["ex","decode"], "lastUsed": null},
    {"id": "H10", "text": "AI told me what 'k' really means and I'm DONE 💀", "status": "active", "maxLines": 2, "tags": ["texting","decode"], "lastUsed": null}
  ]
}
```

### D. /Users/anicca/.openclaw/workspace/tiktok-marketing/reelclaw-empathy-hooks.json

```json
{
  "family": "reelclaw-empathy",
  "version": 1,
  "hooks": {
    "en": [
      {"id": "E1", "text": "tried 50 mental health apps. deleted 49. kept this one", "status": "active", "maxLines": 2, "tags": ["social-proof"], "lastUsed": null},
      {"id": "E2", "text": "my therapist asked what changed. i showed her my phone", "status": "active", "maxLines": 2, "tags": ["social-proof"], "lastUsed": null},
      {"id": "E3", "text": "Send this to someone who needs to hear it today 💙", "status": "active", "maxLines": 2, "tags": ["share"], "lastUsed": null},
      {"id": "E4", "text": "when i open my phone at 2am and it says 'you're not alone'", "status": "active", "maxLines": 2, "tags": ["night"], "lastUsed": null},
      {"id": "E5", "text": "My phone just told me I'll regret staying up. It's right.", "status": "active", "maxLines": 2, "tags": ["night"], "lastUsed": null}
    ],
    "ja": [
      {"id": "E1", "text": "メンタルアプリ50個試した。49個消した。これだけ残った", "status": "active", "maxLines": 2, "tags": ["social-proof"], "lastUsed": null},
      {"id": "E2", "text": "セラピストに『何が変わった？』って聞かれてスマホ見せた", "status": "active", "maxLines": 2, "tags": ["social-proof"], "lastUsed": null},
      {"id": "E3", "text": "今日これが必要な人に送って 💙", "status": "active", "maxLines": 2, "tags": ["share"], "lastUsed": null},
      {"id": "E4", "text": "深夜2時にスマホ見たら『一人じゃないよ』って書いてあった", "status": "active", "maxLines": 2, "tags": ["night"], "lastUsed": null},
      {"id": "E5", "text": "スマホに『明日後悔するよ』って言われた。正解。", "status": "active", "maxLines": 2, "tags": ["night"], "lastUsed": null}
    ]
  }
}
```

### E. /Users/anicca/.openclaw/workspace/tiktok-marketing/reelclaw-widget-rotation.json

```json
{
  "family": "reelclaw-widget",
  "version": 1,
  "lastUsed": {}
}
```

### F. /Users/anicca/.openclaw/workspace/honne-ai/honne-rotation.json

```json
{
  "family": "honne-reelclaw",
  "version": 1,
  "lastUsed": {
    "honne-ja-morning": {"video": null, "hookId": null, "date": null},
    "honne-ja-afternoon": {"video": null, "hookId": null, "date": null},
    "honne-ja-evening": {"video": null, "hookId": null, "date": null}
  }
}
```

---

## Exact New Files to Create

- /Users/anicca/.openclaw/workspace/tiktok-marketing/reelclaw-widget-hooks-ja.json
- /Users/anicca/.openclaw/workspace/tiktok-marketing/reelclaw-widget-hooks-en.json
- /Users/anicca/.openclaw/workspace/honne-ai/honne-hooks-ja.json
- /Users/anicca/.openclaw/workspace/honne-ai/honne-hooks-en.json
- /Users/anicca/.openclaw/workspace/tiktok-marketing/reelclaw-empathy-hooks.json
- /Users/anicca/.openclaw/workspace/tiktok-marketing/reelclaw-widget-rotation.json
- /Users/anicca/.openclaw/workspace/honne-ai/honne-rotation.json

---

## Exact Existing Files to Update

- /Users/anicca/anicca-project/openclaw-skills/jobs.json
- /Users/anicca/anicca-project/.cursor/plans/ios/1.8.3/cron-patches.md
- /Users/anicca/anicca-project/.cursor/plans/ios/1.8.3/10k-mrr-growth-spec.md
- /Users/anicca/.agents/skills/reelclaw/SKILL.md
- /Users/anicca/.openclaw/workspace/honne-ai/honne-mapping.json

---

## Acceptance Criteria

1. Every ReelClaw cron family points to an exact machine-readable hook file.
2. Widget W1-W12 and Honne H1-H10 no longer live only in markdown.
3. Widget and Honne hooks never render in 3 lines.
4. jobs.json no longer says vague things like "from spec".
5. Reviewers can determine the hook source of truth from one exact file path per family.
6. Card ReelClaw, widget ReelClaw, Honne JA, and Honne EN are cleanly separated.
