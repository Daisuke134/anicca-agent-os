# Agent Side Auth Gate

## Queue sign-ins before starting

- Put every planned sign-in for one account in a single queue and order it before opening any login page.

- Run only the first queued sign-in and keep later sign-ins waiting until the first one is fully confirmed.

- Never open two login pages for the same account at the same time, whether the work runs in the main chat, in a subagent, or in scheduled work.

- Sign in through the shared browser profile and let that session become the base for later sites.

- Confirm signed-in state by reading a page that only a signed-in user can see before moving on to the next site.

- Carry the established session into the next site instead of starting a fresh login from scratch.

## Recognize a human only gate

- Treat a password creation step, an MFA enrollment step, a biometric enrollment step, and a device confirmation step as a human only gate when it appears in a browser task.

- Stop the current browser step when such a gate appears instead of presenting the gate to the user.

- Name the gate, the site, and the step that needs it before choosing a route.

- Pause the whole queue when a prompt reports a limit or asks to try later, and do not retry until the lock has cleared.

## Complete the gate on an agent route

- Generate a random password on the agent side when a password step allows agent generation.

- Keep a generated credential out of chat, a skill, and a working file.

- Register MFA on an agent device when the service offers an authenticator app option or a security key option on such a device.

- Read a code only through an established agent device message store.

- Use a saved login or an established session first when one exists for the site.

- Never start account recovery or a password reset to bypass a verification prompt, and use normal login only.

## Save and verify the credential

- Write the credential to the designated shared credential store in the same session where the login, registration, password reset, or token issue first succeeds.

- Write only to that designated store, and never put a credential value in chat, in a skill, or in a general working file.

- Record the service name, the account identifier, and the store location beside the save so a later session can find the entry by service alone.

- Read the saved entry back from the store after writing it, and compare its length and format against what the service issued.

- Reject a saved value that is truncated, partial, or the wrong type for the service, such as a token far shorter than the tokens that service issues.

- Reissue or reset the credential and save again when the read back value fails the length or format check.

- Test the read back value with a harmless authenticated read or a fresh login before the session ends, and count the save as proven only when that test passes.

- Report the store file name, the line or entry location, the service name, and the field names written, without showing any part of the value.

- State the verification result beside the save, naming the test used and whether it passed.

## Restart with a fresh instruction after a correction

- Start a new browser task when a correction changes how a gate must be completed.

- Write the corrected instruction as the original instruction of the new task.

- Name the instruction it supersedes in the new task so the old instruction cannot outrank the correction.

- Do not patch or reuse a task that already rejected the corrected approach.

## Recover a lost credential and record a jam

- Search the designated store and any established session first when a login fails.

- Reset the credential through the agent owned email route when the stored value is missing or fails verification, then save and verify the new value with the steps above.

- Re-register with the agent owned email only when no stored value and no reset route recovers the account.

- Record a gate that has no agent route as an internal jam with the site, the gate type, and the route tried.

- Move to the next site or the next candidate instead of waiting for the user.

- Report the jam, the route tried, and the next step taken without asking the user to complete the gate.

- Retry the jammed site only after a new agent route exists.

- Check whether another task owns the browser window before retrying a failed sign-in, and retry only as the single active sign-in.

- Report which site succeeded, which site is next in the queue, and which site is blocked and why.

## Available connectors

- [1Password](/opt/hatch/connectors/onepassword/CONNECTOR.md) for choosing saved logins to sign in to websites in the Muse browser.

- Use `muse.connector_search` to find other connectors and `muse.skill_search` to find related skills.

- If nothing here fits, look on the web for a maintained API or MCP server and set it up with [Custom Connectors and MCPs](/opt/muse/skills/custom-connector-setup/SKILL.md), or build a custom connector.

## Alternatives for better results

- Prefer a service route that needs no device confirmation over a route that needs one.

- Complete account setup on an agent device before starting paid or time limited work on that account.

- Keep one record per site with its gate type and its working agent route so the next loop starts from the working route.

- Prefer a connector or an already connected session over a fresh browser sign-in when one exists.

- Verify a token at issue time rather than at first use, because a corrupted save is cheapest to replace while the issuing session is still open.

- Keep one store entry per service and update it in place on reset, so a later session never has to choose between a stale value and a current one.
