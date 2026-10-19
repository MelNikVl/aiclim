# Verification record

Development checks on **2026-10-19**, Python 3.11 on Windows. All test data and mocked upstream responses are authored synthetic fixtures. No authenticated Qloo response has been saved or committed.

## Verified locally

- `python -m pytest -q`: **61 passed**. One Starlette TestClient deprecation warning recommends an eventual test-client transport update; it did not fail any test.
- Workflow checks cover query-dependent synthetic candidates, changed interest, exclusions, sparse/empty output, duplicate IDs/coordinates, invalid coordinates, approximate city guard and density-neutral ranking.
- HTTP checks cover exact selection tokens, signature/expiry/session binding, duplicate resolved interests, invalid city/input, ambiguous titles, literal injection text, body/origin guards, per-IP rate limits and global/scenario limits.
- Adapter checks use HTTPX MockTransport for documented request parameters and credentials, 401/403, 429/5xx retry bounds, timeouts, malformed/oversized JSON, schema rejection, current entity subtype validation and missing coordinates. Public errors do not echo a test credential or raw provider messages.
- `python scripts/evaluate.py`: **12/12 synthetic functional scenarios pass**; zero external calls. Correctness assertions cover distinct IDs, exclusions, visible data labels and limits. The run includes change-one-interest, Dune book/film identity, sparse coverage and empty results. Measured sub-millisecond workflow timings are fixture-only timings; they say nothing about network latency or live API quality.
- `node --check app/static/app.js`, Python compilation and `pip check` pass. Editable package installation succeeds.
- Browser at `http://127.0.0.1:8000`: select Nina Simone, Amélie and The Little Prince → three zones and 11 synthetic places. Replacing Nina Simone with Radiohead adds five places and removes five, with a changed zone order. Excluding Tiny Orbit Cinema removes it and refreshes results. No browser console errors were observed.
- Mobile viewport **390 × 844**: the complete selection/discovery flow works, cards stack in one column, the Demo data badge remains visible, and measured document content width equals viewport content width (no horizontal overflow).

Local browser screenshots are in ignored `artifacts/desktop.jpg` and `artifacts/mobile.jpg`; they show synthetic data only. They are review artifacts, not Qloo response fixtures.

## Not verified / blockers

| Check | Status and concrete reason |
| --- | --- |
| Live Qloo smoke | **Not run**: no event key was configured. The smoke script refuses Demo mode. |
| Real New York / three-zone coverage | **Unverified**: requires authenticated responses and independent location/existence checks. |
| Qloo-versus-LLM-only evaluation | **Not run**: no credential or approved LLM provider. See `eval/PLAN.md`; no winner is claimed. |
| Docker build/run | **Blocked locally**: Docker CLI 28.2.2 is installed, but the Linux Engine pipe is unavailable. Starting Docker Desktop did not establish a working daemon. `docker build` failed before executing the Dockerfile. |
| External URL and judging availability | **Not published**: requires the user's separate publication/provider approval. |
| AI coding policy / credential-specific terms | **Unresolved**: sources are recorded in `docs/SOURCES.md`. |

GitHub Actions is prepared to repeat tests, the synthetic scenarios, JavaScript validation, Docker build and a container health/config smoke. This is a configured check, **not evidence that remote CI or Docker has already passed**.

The authored city guard and zones are approximate comparison geometry. A place passing them does not establish independently verified municipal membership, opening status or suitability. The application does not make those claims.
