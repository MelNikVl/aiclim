# Evaluation protocol

`scenarios.json` contains 12 authored cultural-taste scenarios. `scripts/evaluate.py` executes them against synthetic fixtures, measuring functional consistency and elapsed time. These measurements are not evidence of real venues, Qloo quality or user preference.

## Required real comparison (not run)

Use the same 12 scenarios, city, 3–5 resolved favorites, exclusions, maximum 12 displayed places and a fixed maximum time per scenario for both arms. Record the exact model/provider/version/prompt and Qloo API mode, quotas, timestamps and any manual disambiguation. Keep prompts and raw provider responses private when they contain provider data; publish only authorized redacted summaries.

**Qloo arm:** selected favorites → Qloo entity resolution → bounded candidate requests → coordinate/exclusion/deduplication checks → authored-zone/place fallback → evidence templates. Record search plus retry counts, failures, actual latency and provider-reported usage/cost. Never use application score as evidence of quality.

**LLM-only arm:** identical cultural inputs and city constraints, with no Qloo hints/results in the prompt. Maximum two model calls, no extra retrieval during generation, same displayed-place and time limits. Do not connect a paid provider without approval. The current build has no enabled LLM provider, so this arm is explicitly `not_run`.

Evaluate outputs independently of their generation source. For each proposed place, verify existence, current city and coordinates against an allowed independent place source or manual check; log the source and date, and mark unverifiable entries as unknown, not passes. Use the same verification process for both arms. Exact source selection and its licensing are still pending.

Record:

| Measure | Definition |
| --- | --- |
| Existence | Independently confirmed / not found / unknown; do not infer from a model claim |
| City | Independently checked within chosen city, not just a broad coordinate rectangle |
| Constraints | Requested categories, exclusions, distinct places and supported evidence |
| Failures | API errors, invalid JSON, unresolved names, insufficient coverage, timeouts |
| Latency | End-to-end wall time including resolution, retries and model calls |
| Cost | Actual billed or documented usage; unknown if the provider does not report it |
| Human preference | Blinded, randomized side-by-side evaluation with informed participants; absent until run |

Report denominators, missing outcomes and uncertainty. Do not announce a winner using synthetic outputs, self-assigned scores, unverified places or a single handpicked query. Functional tests of ambiguous names, wrong city, empty output, 401/429, timeouts, malformed JSON, injection, limits and secret protection are separate from this product evaluation.
