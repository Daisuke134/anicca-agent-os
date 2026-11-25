#!/bin/sh
# Launcher for the shared LINE session MCP server (linejs-cli `line mcp`).
# The proxy preload is required: without it, linejs network calls from this VM
# fail (see ~/TOOLS.md, linejs proxy preload note).
export NODE_OPTIONS="--require /home/hatch/workspace/tools/linejs-proxy-preload.cjs"
# The shared session lives under /home/hatch/.linejs; under systemd HOME is
# /root, which would make linejs look for the profile in the wrong place.
export HOME=/home/hatch
exec /home/hatch/.local/bin/line mcp
