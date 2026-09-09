#!/usr/bin/env bash
set -euo pipefail
URL="${1:-http://127.0.0.1:8767/?smoke=1}"
BROWSER="$(command -v google-chrome || command -v chromium || command -v chromium-browser || true)"
if [[ -z "$BROWSER" ]]; then echo "no Chromium-compatible browser found" >&2; exit 2; fi
"$BROWSER" --headless --no-sandbox --disable-gpu --disable-dev-shm-usage --virtual-time-budget=7000 --dump-dom "$URL" > /tmp/awa-threejs-dom.html
grep -q 'data-smoke-passed="true"' /tmp/awa-threejs-dom.html
if [[ "$URL" == *"relay=1"* ]]; then
  grep -q 'data-world-entity-id="operator.relay-runner.001"' /tmp/awa-threejs-dom.html
  grep -q 'data-relay-active="true"' /tmp/awa-threejs-dom.html
  grep -q 'data-contract-status="activated"' /tmp/awa-threejs-dom.html
  grep -q 'data-spawned-entity-ids="[^"]*signal.beacon.001[^"]*"' /tmp/awa-threejs-dom.html
  grep -q 'data-relay-asset-loaded="true"' /tmp/awa-threejs-dom.html
else
  grep -q 'data-world-entity-id="creature.crystal-filterer.001"' /tmp/awa-threejs-dom.html
  grep -q 'data-rebuild-count="2"\|data-rebuild-count="3"\|data-rebuild-count="4"\|data-rebuild-count="5"' /tmp/awa-threejs-dom.html
fi
if [[ "$URL" == *"effectRecipe="* ]]; then grep -q 'data-effect-recipe-applied="true"' /tmp/awa-threejs-dom.html; fi
if [[ "$URL" == *"spawn=1"* ]]; then grep -q 'data-spawned-entity-ids="[^"]*egg.crystal-filterer.001[^"]*creature.crystal-filterer.child.001[^"]*"' /tmp/awa-threejs-dom.html; fi
