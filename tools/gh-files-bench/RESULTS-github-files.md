# GitHub-files handoff workload — raw results (2026-11-22)

Method: two clones of this repo (sender/, receiver/) on one VM.
Sequential test: sender appends one line to inbox/bench-b.md, commits, pushes;
receiver pulls and greps for the line. Latency = append start -> line visible
in receiver. Collision test: both clones append different lines to shared.md
from the same HEAD; A pushes, then B pushes; on rejection B tries
pull --rebase + push.

Sequential: 20/20 succeeded.
Latency seconds (see gh-files-lat.txt): min 7.29, median 10.41, max 24.88, mean 10.88.

Collision test: 5 rounds.
- Push rejections (non-fast-forward): 5/5 rounds.
- pull --rebase after rejection: 5/5 rounds hit a content merge conflict in
  shared.md (both writers appended at the same tail). Automatic recovery: 0/5.
  Each round needed manual conflict resolution (recovery attempt itself took
  3.4-4.5 s before failing on the conflict).
- Conclusion: single shared append file = guaranteed conflicts under
  simultaneous writes; per-writer files avoid the class entirely.

Setup measured separately: repo create + 2 clones + seed push/pull ~= 12.2 s
plus seed commit steps. Marginal cost per additional participant: one clone.
Cost: $0 (public repo, GitHub free tier).
