#!/usr/bin/env bash
# The ONLY sanctioned path for submitting an Anicca build for App
# Store review. The E2E gate sits ON the submission path: if the
# deterministic checker does not certify this exact version+build
# (fresh passing Maestro gate record in anicca-ops
# files/e2e-gate-records/), this script refuses and `asc review
# submit` is never invoked.
#
# Usage:
#   submit_with_gate.sh VERSION BUILD_NUMBER BUILD_ID [extra asc flags...]
# Example:
#   submit_with_gate.sh 1.11.2 841 2e09bde9-e886-4cf0-a919-cd7ab76154e5
#
# Env overrides: E2E_GATE_RECORDS_DIR, ASC_BIN.
set -euo pipefail

VERSION=${1:?Usage: submit_with_gate.sh VERSION BUILD_NUMBER BUILD_ID [extra asc flags...]}
BUILD=${2:?Usage: submit_with_gate.sh VERSION BUILD_NUMBER BUILD_ID [extra asc flags...]}
BUILD_ID=${3:?Usage: submit_with_gate.sh VERSION BUILD_NUMBER BUILD_ID [extra asc flags...]}
shift 3

HERE=$(cd "$(dirname "$0")" && pwd)
ASC_BIN=${ASC_BIN:-$HOME/workspace/tools/asc}
APP_ID=6755129214

echo "== e2e-gate: certifying $VERSION ($BUILD) before submission =="
if ! python3 "$HERE/e2e_gate.py" --version "$VERSION" --build "$BUILD"; then
  echo "E2E GATE FAILED — refusing to submit $VERSION ($BUILD) for review." >&2
  echo "Run the gate suite first (workflow anicca-e2e-gate.yml) and land a passing record." >&2
  exit 1
fi

echo "== e2e-gate: PASS — submitting $VERSION ($BUILD) for review =="
exec "$ASC_BIN" review submit --app "$APP_ID" --version "$VERSION" \
  --build-id "$BUILD_ID" --confirm "$@"
