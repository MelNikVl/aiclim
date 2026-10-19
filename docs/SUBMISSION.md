# Submission and deployment checklist

Status on **2026-10-19**: a synthetic local MVP is preparation work. A verified public demo with the real Qloo integration is still required before submission readiness can be claimed.

The [official event rules](https://qloo.devpost.com/rules) set the deadline at **2026-10-30 23:45 America/New_York**, equivalent to **2026-10-31 08:45 Asia/Qyzylorda (UTC+5)**. Judging ends **2026-11-16 23:45 America/New_York**, equivalent to **2026-11-17 09:45 UTC+5** after the US daylight-saving transition. Winners are expected around November 23. Recheck the rules before entry.

## Entry requirements

- [ ] Confirm adult eligibility, residence restrictions, team representation and conflicts directly with the rules; Kazakhstan is not among the explicitly named exclusions, which does not by itself establish individual eligibility.
- [ ] Supply an externally published working demo, a public repository with source and setup instructions, a detectable open-source license, and an English project description. A video is optional. See the [overview requirements](https://qloo.devpost.com/#requirements).
- [ ] Keep judge access free and available until judging ends.
- [ ] Describe the meaningful Qloo-based agent workflow and the work completed during the event; preserve third-party rights.

AI assistance remains an unresolved organizer-policy question. The rules state: “An Entrant may contract with a third party for technical assistance to create the Submission”. They also require original work and ownership. No explicit permission or ban for AI coding was found. Disclose assistance and obtain an organizer clarification before claiming approval. No account registration, agreement acceptance or submission has been performed by this project setup.

## Evidence to attach

- [ ] Record a successful live favorite search with disambiguation, a place recommendation, a changed interest and an excluded place. Preserve a redacted action summary, not raw Qloo responses in Git.
- [ ] Record coordinate and city checks, deduplication, missing-data fallback, request counts, failures and latency. Distinguish documentation review, synthetic tests, and authenticated live evidence.
- [ ] Demonstrate at least three useful zones with several unique supported places each; otherwise state that the product currently recommends city places.
- [ ] Run the 12 evaluation cases with equal constraints for Qloo and LLM-only. Record failures and cost without invented comparisons or application-score quality claims.
- [ ] Record automated test results, mobile browser checks, Docker build/run, secret scan and transitive dependency notices.

The [official starter submission guide](https://github.com/qloo/qloo-hackathon-kit/blob/main/docs/SUBMISSION.md) also recommends a concise problem statement, a redacted request-to-result explanation, the workflow used, reproducible setup, and known limits.

## Hosting choice to approve

A single Render web service can run the FastAPI/Docker application. A static-only deployment cannot protect the Qloo credential while making live requests. Use a server environment secret and ensure redirects, errors and logs do not reveal it.

[Render's free-service documentation](https://render.com/docs/free) currently states that services sleep after 15 idle minutes and typically need about one minute to wake. A workspace receives 750 free instance-hours monthly; exhaustion suspends free services. Files are ephemeral, free services can restart, and outbound/build limits also apply. These constraints can disrupt judging. Free Render is suitable for an initial preview, but a paid compute plan is a stronger availability option if the user approves its current price and billing limits. The [pricing page](https://render.com/pricing) should be checked in the account before approval; no fixed paid price is asserted here because its compute table was not available in the retrieved page.

- [ ] User approves provider, account actions, any cost, publication and any repository visibility change.
- [ ] Inspect current plan limits, set spending controls, configure only required server secrets, and deploy the reviewed revision.
- [ ] Verify the external URL in a fresh browser on mobile and desktop, including live API behavior and quota exhaustion errors.
- [ ] Keep the selected service and event credential available through the judging end time above; maintain a deployable rollback revision.
- [ ] Have the human entrant submit only after the remaining checks pass.

See [SOURCES.md](SOURCES.md) for API evidence, data restrictions, license boundaries and remaining unknowns.
