"""Load places from a JSON seed file (FR-012). Idempotent: upserts by (name, address)."""

import json
from datetime import time
from pathlib import Path
from typing import Any

from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError, CommandParser
from django.db import transaction
from django.utils import timezone

from places.models import FoodType, OpeningInterval, Place

DEFAULT_SEED = Path(__file__).resolve().parents[2] / "data" / "seed.sample.json"
DAYS = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]


class Command(BaseCommand):
    help = "Import places from a JSON seed file"

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("path", nargs="?", default=str(DEFAULT_SEED))
        parser.add_argument(
            "--update", action="store_true",
            help="Overwrite hours and details of places that already exist",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        path = Path(options["path"])
        try:
            items = json.loads(path.read_text())
        except (OSError, ValueError) as exc:
            raise CommandError(f"Cannot read seed file {path}: {exc}") from exc
        with transaction.atomic():
            for item in items:
                self._import_item(item, update=options["update"])
        self.stdout.write(f"Imported {len(items)} places")

    def _import_item(self, item: dict[str, Any], update: bool) -> None:
        try:
            types = [FoodType.objects.get(slug=slug) for slug in item.get("food_types", [])]
            existing = Place.objects.filter(name=item["name"], address=item["address"]).first()
            if existing is not None and not update:
                return  # keep admin edits and the real hours_verified_at
            place = existing or Place(name=item["name"], address=item["address"])
            place.latitude, place.longitude = item["lat"], item["lng"]
            place.instagram_url = item.get("instagram", "")
            place.hours_verified_at = timezone.localdate()
            place.full_clean(exclude=["food_types"])
            place.save()
            place.food_types.set(types)
            place.intervals.all().delete()
            for day, spans in item.get("hours", {}).items():
                for opens, closes in spans:
                    OpeningInterval.objects.create(
                        place=place, weekday=DAYS.index(day),
                        opens=time.fromisoformat(opens), closes=time.fromisoformat(closes),
                    )
        except (FoodType.DoesNotExist, KeyError, ValueError, ValidationError) as exc:
            raise CommandError(f"Bad seed item {item.get('name', '?')!r}: {exc!r}") from exc
