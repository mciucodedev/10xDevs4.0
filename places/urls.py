from django.urls import path

from places import views

urlpatterns = [
    path("", views.map_page, name="map"),
    path("api/places/", views.places_api, name="places-api"),
]
