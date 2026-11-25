# LINE MCP Bridge (shared linejs session window)

Stands up the shared LINE session (linejs-cli, profile `~/.linejs/default.json`)
as an MCP server reachable over Streamable HTTP, so anything running **on this
VM** can read/write LINE through the one shared session instead of logging in
again.

## Shape

- `line-mcp-launcher.sh` — starts `line mcp` (stdio) with the two environment
  fixes this VM needs:
  - `NODE_OPTIONS=--require ~/workspace/tools/linejs-proxy-preload.cjs`
    (without it, linejs network calls from this VM fail), and
  - `HOME=/home/hatch` (under systemd HOME is /root and linejs would look for
    the profile in the wrong place).
- `supergateway` (npm, installed in this directory) bridges stdio MCP to
  Streamable HTTP.
- systemd unit: `/etc/systemd/system/line-mcp-bridge.service` (enabled,
  `Restart=on-failure`). Manage with `systemctl {status,restart} line-mcp-bridge`.

## Endpoint

- `POST http://127.0.0.1:8931/mcp` (Streamable HTTP, stateless)
- `GET  http://127.0.0.1:8931/healthz` → `ok`
- Tools: `list_linejs_cli`, `execute_linejs_cli` (argument is `args`: string[],
  e.g. `{"args":["chats","list"]}`; `--json` is forced; long-running commands
  such as `listen`/`mcp` are rejected by the server itself).

## Why localhost only (measured 2026-11-17)

This VM's Tailscale client is outbound-only: per
`/opt/hatch/connectors/tailscale/CONNECTOR.md` it "accepts none [inbound
connections], hosts nothing". The VM's tailnet address (100.103.95.51) is not
assigned to any local interface — binding to it fails with
`Cannot assign requested address` (verified). So no machine outside this VM
can connect to this bridge today. Agents outside the VM use the GitHub
gateway instead: see anicca-ops
`team-outbox/muse/to-all-2026-11-17-line-gateway-how-to.md`.

## Rules

- Never run `line auth login` / `logout` through this window; that would break
  the shared session for everyone.
- The session file itself is never copied or distributed. Access is only
  through this window (on-VM) or the GitHub gateway (off-VM).
- Verified 2026-11-17: `auth status` → authenticated true; `chats list` →
  40 chats returned, both directly and through the systemd service.
