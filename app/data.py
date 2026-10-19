"""Authored synthetic fixtures, with no Qloo response data or real venues.

Coordinates locate illustrative pins inside three hand-drawn comparison boxes.
These boxes are cultural exploration zones, not official neighborhood borders.
Entity names identify cultural works; all affinities and venue names are invented.
"""

from dataclasses import dataclass

from app.models import City, Entity, Place


CITY = City(id="new-york", name="New York")
# An intentionally broad coordinate guard, not a municipal boundary dataset.
CITY_BOUNDS = (40.49, -74.27, 40.93, -73.68)


@dataclass(frozen=True)
class Zone:
    id: str
    name: str
    description: str
    bounds: tuple[float, float, float, float]

    def contains(self, latitude: float, longitude: float) -> bool:
        south, west, north, east = self.bounds
        return south <= latitude <= north and west <= longitude <= east


ZONES = (
    Zone(
        "downtown-side-streets", "Downtown Side Streets",
        "An authored exploration zone in lower Manhattan. These are comparison boundaries, not an official neighborhood.",
        (40.700, -74.020, 40.735, -73.974),
    ),
    Zone(
        "midtown-culture-loop", "Midtown Culture Loop",
        "An authored exploration zone in central Manhattan. These are comparison boundaries, not an official neighborhood.",
        (40.740, -74.002, 40.774, -73.960),
    ),
    Zone(
        "uptown-riverside-mix", "Uptown Riverside Mix",
        "An authored exploration zone in upper Manhattan. These are comparison boundaries, not an official neighborhood.",
        (40.778, -73.978, 40.820, -73.926),
    ),
)


DEMO_ENTITIES = (
    Entity(id="demo:radiohead", name="Radiohead", type="artist", subtitle="English rock band · synthetic affinity data"),
    Entity(id="demo:khruangbin", name="Khruangbin", type="artist", subtitle="American musical trio · synthetic affinity data"),
    Entity(id="demo:nina-simone", name="Nina Simone", type="artist", subtitle="Singer and pianist · synthetic affinity data"),
    Entity(id="demo:daft-punk", name="Daft Punk", type="artist", subtitle="French electronic music duo · synthetic affinity data"),
    Entity(id="demo:bjork", name="Björk", type="artist", subtitle="Icelandic musician · synthetic affinity data"),
    Entity(id="demo:spirited-away", name="Spirited Away", type="movie", subtitle="2001 animated film · synthetic affinity data"),
    Entity(id="demo:in-the-mood", name="In the Mood for Love", type="movie", subtitle="2000 film · synthetic affinity data"),
    Entity(id="demo:amelie", name="Amélie", type="movie", subtitle="2001 film · synthetic affinity data"),
    Entity(id="demo:dune-movie", name="Dune", type="movie", subtitle="2021 film · choose this film or the book below"),
    Entity(id="demo:dune-book", name="Dune", type="book", subtitle="Novel by Frank Herbert · distinct from the film"),
    Entity(id="demo:beloved", name="Beloved", type="book", subtitle="Novel by Toni Morrison · synthetic affinity data"),
    Entity(id="demo:left-hand", name="The Left Hand of Darkness", type="book", subtitle="Novel by Ursula K. Le Guin · synthetic affinity data"),
    Entity(id="demo:little-prince", name="The Little Prince", type="book", subtitle="Book by Antoine de Saint-Exupéry · synthetic affinity data"),
    Entity(id="demo:juniper", name="Demo: Juniper Book Café", type="place", subtitle="Fictional seed place · synthetic affinity data"),
    Entity(id="demo:red-kite", name="Demo: Red Kite Cinema", type="place", subtitle="Fictional seed place · synthetic affinity data"),
)


@dataclass(frozen=True)
class DemoVenue:
    id: str
    name: str
    category: str
    latitude: float
    longitude: float
    affinities: dict[str, float]


def _venue(number, name, category, latitude, longitude, **affinities):
    return DemoVenue(
        f"demo:place-{number:02}", f"Demo: {name}", category, latitude, longitude,
        {f"demo:{key.replace('_', '-')}": value for key, value in affinities.items()},
    )


# All 18 venues and every association below are authored test fixtures.
DEMO_VENUES = (
    _venue(1, "Paper Lantern Records", "Record shop", 40.7231, -73.9992, radiohead=.95, khruangbin=.84, bjork=.88, beloved=.37, red_kite=.45),
    _venue(2, "Tiny Orbit Cinema", "Independent cinema", 40.7194, -73.9906, spirited_away=.96, in_the_mood=.91, amelie=.90, dune_movie=.80, radiohead=.49),
    _venue(3, "Ink & Ember", "Book café", 40.7283, -74.0031, beloved=.97, left_hand=.83, little_prince=.90, juniper=.95, khruangbin=.55),
    _venue(4, "Blue Thread Listening Room", "Listening room", 40.7141, -74.0041, nina_simone=.99, khruangbin=.92, daft_punk=.62, beloved=.74, spirited_away=.35),
    _venue(5, "Glass Comet Gallery", "Art gallery", 40.7312, -73.9874, bjork=.97, radiohead=.85, dune_book=.69, dune_movie=.73, red_kite=.76),
    _venue(6, "Copper Moon Studio", "Creative studio", 40.7088, -74.0086, daft_punk=.98, spirited_away=.82, little_prince=.71, juniper=.59, nina_simone=.41),
    _venue(7, "Velvet Circuit Records", "Record shop", 40.7511, -73.9888, daft_punk=.97, radiohead=.91, khruangbin=.80, spirited_away=.54, red_kite=.59),
    _venue(8, "Prism Pocket Cinema", "Independent cinema", 40.7574, -73.9766, dune_movie=.98, spirited_away=.93, in_the_mood=.84, amelie=.74, beloved=.40),
    _venue(9, "Margin Notes", "Bookshop", 40.7462, -73.9940, beloved=.94, dune_book=.96, left_hand=.91, juniper=.85, radiohead=.35),
    _venue(10, "Marigold Sound Café", "Music café", 40.7631, -73.9834, khruangbin=.98, nina_simone=.91, amelie=.78, little_prince=.60, spirited_away=.65),
    _venue(11, "Silver Koi Workshop", "Creative studio", 40.7682, -73.9721, bjork=.93, spirited_away=.87, daft_punk=.83, little_prince=.75, juniper=.55),
    _venue(12, "Frame by Frame", "Screening room", 40.7426, -73.9804, red_kite=.98, in_the_mood=.95, dune_movie=.89, radiohead=.82, left_hand=.61),
    _venue(13, "Cedar Sleeve Records", "Record shop", 40.7891, -73.9702, nina_simone=.96, khruangbin=.91, radiohead=.88, beloved=.72, dune_book=.40),
    _venue(14, "Cloud Atlas Reading Room", "Book café", 40.7972, -73.9661, beloved=.99, left_hand=.97, little_prince=.92, juniper=.98, spirited_away=.59),
    _venue(15, "Junebug Picture House", "Independent cinema", 40.7834, -73.9577, spirited_away=.98, amelie=.95, in_the_mood=.91, red_kite=.94, khruangbin=.44),
    _venue(16, "Electric Fern Gallery", "Art gallery", 40.8030, -73.9542, bjork=.98, daft_punk=.91, dune_movie=.80, radiohead=.79, juniper=.41),
    _venue(17, "Indigo Story Studio", "Creative studio", 40.8113, -73.9451, dune_book=.99, left_hand=.94, dune_movie=.96, little_prince=.87, khruangbin=.59),
    _venue(18, "Amber Note Listening Room", "Listening room", 40.8065, -73.9615, nina_simone=.99, khruangbin=.97, beloved=.87, radiohead=.68, spirited_away=.64),
)


class DemoAdapter:
    """Runs entirely on synthetic fixtures and never consumes Qloo requests."""

    mode = "demo"

    async def search(self, query: str, category: str | None, budget) -> list[Entity]:
        needle = query.strip().casefold()
        # Aliases make the promised artist/book queries easy to discover.
        aliases = {"demo:beloved": "toni morrison", "demo:bjork": "bjork"}
        return [
            item.model_copy(deep=True) for item in DEMO_ENTITIES
            if (not category or item.type == category)
            and needle in f"{item.name} {item.subtitle} {aliases.get(item.id, '')}".casefold()
        ][:10]

    async def recommend(self, entities: list[Entity], city, excluded, budget, expand=False) -> list[Place]:
        city_id = city.id if hasattr(city, "id") else city
        if city_id != CITY.id:
            return []
        names = {entity.id: entity.name for entity in entities}
        candidates = []
        for venue in DEMO_VENUES:
            if venue.id in excluded:
                continue
            matches = [(key, value) for key, value in venue.affinities.items() if key in names]
            if not matches:
                continue
            # Explicit authored membership drives both candidate selection and score.
            score = .65 * max(value for _, value in matches) + .35 * sum(
                value for _, value in matches
            ) / max(len(entities), 1)
            candidates.append(Place(
                id=venue.id, name=venue.name, category=venue.category,
                latitude=venue.latitude, longitude=venue.longitude, score=round(score, 6),
                evidence=[f'Synthetic affinity fixture links this fictional place to “{names[key]}”.' for key, _ in matches],
            ))
        return sorted(candidates, key=lambda place: (-place.score, place.id))[:18 if expand else 12]
