# Media Audio Gate Before Posting

## Inspect the audio track before publishing

- Inspect every video and slideshow for an audio stream before you publish it.

- Record whether an audio stream exists and what mean volume it reports.

- Hold any asset with no audio stream and do not publish it in that state.

- Treat a mean volume of -91.0 dB or lower as silent and hold that asset.

- Check the audio again after any edit, mix, or re-export before you publish.

## Match the sound to the post type

- Match the sound to the post type before you publish.

- Require narration plus background music for a monk video.

- Require music for an affirmation slideshow or reel.

- Require music or narration for a demo video.

- Hold a narration track with no background music layer for a monk video even when the narration itself is audible.

## Repair and recheck a held asset

- Mix background music under narration at a low level when a monk video lacks that layer.

- Mix a music track into a silent demo or slideshow before you consider it for publishing.

- Reinspect the repaired asset for a stream, an audible level, and a type matched sound before you publish it.

- Do not reuse a previously published silent asset or an unrepaired held asset in a new post.

## Report the gate result

- Report the stream result, the mean volume, and the sound type for each gated asset.

- Report a held asset with the reason it failed and the repair you applied or still need.

- Keep the silent status attached to past reach readings so a silent asset is not judged only as a weak creative.

## Available connectors

- [Instagram](/opt/hatch/connectors/instagram/CONNECTOR.md) for feed posts, reels, carousels, and stories for the account you plan to use.

- [Threads](/opt/hatch/connectors/threads/CONNECTOR.md) for text and media posts and carousels for the account you plan to use.

- [Facebook](/opt/hatch/connectors/facebook_cli/CONNECTOR.md) for managed Page posts for the account you plan to use.

- Use `muse.connector_search` to find other connectors and `muse.skill_search` to find related skills.

- If nothing here fits, look on the web for a maintained API or MCP server and set it up with [Custom Connectors and MCPs](/opt/muse/skills/custom-connector-setup/SKILL.md), or build a custom connector.

## Alternatives for better results

- Use a music backed slideshow instead of a silent video when the video sound cannot be repaired in time.

- Keep the posting schedule moving with a different asset that already passes the gate while a failed asset is repaired.
