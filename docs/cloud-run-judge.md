# Cloud Run Judge — owner runbook

Code execution moved off the VPS to Google Cloud Run. This documents the
architecture, the one-time setup, the deploy, and how to roll back.

## Why

Two problems, both solved by the same move:

1. **Isolation.** The judge ran submissions as a child process of the API, in
   the same container, with the same environment. A hostile submission could
   read `SECRET_KEY`, `GITHUB_TOKEN` and the database. Cloud Run gives the
   judge its own container with no secrets, no database, and a dedicated
   identity that holds no roles.
2. **Capacity for new languages.** Java needs a JDK and C++ needs a toolchain.
   The 951MB VPS is already running the API and web tier; there is no room.

It also removes the `piston` container, which was 300MB of idle memory for a
service nothing called.

## Architecture

```
merit.nullbit.in → Caddy → merit-web (nginx)
                            merit-api (FastAPI)
                                 │  JUDGE_URL + Google identity token
                                 ▼
                    Cloud Run: merit-judge-light   (python + javascript)
                    Cloud Run: merit-judge-heavy   (java + c++, later)
```

- **`judge-light`** is a straight port of the existing judge: Python and
  JavaScript, same JSON contract, no behaviour change.
- **`judge-heavy`** is planned for Java and C++. It is a separate service so
  the heavy image's cold start is only paid by Java/C++ users.
- When `JUDGE_URL` is **unset**, the API runs the local sandbox exactly as
  before. Local development, CI, and the test suite need no cloud setup.

### Cost shape (free tier, `min-instances=0`)

| Limit | Monthly allowance | Roughly |
|---|---|---|
| Requests | 2,000,000 | far above expected volume |
| Memory | 360,000 GiB-s | ~90,000 submissions at 1 GiB |
| vCPU | 180,000 vCPU-s | ~90,000 submissions at 1 vCPU |

Idle costs nothing. The only line item outside the free tier is Artifact
Registry storage beyond 0.5 GiB — with two images that is roughly $0.05–0.10
per month. `--max-instances 3` caps worst-case spend.

**Cold starts.** With `min-instances=0`, the first submission after an idle
period pays container startup: roughly 2–3s for `judge-light`. This is the
deliberate trade for staying free. `--cpu-boost` recovers a large part of it.

## 1. Prerequisites — billing must be enabled first

**Nothing below works without a billing account attached to the project.** Cloud
Run, Artifact Registry and Cloud Build all require one, and the free tier does
not exempt you from needing it — the free tier is a discount applied to a
billing account, not an alternative to having one.

Without it, `deploy.sh bootstrap` fails at the first `gcloud services enable`:

```
FAILED_PRECONDITION: Billing account for project '...' is not found.
Billing must be enabled for activation of service(s) 'run.googleapis.com, ...'
```

### Attach billing

```bash
gcloud billing accounts list          # find the ACCOUNT_ID
gcloud billing projects link merit-judge --billing-account=ACCOUNT_ID
```

If that list is empty, you have no billing account yet — create one at
<https://console.cloud.google.com/billing>. New accounts are typically offered
a 90-day credit; that sits on top of the always-free tier, so realistic
development use costs nothing either way.

### Then set a budget alert, before deploying anything

This is the actual safety net. It will not cap spend on its own, but it will
email you long before a bill exists:

```bash
gcloud billing budgets create \
  --billing-account=ACCOUNT_ID \
  --display-name="Merit judge guardrail" \
  --budget-amount=1USD \
  --threshold-rule=percent=0.5 \
  --threshold-rule=percent=1.0
```

Alerts fire at 50¢ and $1.00. Expected spend for this workload is **$0.00**.

### Why $0.00 is the realistic number

The binding limit is the vCPU allowance, not requests:

| Free tier | Equals |
|---|---|
| 180,000 vCPU-s | 50 hours of 1-vCPU instance time |
| 360,000 GiB-s | 100 hours of 1 GiB instance time |
| 2,000,000 requests | — |

At roughly 1.5s per submission, 50 hours is on the order of **100,000
submissions per month**. You would need sustained traffic far beyond a
placement-prep site to leave the free tier.

Two things that *are* billed and worth knowing: **Artifact Registry storage**
beyond 0.5 GiB (two images ≈ $0.05–0.10/month), and **Cloud Build** beyond 120
build-minutes/day (a build here takes 2–5 minutes). Neither will realistically
trigger.

## 2. Project setup

```bash
# Install the CLI: https://cloud.google.com/sdk/docs/install
gcloud auth login
gcloud projects create merit-judge --name="Merit Judge"   # or reuse a project
gcloud config set project merit-judge

# Billing must already be linked — see section 1.
```

Then:

```bash
cd /path/to/Algovista
./apps/judge/deploy.sh bootstrap
```

That enables the APIs, creates the Artifact Registry repository, and creates two
service accounts:

- `merit-judge-runtime` — what the judge container runs as. **No roles at all**,
  so a sandbox escape has nothing to authenticate as.
- `merit-judge-invoker` — what the VPS assumes when calling the judge.

## 3. Deploy

```bash
./apps/judge/deploy.sh deploy
```

Builds via Cloud Build (context is the repo root, because the Dockerfile copies
the sandbox out of the API so both paths share one implementation), then
deploys with:

```
--min-instances 0      stay in the free tier
--max-instances 3      cost ceiling
--concurrency 1        each submission is CPU-bound
--cpu-boost            free, shortens cold starts
--no-allow-unauthenticated
```

The last flag is the important one: unauthenticated requests are rejected by
the platform before they reach the container.

It finishes by printing the `JUDGE_URL` and granting the invoker account
`roles/run.invoker` on this service only.

## 4. Mint the VPS identity key

```bash
./apps/judge/deploy.sh key
```

Writes `.judge/judge-sa.json` (gitignored). Copy it to the VPS:

```bash
scp .judge/judge-sa.json Merit:/home/ubuntu/merit/.judge/judge-sa.json
```

## 5. Wire the VPS

Add to the environment used by `docker compose` on the VPS — `apps/api/.env` or
an exported env file, never committed:

```ini
JUDGE_URL=https://merit-judge-light-<hash>-as.a.run.app
GOOGLE_APPLICATION_CREDENTIALS=/run/secrets/judge-sa.json
JUDGE_TIMEOUT_SEC=60
```

`docker-compose.yml` mounts `.judge/` read-only at `/run/secrets`, so the key is
never writable from inside the container.

Startup validation refuses to boot when `JUDGE_URL` is set without
`GOOGLE_APPLICATION_CREDENTIALS`, so a half-configured deploy fails loudly
instead of failing on the first submission.

Then redeploy the API and remove the old Piston container:

```bash
cd /home/ubuntu/merit
git pull
docker compose up -d --build
docker compose ps                 # merit-piston should be gone
docker rm -f merit-piston 2>/dev/null || true
docker volume rm merit_merit-piston-packages 2>/dev/null || true
```

## 6. Verify

```bash
# The service should reject an unauthenticated call with 403:
curl -s -o /dev/null -w "%{http_code}\n" "$JUDGE_URL/health"

# Then, signed in, submit a known-good solution through the UI:
#   open a problem, paste a working solution, Run Samples → expect AC.
# And confirm the failure path is honest: stop the service and submit again —
# the UI must say nothing was graded, not show a score.
```

Server-side confirmation:

```bash
./apps/judge/deploy.sh logs     # expect one line per run, no code content
```

## 7. Rollback

Unset `JUDGE_URL` and restart the API. Submissions immediately run in the local
sandbox again — the code path never left. No data migration, no state to undo.

## Adding Java (next)

Java lands in `judge-heavy`, not here, because the JDK roughly triples the image
and would slow every Python submission's cold start.

The work is:

1. A Java harness in `apps/api/app/services/judge.py` alongside the existing
   Python and JavaScript ones: `javac` the submission plus a generated `Main.java`,
   then run it and parse the same JSON envelope.
2. Careful numeric parity with the existing exact-equality comparison — Java
   prints `1.0` where Python prints `1`.
3. Raising the per-submission time limit for Java, since `javac` alone can take
   1–3s on a cold JVM.
4. A `judge-heavy` service reusing `apps/judge/main.py` with an expanded
   `SUPPORTED_LANGUAGES` and a Dockerfile that adds the JDK.

C++ is deferred pending the per-problem type signature schema, since C++ has no
dynamic types and the harness must know each problem's return type at compile
time.
