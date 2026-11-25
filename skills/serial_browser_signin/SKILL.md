# Serial Browser Sign-In

## Queue sign-ins before starting

- Put every planned sign-in for one account in a single queue and order it before opening any login page.

- Run only the first queued sign-in and keep later sign-ins waiting until the first one is fully confirmed.

- Never open two login pages for the same account at the same time, whether the work runs in the main chat, in a subagent, or in scheduled work.

## Establish one shared session

- Sign in through the shared browser profile and let that session become the base for later sites.

- Confirm signed-in state by reading a page that only a signed-in user can see, before moving on to the next site.

- Carry the established session into the next site instead of starting a fresh login from scratch.

- Record session reuse when the next site needs no new prompt, and continue with that site as the next queued item.

## Handle verification prompts without competing

- Wait for the single verification prompt and let the user complete it before doing anything else.

- Pause the whole queue when a prompt reports a limit or asks to try later, and do not retry until the lock has cleared.

- Never start account recovery or a password reset to bypass a prompt, and use normal login only.

- Use the shared credential store for each login and never copy a credential value into chat, a skill, or a working file.

## Recover and report a failed sign-in

- Check whether another task owns the browser window before retrying a failed sign-in.

- Retry only after the earlier task has finished, and retry only as the single active sign-in.

- Report which site succeeded, which site is next in the queue, and which site is blocked and why.

## Available connectors

- [1Password](/opt/hatch/connectors/onepassword/CONNECTOR.md) for choosing saved logins to sign in to websites in the Muse browser.

- Use `muse.connector_search` to find other connectors and `muse.skill_search` to find related skills.

- If nothing here fits, look on the web for a maintained API or MCP server and set it up with [Custom Connectors and MCPs](/opt/muse/skills/custom-connector-setup/SKILL.md), or build a custom connector.

## Alternatives for better results

- Prefer a connector or an already connected session over a fresh browser sign-in when one exists.

- Do the reading work that needs no sign-in before the sign-in queue, so the queue stays short.

- Schedule sign-in dependent work after the session is established, instead of launching it in parallel.
