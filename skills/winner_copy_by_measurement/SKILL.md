# Copy a Winning Creative by Measurement

## Verify the target account and the winner link first

- Open the target account profile itself before you draft anything and record its display name, its bio, its posting language and the medium of its recent posts.

- Decide language and medium from that profile reading and never from the account name or from memory.

- Fix the copy source as one exact winner post link with its measured numbers and never as a type name, a topic or an account alone.

- Use the winner already fixed for that account in the registry or ledger and record any change of winner before production starts instead of substituting a different post during production.

- Hold production when the exact winner post cannot be opened and remeasure it or choose a replacement winner by measurement before building.

## Download and measure the winner

- Download the winning creative for study before you write your own version.

- Record the source link, the account, the post date, the duration or slide count, the views, the likes, the comments, the shares and the saves for that creative.

- Measure TikTok posts with `/home/hatch/workspace/tools/tikwm/tikwm` so photo posts also return plays, likes, comments, shares and saves.

- Write unmeasured beside any figure the measurement tool fails to return and never carry a figure over from another post or present it as fresh.

- Measure the last several posts in the same winner type before you set a length or format target.

- Record the winner follower count beside the post figures so a large account and a small account are not compared as equals.

- Never repost the downloaded file as your own post.

## Decompose the winner into a copyable type

- List the first frame, the hook, the subtitle style, the cuts, the length, the sound, the caption, the call to action and the format.

- Record the medium exactly as photo post, slideshow, still image or video and hold any build whose medium differs from the winner medium.

- Count the format mix on the winner account before you choose video or stills.

- Name the comment action the winner uses and the real item that action delivers.

- Include a keyword comment action only when you can deliver the named item in reply.

- Fix one execution source for each of your accounts so the copy does not drift between winners.

- Reject a winner whose form depends on a specific person on camera, however large its numbers, when your account cannot reproduce that form.

## Build your own version and verify it pixel by pixel

- Build your own material in the winner type with your own voice, face and words, changing the wording and the hook rather than the background set, the layout or the format.

- Set a length gate from the measured winner range and hold a version that falls outside that range.

- Run [Social Post Lane Check](~/workspace/custom-skills/social_post_lane_check/SKILL.md) before you publish and confirm the owner, the product and the channel handle.

- Compare every slide or frame side by side with the winner original with your own eyes before you schedule anything.

- Measure the visual difference with the pixelmatch setup in `/home/hatch/workspace/tools/pixeldiff` after preparing both images the same way and record the difference percentage for every slide or frame.

- Hold any slide or frame whose difference sits well above the recorded passing range for that winner type and rebuild it instead of scheduling it.

- Treat the eye check as the deciding check because a low pixel difference does not detect clipped text, a wrong language or a wrong medium.

- Check that no text is clipped at either end, that the whole design reads on one screen and that image text, caption and hashtags all use the target account language.

- Count the remaining differences between your version and the winner and keep working until the differences are listed and closed, not until the version feels similar.

- Give each account its own hook, caption and keyword instead of reusing the same file and caption across accounts.

## Measure your post and change the next one

- Record per post views, likes, comments, shares and saves for your own post.

- Label a carried over value as unmeasured and never present it as a fresh measurement.

- Compare your post with the winner post it copied and with your own account baseline for the same format before you call it a win or a failure.

- Promote your own post to a new winner only after its measured numbers pass the source it copied and record the chain back to that source.

- Change one element for the next post, such as the hook or the call to action, and record what changed.

- Repeat the download, measure, decompose and difference count for the next winner type when the current type stops improving.

## Available connectors

- [Instagram](/opt/hatch/connectors/instagram/CONNECTOR.md) for owned post lists, insights and comments for the account you plan to use.

- [Threads](/opt/hatch/connectors/threads/CONNECTOR.md) for owned post lists and insights for the account you plan to use.

- Use `muse.connector_search` to find other connectors and `muse.skill_search` to find related skills.

- If nothing here fits, look on the web for a maintained API or MCP server and set it up with [Custom Connectors and MCPs](/opt/muse/skills/custom-connector-setup/SKILL.md), or build a custom connector.

### When available

- These connectors depend on the user's channel or devices. `muse.connector_search` shows which ones this session has.

- [vidIQ](/opt/hatch/connectors/vidiq_mcp/CONNECTOR.md) for YouTube channel research, standout videos and channel analytics.

## Alternatives for better results

- Keep a pool of several winners in each niche and use the pattern that appears across the pool, not the pattern of one outlier.

- Test one hook variant against another on the same material and keep the variant that earns comments and saves.

- Start a new account with a warmup period of watching and reacting to niche videos before you post, when the account has no posting history.

- Wait for a scaling gate of repeated measured results before you raise daily volume on an account that still earns near zero views.

## Verification (mandatory, added 2026-11-17)

A copy under this skill ships only after it has been measured against the winner it copies. Structure follows the house verification block (invariants / grader / E2E / oracle).

1. **Invariants.** (a) No production starts until the winner is fixed as one exact post URL with its measured numbers recorded (views, likes, comments, shares, saves, post date, winner follower count); any figure the tool fails to return is written as unmeasured, never carried over from another post. (b) The build's medium (photo post, slideshow, still, video) equals the winner's medium, and its length sits inside the measured winner range. (c) Every slide or frame carries both a recorded pixelmatch difference percentage and an eye check; a version with any unlisted, unclosed difference from the winner does not ship.
2. **Grader.** Someone other than the builder does the side-by-side eye check against the winner original. Pixelmatch alone is never the grader: a low pixel difference does not detect clipped text, a wrong language, or a wrong medium, and the eye check is the deciding check.
3. **E2E evidence.** The finished version is swiped or played through in full the way a follower would see it, and after publishing, the own post's numbers are measured with the same tool used on the winner (tikwm) and recorded beside the winner's.
4. **Differential oracle.** The downloaded winner original itself is the oracle — never a description, a type name, or a memory of it. If the winner post cannot be opened, production holds until it is re-measured or a replacement winner is fixed by measurement.
5. **Repeat failures.** A second escape of the same defect (clipped text, wrong medium, wrong language) on the same account turns that check into a pre-publish gate in the owning loop the same day, not another reminder.
