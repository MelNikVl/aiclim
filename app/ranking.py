"""Coordinate validation, deduplication, and density-neutral zone ranking."""

from math import isfinite

from app.data import CITY_BOUNDS, ZONES
from app.models import Place, PlaceResult, ZoneResult


def zone_for(place: Place):
    return next((zone for zone in ZONES if zone.contains(place.latitude, place.longitude)), None)


def eligible_places(candidates: list[Place], excluded: set[str]) -> list[Place]:
    """Keep unique finite candidates inside the approximate city coordinate guard.

    This bounding box does not independently verify municipal membership.
    Unzoned candidates remain available for the limited-coverage place list.
    """
    south, west, north, east = CITY_BOUNDS
    valid = [
        place for place in candidates
        if place.id not in excluded
        and all(isfinite(value) for value in (place.latitude, place.longitude, place.score))
        and south <= place.latitude <= north and west <= place.longitude <= east
    ]
    seen_ids: set[str] = set()
    seen_coordinates: set[tuple[float, float]] = set()
    result = []
    for place in sorted(valid, key=lambda item: (-item.score, item.id)):
        # Six decimals group identical pins while preserving distinct nearby venues.
        coordinate = (round(place.latitude, 6), round(place.longitude, 6))
        if place.id in seen_ids or coordinate in seen_coordinates:
            continue
        seen_ids.add(place.id)
        seen_coordinates.add(coordinate)
        result.append(place)
    return result


def application_score(source_score: float) -> float:
    return round(max(0.0, min(1.0, source_score)) * 100, 1)


def rank_zones(places: list[Place], mode: str) -> list[ZoneResult]:
    results = []
    for zone in ZONES:
        members = sorted(
            (place for place in places if zone.contains(place.latitude, place.longitude)),
            key=lambda place: (-place.score, place.id),
        )
        if not members:
            continue
        top = members[:3]
        zone_score = round(sum(application_score(place.score) for place in top) / len(top), 1)
        source = "synthetic affinity fixtures" if mode == "demo" else "Qloo candidate order"
        explanation = (
            f"Application ranking {zone_score:.1f}/100: the mean of the best {len(top)} "
            f"place scores from {source}. More venues alone do not increase this score."
        )
        results.append(ZoneResult(
            id=zone.id, name=zone.name, description=zone.description, score=zone_score,
            explanation=explanation,
            places=[PlaceResult(**{**place.model_dump(), "score": application_score(place.score)}) for place in members[:4]],
        ))
    return sorted(results, key=lambda zone: (-zone.score, zone.id))[:3]


def city_wide_picks(places: list[Place], mode: str) -> list[ZoneResult]:
    """A limited-coverage place list; deliberately not a neighborhood comparison."""
    if not places:
        return []
    members = sorted(places, key=lambda place: (-place.score, place.id))[:6]
    top = members[:3]
    score = round(sum(application_score(place.score) for place in top) / len(top), 1)
    return [ZoneResult(
        id="city-wide-picks", name="City-wide picks (limited coverage)",
        description="A place list inside an approximate New York coordinate guard. Municipal membership has not been independently verified. This group is not a district or neighborhood.",
        score=score,
        explanation=f"No reliable zone comparison is available. Application ranking {score:.1f}/100 is the mean of the best {len(top)} place scores in this list.",
        places=[PlaceResult(**{**place.model_dump(), "score": application_score(place.score)}) for place in members],
    )]
