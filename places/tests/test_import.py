import json
from datetime import date
from pathlib import Path
from tempfile import TemporaryDirectory

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase
from django.utils import timezone

from places.models import Place

ITEM = {
    "name": "Bagel Bar", "address": "Józefa 1", "lat": 50.05, "lng": 19.94,
    "instagram": "https://instagram.com/bagel", "food_types": ["sweet", "vegan"],
    "hours": {"mon": [["08:00", "14:00"]], "sun": [["09:00", "15:00"], ["18:00", "01:00"]]},
}


def run_import(items: list[dict[str, object]]) -> None:
    with TemporaryDirectory() as tmp:
        path = Path(tmp) / "seed.json"
        path.write_text(json.dumps(items))
        call_command("import_places", str(path))


class ImportPlacesTests(TestCase):
    def test_import_creates_places_and_intervals(self) -> None:
        run_import([ITEM])
        place = Place.objects.get(name="Bagel Bar")
        self.assertEqual(place.intervals.count(), 3)
        self.assertEqual({t.slug for t in place.food_types.all()}, {"sweet", "vegan"})
        self.assertEqual(place.hours_verified_at, timezone.localdate())
        self.assertIsInstance(place.hours_verified_at, date)

    def test_import_twice_does_not_duplicate(self) -> None:
        run_import([ITEM])
        run_import([ITEM])
        self.assertEqual(Place.objects.count(), 1)
        self.assertEqual(Place.objects.get().intervals.count(), 3)

    def test_unknown_food_type_slug_raises_commanderror_and_rolls_back(self) -> None:
        good = dict(ITEM, name="Good")
        bad = dict(ITEM, name="Bad", food_types=["nope"])
        with self.assertRaises(CommandError):
            run_import([good, bad])
        self.assertEqual(Place.objects.count(), 0)

    def test_bundled_sample_seed_file_is_valid(self) -> None:
        call_command("import_places")
        self.assertGreaterEqual(Place.objects.count(), 1)


class ReimportTests(TestCase):
    def test_reimport_keeps_admin_edited_hours_and_verified_date(self) -> None:
        run_import([ITEM])
        place = Place.objects.get()
        place.intervals.all().delete()
        place.hours_verified_at = date(2026, 1, 1)
        place.save()
        run_import([ITEM])
        place.refresh_from_db()
        self.assertEqual(place.intervals.count(), 0)
        self.assertEqual(place.hours_verified_at, date(2026, 1, 1))

    def test_reimport_with_update_flag_overwrites(self) -> None:
        run_import([ITEM])
        Place.objects.get().intervals.all().delete()
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "seed.json"
            path.write_text(json.dumps([ITEM]))
            call_command("import_places", str(path), "--update")
        self.assertEqual(Place.objects.get().intervals.count(), 3)

    def test_invalid_instagram_url_in_seed_is_rejected(self) -> None:
        with self.assertRaises(CommandError):
            run_import([dict(ITEM, instagram="javascript:alert(1)")])
        self.assertEqual(Place.objects.count(), 0)
