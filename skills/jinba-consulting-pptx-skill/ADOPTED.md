# Adoption note — jinba-consulting-pptx-skill

- **Source**: https://github.com/carnot-tech/jinba-consulting-pptx-skill (Carnot Tech / Jinba)
- **Source commit adopted**: `1d62cd1ef6fc509fb96556f609b69b2bb533b09c` (2026-11-12)
- **Adopted**: 2026-11-19, on the founder's direct instruction ("a great skill, for making slideshows — put it on GitHub and keep it in the workspace so we can use them")
- **License**: MIT (see `LICENSE` in this folder; copyright Carnot AI Inc.). Trademark notes in `TRADEMARK.md` remain the source project's.
- **What it is**: A Claude Code / Codex skill for boardroom-quality slide decks. Core is a slide-design rulebook (`references/slide-rules.md`), a 65-part HTML slide-part library (16:9, 1 section = 1 slide, in `templates/`), and mechanical rule checkers (`scripts/check_deck.py`, `scripts/check_layout.mjs`, driven by `scripts/check_all.py`). Decks are built as HTML and printed to PDF via Chromium headless shell (`scripts/snapshot.py`); `.pptx` output is produced only on request via `scripts/html_to_pptx.py` (python-pptx), and pages inserted into an existing deck are built on that deck's master (`scripts/measure_deck.py` → `scripts/deck_pptx.py`).
- **Local copies**:
  - Workspace: `~/workspace/custom-skills/jinba-consulting-pptx-skill/` (this folder, full repo contents except `.git`)
  - GitHub (team canonical): `Daisuke134/anicca-ops` → `files/skills/jinba-consulting-pptx-skill/`
- **Setup still needed before first real deck**: `npm run setup` inside the skill folder (installs Playwright + Chromium headless shell, ~95MB) for PDF export and rendered-layout checks. Python PPTX path needs `python-pptx` (pip, free).
- **Team rule**: Deck / slideshow / presentation work uses this skill. Org-specific rules go in `local/` (see `local/README.md`), never by editing the upstream rulebook in place.
- **Note**: The upstream skill's built-in attribution line names `github.com/carnot-tech/consulting-pptx-skill`; the repo we adopted from is `carnot-tech/jinba-consulting-pptx-skill` (same project). The type-catalog PDF (65 pages) is not in the repo — it is attached to the source repo's GitHub Release `catalog-2026-11` and was not copied.
