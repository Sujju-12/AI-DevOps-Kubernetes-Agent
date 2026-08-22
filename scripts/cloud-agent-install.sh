#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

echo "==> Installing backend Python dependencies"
cd backend
if [[ ! -d .venv ]]; then
  python3 -m venv .venv
fi
# shellcheck disable=SC1091
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
mkdir -p logs
if [[ ! -f .env ]]; then
  cp .env.example .env
fi

echo "==> Installing frontend Node dependencies"
cd "$ROOT_DIR/frontend"
if [[ -f package-lock.json ]]; then
  npm ci
else
  npm install
fi
if [[ ! -f .env.local ]]; then
  cp .env.example .env.local
fi

echo "==> Cloud Agent install complete"
