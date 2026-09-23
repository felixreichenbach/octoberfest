#!/usr/bin/env bash
# Generates a Synthetic Monitoring "Scripted" check YAML from checkout-flow.js,
# for use with `gcx synthetic-monitoring checks create/update -f <file>`.
#
# checkout-flow.js stays the single source of truth for the test logic; this
# script only patches its BASE_URL default, since the check runs inside the
# probe's own network (e.g. a docker-compose service name) rather than on a
# machine where __ENV.BASE_URL / localhost make sense, then base64-encodes it
# as the API requires (plain text is rejected).
#
# All check-specific values are parameters, not hardcoded, since probe names
# and target URLs are specific to whoever's deploying this.
#
# Usage:
#   PROBE_NAME=my-probe TARGET_URL=http://frontend/ k6/generate-check.sh > check.yaml
#   gcx synthetic-monitoring checks create -f check.yaml
#
# Env vars:
#   PROBE_NAME   (required) Name of an existing Synthetic Monitoring probe.
#   TARGET_URL   (default: http://frontend/) URL the check's target field records,
#                and (with any trailing slash stripped) what the script's
#                BASE_URL is set to.
#   JOB_NAME     (default: oktoberfest-checkout-flow)
#   FREQUENCY_MS (default: 60000) How often the check runs, in milliseconds.
#   TIMEOUT_MS   (default: 30000) Must be less than FREQUENCY_MS.
#   SERVICE_NAME (optional) If set, adds a service_name label for correlating
#                this check with a service elsewhere (e.g. Service Center).
#                Note: the API exposes check-level custom labels prefixed —
#                this shows up on logs/metrics as `label_service_name`, not a
#                literal `service_name` (that field is reserved, derived from
#                the check's own job name). Verify in the target UI whether
#                that prefixed form actually satisfies its matching logic.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOURCE_SCRIPT="$SCRIPT_DIR/checkout-flow.js"

: "${PROBE_NAME:?Set PROBE_NAME to an existing Synthetic Monitoring probe name (see: gcx synthetic-monitoring probes list)}"
TARGET_URL="${TARGET_URL:-http://frontend/}"
JOB_NAME="${JOB_NAME:-oktoberfest-checkout-flow}"
FREQUENCY_MS="${FREQUENCY_MS:-60000}"
TIMEOUT_MS="${TIMEOUT_MS:-30000}"
SERVICE_NAME="${SERVICE_NAME:-}"

if [ "$TIMEOUT_MS" -ge "$FREQUENCY_MS" ]; then
  echo "TIMEOUT_MS ($TIMEOUT_MS) must be less than FREQUENCY_MS ($FREQUENCY_MS)" >&2
  exit 1
fi

# Strip any trailing slash for use inside the script (it appends /api/... itself).
BASE_URL="${TARGET_URL%/}"

SCRIPT_B64=$(sed "s|^const BASE_URL = .*|const BASE_URL = '${BASE_URL}';|" "$SOURCE_SCRIPT" | base64 | tr -d '\n')

LABELS_YAML="    - name: source
      value: k6-generate-check"
if [ -n "$SERVICE_NAME" ]; then
  LABELS_YAML="${LABELS_YAML}
    - name: service_name
      value: ${SERVICE_NAME}"
fi

cat <<YAML
apiVersion: syntheticmonitoring.ext.grafana.app/v1alpha1
kind: Check
metadata:
  name: ${JOB_NAME}
spec:
  job: ${JOB_NAME}
  target: ${TARGET_URL}
  frequency: ${FREQUENCY_MS}
  timeout: ${TIMEOUT_MS}
  enabled: true
  labels:
${LABELS_YAML}
  probes:
    - ${PROBE_NAME}
  alertSensitivity: none
  basicMetricsOnly: false
  settings:
    scripted:
      script: ${SCRIPT_B64}
YAML
