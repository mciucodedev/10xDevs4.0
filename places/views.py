from datetime import time

from typing import cast

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from engagement.models import Rating, SavedPlace
from places.forms import PlaceSubmissionForm
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
    today = timezone.localdate()
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
            "is_open": None if r.place.hours_are_stale(today) else is_open_at(r.place, now),
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
    user_rating = None
    is_saved = False
    if request.user.is_authenticated:
        mine = Rating.objects.filter(user_id=request.user.pk, place=place).first()
        user_rating = mine.value if mine else None
        is_saved = SavedPlace.objects.filter(user_id=request.user.pk, place=place).exists()
    return render(request, "places/detail.html", {
        "place": place, "hours": by_day, "avg_rating": avg, "rating_count": count,
        "is_open": is_open_at(place, timezone.now()), "hours_stale": place.hours_are_stale(timezone.localdate()), "user_rating": user_rating, "is_saved": is_saved,
    })


@login_required
def place_new(request: HttpRequest) -> HttpResponse:
    user = cast(User, request.user)
    rated = Rating.objects.filter(user=user).values("place_id").distinct().count()
    missing = settings.MIN_RATINGS_TO_SUBMIT - rated
    if missing > 0:
        return render(request, "places/submit_blocked.html", {"missing": missing}, status=403)
    form = PlaceSubmissionForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        place = form.save(commit=False)
        place.created_by = user
        place.save()
        form.save_m2m()
        return redirect("place-detail", pk=place.pk)
    return render(request, "places/submit.html", {"form": form})
