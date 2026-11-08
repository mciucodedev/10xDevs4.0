from typing import Any

from django.contrib import admin
from django.forms import ModelForm
from django.http import HttpRequest
from django.utils import timezone

from places.models import FoodType, OpeningInterval, Place


class OpeningIntervalInline(admin.TabularInline[OpeningInterval, Place]):
    model = OpeningInterval
    extra = 1


@admin.register(Place)
class PlaceAdmin(admin.ModelAdmin[Place]):
    list_display = ("name", "address", "hours_verified_at", "created_by")
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
