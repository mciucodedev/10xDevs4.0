from django.contrib.auth.models import User
from django.db import IntegrityError, transaction
from django.test import TestCase

from engagement.models import Rating
from places.models import Place
from places.services import PlaceFilter, search_places

PASSWORD = "s3cret-Pass-99"


def make_place(name: str = "P") -> Place:
    return Place.objects.create(name=name, address="x", latitude=50.06, longitude=19.94)


def make_user(name: str = "ola") -> User:
    return User.objects.create_user(name, f"{name}@example.com", PASSWORD)


class RateViewTests(TestCase):
    def setUp(self) -> None:
        self.place = make_place()
        self.url = f"/places/{self.place.pk}/rate/"

    def test_rate_requires_login(self) -> None:
        response = self.client.post(self.url, {"value": "5"})
        self.assertEqual(response.status_code, 302)
        self.assertIn("/accounts/login/?next=", response["Location"])
        self.assertEqual(Rating.objects.count(), 0)

    def test_rate_creates_rating(self) -> None:
        self.client.force_login(make_user())
        self.client.post(self.url, {"value": "4"})
        self.assertEqual(Rating.objects.get().value, 4)

    def test_rating_twice_updates_single_row(self) -> None:
        self.client.force_login(make_user())
        self.client.post(self.url, {"value": "4"})
        self.client.post(self.url, {"value": "2"})
        self.assertEqual(Rating.objects.count(), 1)
        self.assertEqual(Rating.objects.get().value, 2)

    def test_value_6_rejected(self) -> None:
        self.client.force_login(make_user())
        response = self.client.post(self.url, {"value": "6"})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(Rating.objects.count(), 0)

    def test_non_numeric_value_rejected(self) -> None:
        self.client.force_login(make_user())
        self.assertEqual(self.client.post(self.url, {"value": "abc"}).status_code, 400)

    def test_rate_requires_post(self) -> None:
        self.client.force_login(make_user())
        self.assertEqual(self.client.get(self.url).status_code, 405)

    def test_rate_unknown_place_404(self) -> None:
        self.client.force_login(make_user())
        self.assertEqual(self.client.post("/places/999/rate/", {"value": "3"}).status_code, 404)


class AggregateTests(TestCase):
    def test_db_constraint_rejects_value_0(self) -> None:
        with self.assertRaises(IntegrityError), transaction.atomic():
            Rating.objects.create(user=make_user(), place=make_place(), value=0)

    def test_aggregate_avg_and_count_on_detail(self) -> None:
        place = make_place()
        Rating.objects.create(user=make_user("a"), place=place, value=5)
        Rating.objects.create(user=make_user("b"), place=place, value=4)
        response = self.client.get(f"/places/{place.pk}/")
        self.assertContains(response, "4.5★")
        self.assertContains(response, "2 ratings")

    def test_unrated_place_shows_no_ratings_yet(self) -> None:
        place = make_place()
        self.assertContains(self.client.get(f"/places/{place.pk}/"), "no ratings yet")

    def test_detail_shows_rate_form_only_when_logged_in(self) -> None:
        place = make_place()
        self.assertNotContains(self.client.get(f"/places/{place.pk}/"), "/rate/")
        self.client.force_login(make_user())
        self.assertContains(self.client.get(f"/places/{place.pk}/"), f"/places/{place.pk}/rate/")

    def test_min_rating_filter_uses_real_ratings(self) -> None:
        good, bad = make_place("good"), make_place("bad")
        Rating.objects.create(user=make_user("a"), place=good, value=5)
        Rating.objects.create(user=make_user("b"), place=bad, value=2)
        f = PlaceFilter(None, None, frozenset(), 4.0, False, (50.06, 19.94))
        results = search_places(f)
        self.assertEqual([r.place.name for r in results], ["good"])
        self.assertEqual((results[0].avg_rating, results[0].rating_count), (5.0, 1))

    def test_detail_preselects_users_existing_rating(self) -> None:
        place = make_place()
        user = make_user()
        Rating.objects.create(user=user, place=place, value=4)
        self.client.force_login(user)
        self.assertContains(self.client.get(f"/places/{place.pk}/"), 'value="4" selected')
