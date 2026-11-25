---
name: client-work-revenue-recipe
description: The ONE family recipe for making money on Client Work platforms (Lancers, CrowdWorks, Coconala, Upwork, Contra, Mercor, Guru, Freelancer.com, Workana, PeoplePerHour, GoLance, Twine). Covers per-platform measured state and gates, application volume targets, the 1-minute fast-response rule, winner-copy proposal structure, closing steps (in-platform acceptance, payout registration, deadline guard), pricing floors, the P&L guardrail (never spend more than earned), the 7 metrics read every run, and the standing loops that consume this recipe. Use whenever applying, replying, closing, pricing, or measuring on any client-work platform.
---

# Client Work Revenue Recipe — 家族レシピ（全受託プラットフォーム共通）

One recipe for the whole family. Per-platform loops execute it; this file is the shared brain.
Per-platform deadline mechanics live in the sibling skill `platform-deadline-guard`
(`~/workspace/custom-skills/platform-deadline-guard/SKILL.md`) — this recipe cites it, never duplicates it.
No credential values anywhere in this file. Credentials live only in the shared vault.

**Family headline (measured 2026-11-21):** November client-work sales total **$31.81**, almost
entirely Coconala ($31.80). Everything else in the family is pipeline, not revenue: escrowed
amounts, pending offers, and blocked platforms. The recipe below exists to convert pipeline
into paid, delivered work without ever spending ahead of earnings.

---

## 1. Search record (checked 2026-11-21, before writing this skill)

Founder rule applied: search first, use what exists, build only the missing piece.

### 1a. Vercel Labs skills CLI (`npx skills find …`)
- `npx skills find freelance` — attempted twice (60s+ and 40s timeouts): the CLI produced **no
  output** in this VM (hang/empty). Recorded as "no result returned", NOT as "no skill exists".
- `npx skills find upwork` — same run, same outcome: no output returned.
- `npx skills find "client acquisition"` — same run, same outcome: no output returned.
- `npx skills find proposals` — same run, same outcome: no output returned.
- Fallback used instead: the local skill catalog search (`muse.skill_search`), which found
  existing in-house skills that this recipe reuses rather than rebuilding:
  - `upwork-proposal-writer` — `~/workspace/custom-skills/upwork-proposal-writer/SKILL.md`
    (five-move winning-proposal method from a Top Rated Plus freelancer; reused in §3.3).
  - `upwork-client-messenger` — `~/workspace/custom-skills/upwork-client-messenger/SKILL.md`
    (mid-contract messages: delay news, scope pushback, rate raise; reused in §3.2).
  - `upwork-job-qualifier`, `upwork-profile-optimizer`, `upwork-invitation-responder`
    (same Upwork pack; qualifier decides whether a paid-credit application is worth it).
  - `platform-deadline-guard` — `~/workspace/custom-skills/platform-deadline-guard/SKILL.md`
    (per-platform flows, notification patterns, hard deadlines; the closing discipline in §3.4).
  - `winner_copy_by_measurement` — `~/workspace/custom-skills/winner_copy_by_measurement/SKILL.md`
    (the winner-copy method behind §3.3).

### 1b. Web best practices (browser.search, 2026-11-21)
- Upwork proposal win-rate best practices:
  - https://gigradar-io.webflow.io/blog/upwork-proposal-templates-that-convert-12-fill-in-the-blank-examples
    — 133,872 proposals: platform reply rate 7.45%; short (<50 words) or long (700+) proposals
    out-reply the 100–149-word middle; specific question + offer of a short walkthrough lifts replies.
  - https://wf.gigradar.io/blog/upwork-proposal-tips — 166,075 proposals: average reply rate 6.4%;
    restating the job title verbatim *hurts* (5.5%); on dev jobs, mirroring the client's need is
    the best hook (+0.5pt); self-intro openers lose (−0.4pt); top peers write ~630 characters.
  - https://dev.to/yaaver/i-analyzed-500-upwork-proposals-with-a-95-win-rate-heres-the-one-pattern-that-decided-everything-2leh
    — winning pattern: diagnose the buyer's specific problem first, never open with yourself;
    close with one specific question, never "looking forward to hearing from you".
  - https://www.vortenza.com/tools/upwork-proposal-calculator — good win rate = 10–20%
    (established), 3–8% (new); apply within the first 2 hours; avoid jobs with 50+ proposals.
- Contra hiring practices:
  - https://contra.com/blog/how-to-hire-freelancers-a-guide-for-businesses — buyers judge
    portfolio + past work + reviews; clear scope/deliverables/timeline win.
  - https://sidehustlepick.top/platform/contra-review/ — cover letter + attached projects must
    be *entirely* related to the job; simple, intentional letters; portfolio is the storefront.
  - Contra winner behaviour (corroborated by our own Contra loop's DigiNo-type practice):
    daily applications, very short personalised applications, Problem→Build→Result work titles,
    reviews collected early, community posting as inbound.
- Lancers / CrowdWorks / Coconala 受注 tips (Japanese):
  - https://zerokaranetshop.com/2026/10/25/teian-bun/ — 選ばれる提案文の5要素: (1) short
    self-intro, (2) restate your understanding of *their* request in your own words (the single
    most important element), (3) only relevant skills/proof, (4) process + delivery date +
    itemised estimate, (5) 1–3 specific questions. NG: copy-paste templates without a
    job-specific paragraph; "がんばります" only. Official CrowdWorks/Coconala media agree:
    answer every item the buyer asked for; split the estimate per task when budget is tight.

### 1c. Internal proven material (counts as a source)
- **Fast-response doctrine** — cron `anicca-fast-response-sweep` (every 15 min) +
  `hidden_files/fast-response-log.md`: buyer messages are answered in the same sweep they are
  detected in; the standing target is a reply within 1 minute of detection via the wake hooks,
  and never a placeholder reply (see §3.2). Founder doctrine 2026-10-28: reply speed + quality
  decide wins in competitive marketplaces.
- **Platform-deadline-guard skill** — `~/workspace/custom-skills/platform-deadline-guard/SKILL.md`:
  born from the 2026-11-17 loss (a Lancers selection sat unaccepted past its 7-day deadline).
  Rules reused here: first lane to see a deadline item owns it; an acceptance is done only when
  the button press + resulting screen are confirmed on the platform; escrow/selection is NOT
  revenue; the Gmail watchdog (`~/workspace/tools/platform-deadline-watchdog/deadline_watchdog.py`)
  runs inside the fast-response sweep.
- **Per-platform winner playbooks** already in `hidden_files/` (e.g.
  `golance-winner-playbook-2026-11-06.md`, `files/platform-best-practices-2026-11-07.md`):
  platform-specific winner types stay in those files; this recipe holds only the shared rules.

**What was missing (the only thing built here):** a single family-level recipe that joins
volume, response speed, proposal structure, closing, pricing, P&L and metrics across all 12
platforms, with the measured state and the hard gates in one table. That is this file.

---

## 2. Per-platform state table (measured 2026-11-21; source ledger named per row)

Measurement conventions: 仮払い (escrow funded) is not revenue. 当選/選定 (selected) is not a
contract. Revenue counts only when delivered + paid. "未計測" means not measured this run —
never read it as zero.

| Platform | Measured state (2026-11-21) | Gate (only where measured) | Source |
|---|---|---|---|
| **Coconala** | 今月販売額 ¥5,000 / 1件 (売上管理 ¥3,900 — ¥1,100差は未解消として併記); 残高 ¥4,290; 累積 ¥269,484; 応募中 94件 (16:34回で93→94); 取引中 0; 出品 20件公開中. Family revenue is almost entirely this row. | mrkmymt DM 返信送信が35回連続失敗 (内部の詰まり; 文面は入力欄に残留). No money gate. | `coconala-loop-2026-11-21-1634.md`; `contract-platform-ledger.md` |
| **Lancers** | 5627077: 提案一覧で「当選」表示に転換 (当選8名/提案25件) だが自社提案 28135504 詳細は依然「選定中」、契約・仮払い未発生 — **未確定**. dramia 2契約 ¥32,500 仮払い済 (¥2,500 納期2026-11-30 / ¥30,000 納期2026-12-09)・進捗0% — 売上未計上. 受注2・報酬 ¥0. 本日新規応募7件. | (1) 選定期限 **2026-11-21 18:49** — 期限前後の確定状態 (正式契約か選定取消か) を次枠で一次確認. (2) オファー 1406477 (¥35,000) はクライアント承諾待ち. (3) **振込先口座未登録** — 初回報酬の支払い前に必須 (未登録のままでは報酬が失効扱いになり得る警告あり). | `lancers-loop-2026-11-21-1526.md`; `contract-ledger-watch-2026-11-21-1816.md` |
| **CrowdWorks** | 固定報酬契約15件 合算 税込 **¥1,418** のみ (業務中8・検収中3・途中終了2・完了2). 評価5.0 (8件)・受注実績22件. 本回 返信2件・新規応募1件. | (1) オンライン秘書 提示条件同意アイテム: 期限 **2026-12-03 10:28** (ウォッチドッグ; 従来記録では契約成立＋仮払い完了で解消済み、残るのは課題テスト提出 — 一次確認で確定すること). (2) 契約 64831191 (ラフ株式会社採用) 検収未完了 — 検収依頼を送り支払い確認まで台帳に残す. (3) 条件合意後は14日で自動キャンセル — 契約リクエスト即送信 (deadline-guard). | `crowdworks-loop-2026-11-21-1634.md`; `fast-response-log.md` 申し送り67/68/80 |
| **Upwork** | Skyna Gulam R. オファー (ID 113120147, Hourly **$10/hr**): メールでは返信済み、**プラットフォーム側 Accept は未押下**. | **Accept 期限 2026-11-28** (申し送り79, 所有=海外受託レーン). 返信済み ≠ 承諾完了 — ボタン押下＋画面確認までが完了. $10/hr は §3.5 のフロア照合対象: 承諾前に料率判断を記録する. | `fast-response-log.md` (2026-11-21 18:xx 申し送り79); deadline watchdog 18:12版 (要確認1件) |
| **Contra** | Applied **85件** (公開中75 + CLOSED 10); Earned **$0**; Hired 0; 30日プロフィール閲覧 60; Discovery 50 pts; レビュー0件. 本回: 無料表示3件を全件応募 (選別なし) し Applied +3 で着地検証済み. | 無料フィード以外は Pro 有料壁 (All 101件中98件) — **加入しない** (P&L §4). ROUND.1 ビデオAI面接は physical us の段 (保持). | `contra-loop-2026-11-21-1759.md` |
| **Mercor** | **セッション切れ回帰** (16:43回: ログイン未到達、プラットフォーム全項目未確認). 直近 fresh (13:43回): Odin は 2026-11-03 からプラットフォーム側 Paused 継続; Earnings $0; Applications In progress 6 / Submitted 26 / Past 108; 割当タスクなし. | セッション回復は **founder-Chrome 段として通知済み — 再通知しない**. 回復までは Gmail で再開通知のみ監視し、未確認を「変化なし」と書かない. Paused は自社の未達ではない. | `mercor-loop-log.md` (2026-11-21 13:43 / 16:43 実行分) |
| **Guru** | ダッシュボード到達不可 (Google OAuth: アカウント選択後に無言で login.aspx へ戻る、14:25回と同型). 公開プロフィール fresh: サービス $30/hr・Starting at $50、スキル7件、All-Time Earnings **$0**、Portfolio 1件、Feedback 0件. 直近 fresh の残ビッド2件 (2026-11-20実測). | (1) OAuth 無言失敗 — 同型失敗は繰り返さない; /pro/ 直接到達を先に試し、Account Security に進んだ場合のみメール一時コード経路. (2) ビッド補充 **2026-11-28 (+10)** までは残ビッド温存. | `guru-loop-2026-11-21-1725.md`; `contract-ledger-watch-2026-11-21-1816.md` |
| **Freelancer.com** | セッション維持 (@Rasi4op, Free Member, 残高 $0.00). 既存入札2件 (1件 Open・順位100+/219、1件 Closed・落選). 優先候補 40823077 (n8n AI Chat Support, $250–750) は入札締切が迫る. | **入札クレジット 0/6** — 補充は自社計算で **≈2026-11-22 前後** (見込み; 公式確定日時ではない). 枠が戻った回は 40823077 へ最優先で公式型入札. Bid Pack は買わない (§4). | `global-freelance-loop-2026-11-21-1334.md` |
| **Workana** | ログインフォーム未到達 (Cloudflare 検証ループ、試行5回ともリセット). 前回確定値: 到達点 Step 2、応募0件. 本回は未計測 (ゼロと断定しない). | Cloudflare 門が Step 2 (電話番号) 門の手前で遮断継続. 門を越えるための有料手段は使わない. | `global-freelance-loop-2026-11-21-1334.md` |
| **PeoplePerHour** | セッション維持. 会員ステップは MEMBERSHIP PAYMENT が現在地 (ACCOUNT CREATED ✓ → APPLICATION COMPLETE ✓ → **MEMBERSHIP PAYMENT** → START APPLYING 未達). 前回確定値: Proposals 0・Earnings £0. | **有料壁 (門 #19)**: proposal credits は有料会員のみ. 方針どおり **加入しない** (§4: 稼いだ額を超える支出禁止; 本面の Earnings は £0). | `global-freelance-loop-2026-11-21-1334.md` |
| **GoLance** | セッション有効. 応募 **11件** (Pending Requirements 6・Pending 3・Declined 2)、全件変化なし. メッセージ0・オファー0・契約0・残高 $0.00. 30日検索表示 54. | 時給フローは全件 Step 1 of 3 の**動画ゲート**で停止 (Step 1 of 2 は0件) — 固定価格の未応募が出たときだけ動く. | `golance-winner-playbook-2026-11-06.md` §112 (2026-11-21 15:57枠) |
| **Twine** | サインイン未到達が継続. 直近の一次実測は 2026-11-15 (Saved 0・Applied 2・In talks 0・Won 0、無料枠 1件/日). それ以降は全項目未確認. | **Cloudflare Turnstile**「We couldn't verify you're human」でサインイン遮断 (専用ループ集計で連続39回). コード画面にも未到達. 回復するまで新規ピッチなし; 未確認を変化なしと書かない. | `LOGIN-MATRIX-backup-2026-11-21-1737-twine.md` (Twine行); anicca-twine-loop |

---

## 3. The shared money recipe

### 3.1 Application volume (the top of the funnel is a numbers game)
- **Family target: ≥30 new applications/proposals per day across all platforms** (the standing
 合算 target the per-platform loops already report against), split by where free supply exists:
  - Japanese trio (Coconala / Lancers / CrowdWorks): the bulk — every 3h loop scans new posts
    first, then widens pages; apply to **every** listing that passes the floor gates in §3.5.
    Duplicate-application avoidance is checked on the platform, not from memory.
  - Contra: **all free-visible jobs, no selection** (proven 2026-11-21: For you 3→0, Applied
    +3 verified). Pro-walled jobs are not supply.
  - Freelancer.com: bounded by bid credits — when a credit lands, spend it the same run on the
    highest-fit open candidate (queue kept in the loop log; 40823077 is first in line).
  - Guru: bounded by bids — hold until the 2026-11-28 refill, then 5–8 Quotes per run,
    unverified employers first (deadline-guard / Guru playbook rule).
  - GoLance / Upwork / Mercor: apply to every new fit that is free to apply to; Mercor only
    when the session is alive and a real assignment exists (Paused = no busywork).
  - Blocked platforms (Workana / PeoplePerHour / Twine): volume target is **zero by design**
    while the measured gate stands. Record the gate each run; do not burn tokens retrying it
    beyond the loop's single scheduled check, and never pay to pass it (§4).
- Speed of application matters: apply within the first 2 hours of a posting where the loop
  cadence allows (Upwork data, §1b); prefer jobs with few existing proposals (JP rule:
  応募者5人以下を優先; Upwork: avoid 50+ proposal jobs) — but never let preference become
  selection on free Contra supply.
- Every application is logged the same run (platform, job ID, price, deadline) so the §5
  metrics are arithmetic, not memory.

### 3.2 The 1-minute fast-response rule (no placeholder replies, ever)
- Buyer/client messages are answered by the fast-response sweep (`anicca-fast-response-sweep`,
  every 15 min, wake hooks on top): target **reply within 1 minute of detection**, always in
  the same pass that found the message.
- **Placeholder replies are banned absolutely**: no 「確認して本日中にご連絡します」, no
  "I'll confirm and get back to you", no acknowledgement-only replies. The context needed
  (calendar, agreed terms, past answers, ledgers) already exists at receipt time; the reply
  must carry a concrete proposal — deliverable, price range, dates — and close the question
  in that one message. Unanswerable sub-items are logged as 要判断事項 for the team and the
  answerable part is still sent immediately.
- Reply quality bar (from the sweep body + §1b winners): touch the buyer's specific words;
  state the next action (purchase / start / delivery date) inside the agreed terms; short and
  polite. No new discounts, no price commitments outside agreed terms, no phone/Zoom promises
  as a default (interview-required work is routed per the 2026-11-19 解禁 rule: accept the
  proposed time — "we have the time" — and batch the live part to physical us).
- A reply counts only when the sent state is read back on the platform/thread. Never re-send
  blind: read the thread first (duplicate sends are a measured failure mode).
- Platform notifications that require *our* action (acceptance, contract request, evaluation,
  escrow check) are deadline items, not "no reply needed" — see §3.4 and deadline-guard.

### 3.3 Proposal structure (winner-copy)
The shared skeleton, assembled from §1 sources (GigRadar 166k/133k datasets, the dev.to
diagnosis pattern, the JP 5-element form, our `upwork-proposal-writer` five moves, and the
CrowdWorks 「6つの質問に回答する型」 already proven in-house):

1. **Open on their problem, in their words.** First line paraphrases the buyer's need
   (「〇〇のための△△を作るお仕事と理解しました」 / mirror the client's need — the best
   dev hook). Never open with self-introduction, never restate the job title verbatim.
2. **Diagnose one step deeper.** Name the likely real challenge in one or two lines. This is
   what makes the buyer reply. Do not give away the full solution or a step-by-step plan.
3. **Proof, only relevant.** One matched result/sample (link or attachment where the platform
   rewards it). Irrelevant portfolio dumps are banned (Contra rule). Never invent a result:
   use only numbers already verified in our ledgers (e.g. Coconala 総販売32件, Contra's
   shipped-in-5-days agents). If no matched proof exists, say what the sample will be and
   offer to make it — a made sample beats a borrowed claim (JP rule).
4. **Concrete offer block — always all three:** deliverable (exactly what they receive,
   format/count), **price** (itemised per task when the budget is tight — the JP official-media
   method for budget mismatch), **timeline** (「作業開始から〇日」 / "within X days" from start).
   Answer *every* screening question the buyer asked (CrowdWorks 6-question type; missing an
   asked item is an automatic loss).
5. **Close with one specific question** that invites a reply (never "looking forward to
   hearing from you" / 「よろしくお願いします」 alone).
- Length: avoid the dead middle. Short and complete beats long and padded on bid platforms;
  on JP platforms the 5 elements must all be present even if brief. Every proposal contains
  at least one paragraph written for *this* job — pure template reuse is a measured NG.
- Language: match the job post's language, not the buyer's flag.

### 3.4 Closing steps (where money is actually won or lost)
1. **Accept inside the platform, before the deadline.** An email/message saying "we accept"
   is not acceptance. The owning lane presses the platform's accept/agree button and confirms
   the resulting screen state (deadline-guard invariant). Live examples in §2: Upwork Skyna
   Accept by **2026-11-28**; Lancers selections expire **7 days** after selection; CrowdWorks
   condition agreements auto-cancel at **14 days** without a contract request.
2. **Send the contract request the moment terms are agreed** (CrowdWorks rule); on Lancers,
   watch for 仮払い (escrow) — work starts only after escrow is funded; on Guru, never start
   before SafePay funding; on Freelancer.com, never start before the milestone is created.
3. **Register payout methods before the first payment is due.** Open item: **Lancers
   振込先口座 (bank account) is unregistered** — register it before dramia's first delivery
   completes (deliveries 2026-11-30 / 2026-12-09). Any platform showing an unregistered
   payout method while money is in escrow is a red item in the §5 read.
4. **Deliver, then chase acceptance.** Delivered ≠ paid: after delivery, send the
   検収依頼 (acceptance request) and keep the item in the handover until acceptance/payment
   is confirmed (open example: CrowdWorks 64831191). Submit evaluations/reviews before their
   deadlines — they are closing steps, not admin (Coconala 評価期限, Lancers やることリスト).
5. **Deadline-guard sweep every run.** The watchdog
   (`platform-deadline-watchdog/deadline_watchdog.py`) runs inside the fast-response sweep;
   `期限間近・未処理` (≤48h) is handled in that same pass, `期限切れ・未処理の疑い` is
   verified on the platform first — the platform's live state is the oracle, email is only a
   detection signal. No deadline item leaves the handover without a closing event.

### 3.5 Pricing logic (floors first, raises on evidence)
- **Floors (do not bid below; decline or split the scope instead):**
  - JP fixed-price tests/trials under **¥1,000** are declined (proven: ¥110/¥12-class work
    produced 15 contracts totalling ¥1,418 on CrowdWorks — volume without money). Split-scope
    proposals are the alternative when a buyer's budget is below floor for the full job.
  - CrowdWorks selection floor: client 評価 ≥4 and 完了率 ≥80% preferred; low-price test
    formats are skipped as a class (in-house losing pattern, recorded 2026-11-08).
  - Guru: **$30/hr floor, $50 minimum job** (live profile values). Contra: profile band
    **$50–$75/hr**, retainer service from $450/mo. Upwork: inbound offers below the band
    (e.g. the $10/hr Skyna offer) require a recorded rate decision before Accept — the
    decision weighs first-review value against the floor, and is written in the loop log.
  - Freelancer.com: bid at/near the measured market average for the job (e.g. €400 on a
    €250–750 job averaging €403) — never cheapest, never apologetic about price (§1b).
- **When to raise:** only on evidence — after 3–5 paid reviews on that platform, or when
  reply/win rate at the current price is measurably above the §1b baselines (Upwork reply
  ~6–7% platform average; good = 10–20% win). Contra's rule is already set: Earned $0 +
  reviews 0 → hold starting prices; revisit at 3–5 reviews. One variable at a time, recorded
  in the platform ledger.
- **Never** discount in a reply to close faster, and never promise a price in chat that the
  platform offer doesn't carry.

### 3.6 Scalability rule (where the deep tokens go)
Contract work is **kept running but is not the main line**. It is inherently low-scalability:
the family's entire November revenue ($31.81) came from it while costs ran far higher. So:
- Per-platform loops run on their fixed cadence and stop at their measured gates — no loop
  may burn extra tokens retrying a blocked platform, re-reading dead pipelines, or polishing
  beyond the one-improvement-per-run already in their bodies.
- Deep work (research, new playbooks, product fixes) goes to lanes whose ceiling can reach
  **$10k/month profit** (own products / model / distribution). Client Work's job in the
  portfolio is cash flow, reviews, and behaviour data — harvested cheaply, never chased.
- Judge every Client Work change by ROI: does it raise paid-and-delivered per loop-hour?
  If not, it doesn't ship.

---

## 4. P&L guardrail (hard rules, no exceptions)
1. **Never spend more than earned.** No new API payments. No paid membership, bid pack,
   Connects bundle, or proposal-credit purchase unless it is paid **from that platform's
   earned balance** AND a measured gate already allows it. Current applications:
   - PeoplePerHour membership: **do not buy** (Earnings £0; gate #19 stands).
   - Contra Pro: **do not buy** (Earned $0; free supply is exhausted first, every run).
   - Freelancer.com Bid Packs: **do not buy** (balance $0; wait for the free refill).
   - Upwork Connects / Guru bid purchases: only from earned balance on that platform, with
     the `upwork-job-qualifier` / Guru playbook gate recorded in the run log.
2. The $5 micro-test exception from company rules applies to *verification* costs only, not
   to platform memberships or bid inventory.
3. Every spend, however small, is recorded in the run log with amount + resulting balance.
   A platform whose cumulative spend exceeds its cumulative paid revenue is frozen to
   free-only operation until the ledger shows it back under.
4. Report revenue, cost, and profit **together**, per platform, from primary reads only.
   Escrowed (仮払い), selected (当選), and applied amounts are pipeline — never revenue.

---

## 5. Metrics read each run (per platform, every loop)
Each platform loop reads and records these seven, in this order, from the platform itself:
1. **Applications sent** (this run + cumulative, from the platform's own count where shown —
   e.g. Contra Applied, Coconala 応募中 — never from log arithmetic alone).
2. **Replies** (new buyer replies; unreplied count must end at 0 or be named with an owner).
3. **Offers** (inbound offers + their deadlines).
4. **Contracts** (agreed/in-platform accepted, with the accept-screen confirmed).
5. **仮払い (escrow funded)** — amount + job, labelled pipeline, not revenue.
6. **Delivered** (submitted and awaiting acceptance, with the acceptance chase sent).
7. **Paid** (released/received amount + balance after) — the only revenue number.

Ledgers (single-writer discipline — the owning loop writes its platform; the hourly watch
only reconciles):
- `hidden_files/contract-platform-ledger.md` — the family ledger (platform state + cross-checks).
- `hidden_files/fast-response-log.md` — every buyer message, reply time, and the deadline
  handover (申し送り) that carries open items until their closing event.
- Per-platform run logs: `hidden_files/{lancers,crowdworks,coconala,contra,guru,mercor,…}-loop-*.md`,
  reconciled hourly by `contract-ledger-watch-*.md`.
- Measurement conventions: fresh reads only (never carry a prior value forward as this run's
  value; unmeasured = 未計測, not zero); where two screens disagree, record both values;
  the platform's live state outranks email and outranks this skill's table.

## 6. Standing loops (existing consumers of this recipe — do not duplicate)
All under `~/workspace/goals/anicca-revenue-growth-as-life-manager/crons/`:
- `minutely/anicca-fast-response-sweep__interval@15m.md` — **fast-response sweep** (15 min):
  buyer-message replies (§3.2) + runs the deadline watchdog every pass (§3.4.5).
- `hourly/anicca-contract-platforms-loop__interval@1h.md` — **ledger watch** (hourly,
  read-only): reconciles all platform logs into `contract-platform-ledger.md`; never writes
  to a platform (single-writer rule).
- Per-platform owner loops (every 3h unless noted): `anicca-coconala-loop`,
  `anicca-crowdworks-loop`, `anicca-lancers-loop`, `anicca-contra-loop`, `anicca-guru-loop`,
  `anicca-mercor-loop`, `anicca-golance-loop`, `anicca-twine-loop`.
- `hourly/anicca-global-freelance-loop__interval@6h.md` — Workana / Freelancer.com /
  PeoplePerHour (the three gate-blocked or credit-bound platforms).
- Deadline watchdog: not a separate cron — `platform-deadline-watchdog/deadline_watchdog.py`
  executed inside the fast-response sweep, output to `hidden_files/deadline-watchdog-latest.md`.

**Gap found (recommendation only — no cron created or edited by this skill):**
Upwork currently has **no owning loop**: the contract-platforms body assigns "English
platforms" to the global-freelance loop, but that loop's own body covers only Workana /
Freelancer.com / PeoplePerHour and explicitly does not touch Upwork — while the family's
only live offer (Skyna, deadline 2026-11-28) sits on Upwork, carried only as a fast-response
handover item. Recommended exact addition: **one `anicca-upwork-loop` (every 3h)** owning
Upwork offers/proposals/Accept actions under this recipe, created through the normal
company-task-management route. Until it exists, the fast-response sweep's handover item 79
is the owner of record for the Skyna Accept.

## Verification (mandatory)
Work done under this skill is verified against these invariants before being reported:
1. **Invariants.** (a) Every number reported traces to a fresh platform read in the named
   source log — no carried-forward values, no log-arithmetic presented as a platform count.
   (b) 仮払い・当選・応募 are never reported as revenue; paid is the only revenue.
   (c) No spend occurred that §4 forbids. (d) Every open deadline item has a named owner
   and stays in the handover until its closing event is confirmed on the platform.
2. **Grader.** The hourly ledger watch (a different lane than the platform owner) re-derives
   the family totals from the per-platform logs; disagreements are recorded with both values.
3. **E2E.** For any claimed close (accept, contract request, delivery, payment), the
   platform screen state after the action is the evidence — a sent message is not evidence.
4. **Differential oracle.** Platform live state > email notification > this table. When this
   table and a fresh read disagree, the fresh read wins and the table is updated the same day.
