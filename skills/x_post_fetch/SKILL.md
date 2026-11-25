# Read X Posts and Threads

## Choose the route

- Reach for the `custom.x_thread` helper first whenever the user shares an X or Twitter status URL, or asks what a post says, what a thread says, or whether the full text was retrieved. It needs no browser, no login and no API key.

- Run it with `muse.exec`. Give it the URL exactly as the user shared it, because it also accepts mirror and oembed URLs.

```text
python3 ~/workspace/custom-connectors/custom.x_thread/bin/x_thread.py "<url>"
```

- Use `--mode post` only when the user wants the single post and speed matters more than completeness. Say that long-form text may be truncated in that mode.

- Fall back to `browser.open`, `browser.browse` or `social.search` only when the helper reports the post unavailable, or when the user needs something this route cannot give, such as media viewing or a logged-in view. Name which route actually produced the text when you report back.

## Read the result

- Treat the digest as the post content. The header line gives the author, the post count, the root ID and the start ID, so check that the start ID matches the URL the user shared before summarizing.

- Keep the sections apart when you summarize. The numbered body is the author's own thread, quoted posts are other people's words quoted by the thread, the start path is other authors between the shared post and the root, and replies by others are reactions rather than part of the author's claim.

- Present an article post's body as the article. Its heading lines and any fenced code block are part of the article, so do not drop a code block when the user asked for the full text.

- Watch the completeness signals. A thread count of 1 for a post the user described as a thread, a note that stayed short, or replies that look sparse can mean the public page exposed only part of the conversation. Say what was actually retrieved, including the reply count, instead of claiming the whole conversation.

## Handle failures

- On exit code 3, check the ID once against the user's URL for a copy mistake. Then report the post as unavailable through this route and offer the browser fallback.

- Never retry the helper in a loop and never widen it into bulk collection. One shared link is one build.

## Available connectors

- [X Thread (no browser)](~/workspace/custom-connectors/custom.x_thread/CONNECTOR.md) for the helper's commands, output format, error codes and limits.

- Use `muse.connector_search` to find other connectors and `muse.skill_search` to find related skills.

- If nothing here fits, look on the web for a maintained API or MCP server and set it up with [Custom Connectors and MCPs](/opt/muse/skills/custom-connector-setup/SKILL.md), or build a custom connector.

## Verification (mandatory, added 2026-11-17)

Structure follows the house verification block (invariants / grader / E2E / oracle).

1. **Invariants.** (a) The digest's start ID matches the status ID in the URL the user shared; if it does not, nothing is summarized until the mismatch is resolved. (b) The author's thread, quoted posts, the start path, and other people's replies are reported as separate things — never merged into one claim. (c) Completeness is stated from the digest's own signals (post count, reply count); partial retrieval is reported as partial, never as "the whole thread". (d) When full text was requested, article bodies including fenced code blocks are delivered in full, or the truncation is stated explicitly.
2. **Grader.** The report names the route that actually produced the text (helper, browser, or social search). A summary produced from a fallback route is cross-checked against the shared URL's ID before it is presented.
3. **E2E evidence.** The helper is run on the exact URL as shared; its full digest — not a search snippet about the post — is what gets summarized.
4. **Differential oracle.** The shared URL and its root ID are the oracle. Any second source (mirror, oEmbed, search result) that disagrees with the digest on author or ID is treated as suspect, and the disagreement is reported.
5. **Repeat failures.** If the helper fails on the same class of link twice, the failure and the working fallback are written into this skill the same day.
