"""Measure synthetic functional behavior only. Never calls Qloo or an LLM."""
import asyncio
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.data import DEMO_ENTITIES, DemoAdapter
from app.models import RecommendRequest
from app.security import Budget, GlobalBudget
from app.workflow import run_workflow


async def main():
    scenarios = json.loads((Path(__file__).resolve().parents[1] / "eval/scenarios.json").read_text())
    entities = {item.id: item for item in DEMO_ENTITIES}
    results, rows = {}, []
    for case in scenarios:
        previous = results.get(case.get("compare_to"))
        request = RecommendRequest(
            interest_tokens=case["interests"], excluded_place_ids=case.get("exclude", []),
            previous_place_ids=[p.id for z in previous.zones for p in z.places] if previous else [],
            previous_zone_ids=[z.id for z in previous.zones] if previous else [],
        )
        started = time.perf_counter()
        result = await run_workflow([entities[item] for item in case["interests"]], request, DemoAdapter(), Budget(GlobalBudget(1)))
        elapsed = (time.perf_counter() - started) * 1000
        places = [p for z in result.zones for p in z.places]
        ids = [p.id for p in places]
        checks = {
            "unique_ids": len(ids) == len(set(ids)),
            "exclusions_respected": not set(ids).intersection(case.get("exclude", [])),
            "demo_marked": result.mode == "demo" and any("Demo data" in w for w in result.warnings),
            "zero_external_calls": result.usage.qloo_requests == 0 and result.usage.llm_calls == 0,
            "max_12_places": len(places) <= 12,
        }
        if case["id"] == "11-empty-results":
            checks["empty_honest"] = not places and bool(result.warnings)
        if previous:
            checks["change_visible"] = bool(result.changes.added_places or result.changes.removed_places) or any(
                result.zones[i].score != previous.zones[i].score
                for i in range(min(len(result.zones), len(previous.zones)))
            )
        results[case["id"]] = result
        rows.append({"scenario": case["id"], "places": len(places), "groups": len(result.zones), "latency_ms": round(elapsed, 3), "checks": checks})
    print(json.dumps({"mode": "synthetic_functional_only", "real_world_existence": "not_verified", "live_qloo": "not_run_no_credential", "llm_only": "not_run_no_provider", "passed": all(all(r["checks"].values()) for r in rows), "scenarios": rows}, indent=2))
    return 0 if all(all(r["checks"].values()) for r in rows) else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
