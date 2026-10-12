# Merit Judge — Cloud Run workload
#
# Deliberately minimal: Python and Node only, no compiler toolchain, no
# database driver, no secrets. Java and C++ will live in a separate heavier
# service so this one keeps a short cold start.
#
# Build context is the REPO ROOT (not this directory) because the sandbox is
# copied from the API so both share one implementation.

FROM node:20-slim AS node

FROM python:3.12-slim

# Two identities, and the server keeps the container's default root so it can
# hand each submission to a *different* one. Sharing a single account between
# the server and the code it runs means a submission that escapes the sandbox
# holds the same privileges as the process it escaped. `sandbox` is that second
# identity: it owns nothing, and /app stays owned by `judge`.
RUN useradd --create-home --shell /usr/sbin/nologin judge \
    && useradd --no-create-home --shell /usr/sbin/nologin sandbox

WORKDIR /app

# Node is copied from the official image rather than installed via apt so the
# runtime version is pinned instead of tracking the Debian release.
COPY --from=node /usr/local/bin/node /usr/local/bin/node

# Single source of truth for the sandbox: the API runs the exact same file
# locally when no remote judge is configured.
COPY apps/api/app/services/judge.py /app/sandbox.py
COPY apps/judge/main.py /app/main.py
COPY apps/judge/requirements.txt /app/requirements.txt

RUN pip install --no-cache-dir -r /app/requirements.txt

# The sandbox writes its scratch files into a temp dir per run.
RUN chown -R judge:judge /app

ENV PORT=8080
EXPOSE 8080

# One worker: each request is CPU-bound and the platform scales by instance.
# $PORT is expanded at start so this, deploy.sh's --port, and Cloud Run's
# PORT all describe the same socket instead of three independent numbers.
CMD ["sh", "-c", "exec python -m uvicorn main:app --host 0.0.0.0 --port ${PORT:-8080} --workers 1"]
