"""Validated public API and adapter contracts for TasteDistrict."""

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


EntityType = Literal["artist", "movie", "book", "place"]
Identifier = Annotated[str, Field(min_length=1, max_length=256)]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)


class Entity(StrictModel):
    id: Identifier
    name: str = Field(min_length=1, max_length=300)
    type: EntityType
    subtitle: str = Field(default="", max_length=500)


class Place(StrictModel):
    """A source candidate; score is its source order normalized to 0–1.

    Demo data instead uses explicitly authored synthetic affinity weights.
    """

    id: Identifier
    name: str = Field(min_length=1, max_length=300)
    category: str = Field(min_length=1, max_length=200)
    latitude: float
    longitude: float
    score: float
    evidence: list[str] = Field(default_factory=list, max_length=10)


class RecommendRequest(StrictModel):
    city_id: Literal["new-york"] = "new-york"
    interest_tokens: list[Annotated[str, Field(min_length=1, max_length=4096)]] = Field(
        min_length=3, max_length=5
    )
    excluded_place_ids: list[Identifier] = Field(default_factory=list, max_length=20)
    previous_place_ids: list[Identifier] = Field(default_factory=list, max_length=20)
    previous_zone_ids: list[Identifier] = Field(default_factory=list, max_length=20)

    @field_validator(
        "interest_tokens", "excluded_place_ids", "previous_place_ids", "previous_zone_ids"
    )
    @classmethod
    def require_unique(cls, values: list[str]) -> list[str]:
        if len(values) != len(set(values)):
            raise ValueError("List entries must be unique.")
        return values


class City(StrictModel):
    id: str
    name: str


class PlaceResult(Place):
    """A displayed place; score is the application's 0–100 ranking."""


class ZoneResult(StrictModel):
    id: str
    name: str
    description: str
    score: float
    explanation: str
    places: list[PlaceResult]


class WorkflowStep(StrictModel):
    step: str
    status: Literal["completed", "limited", "skipped"]
    detail: str


class Changes(StrictModel):
    added_places: list[str]
    removed_places: list[str]
    message: str


class Usage(StrictModel):
    qloo_requests: int = Field(ge=0)
    llm_calls: Literal[0] = 0


class Coverage(StrictModel):
    eligible_places: int = Field(ge=0)
    zone_count: int = Field(ge=0)


class RecommendResponse(StrictModel):
    mode: Literal["demo", "live"]
    city: City
    zones: list[ZoneResult]
    workflow: list[WorkflowStep]
    warnings: list[str]
    changes: Changes
    usage: Usage
    coverage: Coverage
    request_id: str
