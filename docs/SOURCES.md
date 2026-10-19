# Sources and integration boundaries

Checked on **2026-10-19**. This records documentation review, not a successful authenticated API test. No live Qloo response data belongs in this repository.

## Qloo API contract

The [event developer guide](https://docs.qloo.com/reference/qloo-llm-hackathon-developer-guide), updated 2026-10-07, specifies `https://hackathon.api.qloo.com` for event credentials. Production and staging hosts reject those keys. Authenticate with the server-side `X-Api-Key` header. Use GET requests with query parameters. `/recommendations` and `/recs` are unsupported. All documented API endpoints are available for the event; the guide explicitly demonstrates direct REST requests.

| Purpose | Documented request |
| --- | --- |
| Resolve favorites | `GET /search?query=<name>&types=urn:entity:artist&take=8` |
| Retrieve places | `GET /v2/insights?filter.type=urn:entity:place&signal.interests.entities=<resolved IDs>&filter.location.query=New York City&filter.location.radius=0&take=50` |
| Exclude rejected places | Add `filter.exclude.entities=<IDs>` to Insights |
| Request supporting explanation metadata | Add `feature.explainability=true` to Insights |

The [current Search reference](https://docs.qloo.com/reference/get-search) defines `types` as a comma-separated array. The MVP uses artist, movie, book and place types, each prefixed `urn:entity:`. Search returns `success`, a `results` array, and `duration`. Search location pairs use `latitude,longitude`; its `filter.radius` is in miles.

The [Insights reference](https://docs.qloo.com/reference/insights-api-deep-dive) defines `results.entities`, requires `filter.type`, and supports comma-separated `signal.interests.entities` and `filter.exclude.entities`. `take` is 1–50. `filter.location.query` fuzzy-matches a named locality; a failed match produces 400. `filter.location.radius=0` disables boundary padding. A WKT `filter.location` uses longitude first, such as `POINT(<longitude> <latitude>)`. Insights radius values are meters. The [entity type guide](https://docs.qloo.com/reference/available-parameters-by-entity-type) limits location filters to relevant geographic types. Never substitute a location signal for a geographic constraint.

The [Schema & Taxonomy reference](https://docs.qloo.com/reference/schema-taxonomy) documents place identifiers as UUID `entity_id`, `type=urn:entity`, `subtype=urn:entity:place`, and `name`. Its canonical example has nullable root-level `lat`, `lon`, `address`, `city`, `country_code`, and root-level `is_closed`, `affinity`, `popularity`, `tags`, `disambiguation`. The [recommendation guide](https://docs.qloo.com/reference/basic-insights-use-case) also shows nested `properties` metadata. The current endpoint schema leaves entity item details incomplete, and Search contains unresolved schema includes. Therefore metadata shape must be confirmed with the assigned credential; undocumented fields must not be assumed present. Missing or invalid coordinates must exclude a place from zone comparisons.

`feature.explainability` documents per-result `query.explainability` influence scores from 0 to 1 and a possible warning when unavailable. Its complete object layout is not specified, so this project must not invent per-seed causal explanations. The [affinity interpretation guide](https://docs.qloo.com/docs/interpreting-affinity-scores) says scores are normalized per query. Use Qloo order within a request; an application score must be labeled as such. Neither score establishes a person's compatibility probability.

Documentation caveat: [qloo/docs-public](https://github.com/qloo/docs-public) is an official mirror, but its current `openapi-schema.json` is the generic OpenAPI document schema rather than a complete Qloo endpoint specification. Current docs.qloo.com endpoint schemas were inspected from their public page payload instead. Mirror examples may be older than the live reference.

## Data use, credentials and licensing

The [event guide FAQ](https://docs.qloo.com/reference/qloo-llm-hackathon-developer-guide#faqs) permits private server caching without a fixed retention limit and prohibits placing response data in a public repository. Numeric quotas are not published there; event keys last through judging. Confirm the actual quota and expiration supplied with the credential. Our implementation should keep raw responses transient, use synthetic fixtures, bound request/retry counts, and never disguise failed live requests as real results.

The [kit access policy](https://github.com/qloo/qloo-hackathon-kit/blob/main/docs/API_ACCESS.md) requires attributable event credentials, bounded retries and minimal calls. The [safe-use policy](https://github.com/qloo/qloo-hackathon-kit/blob/main/docs/SAFE_USE.md) distinguishes aggregate cultural affinity from personal traits or housing eligibility. TasteDistrict is a cultural exploration tool. It must not advise on housing eligibility, neighborhood safety, rents, health, demographics, or other unsupported characteristics.

[Qloo terms](https://www.qloo.com/legal/terms) retain Qloo ownership of its output and refer to additional API-specific terms supplied to customers. [Qloo privacy terms](https://www.qloo.com/legal/privacy) reject PII in API input and describe learning from anonymized entity arrays. Send selected cultural entities and the chosen city; never send identity fields, location histories, keys in prompts, or user accounts. A no-registration interface does not imply zero upstream retention. The event credential's additional terms have not been inspected; commercial reuse and redistribution rights remain unverified. The project MIT license covers authored code and fixtures, not Qloo data, trademarks, or images.

The event requires a functioning public Qloo-powered demonstration, so displaying the minimal recommendation fields in the product flow is an intended use inferred from those requirements. That is not a blanket license to redistribute Qloo datasets. Serve only the fields needed for the interaction, label their source, and avoid public raw-response downloads, fixture exports or bulk query features. Check any credential-specific display or attribution conditions before external launch.

Direct dependency metadata was checked against version-specific PyPI records: [FastAPI 0.135.1](https://pypi.org/pypi/fastapi/0.135.1/json), [HTTPX 0.28.1](https://pypi.org/pypi/httpx/0.28.1/json), [pydantic-settings 2.13.1](https://pypi.org/pypi/pydantic-settings/2.13.1/json), [Uvicorn 0.41.0](https://pypi.org/pypi/uvicorn/0.41.0/json), [pytest 9.0.2](https://pypi.org/pypi/pytest/9.0.2/json), [pytest-asyncio 1.3.0](https://pypi.org/pypi/pytest-asyncio/1.3.0/json). They declare MIT, BSD-3-Clause, or Apache-2.0 licenses. These allow integration with MIT-authored application code when their notices and other license obligations are preserved. A release must also inventory resolved transitive packages and retain their license texts; the direct dependency review alone is not a complete distribution audit.

The local installed direct/transitive inventory is now recorded in [DEPENDENCIES.md](DEPENDENCIES.md), including certifi's MPL-2.0 exception to an all-permissive description. Docker build and startup succeeded in GitHub Actions and on the designated LAN server. A complete container component/license inventory remains pending; successful execution does not establish that audit.

## Authored zone and fixture provenance

`app/data.py` contains hand-drawn comparison rectangles created for this MVP:

| Authored exploration zone | South, west, north, east |
| --- | --- |
| Downtown Side Streets | `40.700, -74.020, 40.735, -73.974` |
| Midtown Culture Loop | `40.740, -74.002, 40.774, -73.960` |
| Uptown Riverside Mix | `40.778, -73.978, 40.820, -73.926` |

These are original comparison geometry, not official neighborhoods or a licensed municipal boundary dataset. The broader city coordinate guard is also authored and does not prove municipal membership. Gaps and excluded areas are intentional. Zone names do not assert neighborhood identities. All demo venues, coordinates and affinity values are synthetic examples, not evidence of real Qloo coverage. Cultural work names identify the user's possible interests; no third-party artwork or catalog was copied. No external map tiles or administrative geodata are bundled.

## Open issues before a live release

- Obtain an event key through the user's authorized account and inspect its extra terms and limits.
- Verify the response shapes and meaningful New York coverage; require enough unique valid places per comparison zone, otherwise return a city place list or investigate another city.
- Complete and record the 12-scenario Qloo-versus-LLM-only evaluation with measured results and human review where relevant.
- Confirm the organizer's policy on AI coding assistance; do not claim explicit permission from silence.
- Verify external deployment, live quota controls, and the final image's dependency license inventory. Synthetic mobile/browser flows and Docker execution in GitHub Actions are recorded in [VERIFICATION.md](VERIFICATION.md).
