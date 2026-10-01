#!/usr/bin/env bash
#
# Deploy the Merit judge (light tier: Python + JavaScript) to Cloud Run.
#
# Usage:
#   ./apps/judge/deploy.sh bootstrap   # one-time project setup (needs owner)
#   ./apps/judge/deploy.sh deploy      # build + deploy the service
#   ./apps/judge/deploy.sh key         # mint the VPS identity key
#   ./apps/judge/deploy.sh url         # print the value for JUDGE_URL
#   ./apps/judge/deploy.sh logs        # tail service logs
#
# Design notes:
#   * min-instances=0 keeps the free tier: nothing is billed while idle.
#   * concurrency=1 because each submission is CPU-bound; the platform scales
#     by adding instances rather than by multiplexing one.
#   * max-instances caps worst-case spend if someone floods the judge.
#   * cpu-boost is free and recovers a large part of the cold start.
#   * The service is NOT publicly callable; only the invoker SA can reach it.
#
set -euo pipefail

REGION="${REGION:-asia-south1}"          # Mumbai: closest to the Hyderabad VPS
SERVICE="${SERVICE:-merit-judge-light}"
AR_REPO="${AR_REPO:-merit}"
RUNTIME_SA="${RUNTIME_SA:-merit-judge-runtime}"
INVOKER_SA="${INVOKER_SA:-merit-judge-invoker}"

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

# Deliberately NOT computed at load time: this calls gcloud, and with `set -e`
# a missing or unauthenticated gcloud would abort the script before it printed
# anything at all — including for subcommands that do not need it.
image_ref() {
  echo "${REGION}-docker.pkg.dev/$(gcloud config get-value project 2>/dev/null)/${AR_REPO}/${SERVICE}:latest"
}

require_gcloud() {
  if ! command -v gcloud >/dev/null 2>&1; then
    echo "gcloud is not installed. See https://cloud.google.com/sdk/docs/install" >&2
    exit 1
  fi
}

require_project() {
  require_gcloud
  local project
  project="$(gcloud config get-value project 2>/dev/null || true)"
  if [[ -z "$project" || "$project" == "(unset)" ]]; then
    echo "No GCP project selected. Run: gcloud config set project <PROJECT_ID>" >&2
    exit 1
  fi
  echo "Project: $project   Region: $REGION   Service: $SERVICE"
}

require_billing() {
  local project account
  project="$(gcloud config get-value project 2>/dev/null || true)"
  # If the describe fails outright (missing component, missing permission) we
  # cannot tell, so we proceed and let the real command surface the error rather
  # than blocking on a check that might itself be wrong.
  account="$(gcloud billing projects describe "$project" \
    --format='value(billingAccountName)' 2>/dev/null || true)"
  if [[ "$account" == billingAccountName* ]]; then
    return 0   # command unavailable; fall through to the real error
  fi
  if [[ -z "$account" ]]; then
    cat >&2 <<'MSG'
Billing is not enabled on this project.

Cloud Run, Artifact Registry and Cloud Build all require a billing account.
The free tier is a discount applied to a billing account, not a replacement for
having one, so this is required even though the expected spend is $0.00.

  gcloud billing accounts list                       # find ACCOUNT_ID
  gcloud billing projects link PROJECT_ID --billing-account=ACCOUNT_ID

If that list is empty, create one at:
  https://console.cloud.google.com/billing

Then re-run this command. See docs/cloud-run-judge.md section 1.
MSG
    exit 1
  fi
  echo "Billing: $account"
}

cmd_bootstrap() {
  require_project
  require_billing
  local project
  project="$(gcloud config get-value project)"

  echo "==> Enabling APIs"
  gcloud services enable \
    run.googleapis.com \
    artifactregistry.googleapis.com \
    cloudbuild.googleapis.com \
    iamcredentials.googleapis.com

  echo "==> Artifact Registry repository (${AR_REPO})"
  gcloud artifacts repositories describe "$AR_REPO" --location="$REGION" >/dev/null 2>&1 ||
    gcloud artifacts repositories create "$AR_REPO" \
      --repository-format=docker \
      --location="$REGION" \
      --description="Merit images"

  echo "==> Runtime service account (${RUNTIME_SA})"
  # A dedicated runtime identity with no roles at all: the judge container has
  # nothing to authenticate as, so a sandbox escape cannot reach anything.
  gcloud iam service-accounts describe "${RUNTIME_SA}@${project}.iam.gserviceaccount.com" >/dev/null 2>&1 ||
    gcloud iam service-accounts create "$RUNTIME_SA" \
      --display-name="Merit judge runtime"

  echo "==> Invoker service account (${INVOKER_SA})"
  # This is the identity the VPS assumes to call the judge.
  gcloud iam service-accounts describe "${INVOKER_SA}@${project}.iam.gserviceaccount.com" >/dev/null 2>&1 ||
    gcloud iam service-accounts create "$INVOKER_SA" \
      --display-name="Merit judge invoker (VPS)"

  echo
  echo "Bootstrap complete. Next: ./apps/judge/deploy.sh deploy"
}

cmd_deploy() {
  require_project
  require_billing
  local project
  project="$(gcloud config get-value project)"

  local image
  image="$(image_ref)"

  echo "==> Building image with Cloud Build (repo root is the build context)"
  # The build context must be the repo root because the Dockerfile copies the
  # sandbox straight out of the API, so both share one implementation.
  gcloud builds submit "$REPO_ROOT" \
    --config "$REPO_ROOT/apps/judge/cloudbuild.yaml" \
    --substitutions "_IMAGE=${image}"

  echo "==> Deploying to Cloud Run"
  gcloud run deploy "$SERVICE" \
    --image "$image" \
    --region "$REGION" \
    --service-account "${RUNTIME_SA}@${project}.iam.gserviceaccount.com" \
    --memory 1Gi \
    --cpu 1 \
    --concurrency 1 \
    --min-instances 0 \
    --max-instances 3 \
    --timeout 60 \
    --cpu-boost \
    --port 8080 \
    --no-allow-unauthenticated

  echo "==> Granting ${INVOKER_SA} permission to call ${SERVICE}"
  gcloud run services add-iam-policy-binding "$SERVICE" \
    --region "$REGION" \
    --member="serviceAccount:${INVOKER_SA}@${project}.iam.gserviceaccount.com" \
    --role="roles/run.invoker" >/dev/null

  cmd_url
}

cmd_key() {
  require_project
  require_billing
  local project
  project="$(gcloud config get-value project)"
  local key_path="${REPO_ROOT}/.judge/judge-sa.json"

  mkdir -p "$(dirname "$key_path")"
  if [[ -f "$key_path" ]]; then
    echo "Key already exists at $key_path — remove it first to rotate." >&2
    exit 1
  fi

  gcloud iam service-accounts keys create "$key_path" \
    --iam-account="${INVOKER_SA}@${project}.iam.gserviceaccount.com"

  echo
  echo "Key written to $key_path (gitignored)."
  echo "Copy it to the VPS and set these in the API environment:"
  echo "  JUDGE_URL=$(gcloud run services describe "$SERVICE" --region "$REGION" --format='value(status.url)')"
  echo "  GOOGLE_APPLICATION_CREDENTIALS=/run/secrets/judge-sa.json"
}

cmd_url() {
  require_project
  echo
  echo "JUDGE_URL=$(gcloud run services describe "$SERVICE" --region "$REGION" --format='value(status.url)')"
}

cmd_logs() {
  require_project
  gcloud run services logs read "$SERVICE" --region "$REGION" --limit 50
}

case "${1:-}" in
  bootstrap) cmd_bootstrap ;;
  deploy) cmd_deploy ;;
  key) cmd_key ;;
  url) cmd_url ;;
  logs) cmd_logs ;;
  *)
    sed -n '2,20p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'
    exit 1
    ;;
esac
