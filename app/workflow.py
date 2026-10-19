"""Bounded recommendation workflow with inspectable actions and sourced evidence."""

from uuid import uuid4

from app.data import CITY
from app.models import (
    Changes, Coverage, Entity, RecommendRequest, RecommendResponse, Usage, WorkflowStep,
)
from app.ranking import city_wide_picks, eligible_places, rank_zones, zone_for


async def run_workflow(entities: list[Entity], request: RecommendRequest, adapter, budget) -> RecommendResponse:
    steps = [
        WorkflowStep(step="Parse request", status="completed", detail=f"Validated {len(entities)} interests and requested New York city scope."),
        WorkflowStep(step="Resolve entities", status="completed", detail=f"Resolved {len(entities)} previously selected cultural entities using signed search selections."),
    ]
    excluded = set(request.excluded_place_ids)
    candidates = await adapter.recommend(entities, CITY, excluded, budget, expand=False)
    steps.append(WorkflowStep(
        step="Find candidates", status="completed",
        detail=f"Received {len(candidates)} candidate places from {'synthetic Demo data' if adapter.mode == 'demo' else 'Qloo'}.",
    ))
    eligible = eligible_places(candidates, excluded)
    initial_eligible = len(eligible)
    def coverage(places):
        counts = {}
        for place in places:
            zone = zone_for(place)
            if zone:
                counts[zone.id] = counts.get(zone.id, 0) + 1
        return len(counts), sum(count >= 2 for count in counts.values())

    zone_count, supported_zone_count = coverage(eligible)
    warnings = [
        "Exploration zones are authored comparison areas, not official neighborhood boundaries.",
        "Scores are application rankings, not probabilities of compatibility.",
        "Location checks use an approximate coordinate guard and, in live mode, Qloo's city query filter. Municipal membership is not independently verified.",
    ]
    if adapter.mode == "demo":
        warnings.insert(0, "Demo data: all venues, coordinates and affinities are synthetic. This is not a live Qloo result.")
    if len(eligible) < 6 or zone_count < 3 or supported_zone_count < 2:
        if getattr(budget, "used", 0) < getattr(budget, "max_requests", 10):
            additional = await adapter.recommend(entities, CITY, excluded, budget, expand=True)
            candidates.extend(additional)
            eligible = eligible_places(candidates, excluded)
            steps.append(WorkflowStep(
                step="Expand search", status="completed",
                detail=f"Made one broader candidate request after finding {initial_eligible} eligible places across {zone_count} zones. Received {len(additional)} additional candidates.",
            ))
        else:
            steps.append(WorkflowStep(step="Expand search", status="limited", detail="The request budget was exhausted; no additional request was made."))
    else:
        steps.append(WorkflowStep(step="Expand search", status="skipped", detail="At least six eligible places cover all three exploration zones."))
    steps.append(WorkflowStep(
        step="Validate candidates", status="completed",
        detail=f"Kept {len(eligible)} unique places after finite-coordinate, approximate city guard, exclusion and duplicate checks. Assigned authored zones where coordinates fit; municipal membership was not independently verified.",
    ))
    zone_count, supported_zone_count = coverage(eligible)
    use_city_list = supported_zone_count < 2
    zones = city_wide_picks(eligible, adapter.mode) if use_city_list else rank_zones(eligible, adapter.mode)
    if zone_count < 3 or len(eligible) < 6 or supported_zone_count < 3:
        warnings.append("Coverage is limited: fewer than three zones have at least two unique places, or fewer than six eligible places are available. Treat these as place suggestions; a reliable three-zone comparison is unavailable.")
    if use_city_list and eligible:
        warnings.append("City-wide picks are shown because fewer than two exploration zones have at least two unique places. This place list is not a district ranking.")
    if not use_city_list and any(len(zone.places) < 2 for zone in zones):
        warnings.append("At least one zone has fewer than two unique places; its ranking has limited support.")
    if not zones:
        warnings.append("No eligible places were found. Change an interest or remove an exclusion and try again.")
    steps.extend([
        WorkflowStep(step="Rank zones", status="limited" if use_city_list else "completed", detail="Used a city-wide place list because fewer than two zones have two unique eligible places." if use_city_list else "Ranked each zone by its best three place scores, averaging scores so venue count alone cannot win."),
        WorkflowStep(step="Explain results", status="completed", detail="Used source evidence and fixed templates; no LLM calls or inferred venue attributes."),
    ])
    current_ids = [place.id for zone in zones for place in zone.places]
    previous = set(request.previous_place_ids)
    current = set(current_ids)
    added = [place_id for place_id in current_ids if place_id not in previous]
    removed = [place_id for place_id in request.previous_place_ids if place_id not in current]
    previous_zones = request.previous_zone_ids
    new_zone_order = [zone.id for zone in zones]
    if not previous and not previous_zones:
        message = f"Found {len(current_ids)} city-wide place suggestions; a reliable zone comparison is unavailable." if use_city_list else f"Found {len(current_ids)} places across {len(zones)} exploration zones. Change one interest to compare results."
    elif not added and not removed:
        message = "The same places remain; application scores and order may change with your interests."
    else:
        message = f"{len(added)} places added and {len(removed)} removed after your change."
    if previous_zones and previous_zones != new_zone_order:
        message += " Zone order or coverage also changed."
    return RecommendResponse(
        mode=adapter.mode, city=CITY, zones=zones, workflow=steps, warnings=warnings,
        changes=Changes(added_places=added, removed_places=removed, message=message),
        usage=Usage(qloo_requests=budget.used, llm_calls=0),
        coverage=Coverage(eligible_places=len(eligible), zone_count=0 if use_city_list else len(zones)),
        request_id=str(uuid4()),
    )
