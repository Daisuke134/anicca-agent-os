# anicca-agent-os

**The single shared identity and operating system of the Anicca agent team — published in full.**

Anicca is an autonomous company run by AI agents. This repository is not one agent's
config folder. It is the **one canonical identity** that every agent on the team runs on:

**Grok · Instinct · ChatGPT · Codex · Dots · Pickle · Devin · OpenCode · Command Code · Pally · Gemini · Muse**

One set of MD files. One set of skills. One set of tools. No per-agent forks, no private
identity variants. A change is made once, here, and every agent picks up the same change.
This is what our company culture — **One Flesh** — means applied to the team itself:
Manager is One Model, ManagerBench is One Eval, Anicca is One Product, and the team that
builds them is One Identity.

> Founder's directive, 2026-11-25: *"Everything has to be open source. Everything. Every
> single thing. Your IDENTITY.md, AGENTS.md, everything has to be open sourced. On GitHub."*
> and *"Everybody using the same MD file, the same shared identity."*

## Layout

| Path | What it is |
|---|---|
| [`self/`](self/) | The identity itself: `AGENTS.md` (operating rules), `SOUL.md` (persona), `IDENTITY.md`, `TOOLS.md` (tool notes). Published as-is. |
| [`skills/`](skills/) | The full custom skill library every agent works from (writing, distribution, ASO/SEO/GEO, eval gates, delegation, revenue recipes, behavior-science gates, and more). |
| [`tools/`](tools/) | Tools we built ourselves: publish verification (`publish-verify`), delegation/landing audit (`delegation-check`), measurement (`measurement`), Langfuse emitter (`langfuse`), gate checkers (`*-check`), `tikwm`, `fxtwittergo`, `pixeldiff`, `manager-health`, `mspw-check`, and the rest. |
| [`prompts/`](prompts/) | Standalone prompts and playbooks that define how the company runs, including the team communication prompt. |

## Rules of this repo

1. **Public is the default.** Everything the team makes is published. Non-public is the exception and must be justified by the exception list below.
2. **One canonical set.** Agents adopt this repo as their identity/instructions. Adoption is confirmed by each agent on GitHub (team-outbox), naming the commit adopted.
3. **Pre-push secret scan is mandatory.** Every push is preceded by a secret-pattern scan (gitleaks + pattern scan) over the exact file set, and ships only on zero hits.

## What is deliberately NOT here

The only exceptions to "everything is open source" are **secrets themselves** and
**private personal records**:

- Credentials, API keys, tokens, passwords, `.env` files, SSH keys — these live in the team's private vault, never in any repo.
- Personal and family records, tax documents, raw me-data (the founder's personal data corpus).
- Browser profiles, session files, and auth artifacts (e.g. login QR images).
- Infrastructure access scripts (SSH wrappers, host files).
- Runtime state, logs, datasets, and generated media bulk (kept in their own lanes).

## Third-party tools we use (upstream is canonical — not re-published here)

We run on the shoulders of existing tools and never re-invent them. These live in their
own upstream repositories: [gitleaks](https://github.com/gitleaks/gitleaks) and
trufflehog (secret scanning), [Beads](https://github.com/gastownhall/beads) (delegation
ledger), pixelmatch, OwlASO, ReviewMetrix, AsoBeast, OpenSEO, geo-optimizer-skill,
recadro, rubric-eval, jitai-lab, app-store-scraper, appstore-review-cli, appshots,
theHarvester, EmailFinder, icloudpd, HumorBench, Chrome for Testing, Playwright,
Codex CLI, Command Code CLI, Gemini CLI, OpenCode, cloudflared, asc (App Store Connect
CLI), RevenueCat CLI, Kokoro, linejs.

## Sibling public repos

- [halo-manager-posttrain](https://github.com/Daisuke134/halo-manager-posttrain) — Manager model post-training, frozen baseline release.
- [delegation-verification-beads](https://github.com/Daisuke134/delegation-verification-beads) — how we verify delegated work actually landed, built on Beads.
- [anicca-agent-fleet](https://github.com/Daisuke134/anicca-agent-fleet) — the 24/7 resident agent workers.
- [anicca](https://github.com/Daisuke134/anicca) — the product monorepo (Manager / ManagerBench / Anicca app).
- [anicca-products](https://github.com/Daisuke134/anicca-products) — landing site and product pages.
- [zenn-articles](https://github.com/Daisuke134/zenn-articles) — research articles.

## Redactions

Initial publication (2026-11-25): **none.** The pre-push scan (gitleaks 8.28.0 + a
custom pattern scan for key prefixes, token shapes, private-key blocks, JWTs, password
assignments, and phone numbers) ran over the exact published file set and found zero
credential values. Files that mix secrets with publishable content were excluded whole
and are listed under "What is deliberately NOT here" instead of being partially redacted.

## License

MIT — see [LICENSE](LICENSE).
