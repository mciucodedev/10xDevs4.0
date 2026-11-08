from django.urls import path

from places import views

urlpatterns = [
    path("", views.map_page, name="map"),
    path("places/new/", views.place_new, name="place-new"),
    path("places/<int:pk>/", views.place_detail, name="place-detail"),
    path("api/places/", views.places_api, name="places-api"),
]
