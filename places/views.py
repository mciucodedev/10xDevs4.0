from datetime import time

from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.utils import timezone

from places.models import WEEKDAYS, FoodType, Place
from places.services import PlaceFilter, is_open_at, place_rating, search_places

DEFAULT_ORIGIN = (50.0614, 19.9366)


class BadParam(ValueError):
    pass


def _float(request: HttpRequest, name: str, lo: float, hi: float) -> float | None:
    raw = request.GET.get(name)
    if raw in (None, ""):
        return None
    try:
        value = float(raw)
    except ValueError as exc:
        raise BadParam(f"{name} must be a number") from exc
    if not lo <= value <= hi:
        raise BadParam(f"{name} must be between {lo:g} and {hi:g}")
    return value


def parse_filter(request: HttpRequest) -> PlaceFilter:
    lat = _float(request, "lat", -90, 90)
    lng = _float(request, "lng", -180, 180)
    origin = DEFAULT_ORIGIN if lat is None or lng is None else (lat, lng)
    day_raw, at_raw = request.GET.get("day", ""), request.GET.get("at", "")
    open_at: tuple[int, time] | None = None
    if day_raw and at_raw:
        try:
            day = int(day_raw)
            at = time.fromisoformat(at_raw)
        except ValueError as exc:
            raise BadParam("day must be 0-6 and at must be HH:MM") from exc
        if not 0 <= day <= 6:
            raise BadParam("day must be 0-6")
        open_at = (day, at)
    return PlaceFilter(
        open_now_at=timezone.now() if request.GET.get("open_now") == "1" else None,
        open_at=open_at,
        food_types=frozenset(request.GET.getlist("food")),
        min_rating=_float(request, "min_rating", 1, 5),
        include_unrated=request.GET.get("include_unrated") == "1",
        origin=origin,
    )


def map_page(request: HttpRequest) -> HttpResponse:
    return render(request, "places/map.html", {"food_types": FoodType.objects.all()})


def places_api(request: HttpRequest) -> JsonResponse:
    try:
        place_filter = parse_filter(request)
    except BadParam as exc:
        return JsonResponse({"error": str(exc)}, status=400)
    now = timezone.now()
    results = [
        {
            "id": r.place.pk,
            "name": r.place.name,
            "lat": r.place.latitude,
            "lng": r.place.longitude,
            "distance_km": round(r.distance_km, 2),
            "avg_rating": r.avg_rating,
            "rating_count": r.rating_count,
            "food_types": sorted(t.slug for t in r.place.food_types.all()),
            "is_open": is_open_at(r.place, now),
            "url": f"/places/{r.place.pk}/",
        }
        for r in search_places(place_filter)
    ]
    return JsonResponse({"results": results, "count": len(results)})


def place_detail(request: HttpRequest, pk: int) -> HttpResponse:
    place = get_object_or_404(Place.objects.prefetch_related("intervals", "food_types"), pk=pk)
    by_day: dict[str, list[str]] = {name: [] for name in WEEKDAYS}
    for iv in place.intervals.all():
        by_day[WEEKDAYS[iv.weekday]].append(f"{iv.opens:%H:%M}–{iv.closes:%H:%M}")
    avg, count = place_rating(place)
    return render(request, "places/detail.html", {
        "place": place, "hours": by_day, "avg_rating": avg, "rating_count": count,
        "is_open": is_open_at(place, timezone.now()),
    })
