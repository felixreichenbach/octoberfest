# Oktoberfest Demo

This repository contains instructions to use Grafana's Agent O11y observability with Visual Studio Code.

## Oktoberfest Shop App

A simple 3-tier online shop for Oktoberfest booth items. See [REQUIREMENTS.md](REQUIREMENTS.md) for the full requirements.

Run the whole stack with Docker:

```shell
docker compose up --build
```

- Frontend: http://localhost:8080
- Backend API: http://localhost:8000
- Demo login: `demo` / `demo123`

### Deploying to Kubernetes / minikube

Manifests are in `k8s/` (plain YAML + a `kustomization.yaml`, no Helm). They expect the container images to already exist in the cluster's image store as `oktoberfest-backend:latest` and `oktoberfest-frontend:latest`.

```shell
minikube start

# Build the images directly inside minikube (no registry needed)
minikube image build -t oktoberfest-backend:latest ./backend
minikube image build -t oktoberfest-frontend:latest ./frontend

kubectl apply -k k8s/

minikube service frontend -n oktoberfest   # opens the shop in your browser
```

Notes:

- There's no Compose-style `depends_on` in Kubernetes, so the backend retries its database connection internally with backoff on startup instead of relying on restarts — it comes up clean even if `db` isn't ready yet.
- `k8s/secret.yaml` ships the same demo credentials as `docker-compose.yml`, for the same reason — replace them before any real deployment.
- To tear down: `kubectl delete -k k8s/` (and `minikube stop` if you're done with the cluster).

### Synthetic Monitoring (optional, via `gcx`)

There's an opt-in private [Grafana Synthetic Monitoring](https://grafana.com/docs/grafana-cloud/testing/synthetic-monitoring/) probe you can run alongside the app, so checks can target it on its private network (`frontend`, `backend:8000`, etc. — plain `localhost` or cluster-internal addresses aren't reachable by Grafana Cloud's public probes). Setting this up end to end is two steps: **deploy the probe**, then **create a check** that targets it.

#### 1. Deploy the probe

1. Provision the probe against your Grafana Cloud stack and grab its token:
   ```shell
   gcx synthetic-monitoring probes create --name oktoberfest-probe --region <region>
   ```
2. Put the resulting `serverAddress` and token into:
   - **Docker Compose**: `.env` (`SM_API_SERVER_ADDRESS`, `SM_AGENT_API_TOKEN`), then start it — it's excluded from a plain `docker compose up`:
     ```shell
     docker compose --profile monitoring up -d sm-probe
     ```
   - **Kubernetes**: `k8s/monitoring/secret.yaml`, then apply — it's kept separate from `k8s/kustomization.yaml`, so it isn't part of the main `kubectl apply -k k8s/`:
     ```shell
     kubectl apply -k k8s/monitoring/
     ```
3. Confirm it's live before creating a check against it:
   ```shell
   gcx synthetic-monitoring probes list
   ```

#### 2. Create a check that targets the probe

`k6/checkout-flow.js` exercises the full shop flow end to end — login, list products, add to cart, submit purchase, fetch the confirmation, logout — asserting on each step. `k6/generate-check.sh` turns it into a Synthetic Monitoring "Scripted" check, run periodically by the probe.

1. Make sure the probe accepts Scripted checks — on its edit page in the Grafana UI, clear **Unsupported check types: Scripted, Browser** (no `gcx` command can do this).
2. Generate the check YAML and create it:
   ```shell
   PROBE_NAME=<your-probe-name> TARGET_URL=http://frontend/ k6/generate-check.sh > check.yaml
   gcx synthetic-monitoring checks create -f check.yaml
   ```
   `PROBE_NAME` is required (see `gcx synthetic-monitoring probes list`). `TARGET_URL` defaults to `http://frontend/`, which works whether the probe was deployed via Compose or Kubernetes — in both cases the probe runs alongside the `frontend` Service (same Compose network / same `oktoberfest` namespace), so plain Service-name DNS resolves either way. Other options (`JOB_NAME`, `FREQUENCY_MS`, `TIMEOUT_MS`, `SERVICE_NAME`) are optional — see the comments at the top of `k6/generate-check.sh`.
3. Confirm it's running:
   ```shell
   gcx synthetic-monitoring checks status <ID>
   ```
   To update the check later instead of creating a new one: `gcx synthetic-monitoring checks update <ID> -f check.yaml`.

This check runs every `FREQUENCY_MS` (default 60s) for as long as the app + probe stay up, and **each successful run adds a real order** — expect a steadily growing `orders` table.

Things worth knowing:
- Scripted/Browser checks refuse targets in `10.0.0.0/8` by default (an SSRF guard baked into the probe agent, `--blocked-nets`, default `10.0.0.0/8`) — since minikube's Service network lives in that range, the check fails instantly with `IP is in a blacklisted range` until the probe is deployed with `--blocked-nets=` (already set in [k8s/monitoring/deployment.yaml](k8s/monitoring/deployment.yaml)). If you retarget the probe at something in a different private range (e.g. `192.168.0.0/16`), widen or clear `--blocked-nets` accordingly.
- `SERVICE_NAME=<value>` adds a `service_name` label at check-creation time (e.g. for correlating the check with a service in Service Center), but verified in practice: it comes back on logs/metrics as `label_service_name`, not a literal `service_name` (that field is reserved — derived from the check's own job name). Confirm in the target UI whether the prefixed form actually satisfies its matching logic before relying on it.

#### Running checkout-flow.js directly (local/CI smoke test)

Since it's a plain k6 script, `checkout-flow.js` also doubles as a smoke test you can run yourself instead of via a probe:
```shell
k6 run k6/checkout-flow.js                                  # against http://localhost:8080
k6 run -e BASE_URL=https://your-deployed-host k6/checkout-flow.js
```
It exits non-zero on any failed check (enforced via a `checks` threshold), and true to the flow it tests, **every successful run places a real order**.

#### Pointing the Compose probe at the minikube deployment instead

`sm-probe` and the minikube-deployed app are on separate Docker networks, so `sm-probe` can't resolve minikube's Service names directly. It *can* reach anything port-forwarded onto the host, though, via `host.docker.internal` (verified: `docker compose exec sm-probe wget -qO- http://host.docker.internal:8090/api/health` worked while a port-forward was open):
```shell
kubectl -n oktoberfest port-forward svc/frontend 8090:80 &
TARGET_URL=http://host.docker.internal:8090/ PROBE_NAME=oktoberfest-probe k6/generate-check.sh > check.yaml
gcx synthetic-monitoring checks create -f check.yaml
```
Two caveats: `kubectl port-forward` isn't durable — it's a foreground process tied to your session, so this only lasts as long as that command keeps running; and `host.docker.internal` is a Docker Desktop (Mac/Windows) convenience that doesn't exist on native Linux Docker. For monitoring the minikube deployment on an ongoing basis, deploying a probe inside the cluster via `k8s/monitoring/` (with its own probe/token) is the more robust option.

### Root-cause demo: broken order regression

`scripts/deploy-broken-order.sh` ships an intentional one-line regression (`item.unit_price` → `item.unit_prices` in `backend/app/routers/orders.py`) that breaks order submission/lookup with an `AttributeError` — for demoing the Synthetic Monitoring check catching a real outage, root-caused via `gcx` logs/traces, then fixed by reverting the file and redeploying. **Never commit the patched file.**

```shell
scripts/deploy-broken-order.sh
```

Watch the check (created in the Synthetic Monitoring section above) flip to `FAILING` within a minute or two — look up its ID by job name rather than hardcoding it, since it isn't stable across recreations:
```shell
CHECK_ID=$(gcx synthetic-monitoring checks list --job 'oktoberfest-checkout-flow' --jq '.[0].metadata.name' | tr -d '"' | grep -oE '[0-9]+$')
gcx synthetic-monitoring checks status "$CHECK_ID"
gcx synthetic-monitoring checks timeline "$CHECK_ID" --from now-10m --to now
```

To recover: `git checkout -- backend/app/routers/orders.py`, then rebuild and restart the backend the same way. Full walkthrough, including where to look for the root cause: [docs/demo-broken-order.md](docs/demo-broken-order.md).

### Running backend tests

The backend has a pytest suite (`backend/tests/`) covering auth, products, cart, and orders against an in-memory database — no Docker or Postgres needed. Run it before deploying any backend change:

```shell
cd backend
python3 -m venv .venv && .venv/bin/pip install -r requirements-dev.txt
.venv/bin/pytest -v
```

## Grafana `agento11y` Installation

Install packages:

```shell
brew install grafana/grafana/agento11y
```

Configure `agento11y`:

```shell
agento11y login
```

Activate the VS Code Integration:

For Copilot:

```shell
agento11y copilot install
```
> Note: Copilot does not expose token consumption metrics currently.

For Claude Code

```shell
agento11y claude install
```


Verify the installation:

```shell
agento11y local status
agento11y doctor
```
