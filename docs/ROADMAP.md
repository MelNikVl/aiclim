# Next improvements

Priority after the 2026-10-19 synthetic MVP and LAN deployment:

1. **Prove live Qloo coverage.** Obtain the assigned event key, validate the real schema and test several taste profiles, exclusions and changes. Independently verify venues and city membership. Keep place-list scope if three useful zones are unsupported.
2. **Make the central comparison more informative.** Store bounded previous-result snapshots and show concrete rank/score changes alongside entered/removed places and the favorite the user replaced. Do not invent per-interest causal attribution from a combined Qloo query.
3. **Spend fewer searches per scenario.** Replace the short typing debounce with a deliberate search trigger, expose the remaining allowance and reserve requests for recommendations. Add persistent/operator quota controls before serving many users.
4. **Execute the evaluation protocol.** Turn `eval/PLAN.md` into measured Qloo-versus-LLM-only runs with equal constraints, independent venue checks and explicit missing outcomes. Human preference still requires human evaluation; app scores are not quality evidence.
5. **Provide judge access.** After the user approves publication, configure an external HTTPS URL and verify availability through judging. The LAN demo does not meet this requirement.

Current fixes improve operations and honesty: Compose-based environment recreation, recoverable expansion errors keep valid partial results, and the interface distinguishes configured live mode from a successful live result. These fixes do not close the live-integration and evaluation gaps above.
