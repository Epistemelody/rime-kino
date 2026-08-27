#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
python3 "$ROOT/scripts/gen_overlay.py" --root "$ROOT" --overlay "$ROOT/overlay"
exec python3 "$ROOT/scripts/deploy.py"
