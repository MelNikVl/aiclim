# Deployment procedure

## LAN demo on the existing server

The application is deployed on the user's existing server at **http://192.168.0.15:8000**. Its isolated checkout is `/home/nik/tastedistrict`, and its container is `tastedistrict`. On 2026-10-19, revision `12ad190c632b19c39605d04ee426238e841663c9` was built as `tastedistrict:12ad190` and verified from a browser on the Windows workstation. See [VERIFICATION.md](VERIFICATION.md) for the evidence and limits.

This deployment uses **Demo data**: fictional venues and synthetic affinities. No Qloo credential is configured. It is available only to clients that can reach the LAN server; it is not an externally published contest demo. External publication, new accounts, paid resources and repository visibility changes still need the user's separate approval.

Connect and inspect only this application:

```sh
ssh nik@192.168.0.15
cd /home/nik/tastedistrict
docker ps --filter 'name=^/tastedistrict$'
docker compose ps
docker compose logs --tail 100 tastedistrict
```

Before the first deployment, `ss -ltn` showed no listener on TCP port **8000**, and no running Docker container published it. After deployment, `ss -ltn '( sport = :8000 )'` and `docker ps --filter publish=8000` show only TasteDistrict at `192.168.0.15:8000`. Repeat those checks before changing the binding.

`compose.yaml` now records the dedicated container, LAN binding, restart policy, read-only filesystem, temporary `/tmp`, dropped capabilities, no-new-privileges, one CPU, 256 MB memory, bounded logs and process health check. It manages this application only. Do not restart or prune the Docker host or operate on unrelated services.

### Apply a key or another environment-only change

Edit `/home/nik/tastedistrict/.env` privately with `nano .env`; keep the existing `APP_SECRET`. Use the [official event key request form](https://forms.gle/zz12orkLHTAneLGz6) to obtain an event-issued credential. Set `QLOO_API_KEY` and `DATA_MODE=live`; keep `QLOO_BASE_URL=https://hackathon.api.qloo.com`. Check credential terms/quota before making live requests.

```sh
docker compose config --quiet
docker compose run --rm --no-deps --entrypoint python \
  -v "$PWD/scripts:/smoke:ro" tastedistrict /smoke/live_smoke.py
# Continue only if the live check passes:
docker compose up -d --force-recreate
curl --fail http://192.168.0.15:8000/api/config
```

The smoke uses the updated environment in a temporary container without publishing another port. It makes bounded real Qloo calls and emits summaries only. If it fails, the currently running service keeps its old environment; resolve the key/schema/coverage problem before recreating it. Configured live mode alone is not evidence of successful authentication.

**`docker restart` / `docker compose restart` does not reload changed environment variables.** Recreate the service with `docker compose up -d --force-recreate`. An environment-only edit needs no image rebuild. See [Docker's restart documentation](https://docs.docker.com/reference/cli/docker/compose/restart/) and [up documentation](https://docs.docker.com/reference/cli/docker/compose/up/). Never print `docker compose config` without `--quiet`, because it can expose resolved secrets.

### Update application source

Review the exact passing revision, preserve the private `.env`, then update this checkout from `main` and run:

```sh
docker compose config --quiet
docker compose build
docker compose up -d --force-recreate
docker compose ps
curl --fail http://192.168.0.15:8000/health
```

Retain the previous reviewed image for rollback and record the new image/revision in `VERIFICATION.md`. Recheck `/api/config`, data labels and a complete browser selection/recommendation flow. The health check verifies the process, not Qloo coverage. A plain restart is suitable only when intentionally keeping the same image/environment.

The server `.env` has mode `600` and a generated persistent `APP_SECRET`; its value was not exposed. Keep `DATA_MODE=demo`, `LLM_PROVIDER=none`, and no Qloo key until an event credential is available and its terms and live schema are checked. Binding specifically to the LAN address limits the published interface. No router, DNS, TLS or public ingress change is part of this LAN deployment.

## External one-service deployment

The service is stateless FastAPI with static assets served by the same process. Use the repository Dockerfile, one worker and `/health` as the health check. The host may inject `PORT`; default is 8000. `/health` only verifies the application process, not Qloo key validity or city coverage.

Render supports this shape of service. Its free service sleeps after 15 idle minutes and can need about a minute to wake; workspace instance-hour and other limits apply. That makes availability during judging uncertain. A non-sleeping paid service is an option only after checking the current account price and obtaining cost approval. Verified source links and judging dates are in [SUBMISSION.md](SUBMISSION.md).

## External steps after approval

1. Review the exact revision and dependency notices; deploy that revision from the public repository or its Docker image.
2. Set `DATA_MODE=demo` for an explicitly synthetic preview, or `DATA_MODE=live` with the assigned private `QLOO_API_KEY` after inspecting its terms. Never claim a synthetic preview is the final live submission.
3. Set a persistent random `APP_SECRET` of at least 32 characters. Keep one worker because rate counters, sessions and request budgets are process-local. TLS is required for external hosting. Secure cookies derive from the request scheme: configure forwarded headers only for the host's trusted proxy addresses.
4. Check the credential quota and configure `QLOO_GLOBAL_REQUEST_LIMIT`, `QLOO_SCENARIO_REQUEST_LIMIT` (maximum 10), `QLOO_TIMEOUT_SECONDS`, and `RATE_LIMIT_PER_MINUTE`. Set provider-level quota/spending controls too: an in-process limit resets on restart and is not a monthly spending cap.
5. Disable access query logging in both Uvicorn (`--no-access-log`, already in Docker) and the provider/proxy where configurable. Do not attach raw Qloo bodies or search selections to error reporting.
6. Run `scripts/live_smoke.py` privately against the deployment's credential and check the external UI in a fresh mobile/desktop browser. Confirm several unique venues in three zones, actual city scope, change-one-interest behavior, exclusion, 401/429/timeout states, and quota exhaustion. If coverage is weak, present only the limited place list and revise scope.
7. Keep the host and event credential available through judging, and preserve a rollback revision. Do not submit until the checklist is complete.

No files need persistent storage. The application does not expose `.env`, source files or debug documentation routes. Health and static routes do not call Qloo.
