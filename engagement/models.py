from django.conf import settings
from django.db import models

from places.models import Place


class Rating(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="ratings")
    place = models.ForeignKey(Place, on_delete=models.CASCADE, related_name="ratings")
    value = models.PositiveSmallIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "place"], name="one_rating_per_user_place"),
            models.CheckConstraint(condition=models.Q(value__gte=1, value__lte=5), name="rating_1_to_5"),
        ]

    def __str__(self) -> str:
        return f"{self.user} rated {self.place} {self.value}"


class SavedPlace(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="saved_places")
    place = models.ForeignKey(Place, on_delete=models.CASCADE, related_name="saved_by")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["user", "place"], name="one_save_per_user_place")]
        ordering = ["-created_at"]
