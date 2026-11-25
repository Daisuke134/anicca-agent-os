#!/bin/bash
# Capafy Publisher CLI wrapper (durable).
# - Loads CAPAFY_ACCESS_TOKEN from the shared credentials.json (value never printed)
# - Starts the local curl relay if not running (urllib responses from
#   api.capafy.ai are truncated by this VM's egress proxy; curl is intact)
# - Points the official CLI at the relay via CAPAFY_PLATFORM_BASE_URL
set -e
BASE="$HOME/workspace/tools/capafy-publisher-skill"
if ! curl -sS -o /dev/null --max-time 3 http://127.0.0.1:8799/agent/account 2>/dev/null; then
  nohup python3 "$BASE/capafy-relay.py" 8799 > /tmp/capafy-relay.log 2>&1 &
  sleep 1
fi
export CAPAFY_ACCESS_TOKEN="$(python3 -c "
import json
d=json.load(open('$HOME/workspace/anicca-ops-push/credentials.json'))
print(d['credentials'][2]['CAPAFY_ACCESS_TOKEN'])
")"
export CAPAFY_PLATFORM_BASE_URL="http://127.0.0.1:8799"
cd "$BASE/capafy-publisher"
exec python3 packager.py "$@"
