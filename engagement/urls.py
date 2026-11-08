from django.urls import path

from engagement import views

urlpatterns = [
    path("places/<int:pk>/rate/", views.rate_place, name="rate"),
    path("places/<int:pk>/save/", views.save_place, name="save"),
    path("places/<int:pk>/unsave/", views.unsave_place, name="unsave"),
    path("saved/", views.saved_list, name="saved"),
]
