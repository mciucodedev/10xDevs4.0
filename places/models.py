from datetime import date, timedelta

from django.conf import settings
from django.core.validators import MaxValueValidator
from django.db import models

HOURS_MAX_AGE_DAYS = 90
WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


class FoodType(models.Model):
    slug = models.SlugField(unique=True)
    name = models.CharField(max_length=50)

    def __str__(self) -> str:
        return self.name


class Place(models.Model):
    name = models.CharField(max_length=200)
    address = models.CharField(max_length=300)
    city = models.CharField(max_length=100, default="Kraków")
    latitude = models.FloatField()
    longitude = models.FloatField()
    instagram_url = models.URLField(blank=True)
    food_types = models.ManyToManyField(FoodType, blank=True, related_name="places")
    hours_verified_at = models.DateField(null=True, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return self.name

    def hours_are_stale(self, today: date) -> bool:
        if self.hours_verified_at is None:
            return True
        return today - self.hours_verified_at > timedelta(days=HOURS_MAX_AGE_DAYS)


class OpeningInterval(models.Model):
    """One opening interval on a weekday (0=Mon..6=Sun); closes <= opens means past midnight."""

    place = models.ForeignKey(Place, on_delete=models.CASCADE, related_name="intervals")
    weekday = models.PositiveSmallIntegerField(
        choices=list(enumerate(WEEKDAYS)), validators=[MaxValueValidator(6)]
    )
    opens = models.TimeField()
    closes = models.TimeField()

    class Meta:
        ordering = ["weekday", "opens"]

    def __str__(self) -> str:
        return f"{self.place} {WEEKDAYS[self.weekday]} {self.opens:%H:%M}-{self.closes:%H:%M}"
