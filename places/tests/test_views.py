from datetime import time

from django.test import TestCase
from django.urls import reverse

from places.models import FoodType, OpeningInterval, Place


def make_place(name: str, lat: float = 50.0614, lng: float = 19.9366, types: list[str] | None = None,
               always_open: bool = False) -> Place:
    place = Place.objects.create(name=name, address="x", latitude=lat, longitude=lng)
    if types:
        place.food_types.set(FoodType.objects.filter(slug__in=types))
    if always_open:
        for day in range(7):
            OpeningInterval.objects.create(place=place, weekday=day, opens=time(0, 0), closes=time(23, 59))
    return place


class ApiTests(TestCase):
    url = "/api/places/"

    def test_api_returns_matching_places_sorted_by_distance(self) -> None:
        make_place("far", lat=50.10)
        make_place("near", lat=50.062)
        data = self.client.get(self.url).json()
        self.assertEqual([r["name"] for r in data["results"]], ["near", "far"])
        self.assertEqual(data["count"], 2)

    def test_api_filters_combine(self) -> None:
        make_place("open vegan", types=["vegan"], always_open=True)
        make_place("open sweet", types=["sweet"], always_open=True)
        make_place("closed vegan", types=["vegan"])
        data = self.client.get(self.url, {"open_now": "1", "food": ["vegan"]}).json()
        self.assertEqual([r["name"] for r in data["results"]], ["open vegan"])

    def test_api_bad_lat_returns_400(self) -> None:
        response = self.client.get(self.url, {"lat": "abc", "lng": "19.9"})
        self.assertEqual(response.status_code, 400)
        self.assertIn("error", response.json())

    def test_api_bad_min_rating_returns_400(self) -> None:
        self.assertEqual(self.client.get(self.url, {"min_rating": "x"}).status_code, 400)

    def test_api_lat_out_of_range_returns_400(self) -> None:
        self.assertEqual(self.client.get(self.url, {"lat": "999", "lng": "19.9"}).status_code, 400)

    def test_api_missing_origin_falls_back_to_default(self) -> None:
        make_place("p")
        self.assertEqual(self.client.get(self.url).status_code, 200)

    def test_api_no_matches_returns_empty_list_count_0(self) -> None:
        make_place("closed")
        data = self.client.get(self.url, {"open_now": "1"}).json()
        self.assertEqual(data, {"results": [], "count": 0})

    def test_api_fields(self) -> None:
        make_place("p", types=["vegan"], always_open=True)
        (row,) = self.client.get(self.url).json()["results"]
        self.assertEqual(set(row), {"id", "name", "lat", "lng", "distance_km", "avg_rating",
                                    "rating_count", "food_types", "is_open", "url"})
        self.assertEqual(row["food_types"], ["vegan"])
        self.assertTrue(row["is_open"])

    def test_api_open_at_chosen_day_and_time(self) -> None:
        make_place("always", always_open=True)
        make_place("never")
        data = self.client.get(self.url, {"day": "6", "at": "10:00"}).json()
        self.assertEqual([r["name"] for r in data["results"]], ["always"])


class MapPageTests(TestCase):
    def test_map_page_renders_200_for_anonymous(self) -> None:
        response = self.client.get(reverse("map"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "leaflet")
        self.assertContains(response, "Include unrated")


class DetailTests(TestCase):
    def test_detail_shows_address_hours_types_and_maps_link(self) -> None:
        place = make_place("Bagel", types=["vegan"])
        place.address = "Józefa 1"
        place.save()
        OpeningInterval.objects.create(place=place, weekday=0, opens=time(8), closes=time(14))
        response = self.client.get(f"/places/{place.pk}/")
        self.assertContains(response, "Józefa 1")
        self.assertContains(response, "Monday")
        self.assertContains(response, "08:00")
        self.assertContains(response, "Vegan")
        self.assertContains(response, "https://www.google.com/maps?q=50.0614,19.9366")
        self.assertContains(response, "no ratings yet")

    def test_detail_hides_instagram_when_blank(self) -> None:
        place = make_place("p")
        self.assertNotContains(self.client.get(f"/places/{place.pk}/"), "Instagram")

    def test_detail_shows_instagram_when_present(self) -> None:
        place = make_place("p")
        place.instagram_url = "https://instagram.com/p"
        place.save()
        self.assertContains(self.client.get(f"/places/{place.pk}/"), 'href="https://instagram.com/p"')

    def test_detail_escapes_user_supplied_name(self) -> None:
        place = make_place("<script>alert(1)</script>")
        self.assertNotContains(self.client.get(f"/places/{place.pk}/"), "<script>alert(1)")

    def test_detail_404_unknown_place(self) -> None:
        self.assertEqual(self.client.get("/places/999/").status_code, 404)
