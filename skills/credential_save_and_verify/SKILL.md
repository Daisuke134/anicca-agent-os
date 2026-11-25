# Credential Save and Verify

## Save at the moment of success

- Write the credential to the designated shared credential store in the same session where the login, registration, password reset, or token issue first succeeds.

- Write only to that designated store, and never put a credential value in chat, in a skill, or in a general working file.

- Record the service name, the account identifier, and the store location beside the save so a later session can find the entry by service alone.

- Treat the login work as unfinished until this save is done, even when the site itself already works.

## Verify the saved value by reading it back

- Read the saved entry back from the store after writing it, and compare its length and format against what the service issued.

- Reject a saved value that is truncated, partial, or the wrong type for the service, such as a token far shorter than the tokens that service issues.

- Reissue or reset the credential and save again when the read back value fails the length or format check.

- Test the read back value with a harmless authenticated read or a fresh login before the session ends, and count the save as proven only when that test passes.

## Report the save without the value

- Report the store file name, the line or entry location, the service name, and the field names written, without showing any part of the value.

- State the verification result beside the save, naming the test used and whether it passed.

- Record a save that could not be verified as an internal jam with the service and the check that failed, and keep working another route instead of asking the user for the credential.

## Recover a lost credential on an agent route

- Search the designated store and any established session first when a login fails.

- Reset the credential through the agent owned email route when the stored value is missing or fails verification, then save and verify the new value with the steps above.

- Re-register with the agent owned email only when no stored value and no reset route recovers the account.

## Available connectors

- [1Password](/opt/hatch/connectors/onepassword/CONNECTOR.md) for choosing saved logins to sign in to websites in the Muse browser.

- Use `muse.connector_search` to find other connectors and `muse.skill_search` to find related skills.

- If nothing here fits, look on the web for a maintained API or MCP server and set it up with [Custom Connectors and MCPs](/opt/muse/skills/custom-connector-setup/SKILL.md), or build a custom connector.

## Alternatives for better results

- Verify a token at issue time rather than at first use, because a corrupted save is cheapest to replace while the issuing session is still open.

- Keep one store entry per service and update it in place on reset, so a later session never has to choose between a stale value and a current one.

## Verification (mandatory, added 2026-11-17)

A credential save under this skill is verified by use, not by the act of writing it. Structure follows the house verification block (invariants / grader / E2E / oracle).

1. **Invariants.** (a) Login or registration work is not "done" until the credential sits in the designated shared store and the save is reported by store file name, entry location, service name, and field names only — no credential value, and no part of one, ever appears in chat, in a skill, or in a general working file. (b) The saved value passes both the read-back length/format check and a harmless authenticated read or fresh login before the session ends. (c) One store entry per service, updated in place on reset, so no later session ever chooses between a stale value and a current one.
2. **Grader.** A fresh session or a different agent finds the entry by service name alone and completes the authenticated read. The saver's own test is necessary but is not the only grade.
3. **E2E evidence.** The authenticated read or fresh login performed with the read-back value is the evidence; a store file merely containing a string of the right shape is not.
4. **Differential oracle.** The service's own response is the oracle: the authenticated read must return the intended account (matching account identifier recorded beside the save), not merely *an* account.
5. **Repeat failures.** A second truncated or wrong-type save for the same service becomes a save-time format check in the owning workflow the same day, and the unverifiable save is recorded as an internal jam with the check that failed — never routed to the user as a request for the credential.
