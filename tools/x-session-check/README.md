# x-session-check

Checks whether a saved Playwright `storage_state` session for x.com is still valid and identifies the logged-in account. Standard library only.

## Usage

```sh
./x-session-check <path-to-storage_state.json>
```

`storage_state.json` is a Playwright session export containing a `cookies` list. Cookies whose domain is `x.com` or `*.x.com` are used. If the file lacks a `ct0` cookie, one is fetched from `https://x.com/` first.

## Output

On success:

```
handle: @<screen_name>
name: <name>
session: valid
```

On any failure (bad/missing file, network error, HTTP error, login redirect, missing fields):

```
handle: unknown
name: unknown
session: invalid
```

Cookie values, tokens, the Authorization header, response bodies, and exception details are never printed.

## Exit codes

- `0` — session valid
- `1` — session invalid or any error
