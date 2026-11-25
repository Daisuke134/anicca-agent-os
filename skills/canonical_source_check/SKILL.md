# Canonical Source Check

## Identify the canonical source

- Name the one canonical source for the thing you are about to measure or diagnose before you read any copy of it.

- Treat any second copy, mirror, export or duplicate folder holding the same thing as suspect until you prove it matches the canonical source.

- Stop and find the canonical source first when two copies disagree about a fact you need.

## Check the freshness of the copy in hand

- Compare the revision of the copy in hand with the canonical source before you draw a conclusion from it, using a commit hash, a version and build number, or a live read back from the service.

- Check how far behind the canonical source a local copy sits and note any uncommitted or local only changes before you trust its contents.

- Re-read the fact from the canonical source at its current revision when the copy in hand is behind, is a mirror, or carries no revision you can compare.

- Treat a missing feature, a missing setting or a missing file found only in a stale copy as unproven, never as a gap in the real product.

## Spot a frozen series

- Compare the latest answers with the previous runs in the same ledger before you report a number.

- Treat byte identical answers across many runs as a suspected freeze, not as a stable result.

- Count how many runs share the identical answer and name the run range in your report.

- Keep a frozen series out of any claim about a change or a trend until you test it.

## Probe with a changed input and re-measure

- Send one probe that differs from the repeated prompt in a seed, a private wording, or a fresh session.

- Compare the probe answer with the repeated answer word for word.

- Treat a different probe answer as proof that the repeated series was cached and not fresh.

- Treat an identical probe answer as an open question and try a second kind of change before you trust the series.

- Change the cache busting input that the probe showed matters, such as a new seed or a reworded private probe.

- Re-run the full prompt set once with the changed input and record the new answers.

- Report the frozen range, the probe result, and the re-measured result as three separate facts.

- Label the earlier frozen values as unmeasured for the frozen window and never present them as fresh measurements.

## Diagnose only from the verified source

- Base every measurement, gap claim and fix plan on the verified canonical reading, and rerun the check from that reading when an earlier reading came from a stale copy.

- Withdraw a conclusion openly and correct the shared record when a stale copy produced it, naming the copy that misled the reading.

- Mark the stale copy itself as stale at its location when you can, so the next reader does not repeat the reading.

## Record the source in the report

- State the canonical path or service, the revision or version you read, and how you compared it in every report that rests on the reading.

- Name any copy you rejected as stale and the revision gap you measured, so a verifier can repeat the comparison.

- Leave the finding unreported rather than reporting it from an unverified copy when you cannot reach the canonical source.

## Available connectors

- Use `muse.connector_search` to find other connectors and `muse.skill_search` to find related skills.

- If nothing here fits, look on the web for a maintained API or MCP server and set it up with [Custom Connectors and MCPs](/opt/muse/skills/custom-connector-setup/SKILL.md), or build a custom connector.

## Alternatives for better results

- Compare against the live service state instead of any local copy when the service itself is the canonical source and a harmless read can reach it.

- Ask a teammate agent which copy is canonical when two copies both claim current status and neither carries a comparable revision.

- Check a short window first when a series looks frozen, so a long freeze is caught before more runs pile up.

- Keep one probe prompt per measurement set that you never reuse, so the probe stays a fresh input.

- Record the cache test beside the metric in the ledger, so the next reader sees why the old values were set aside.
