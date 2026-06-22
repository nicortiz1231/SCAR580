#!/usr/bin/env bash
# Deploy staged iOS build when Editor "Launch On Device" fails (ideviceinstaller UDID mismatch).
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
APP="${PROJECT_DIR}/Saved/StagedBuilds/IOS/SCAR.app"
DEVICE="${1:-00008150-001679820A38401C}"
MAP="${2:-/Game/SCAR580/Maps/Map_AR}"

if [[ ! -d "$APP" ]]; then
  echo "Missing staged app: $APP"
  echo "Run Launch On Device (or UAT BuildCookRun) in the Editor first."
  exit 1
fi

echo "Installing to ${DEVICE}..."
xcrun devicectl device install app --device "$DEVICE" "$APP"

echo "Launching ${MAP}..."
xcrun devicectl device process launch --device "$DEVICE" com.scar580.game -- -game "$MAP"

echo "Done."
