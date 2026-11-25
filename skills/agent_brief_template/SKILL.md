# Write Every Delegation as a Brief

Sources: David Ch, "How to master Muse" (X, 2026-09-26); aiagentslibrary.com, "100 Best Meta Muse Prompts For Work" (five-part formula, test-lab scored); museexplained.com, "How to Use Muse: The Complete Guide" (delegate, don't chat; the one-job rule).

## Give an ongoing result, not the next action

- State the destination first: the state that should keep being true when the work is done, not the single next step. "Give it an ongoing result, not merely the next action" (David Ch).
- Add one line of why before anything else: which product grows, who installs or uses it, and how it becomes revenue.
- A vague brief gets vague work. If the outcome cannot be stated in one sentence, the delegation is not ready.

## Use the five parts, in this order

1. **Outcome.** What exists at the end, in one sentence, and who it is for. For recurring work, phrase it as the standing result each window must produce (posts published, replies sent, listings live), with the count or artifact named.
2. **Context you may use.** Name the exact connected accounts, files, ledgers, and links. A file that merely exists in the workspace is not context: name it in the brief, and paste critical facts inline for subagents, because a child does not inherit later corrections. Anything that cannot be verified gets labeled unconfirmed instead of being filled in.
3. **Boundaries.** What must not happen: surfaces not to touch, the single-writer rule for that surface, no credential values in files or chat, no reposting a downloaded winner file, no KYC step routed to a human.
4. **Stop conditions.** This house never routes a question, approval, code, or tap to the user. When a step is blocked, record the blocker and its concrete unblocking step in the goal's hidden_files, treat it as an internal jam, and keep every other part of the work moving. Name the routes that are banned for this task (for example a card-surfacing route) so the worker switches routes instead of waiting.
5. **Done when.** The finish line is a verified artifact, not a status: open the final output and read its full content and numbers; confirm arrival on the counterpart side (the public URL loads, the ledger row exists, the recipient-side state changed). Attach a "could not confirm" list to every deliverable; mark unknowns as unconfirmed and never smooth a gap over with a plausible value (the [CONFIRM] habit).

## Verification is a mandatory part of every brief (2026-11-17)

Source: Addy Osmani, "How the Claude Code team thinks about verification" (https://x.com/addyosmani/status/2122590683055993308). Verification loops are what let you delegate more: without them, delegation collapses back into a human checking everything by hand. A brief without a verification block is not ready to send. The block rides inside part 5 (Done when) or as its own labeled section, and must name all four of these:

1. **Invariants, written as sentences before the work starts (property).** State what must never break, in plain sentences a machine can hunt counterexamples against: "the headline glyph height is identical on every screenshot", "no published post contains a paywall frame", "the ledger total equals the sum of its rows". Vague checks ("looks consistent", "template matches") are not invariants. If the invariant cannot be written as a sentence, the brief is not ready.
2. **A named grader who is not the maker.** Someone other than the worker who produced the artifact scores it against the rubric (the invariants above). In the article's internal testing, a separate grader improved task success by up to 10 points. "The worker checked it themselves" does not satisfy this line; name the grader (another agent, a checker tool, a gate script) in the brief.
3. **E2E evidence.** The artifact must be run or opened end to end the way its real consumer would: the page loaded, the video played with sound, the full screenshot set swiped through. Proxy signals (file size, pixel-diff against a template, a marker string, a status field) are supporting numbers, never the evidence itself.
4. **A differential oracle.** Name the baseline the output is compared against on the same input: the winner's original post, the previous version, the fixed spec. If the oracle itself could be broken, say how the oracle was verified first — a differential against a broken oracle proves nothing.

And when the same failure repeats: do not just fix the instance. Turn the invariant into a hook, a checker, or an explicit rule the same day, so the failure is structurally impossible to repeat. House example: screenshot "verification" once compared templates and pixel-diffs only, never wrote the invariant "headline glyph height is identical on every image", and shipped en_01 at 84px against en_02 at 107px. The fix became a checker (screenshot-consistency-check, Gate D: glyph height within ±3px of the median across the whole set) that now gates every submission.

## Calibrate before you scale

- The first delegation of a new kind is one job whose wrong answer you would recognize immediately (the one-job rule).
- Two consecutive hand successes before anything becomes a loop. A loop with a bad brief does not fail once; it fails on a schedule.
- After looping, verify the first two runs against the artifact itself before calling the loop "running".

## Close the loop on every run

- Compare the result against the brief, not against effort.
- Write each correction as one permanent sentence into the brief, the loop body, or the owning skill, so the same mistake is not re-taught next week.
- If a pattern recurs across delegations, promote it: a convention line in AGENTS.md or a step in the owning skill, the same day it is learned.
