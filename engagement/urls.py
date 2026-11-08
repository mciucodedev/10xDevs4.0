from django.urls import path

from engagement import views

urlpatterns = [
    path("places/<int:pk>/rate/", views.rate_place, name="rate"),
]
