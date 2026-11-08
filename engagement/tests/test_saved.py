from django.contrib.auth.models import User
from django.test import TestCase

from engagement.models import SavedPlace
from places.models import Place

PASSWORD = "s3cret-Pass-99"


def make_place(name: str = "P") -> Place:
    return Place.objects.create(name=name, address="x", latitude=50.06, longitude=19.94)


def make_user(name: str = "ola") -> User:
    return User.objects.create_user(name, f"{name}@example.com", PASSWORD)


class SavedTests(TestCase):
    def test_save_requires_login(self) -> None:
        place = make_place()
        response = self.client.post(f"/places/{place.pk}/save/")
        self.assertIn("/accounts/login/?next=", response["Location"])
        self.assertEqual(SavedPlace.objects.count(), 0)

    def test_saving_twice_keeps_one_row(self) -> None:
        place = make_place()
        self.client.force_login(make_user())
        self.client.post(f"/places/{place.pk}/save/")
        self.client.post(f"/places/{place.pk}/save/")
        self.assertEqual(SavedPlace.objects.count(), 1)

    def test_unsave_removes(self) -> None:
        place = make_place()
        user = make_user()
        SavedPlace.objects.create(user=user, place=place)
        self.client.force_login(user)
        self.client.post(f"/places/{place.pk}/unsave/")
        self.assertEqual(SavedPlace.objects.count(), 0)

    def test_unsave_when_not_saved_is_harmless(self) -> None:
        place = make_place()
        self.client.force_login(make_user())
        self.assertEqual(self.client.post(f"/places/{place.pk}/unsave/").status_code, 302)

    def test_save_requires_post(self) -> None:
        place = make_place()
        self.client.force_login(make_user())
        self.assertEqual(self.client.get(f"/places/{place.pk}/save/").status_code, 405)

    def test_saved_page_lists_only_own_places(self) -> None:
        mine, theirs = make_place("Mine"), make_place("Theirs")
        me, other = make_user("me"), make_user("other")
        SavedPlace.objects.create(user=me, place=mine)
        SavedPlace.objects.create(user=other, place=theirs)
        self.client.force_login(me)
        response = self.client.get("/saved/")
        self.assertContains(response, "Mine")
        self.assertNotContains(response, "Theirs")

    def test_saved_page_requires_login(self) -> None:
        self.assertEqual(self.client.get("/saved/").status_code, 302)

    def test_saved_page_empty_state(self) -> None:
        self.client.force_login(make_user())
        self.assertContains(self.client.get("/saved/"), "nothing saved yet")

    def test_detail_shows_save_or_unsave_button(self) -> None:
        place = make_place()
        user = make_user()
        self.client.force_login(user)
        self.assertContains(self.client.get(f"/places/{place.pk}/"), f"/places/{place.pk}/save/")
        SavedPlace.objects.create(user=user, place=place)
        self.assertContains(self.client.get(f"/places/{place.pk}/"), f"/places/{place.pk}/unsave/")
