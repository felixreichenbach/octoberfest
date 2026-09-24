#!/usr/bin/env bash
# Ships the intentional order-submission regression for the root-cause demo
# (see docs/demo-broken-order.md): patches _serialize() in orders.py to the
# same one-line typo as the demo-broken-order-typo branch (item.unit_price ->
# item.unit_prices), rebuilds the backend image inside minikube, and restarts
# the deployment so the bug is live. Never commit this change to main.
#
# Usage:
#   scripts/deploy-broken-order.sh

set -euo pipefail

NAMESPACE="oktoberfest"
ORDERS_FILE="backend/app/routers/orders.py"

if [ -n "$(git status --porcelain -- "$ORDERS_FILE")" ]; then
  echo "$ORDERS_FILE already has uncommitted changes — commit, stash, or discard them first." >&2
  exit 1
fi

if grep -q 'item\.unit_prices' "$ORDERS_FILE"; then
  echo "$ORDERS_FILE already has the regression applied." >&2
  exit 1
fi

sed -i.bak -E 's/item\.unit_price([,) ])/item.unit_prices\1/g' "$ORDERS_FILE"
rm -f "${ORDERS_FILE}.bak"

minikube image build -t oktoberfest-backend:latest ./backend
kubectl -n "$NAMESPACE" rollout restart deployment/backend
kubectl -n "$NAMESPACE" rollout status deployment/backend

echo "Regression deployed (patched $ORDERS_FILE). Watch the check flip to FAILING, then recover with:"
echo "  git checkout -- $ORDERS_FILE && minikube image build -t oktoberfest-backend:latest ./backend && kubectl -n $NAMESPACE rollout restart deployment/backend"
