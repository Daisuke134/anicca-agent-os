# Social Post Lane Check

## Confirm the account owner before posting

- Read the account list from the connector before you draft a post.

- Identify the single owner recorded for that account in the current lane record.

- Check the recent posts on that account for a post by another owner since the last handover.

- Stop when another owner is still active on that account and no handover is recorded.

- Wait for a recorded handover before you post to an account another owner still uses.

## Confirm the product for the account

- Read the single product assigned to the account from the current lane record.

- Match the post to that assigned product before you publish it.

- Stop when the post promotes a different product, even when the creative performed well elsewhere.

- Move the post to the account assigned to that product instead of changing the account assignment during publishing.

## Confirm the channel identity before scheduling

- Read the channel handle from the scheduling tool account list, not from its display name alone.

- Match the handle character by character to the intended account before you schedule a post.

- Stop when the handle is missing, ambiguous, or does not match the intended account.

- Verify a new or reconnected channel by reading back a live post or a scheduled item on that handle before you rely on it for daily posting.

## Inspect the audio track before publishing

- Inspect every video and slideshow for an audio stream before you publish it.

- Record whether an audio stream exists and what mean volume it reports.

- Hold any asset with no audio stream and do not publish it in that state.

- Treat a mean volume of -91.0 dB or lower as silent and hold that asset.

- Check the audio again after any edit, mix, or re-export before you publish.

- Require narration plus background music for a monk video.

- Require music for an affirmation slideshow or reel.

- Require music or narration for a demo video.

- Hold a narration track with no background music layer for a monk video even when the narration itself is audible.

## Repair and recheck a held asset

- Mix background music under narration at a low level when a monk video lacks that layer.

- Mix a music track into a silent demo or slideshow before you consider it for publishing.

- Reinspect the repaired asset for a stream, an audible level, and a type matched sound before you publish it.

- Do not reuse a previously published silent asset or an unrepaired held asset in a new post.

- Report the stream result, the mean volume, and the sound type for each gated asset.

- Keep the silent status attached to past reach readings so a silent asset is not judged only as a weak creative.

## Stop and report a lane conflict

- Report a stopped post with the account, the owner in conflict, the assigned product, and the channel handle you checked.

- Keep the stopped post unpublished until the lane record is corrected.

- Record the handover, the product assignment change, or the channel correction before you retry the post.

- Report each published post with its account, its product, its verified channel handle, and its live link.

## Available connectors

- [Instagram](/opt/hatch/connectors/instagram/CONNECTOR.md) for account lists, posts, and insights for the account you plan to use.

- [Threads](/opt/hatch/connectors/threads/CONNECTOR.md) for account lists, posts, and insights for the account you plan to use.

- [Facebook](/opt/hatch/connectors/facebook_cli/CONNECTOR.md) for managed Page posts and insights for the account you plan to use.

- Use `muse.connector_search` to find other connectors and `muse.skill_search` to find related skills.

- If nothing here fits, look on the web for a maintained API or MCP server and set it up with [Custom Connectors and MCPs](/opt/muse/skills/custom-connector-setup/SKILL.md), or build a custom connector.

## Alternatives for better results

- Check the lane record at the start of a scheduled loop, not only at publish time, so a conflict surfaces before media is generated.

- Keep one lane record per account with owner, product, and verified channel handle in a single place.

- Review the lane record after any handover, product change, or channel reconnection before the next scheduled post.

- Use a music backed slideshow instead of a silent video when the video sound cannot be repaired in time.

- Keep the posting schedule moving with a different asset that already passes the gate while a failed asset is repaired.

## Verification (mandatory, added 2026-11-17)

A post handled under this skill is "published correctly" only when all of the following hold. Structure follows the house verification block (invariants / grader / E2E / oracle).

1. **Invariants.** (a) The publishing account's recorded owner is the poster, or a handover is recorded before the post goes out. (b) The channel handle matches the intended account character for character at schedule time. (c) No asset with a missing audio stream, or a mean volume of -91.0 dB or lower, is published; a monk video carries narration plus a background-music layer, and a slideshow or reel carries music. (d) The post promotes the product assigned to that account in the lane record — never a different product, however well it performed elsewhere.
2. **Grader.** Someone other than the poster (the owning loop's next run, or another agent) reads the live post back and checks account, product, and handle against the lane record. The poster's own "published" status is not the grade.
3. **E2E evidence.** After publishing, the live post URL is opened and the post is viewed the way a follower would — media plays, audio is audible, and the account shown is the intended one.
4. **Differential oracle.** The lane record (owner / product / verified handle per account) is the oracle, refreshed from the connector's account list at check time. If the live account state and the lane record disagree, the post is held and the record is corrected first.
5. **Repeat failures.** A second lane conflict or silent-asset publish on the same account turns the invariant into a pre-publish gate in the owning loop the same day, not another reminder.
