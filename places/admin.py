from datetime import timedelta
from typing import Any

from django.contrib import admin
from django.db.models import Q, QuerySet
from django.forms import ModelForm
from django.http import HttpRequest
from django.utils import timezone

from places.models import HOURS_MAX_AGE_DAYS, FoodType, OpeningInterval, Place


class OpeningIntervalInline(admin.TabularInline[OpeningInterval, Place]):
    model = OpeningInterval
    extra = 1


class StaleHoursFilter(admin.SimpleListFilter):
    title = "opening hours"
    parameter_name = "hours"

    def lookups(self, request: HttpRequest, model_admin: Any) -> list[tuple[str, str]]:
        return [("stale", "older than 90 days or never verified")]

    def queryset(self, request: HttpRequest, queryset: QuerySet[Place]) -> QuerySet[Place] | None:
        if self.value() != "stale":
            return None
        cutoff = timezone.localdate() - timedelta(days=HOURS_MAX_AGE_DAYS)
        return queryset.filter(Q(hours_verified_at__isnull=True) | Q(hours_verified_at__lt=cutoff))


@admin.register(Place)
class PlaceAdmin(admin.ModelAdmin[Place]):
    list_display = ("name", "address", "hours_verified_at", "created_by")
    list_filter = (StaleHoursFilter,)
    search_fields = ("name", "address")
    filter_horizontal = ("food_types",)
    inlines = [OpeningIntervalInline]

    def save_related(
        self, request: HttpRequest, form: ModelForm[Place], formsets: Any, change: bool
    ) -> None:
        super().save_related(request, form, formsets, change)
        if any(fs.has_changed() for fs in formsets):
            Place.objects.filter(pk=form.instance.pk).update(hours_verified_at=timezone.localdate())


admin.site.register(FoodType)
