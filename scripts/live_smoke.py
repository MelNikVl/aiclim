"""Private, bounded live check. Prints aggregate validation only, never Qloo bodies."""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.config import Settings
from app.models import RecommendRequest
from app.qloo import QlooAdapter
from app.security import AppError, Budget, GlobalBudget
from app.workflow import run_workflow


async def main():
    settings = Settings()
    if settings.data_mode != "live":
        print("NOT RUN: set DATA_MODE=live and a private server-side event credential first.")
        return 2
    adapter = QlooAdapter(settings)
    budget = Budget(GlobalBudget(settings.qloo_global_request_limit), settings.qloo_scenario_request_limit)
    try:
        selected = []
        for query, category in [("Radiohead", "artist"), ("Spirited Away", "movie"), ("Beloved", "book")]:
            matches = await adapter.search(query, category, budget)
            exact = [item for item in matches if item.name.casefold() == query.casefold()]
            if len(exact) != 1:
                print("INCOMPLETE: a seed is absent or ambiguous. Resolve it manually in the UI; no automatic first-match guess was made.")
                return 1
            selected.append(exact[0])
        request = RecommendRequest(interest_tokens=["smoke-1", "smoke-2", "smoke-3"])
        result = await run_workflow(selected, request, adapter, budget)
        print(f"LIVE RESPONSE VALIDATED: {result.coverage.eligible_places} eligible candidates; {len(result.zones)} result groups; {budget.used} upstream attempts.")
        full = len(result.zones) == 3 and all(len(zone.places) >= 3 for zone in result.zones)
        print("THREE-ZONE COVERAGE: " + ("supported in this query; independently verify city/venues next." if full else "not established. Keep the limited place-list scope or investigate another city."))
        print("Still required: changed-interest/exclusion smoke, independent place verification and external deployment check.")
        return 0 if full else 1
    except AppError as exc:
        print(f"LIVE CHECK FAILED [{exc.code}]: {exc.message}")
        return 1
    finally:
        await adapter.close()


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
