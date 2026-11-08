"""Pure filtering, open-hours and distance logic for the map (FR-002/003/004/013)."""

from dataclasses import dataclass
from datetime import datetime, time
from math import asin, cos, radians, sin, sqrt
from zoneinfo import ZoneInfo

from django.db.models import Avg, Count

from engagement.models import Rating
from places.models import Place

WARSAW = ZoneInfo("Europe/Warsaw")
EARTH_RADIUS_KM = 6371.0088


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    dlat, dlon = radians(lat2 - lat1), radians(lon2 - lon1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    return 2 * EARTH_RADIUS_KM * asin(sqrt(a))


def is_open_on(place: Place, weekday: int, at: time) -> bool:
    """Open at local weekday/time? Intervals with closes <= opens run past midnight."""
    for iv in place.intervals.all():
        if iv.closes > iv.opens:
            if iv.weekday == weekday and iv.opens <= at < iv.closes:
                return True
        elif iv.weekday == weekday and at >= iv.opens:
            return True
        elif iv.weekday == (weekday - 1) % 7 and at < iv.closes:
            return True
    return False


def is_open_at(place: Place, moment: datetime) -> bool:
    local = moment.astimezone(WARSAW)
    return is_open_on(place, local.weekday(), local.time())


@dataclass(frozen=True)
class PlaceFilter:
    open_now_at: datetime | None
    open_at: tuple[int, time] | None
    food_types: frozenset[str]
    min_rating: float | None
    include_unrated: bool
    origin: tuple[float, float]


@dataclass(frozen=True)
class PlaceResult:
    place: Place
    distance_km: float
    avg_rating: float | None
    rating_count: int


def _rating_stats(place_ids: list[int]) -> dict[int, tuple[float | None, int]]:
    rows = (
        Rating.objects.filter(place_id__in=place_ids)
        .values("place_id")
        .annotate(avg=Avg("value"), n=Count("id"))
    )
    return {row["place_id"]: (row["avg"], row["n"]) for row in rows}


def place_rating(place: Place) -> tuple[float | None, int]:
    return _rating_stats([place.pk]).get(place.pk, (None, 0))


def search_places(f: PlaceFilter) -> list[PlaceResult]:
    places = list(Place.objects.prefetch_related("intervals", "food_types"))
    stats = _rating_stats([p.pk for p in places])
    results: list[PlaceResult] = []
    for place in places:
        if f.open_now_at is not None and not is_open_at(place, f.open_now_at):
            continue
        if f.open_at is not None and not is_open_on(place, *f.open_at):
            continue
        if f.food_types and not {t.slug for t in place.food_types.all()} & f.food_types:
            continue
        avg, count = stats.get(place.pk, (None, 0))
        if f.min_rating is not None:
            if avg is None:
                if not f.include_unrated:
                    continue
            elif avg < f.min_rating:
                continue
        distance = haversine_km(f.origin[0], f.origin[1], place.latitude, place.longitude)
        results.append(PlaceResult(place, distance, avg, count))
    results.sort(key=lambda r: r.distance_km)
    return results
