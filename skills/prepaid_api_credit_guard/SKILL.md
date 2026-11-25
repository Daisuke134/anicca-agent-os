# Prepaid API Credit Guard

## Check the funding source before the first paid call

- Identify how the API is funded before the first paid call in a lane, naming whether usage draws on a prepaid wallet, on credit bundled with an already paid plan, or on pay as you go billing.

- Read the current balance or remaining credit from the vendor billing page or a harmless billing read, and record the amount, the source type, and the date checked.

- Treat bundled plan credit and prepaid wallet credit as separate sources, and use the already paid source the standing rule names first.

## Disable and verify auto reload

- Find every auto reload, auto top up, auto refill, and low balance threshold setting on the account before running paid calls.

- Turn each such setting off, then read the setting back and record it as off only when the read back shows it off.

- Stop before any paid call when a reload setting exists and you cannot verify it is off, and record that stop as an internal jam with the setting you could not confirm.

- Never enable a reload, raise a threshold, add a payment method, or buy credit to finish a job that is running out of balance.

## Spend only against the recorded balance

- Track spend against the balance recorded at the start, and stop the lane before usage reaches a point where the vendor would charge again.

- Re-read the balance after a batch of paid calls and record the new amount beside the starting amount, so a charge cannot hide inside a batch.

- Switch to a free route or another already paid source when the recorded credit runs low, rather than letting the current source refill itself.

## Report exhaustion and any charge found

- Report an exhausted source as exhausted, with the vendor, the last verified balance, and the surface that stopped, and do not buy around it.

- Disable the reload setting at once when you discover a new charge, verify it is off by reading it back, and check the other paid APIs in active use for the same setting in the same session.

- Report a discovered charge with its amount, its vendor, the remaining balance, and the verified off state of its reload setting, and never describe it as a planned purchase.

## Available connectors

- Use `muse.connector_search` to find other connectors and `muse.skill_search` to find related skills.

- If nothing here fits, look on the web for a maintained API or MCP server and set it up with [Custom Connectors and MCPs](/opt/muse/skills/custom-connector-setup/SKILL.md), or build a custom connector.

## Alternatives for better results

- Check the reload setting when a credential or account is first set up, not only when a lane starts, so a new account never carries a live refill into its first job.

- Prefer a vendor route that bills against an already paid plan over a wallet route for the same work, because a plan credit balance cannot top itself up.
