# Demo: synthetic monitoring catches a broken checkout, root-caused via gcx + Claude Code

A repeatable demo: ship a regression that breaks order submission, watch the
existing Synthetic Monitoring check (job `oktoberfest-checkout-flow`) go red,
root-cause it via `gcx` (logs/traces) with Claude Code, fix it, and redeploy
straight to minikube.

The bug lives on the `demo-broken-order-typo` branch — a one-line typo in
`backend/app/routers/orders.py`'s `_serialize()` helper (`item.unit_price` →
`item.unit_prices`), which breaks both order submission and order lookup
with an `AttributeError` → 500. `main` is always the known-good state.

## Prerequisites

- minikube running with the app deployed (`k8s/`) and the private probe +
  check already set up (see the Synthetic Monitoring section of the main
  README).
- `gcx` authenticated against the same Grafana Cloud stack as the check.

## 1. Resolve the check ID and confirm the baseline is green

The check's numeric ID isn't stable across recreations, so look it up by job
name rather than hardcoding it (the ID is the numeric suffix of
`metadata.name`, i.e. `<job>-<id>`):

```shell
CHECK_ID=$(gcx synthetic-monitoring checks list --job 'oktoberfest-checkout-flow' --jq '.[0].metadata.name' | tr -d '"' | grep -oE '[0-9]+$')
gcx synthetic-monitoring checks status "$CHECK_ID"
```

Should show `status: OK`. Keep `$CHECK_ID` exported in your shell for the
rest of this walkthrough.

## 2. Ship the regression

```shell
git checkout demo-broken-order-typo
minikube image build -t oktoberfest-backend:latest ./backend
kubectl -n oktoberfest rollout restart deployment/backend
kubectl -n oktoberfest rollout status deployment/backend
```

## 3. Watch the check catch it

Wait for the next scheduled run (checks every 60s):

```shell
gcx synthetic-monitoring checks status "$CHECK_ID"
gcx synthetic-monitoring checks timeline "$CHECK_ID" --from now-10m --to now
```

Should flip to `status: FAILING` within a minute or two.

## 4. Root-cause it (the actual demo part — do this live)

This is deliberately left open — the point of the demo is doing this
investigation live in Claude Code with `gcx`. Useful starting points:

- `gcx synthetic-monitoring checks get "$CHECK_ID"` — confirm which check/target.
- Backend logs around the failure window, e.g.:
  ```shell
  gcx logs query -d <loki-datasource-uid> '{k8s_pod_name=~"backend.*"}' --limit 50
  ```
  (the Python traceback for the `AttributeError` should be right there)
- Traces for the `backend` service around the same window (`gcx traces
  query`) — the error should show up as a failed span on `POST /api/orders`.
- Once the log/trace points at `orders.py`, open it in VS Code / Claude Code
  to find and fix the actual line.

## 5. Fix it and redeploy

```shell
git checkout main
minikube image build -t oktoberfest-backend:latest ./backend
kubectl -n oktoberfest rollout restart deployment/backend
kubectl -n oktoberfest rollout status deployment/backend
```

## 6. Confirm recovery

```shell
gcx synthetic-monitoring checks status "$CHECK_ID"
```

Should be back to `status: OK` within a minute or two.

## Resetting for a re-run

Nothing persists between runs except the `orders` table (each check run adds
a real order) — no other cleanup needed. Just repeat from step 2.
