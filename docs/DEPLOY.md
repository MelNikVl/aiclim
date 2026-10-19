# Deployment procedure

## LAN demo on the existing server

The application is deployed on the user's existing server at **http://192.168.0.15:8000**. Its isolated checkout is `/home/nik/tastedistrict`, and its container is `tastedistrict`. On 2026-10-19, revision `12ad190c632b19c39605d04ee426238e841663c9` was built as `tastedistrict:12ad190` and verified from a browser on the Windows workstation. See [VERIFICATION.md](VERIFICATION.md) for the evidence and limits.

This deployment uses **Demo data**: fictional venues and synthetic affinities. No Qloo credential is configured. It is available only to clients that can reach the LAN server; it is not an externally published contest demo. External publication, new accounts, paid resources and repository visibility changes still need the user's separate approval.

Connect and inspect only this application:

```sh
ssh nik@192.168.0.15
cd /home/nik/tastedistrict
docker ps --filter 'name=^/tastedistrict$'
docker logs --tail 100 tastedistrict
```

Restart the existing application with `docker restart tastedistrict`. This resets its in-memory sessions and request counters. Check `curl --fail http://192.168.0.15:8000/health` and the browser afterward. Do not restart or prune the Docker host or operate on unrelated containers.

For an update, review the changes on `codex/tastedistrict-mvp` and select its exact commit before transferring or checking out source in this directory. Preserve the private server `.env`; do not print or copy its values into Git or chat. Build a new image tagged with the reviewed commit, retain the previous image for rollback, and replace only the `tastedistrict` container. Keep the same environment file, single worker and host binding `192.168.0.15:8000:8000`. Retain the current runtime restrictions: `--restart unless-stopped --read-only --tmpfs /tmp:rw,noexec,nosuid,size=16m --cap-drop ALL --security-opt no-new-privileges --cpus 1 --memory 256m --init`. Recheck health, `/api/config`, visible Demo labels and a complete selection/recommendation flow. A successful build alone does not verify the UI.

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
