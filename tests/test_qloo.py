"""Synthetic MockTransport responses exercise verified current Qloo JSON shapes.

These fixtures are authored examples, not saved API responses or evidence that
the current event key or New York coverage has been verified against live Qloo.
"""

import asyncio
from uuid import UUID

import httpx
import pytest
from pydantic import ValidationError

from app.config import Settings
from app.data import CITY
from app.models import Entity, RecommendRequest
from app.qloo import QlooAdapter
from app.ranking import eligible_places
from app.security import AppError, Budget, GlobalBudget
from app.workflow import run_workflow


KEY = "synthetic-mock-upstream-secret"


def uid(number):
    return str(UUID(int=number))


def cultural_row(number=1, **overrides):
    return {"entity_id": uid(number), "name": f"Synthetic Artist {number}", "subtype": "urn:entity:artist", **overrides}


def place_row(number=1, **overrides):
    return {"entity_id": uid(number), "name": f"Synthetic Venue {number}", "subtype": "urn:entity:place", "lat": 40.720 + number / 10000, "lon": -74.000, **overrides}


def config(**overrides):
    return Settings(_env_file=None, data_mode="live", qloo_api_key=KEY, **overrides)


def budget(max_requests=10, global_limit=100):
    return Budget(GlobalBudget(global_limit), max_requests)


def run(coroutine):
    return asyncio.run(coroutine)


async def use_adapter(handler, action):
    settings = config()
    async with httpx.AsyncClient(base_url=settings.qloo_base_url, transport=httpx.MockTransport(handler)) as client:
        return await action(QlooAdapter(settings, client))


@pytest.fixture(autouse=True)
def skip_retry_delay(monkeypatch):
    async def no_wait(_delay):
        return None
    monkeypatch.setattr("app.qloo.asyncio.sleep", no_wait)


def test_search_uses_exact_documented_query_and_server_only_auth_header():
    seen = []

    def handler(request):
        seen.append(request)
        return httpx.Response(200, json={"success": True, "results": [cultural_row()]})

    allowance = budget()
    rows = run(use_adapter(handler, lambda adapter: adapter.search("Synthetic Artist", "artist", allowance)))
    request = seen[0]
    assert request.method == "GET" and request.url.path == "/search"
    assert dict(request.url.params) == {"query": "Synthetic Artist", "types": "urn:entity:artist", "take": "8"}
    assert request.headers["x-api-key"] == KEY
    assert KEY not in str(request.url)
    assert rows[0].id == uid(1) and rows[0].type == "artist"
    assert allowance.used == 1


def test_search_validates_current_subtype_id_name_and_deduplicates():
    rows = [
        cultural_row(), cultural_row(), "malformed",
        cultural_row(2, subtype="urn:entity:movie"),
        cultural_row(3, entity_id="not-a-uuid"),
        cultural_row(4, name=""),
        # A response types[] field is not a verified substitute for subtype.
        cultural_row(5, subtype=None, types=["urn:entity:artist"]),
    ]
    result = run(use_adapter(lambda _: httpx.Response(200, json={"success": True, "results": rows}), lambda adapter: adapter.search("Synthetic", "artist", budget())))
    assert [entity.id for entity in result] == [uid(1)]


def test_search_rows_without_verified_subtype_require_schema_review():
    row = cultural_row(subtype=None, types=["urn:entity:artist"])
    with pytest.raises(AppError) as error:
        run(use_adapter(lambda _: httpx.Response(200, json={"success": True, "results": [row]}), lambda adapter: adapter.search("Synthetic", "artist", budget())))
    assert error.value.code == "qloo_schema"


def test_empty_search_is_valid_and_all_invalid_rows_require_schema_review():
    empty = run(use_adapter(lambda _: httpx.Response(200, json={"success": True, "results": []}), lambda adapter: adapter.search("None", "artist", budget())))
    assert empty == []
    with pytest.raises(AppError) as error:
        run(use_adapter(lambda _: httpx.Response(200, json={"success": True, "results": [cultural_row(entity_id="invalid")]}), lambda adapter: adapter.search("None", "artist", budget())))
    assert error.value.code == "qloo_schema"


@pytest.mark.parametrize("status", [401, 403])
def test_auth_failure_is_not_retried_or_exposed(status):
    seen, allowance = [], budget()

    def handler(request):
        seen.append(request)
        return httpx.Response(status, json={"error": KEY})

    with pytest.raises(AppError) as error:
        run(use_adapter(handler, lambda adapter: adapter.search("Synthetic", "artist", allowance)))
    assert error.value.code == "qloo_auth" and error.value.status == 503
    assert len(seen) == allowance.used == 1
    assert KEY not in str(error.value)


@pytest.mark.parametrize("status", [429, 500, 503])
def test_busy_response_has_one_bounded_retry(status):
    seen, allowance = [], budget()

    def handler(request):
        seen.append(request)
        return httpx.Response(status, json={"error": KEY})

    with pytest.raises(AppError) as error:
        run(use_adapter(handler, lambda adapter: adapter.search("Synthetic", "artist", allowance)))
    assert error.value.code == "qloo_busy"
    assert len(seen) == allowance.used == 2
    assert KEY not in str(error.value)


def test_retry_can_recover_and_both_attempts_are_charged():
    allowance, statuses = budget(), iter([429, 200])

    def handler(_request):
        return httpx.Response(next(statuses), json={"success": True, "results": [cultural_row()]})

    rows = run(use_adapter(handler, lambda adapter: adapter.search("Synthetic", "artist", allowance)))
    assert len(rows) == 1 and allowance.used == 2


@pytest.mark.parametrize("exception", [httpx.ReadTimeout, httpx.ConnectError])
def test_transport_failures_retry_once_and_return_safe_error(exception):
    allowance, seen = budget(), []

    def handler(request):
        seen.append(request)
        raise exception(f"synthetic failure containing {KEY}", request=request)

    with pytest.raises(AppError) as error:
        run(use_adapter(handler, lambda adapter: adapter.search("Synthetic", "artist", allowance)))
    assert error.value.code == "qloo_timeout" and error.value.status == 504
    assert len(seen) == allowance.used == 2
    assert KEY not in str(error.value)


def test_scenario_and_global_budgets_include_retry_attempts():
    for allowance, expected in [(budget(max_requests=1), "scenario_budget"), (budget(global_limit=1), "global_budget")]:
        seen = []

        def handler(request):
            seen.append(request)
            return httpx.Response(429)

        with pytest.raises(AppError) as error:
            run(use_adapter(handler, lambda adapter: adapter.search("Synthetic", "artist", allowance)))
        assert error.value.code == expected
        assert len(seen) == allowance.used == 1


@pytest.mark.parametrize("response", [
    httpx.Response(200, content=b"{broken-json", headers={"content-type": "application/json"}),
    httpx.Response(200, json=[]),
    httpx.Response(200, json={"success": False, "error": KEY}),
    httpx.Response(200, json={"success": True, "results": {}}),
])
def test_malformed_search_json_or_shape_is_a_safe_schema_error(response):
    with pytest.raises(AppError) as error:
        run(use_adapter(lambda _: response, lambda adapter: adapter.search("Synthetic", "artist", budget())))
    assert error.value.code == "qloo_schema"
    assert KEY not in str(error.value)


def test_large_response_is_bounded():
    with pytest.raises(AppError) as error:
        run(use_adapter(lambda _: httpx.Response(200, content=b"x" * 2_000_001), lambda adapter: adapter.search("Synthetic", "artist", budget())))
    assert error.value.code == "qloo_schema"


def test_unexpected_client_error_or_redirect_is_not_followed():
    for status in [400, 302]:
        seen = []

        def handler(request):
            seen.append(request)
            return httpx.Response(status, headers={"location": "https://attacker.invalid"})

        with pytest.raises(AppError) as error:
            run(use_adapter(handler, lambda adapter: adapter.search("Synthetic", "artist", budget())))
        assert error.value.code == "qloo_request"
        assert len(seen) == 1


def test_recommendation_params_use_selected_ids_and_explicit_exclusions():
    seen = []
    entity = Entity(id=uid(90), name="Synthetic seed", type="artist")

    def handler(request):
        seen.append(request)
        return httpx.Response(200, json={"success": True, "results": {"entities": [place_row()]}})

    rows = run(use_adapter(handler, lambda adapter: adapter.recommend([entity], CITY, {uid(8), uid(9)}, budget(), expand=True)))
    params = dict(seen[0].url.params)
    excluded = set(params.pop("filter.exclude.entities").split(","))
    assert excluded == {uid(8), uid(9)}
    assert params == {
        "filter.type": "urn:entity:place", "signal.interests.entities": uid(90),
        "filter.location.query": "New York City", "filter.location.radius": "0", "take": "50",
    }
    assert seen[0].url.path == "/v2/insights"
    assert rows[0].latitude == 40.7201 and rows[0].longitude == -74.0
    assert rows[0].score == 1
    assert "combined selected interests" in rows[0].evidence[0]


def test_flat_place_schema_rejects_bad_coordinates_then_workflow_deduplicates_and_checks_city():
    rows = [
        place_row(1), place_row(1),
        place_row(2, lat=40.7201),  # Same pin under a different ID.
        place_row(3, lat=34.0522, lon=-118.2437),
        place_row(4, lat=True), place_row(5, lat="40.72"),
        place_row(6, lat=91), place_row(7, lon=-181),
        place_row(8, is_closed=True), place_row(9, entity_id="bad"),
        place_row(10, lat=None, location={"lat": 40.72, "lon": -74}),
    ]
    result = run(use_adapter(
        lambda _: httpx.Response(200, json={"success": True, "results": {"entities": rows}}),
        lambda adapter: adapter.recommend([], CITY, set(), budget()),
    ))
    assert [place.id for place in result] == [uid(1), uid(1), uid(2), uid(3)]
    assert [place.id for place in eligible_places(result, set())] == [uid(1)]
    assert eligible_places(result, {uid(1), uid(2)}) == []


def test_recommendations_skip_non_place_rows_even_with_valid_id_name_and_coordinates():
    rows = [
        place_row(1, subtype="urn:entity:artist"),
        place_row(2, subtype="urn:entity:movie"),
        place_row(3, subtype=None, types=["urn:entity:place"]),
        place_row(4),
    ]
    result = run(use_adapter(
        lambda _: httpx.Response(200, json={"success": True, "results": {"entities": rows}}),
        lambda adapter: adapter.recommend([], CITY, set(), budget()),
    ))
    assert [place.id for place in result] == [uid(4)]


@pytest.mark.parametrize("results", [[], {"entities": {}}, {"wrong_key": []}, None])
def test_invalid_recommendation_shape_is_rejected(results):
    with pytest.raises(AppError) as error:
        run(use_adapter(lambda _: httpx.Response(200, json={"success": True, "results": results}), lambda adapter: adapter.recommend([], CITY, set(), budget())))
    assert error.value.code == "qloo_schema"


def test_workflow_retries_for_sparse_live_coverage_without_inventing_places():
    seen, allowance = [], budget()
    seeds = [Entity(id=uid(index), name=f"Synthetic seed {index}", type="artist") for index in (90, 91, 92)]

    def handler(request):
        seen.append(request)
        return httpx.Response(200, json={"success": True, "results": {"entities": [place_row()]}})

    result = run(use_adapter(handler, lambda adapter: run_workflow(
        seeds, RecommendRequest(interest_tokens=["a", "b", "c"]), adapter, allowance,
    )))
    assert [request.url.params["take"] for request in seen] == ["30", "50"]
    assert result.coverage.eligible_places == 1
    assert len(result.zones[0].places) == 1
    assert result.usage.qloo_requests == 2
    assert any("reliable three-zone comparison is unavailable" in warning for warning in result.warnings)


def test_settings_restrict_upstream_host_and_require_live_key():
    with pytest.raises(ValidationError):
        Settings(_env_file=None, data_mode="live", qloo_api_key="")
    with pytest.raises(ValidationError):
        config(qloo_base_url="https://attacker.invalid")
