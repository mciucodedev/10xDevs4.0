from datetime import datetime, time
from zoneinfo import ZoneInfo

from django.test import TestCase

from places.models import FoodType, OpeningInterval, Place
from places.services import PlaceFilter, haversine_km, is_open_at, search_places

WARSAW = ZoneInfo("Europe/Warsaw")
RYNEK = (50.0614, 19.9366)
# 2026-11-09 is a Monday
MON_10 = datetime(2026, 11, 9, 10, 0, tzinfo=WARSAW)


def make_place(
    name: str = "P",
    lat: float = 50.0614,
    lng: float = 19.9366,
    hours: list[tuple[int, str, str]] | None = None,
    types: list[str] | None = None,
) -> Place:
    place = Place.objects.create(name=name, address="x", latitude=lat, longitude=lng)
    for weekday, opens, closes in hours or []:
        OpeningInterval.objects.create(
            place=place, weekday=weekday, opens=time.fromisoformat(opens),
            closes=time.fromisoformat(closes),
        )
    if types:
        place.food_types.set(FoodType.objects.filter(slug__in=types))
    return place


def make_filter(**kw: object) -> PlaceFilter:
    base: dict[str, object] = dict(
        open_now_at=None, open_at=None, food_types=frozenset(), min_rating=None,
        include_unrated=False, origin=RYNEK,
    )
    base.update(kw)
    return PlaceFilter(**base)  # type: ignore[arg-type]


class OpenAtTests(TestCase):
    def test_open_inside_interval(self) -> None:
        self.assertTrue(is_open_at(make_place(hours=[(0, "08:00", "14:00")]), MON_10))

    def test_closed_at_closing_minute(self) -> None:
        place = make_place(hours=[(0, "08:00", "10:00")])
        self.assertFalse(is_open_at(place, MON_10))

    def test_place_without_intervals_not_open(self) -> None:
        self.assertFalse(is_open_at(make_place(), MON_10))

    def test_interval_closing_0200_is_open_at_0100_next_day(self) -> None:
        place = make_place(hours=[(0, "23:00", "02:00")])
        tue_1 = datetime(2026, 11, 10, 1, 0, tzinfo=WARSAW)
        self.assertTrue(is_open_at(place, tue_1))
        self.assertFalse(is_open_at(place, datetime(2026, 11, 10, 3, 0, tzinfo=WARSAW)))

    def test_sunday_past_midnight_wraps_to_monday(self) -> None:
        place = make_place(hours=[(6, "22:00", "01:00")])
        self.assertTrue(is_open_at(place, datetime(2026, 11, 9, 0, 30, tzinfo=WARSAW)))

    def test_aware_utc_moment_is_converted_to_warsaw(self) -> None:
        from datetime import UTC
        place = make_place(hours=[(0, "08:00", "14:00")])
        self.assertTrue(is_open_at(place, datetime(2026, 11, 9, 9, 0, tzinfo=UTC)))  # 10:00 CET


class DistanceTests(TestCase):
    def test_haversine_rynek_to_wawel_about_0_5km(self) -> None:
        km = haversine_km(50.0614, 19.9366, 50.0540, 19.9352)
        self.assertGreater(km, 0.4)
        self.assertLess(km, 1.0)


class SearchTests(TestCase):
    def test_search_orders_by_distance(self) -> None:
        make_place("far", lat=50.10)
        make_place("near", lat=50.062)
        names = [r.place.name for r in search_places(make_filter())]
        self.assertEqual(names, ["near", "far"])

    def test_filters_combine_open_and_vegan(self) -> None:
        make_place("open vegan", hours=[(0, "08:00", "14:00")], types=["vegan"])
        make_place("open sweet", hours=[(0, "08:00", "14:00")], types=["sweet"])
        make_place("closed vegan", types=["vegan"])
        result = search_places(make_filter(open_now_at=MON_10, food_types=frozenset({"vegan"})))
        self.assertEqual([r.place.name for r in result], ["open vegan"])

    def test_food_types_match_any_selected(self) -> None:
        make_place("a", types=["vegan"])
        make_place("b", types=["sweet"])
        make_place("c", types=["vegetarian"])
        result = search_places(make_filter(food_types=frozenset({"vegan", "sweet"})))
        self.assertEqual({r.place.name for r in result}, {"a", "b"})

    def test_open_at_chosen_weekday_and_time(self) -> None:
        make_place("sun", hours=[(6, "09:00", "13:00")])
        make_place("mon", hours=[(0, "09:00", "13:00")])
        result = search_places(make_filter(open_at=(6, time(10, 0))))
        self.assertEqual([r.place.name for r in result], ["sun"])

    def test_min_rating_excludes_unrated_by_default(self) -> None:
        make_place("unrated")
        self.assertEqual(search_places(make_filter(min_rating=4.0)), [])

    def test_include_unrated_keeps_unrated_places(self) -> None:
        make_place("unrated")
        result = search_places(make_filter(min_rating=4.0, include_unrated=True))
        self.assertEqual([r.place.name for r in result], ["unrated"])

    def test_no_match_returns_empty_list(self) -> None:
        make_place("closed")
        self.assertEqual(search_places(make_filter(open_now_at=MON_10)), [])

    def test_result_has_distance_and_zero_rating_count(self) -> None:
        make_place("here")
        (result,) = search_places(make_filter())
        self.assertAlmostEqual(result.distance_km, 0.0, places=3)
        self.assertIsNone(result.avg_rating)
        self.assertEqual(result.rating_count, 0)
