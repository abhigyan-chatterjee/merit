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
IMAGE="${REGION}-docker.pkg.dev/$(gcloud config get-value project 2>/dev/null)/${AR_REPO}/${SERVICE}:latest"

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

require_project() {
  local project
  project="$(gcloud config get-value project 2>/dev/null || true)"
  if [[ -z "$project" || "$project" == "(unset)" ]]; then
    echo "No GCP project selected. Run: gcloud config set project <PROJECT_ID>" >&2
    exit 1
  fi
  echo "Project: $project   Region: $REGION   Service: $SERVICE"
}

cmd_bootstrap() {
  require_project
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
  local project
  project="$(gcloud config get-value project)"

  echo "==> Building image with Cloud Build (repo root is the build context)"
  # The build context must be the repo root because the Dockerfile copies the
  # sandbox straight out of the API, so both share one implementation.
  gcloud builds submit "$REPO_ROOT" \
    --config "$REPO_ROOT/apps/judge/cloudbuild.yaml" \
    --substitutions "_IMAGE=${IMAGE}"

  echo "==> Deploying to Cloud Run"
  gcloud run deploy "$SERVICE" \
    --image "$IMAGE" \
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
