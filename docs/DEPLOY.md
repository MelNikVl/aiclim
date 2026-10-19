# Deployment procedure

Publication, account creation, paid resources and repository visibility changes require the user's separate approval. This document prepares the concrete deployment; it does not publish anything.

## One-service deployment

The service is stateless FastAPI with static assets served by the same process. Use the repository Dockerfile, one worker and `/health` as the health check. The host may inject `PORT`; default is 8000. `/health` only verifies the application process, not Qloo key validity or city coverage.

Render supports this shape of service. Its free service sleeps after 15 idle minutes and can need about a minute to wake; workspace instance-hour and other limits apply. That makes availability during judging uncertain. A non-sleeping paid service is an option only after checking the current account price and obtaining cost approval. Verified source links and judging dates are in [SUBMISSION.md](SUBMISSION.md).

## Steps after approval

1. Review the exact revision and dependency notices; deploy that revision from the public repository or its Docker image.
2. Set `DATA_MODE=demo` for an explicitly synthetic preview, or `DATA_MODE=live` with the assigned private `QLOO_API_KEY` after inspecting its terms. Never claim a synthetic preview is the final live submission.
3. Set a persistent random `APP_SECRET` of at least 32 characters. Keep one worker because rate counters, sessions and request budgets are process-local. TLS is required for external hosting. Secure cookies derive from the request scheme: configure forwarded headers only for the host's trusted proxy addresses.
4. Check the credential quota and configure `QLOO_GLOBAL_REQUEST_LIMIT`, `QLOO_SCENARIO_REQUEST_LIMIT` (maximum 10), `QLOO_TIMEOUT_SECONDS`, and `RATE_LIMIT_PER_MINUTE`. Set provider-level quota/spending controls too: an in-process limit resets on restart and is not a monthly spending cap.
5. Disable access query logging in both Uvicorn (`--no-access-log`, already in Docker) and the provider/proxy where configurable. Do not attach raw Qloo bodies or search selections to error reporting.
6. Run `scripts/live_smoke.py` privately against the deployment's credential and check the external UI in a fresh mobile/desktop browser. Confirm several unique venues in three zones, actual city scope, change-one-interest behavior, exclusion, 401/429/timeout states, and quota exhaustion. If coverage is weak, present only the limited place list and revise scope.
7. Keep the host and event credential available through judging, and preserve a rollback revision. Do not submit until the checklist is complete.

No files need persistent storage. The application does not expose `.env`, source files or debug documentation routes. Health and static routes do not call Qloo.
