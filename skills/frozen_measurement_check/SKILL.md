# Check a Frozen Measurement Before You Trust It

## Spot a frozen series

- Compare the latest answers with the previous runs in the same ledger before you report a number.

- Treat byte identical answers across many runs as a suspected freeze, not as a stable result.

- Count how many runs share the identical answer and name the run range in your report.

- Keep a frozen series out of any claim about a change or a trend until you test it.

## Probe with a changed input

- Send one probe that differs from the repeated prompt in a seed, a private wording, or a fresh session.

- Compare the probe answer with the repeated answer word for word.

- Treat a different probe answer as proof that the repeated series was cached and not fresh.

- Treat an identical probe answer as an open question and try a second kind of change before you trust the series.

## Break the cache and re-measure

- Change the cache busting input that the probe showed matters, such as a new seed or a reworded private probe.

- Re-run the full prompt set once with the changed input and record the new answers.

- Report the frozen range, the probe result, and the re-measured result as three separate facts.

- Label the earlier frozen values as unmeasured for the frozen window and never present them as fresh measurements.

## Available connectors

- Use `muse.connector_search` to find other connectors and `muse.skill_search` to find related skills.

- If nothing here fits, look on the web for a maintained API or MCP server and set it up with [Custom Connectors and MCPs](/opt/muse/skills/custom-connector-setup/SKILL.md), or build a custom connector.

## Alternatives for better results

- Check a short window first when a series looks frozen, so a long freeze is caught before more runs pile up.

- Keep one probe prompt per measurement set that you never reuse, so the probe stays a fresh input.

- Record the cache test beside the metric in the ledger, so the next reader sees why the old values were set aside.
