from django.contrib.auth.models import User
from django.test import TestCase, override_settings

from engagement.models import Rating
from places.models import Place

PASSWORD = "s3cret-Pass-99"
VALID = {
    "name": "New Cafe", "address": "Floriańska 1", "latitude": "50.0640", "longitude": "19.9400",
    "instagram_url": "", "food_types": ["vegan"],
}


def user_with_ratings(n: int) -> User:
    user = User.objects.create_user("ola", "ola@example.com", PASSWORD)
    for i in range(n):
        place = Place.objects.create(name=f"r{i}", address="x", latitude=50.06, longitude=19.94)
        Rating.objects.create(user=user, place=place, value=4)
    return user


def vegan_pk() -> str:
    from places.models import FoodType
    return str(FoodType.objects.get(slug="vegan").pk)


def payload(**over: object) -> dict[str, object]:
    data: dict[str, object] = dict(VALID, food_types=[vegan_pk()])
    data.update(over)
    return data


@override_settings(MIN_RATINGS_TO_SUBMIT=3)
class SubmitTests(TestCase):
    def test_submit_requires_login(self) -> None:
        self.assertEqual(self.client.get("/places/new/").status_code, 302)

    def test_submit_blocked_below_threshold(self) -> None:
        self.client.force_login(user_with_ratings(2))
        response = self.client.post("/places/new/", payload())
        self.assertEqual(response.status_code, 403)
        self.assertContains(response, "rate 1 more", status_code=403)
        self.assertFalse(Place.objects.filter(name="New Cafe").exists())

    def test_form_blocked_below_threshold(self) -> None:
        self.client.force_login(user_with_ratings(0))
        self.assertEqual(self.client.get("/places/new/").status_code, 403)

    def test_submit_publishes_immediately_at_threshold(self) -> None:
        user = user_with_ratings(3)
        self.client.force_login(user)
        response = self.client.post("/places/new/", payload())
        place = Place.objects.get(name="New Cafe")
        self.assertRedirects(response, f"/places/{place.pk}/", fetch_redirect_response=False)
        self.assertEqual(place.created_by, user)
        self.assertEqual([t.slug for t in place.food_types.all()], ["vegan"])

    def test_submit_rejects_coordinates_outside_krakow_bbox(self) -> None:
        self.client.force_login(user_with_ratings(3))
        self.client.post("/places/new/", payload(latitude="52.23", longitude="21.01"))
        self.assertFalse(Place.objects.filter(name="New Cafe").exists())

    def test_submit_rejects_non_http_instagram_url(self) -> None:
        self.client.force_login(user_with_ratings(3))
        self.client.post("/places/new/", payload(instagram_url="javascript:alert(1)"))
        self.assertFalse(Place.objects.filter(name="New Cafe").exists())

    def test_submit_accepts_http_instagram_url(self) -> None:
        self.client.force_login(user_with_ratings(3))
        self.client.post("/places/new/", payload(instagram_url="https://instagram.com/newcafe"))
        self.assertEqual(Place.objects.get(name="New Cafe").instagram_url, "https://instagram.com/newcafe")

    def test_submitted_place_has_no_hours_so_not_open_now(self) -> None:
        self.client.force_login(user_with_ratings(3))
        self.client.post("/places/new/", payload())
        data = self.client.get("/api/places/", {"open_now": "1"}).json()
        self.assertEqual(data["count"], 0)

    def test_only_rated_places_count_distinct_places(self) -> None:
        user = user_with_ratings(2)
        place = Place.objects.first()
        assert place is not None
        Rating.objects.filter(user=user, place=place).update(value=5)  # still 2 places
        self.client.force_login(user)
        self.assertEqual(self.client.get("/places/new/").status_code, 403)
