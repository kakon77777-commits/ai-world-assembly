#!/usr/bin/env bash
set -euo pipefail
URL="${1:-http://127.0.0.1:8767/?smoke=1}"
BROWSER="$(command -v google-chrome || command -v chromium || command -v chromium-browser || true)"
if [[ -z "$BROWSER" ]]; then echo "no Chromium-compatible browser found" >&2; exit 2; fi
"$BROWSER" --headless --no-sandbox --disable-gpu --disable-dev-shm-usage --virtual-time-budget=6000 --dump-dom "$URL" > /tmp/awa-threejs-dom.html
grep -q 'data-smoke-passed="true"' /tmp/awa-threejs-dom.html
grep -q 'data-world-entity-id="creature.crystal-filterer.001"' /tmp/awa-threejs-dom.html
grep -q 'data-rebuild-count="2"\|data-rebuild-count="3"\|data-rebuild-count="4"' /tmp/awa-threejs-dom.html

if [[ "$URL" == *"effectRecipe="* ]]; then grep -q 'data-effect-recipe-applied="true"' /tmp/awa-threejs-dom.html; fi
