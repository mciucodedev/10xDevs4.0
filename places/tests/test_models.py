from datetime import date, time, timedelta

from django.core.exceptions import ValidationError
from django.test import TestCase

from places.models import FoodType, OpeningInterval, Place


def make_place(name: str = "Cafe") -> Place:
    return Place.objects.create(name=name, address="Rynek 1", latitude=50.06, longitude=19.94)


class PlaceModelTests(TestCase):
    def test_place_str_is_name(self) -> None:
        self.assertEqual(str(make_place("Bagel")), "Bagel")

    def test_city_defaults_to_krakow(self) -> None:
        self.assertEqual(make_place().city, "Kraków")

    def test_interval_rejects_weekday_7(self) -> None:
        interval = OpeningInterval(place=make_place(), weekday=7, opens=time(8), closes=time(14))
        with self.assertRaises(ValidationError):
            interval.full_clean()

    def test_default_food_types_exist(self) -> None:
        slugs = set(FoodType.objects.values_list("slug", flat=True))
        self.assertEqual(slugs, {"sweet", "vegan", "vegetarian"})


class PlaceAdminTests(TestCase):
    def test_editing_hours_in_admin_refreshes_verified_date(self) -> None:
        from datetime import date

        from django.contrib.auth.models import User
        from django.urls import reverse

        User.objects.create_superuser("root", "r@example.com", "pw-12345-x")
        self.client.login(username="root", password="pw-12345-x")
        place = make_place()
        data = {
            "name": place.name, "address": place.address, "city": place.city,
            "latitude": "50.06", "longitude": "19.94", "instagram_url": "",
            "intervals-TOTAL_FORMS": "1", "intervals-INITIAL_FORMS": "0",
            "intervals-MIN_NUM_FORMS": "0", "intervals-MAX_NUM_FORMS": "1000",
            "intervals-0-weekday": "0", "intervals-0-opens": "08:00",
            "intervals-0-closes": "14:00",
        }
        response = self.client.post(reverse("admin:places_place_change", args=[place.pk]), data)
        self.assertEqual(response.status_code, 302)
        place.refresh_from_db()
        self.assertEqual(place.hours_verified_at, date.today())
        self.assertEqual(place.intervals.count(), 1)


class HoursFreshnessTests(TestCase):
    TODAY = date(2026, 11, 8)

    def place_verified(self, days_ago: int | None) -> Place:
        place = make_place()
        if days_ago is not None:
            place.hours_verified_at = self.TODAY - timedelta(days=days_ago)
        return place

    def test_stale_after_91_days(self) -> None:
        self.assertTrue(self.place_verified(91).hours_are_stale(self.TODAY))

    def test_not_stale_at_90_days(self) -> None:
        self.assertFalse(self.place_verified(90).hours_are_stale(self.TODAY))

    def test_none_verified_is_stale(self) -> None:
        self.assertTrue(self.place_verified(None).hours_are_stale(self.TODAY))


class StaleAdminFilterTests(TestCase):
    def test_admin_filter_lists_only_stale_places(self) -> None:
        from django.contrib.auth.models import User
        from django.utils import timezone

        User.objects.create_superuser("root", "r@example.com", "pw-12345-x")
        self.client.login(username="root", password="pw-12345-x")
        make_place("Never verified")
        fresh = make_place("Fresh")
        fresh.hours_verified_at = timezone.localdate()
        fresh.save()
        response = self.client.get("/admin/places/place/?hours=stale")
        self.assertContains(response, "Never verified")
        self.assertNotContains(response, "Fresh")
