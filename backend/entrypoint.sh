#!/bin/sh
set -eu
CONFIG="${KUBECONFIG_PATH:-/kube/config}"
if [ -f "$CONFIG" ]; then
  export KUBECONFIG="$CONFIG"
else
  unset KUBECONFIG || true
  export DEMO_MODE=true
  echo "No kubeconfig at ${CONFIG}; starting in DEMO_MODE"
fi
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
