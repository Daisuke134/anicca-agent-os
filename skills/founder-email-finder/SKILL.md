---
name: founder-email-finder
description: Find founder and company emails without paid APIs — free OSS tools (theHarvester, EmailFinder, Prospector) plus primary sources (official privacy/contact pages, paper author lines, personal sites) and DoH-based MX verification. Never end with "no public email" without running this playbook.
---

# Founder Email Finder

Rule: 「公開メールが無い」で終わらせない。創業者・企業メールはこの手順で探し尽くす。

## Stack (all free, no API keys, no new payments)
- `~/workspace/tools/email-finder-stack/theHarvester` — laramies/theHarvester (OSINT, 18k★)
- `~/workspace/tools/email-finder-stack/EmailFinder` — Josue87/EmailFinder (search-engine @domain extraction)
- `~/workspace/tools/email-finder-stack/prospector-mcp-email-finder` — JosieBot26/prospector-mcp-email-finder
  - engine: `src/email-engine.js` exports verifyEmail / verifyMX / verifySMTP / scrapeEmailsFromWebsite / generateEmailCandidates
  - runs on Node dns/net only; no external subscription.

## Procedure
1. **Primary sources first** (highest hit rate for founders):
   - Company official Privacy Policy / Cookie Policy / Terms "Contact Us" section (legal@, inquiries@ live here).
   - Founder's academic papers: arXiv author lines and "Correspondence to" give university emails (e.g. kzliu@cs.stanford.edu, joonspk@stanford.edu).
   - Founder's personal site / GitHub repo README contact lines (e.g. hi@erikchi.com, repo README contact).
   - Official press releases (GlobeNewswire etc.) for company comms inboxes (e.g. comms@ssi.inc).
   - Founder's own public statements (HN posts, interviews) for personal addresses (e.g. pg@ycombinator.com, sam@openai.com).
2. **Tool runs**: Prospector `scrapeEmailsFromWebsite` on the company domain; theHarvester / EmailFinder for @domain extraction from search engines.
3. **Verify the domain, label honestly**:
   - This VM's DNS returns 198.18.0.0/15 fake IPs for public domains — local dig/MX is USELESS. Always verify MX via DoH: `curl -s "https://dns.google/resolve?name=<domain>&type=MX" -H "accept: application/dns-json"` (curl respects the egress proxy; python urllib direct connections hang — do not use).
   - Prospector's built-in verifyEmail fails on this VM with `dns_error: EREFUSED` — that is an environment failure, NOT an invalid email. Record it as such.
   - SMTP RCPT checks need direct port 25, which the proxy environment blocks; do not claim SMTP verification unless actually run.
4. **Tiers**: A = published by the person/company themselves (primary source). B = reputable secondary (Crunchbase, Golden, Clay format dossiers). Pattern guesses (firstname@domain) are ALWAYS labeled 推測・未検証 and never treated as found.
5. **Record**: every found email goes to anicca-ops `files/` with source URL + verification method. No sending from this skill — discovery and recording only.

## Proven results (2026-11-18)
See anicca-ops `files/founder-emails-found-2026-11-18.md`: Simile (joonspk@stanford.edu, legal@simile.com/.ai), Second (kzliu@cs.stanford.edu, hi@erikchi.com), Aaru (inquiries@aaru.com), SSI (comms@ssi.inc), OpenAI (sam@openai.com), YC (pg@ycombinator.com). All domains MX-verified via DoH.
