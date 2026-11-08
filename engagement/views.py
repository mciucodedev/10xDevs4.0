from typing import cast

from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import HttpRequest, HttpResponse, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect
from django.views.decorators.http import require_POST

from engagement.models import Rating
from places.models import Place


@login_required
@require_POST
def rate_place(request: HttpRequest, pk: int) -> HttpResponse:
    place = get_object_or_404(Place, pk=pk)
    try:
        value = int(request.POST.get("value", ""))
    except ValueError:
        return HttpResponseBadRequest("value must be an integer 1-5")
    if not 1 <= value <= 5:
        return HttpResponseBadRequest("value must be an integer 1-5")
    Rating.objects.update_or_create(user=cast(User, request.user), place=place, defaults={"value": value})
    return redirect("place-detail", pk=place.pk)
