# Legacy Loop Takeover Proof

## Prove the replacement for one account

- Define proof as a live output from the replacement for that exact account.

- Accept a live link, a platform record, or a verified scheduled item for that account as proof.

- Reject a plan, a draft, a test on another account, or a general claim that the replacement works as proof.

- Record the proof, the account, and the date in the coverage record before you stop anything.

- Treat each account separately even when one job covers several accounts.

## Stop reversibly one account at a time

- Stop the legacy job for one proven account only.

- Use a reversible stop when the platform allows one, so you can restore the job without rebuilding it.

- Keep the legacy job running for every account that lacks proof.

- Record the stop, the proof it relied on, and how to restore the job.

## Verify coverage after the stop

- Check the coverage record after each stop and confirm that the account still has a working publisher.

- Check that no account is left with no publisher after a stop.

- Check the replacement output again on its next scheduled run, not only on the day you stopped the legacy job.

- Report the account, the proof, and the next scheduled output for each completed takeover.

## Restore the bridge when proof fails

- Restore the legacy job at once when the replacement misses its next output or its proof turns out to be wrong.

- Keep the restored job running until a fresh proof for that exact account exists.

- Record the gap, the restore, and the fresh proof before you stop the legacy job again.

- Do not stop a second account to compensate for a gap on the first account.

## Available connectors

- Use `muse.connector_search` to find other connectors and `muse.skill_search` to find related skills.

- If nothing here fits, look on the web for a maintained API or MCP server and set it up with [Custom Connectors and MCPs](/opt/muse/skills/custom-connector-setup/SKILL.md), or build a custom connector.

## Alternatives for better results

- Build the coverage record before a migration starts, so a stop decision never relies on memory.

- Migrate the account with the strongest proof first, and use what you learn there for the harder accounts.

- Review the coverage record whenever a publisher, a product assignment, or a channel changes.
