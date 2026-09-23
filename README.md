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

There's an opt-in private [Grafana Synthetic Monitoring](https://grafana.com/docs/grafana-cloud/testing/synthetic-monitoring/) probe you can run alongside the app, so checks can target it on its private network (`frontend`, `backend:8000`, etc. — plain `localhost` or cluster-internal addresses aren't reachable by Grafana Cloud's public probes).

1. Provision the probe against your Grafana Cloud stack and grab its token:
   ```shell
   gcx synthetic-monitoring probes create --name oktoberfest-probe --region <region>
   ```
2. Put the resulting `serverAddress` and token into:
   - **Docker Compose**: `.env` (`SM_API_SERVER_ADDRESS`, `SM_AGENT_API_TOKEN`), then start it with `docker compose --profile monitoring up -d sm-probe` (it's excluded from a plain `docker compose up`).
   - **Kubernetes**: `k8s/monitoring/secret.yaml`, then `kubectl apply -k k8s/monitoring/` (kept separate from `k8s/kustomization.yaml` — it isn't applied by the main `kubectl apply -k k8s/`).
3. Once the probe shows up in `gcx synthetic-monitoring probes list`, create a check that targets it (e.g. `http://frontend/` from Compose, or the frontend Service's cluster address from Kubernetes) — see the `synth-manage-checks` gcx agent skill for the YAML format.

#### k6 checkout-flow script

`k6/checkout-flow.js` exercises the full shop flow end to end — login, list products, add to cart, submit purchase, fetch the confirmation, logout — asserting on each step. It's a plain k6 script, so it doubles as:

- **A local/CI smoke test**, runnable directly:
  ```shell
  k6 run k6/checkout-flow.js                                  # against http://localhost:8080
  k6 run -e BASE_URL=https://your-deployed-host k6/checkout-flow.js
  ```
  It exits non-zero on any failed check (enforced via a `checks` threshold), and true to the flow it tests, **every successful run places a real order**.
- **The body of a Synthetic Monitoring "Scripted" check**, run periodically by a probe (e.g. the private one above) instead of by you. `checkout-flow.js` stays the one source of truth for the test logic — `k6/generate-check.sh` derives the check YAML from it rather than a hand-maintained copy, since the API needs the script base64-encoded and pointed at a URL the probe (not you) can reach:
  ```shell
  PROBE_NAME=<your-probe-name> TARGET_URL=http://frontend/ k6/generate-check.sh > check.yaml
  gcx synthetic-monitoring checks create -f check.yaml
  gcx synthetic-monitoring checks status <ID>
  ```
  `PROBE_NAME` is required (see `gcx synthetic-monitoring probes list`); `TARGET_URL`, `JOB_NAME`, `FREQUENCY_MS`, `TIMEOUT_MS` all have defaults — run the script with no args set to see them, or read the comments at the top of `k6/generate-check.sh`. To update an existing check instead of creating a new one: `gcx synthetic-monitoring checks update <ID> -f check.yaml`.

  A thing worth knowing:
  - A private probe may come back from `gcx synthetic-monitoring probes create` with `disableScriptedChecks`/`disableBrowserChecks` set to `true` — no `gcx` command can toggle this (there's no `probes update`); it has to be enabled from the probe's edit page in the Grafana UI first.

  This check runs every `FREQUENCY_MS` (default 60s) for as long as the app + probe stay up, and **each successful run adds a real order** — expect a steadily growing `orders` table.

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
