from django.urls import path

from . import views

app_name = "hostels"

urlpatterns = [
    path("", views.hostel_list, name="hostel_list"),
    path("my-listings/", views.my_listings, name="my_listings"),
    path("add/", views.hostel_add, name="hostel_add"),
    path("<int:pk>/", views.hostel_detail, name="hostel_detail"),
    path("<int:pk>/edit/", views.hostel_edit, name="hostel_edit"),
    path("<int:pk>/delete/", views.hostel_delete, name="hostel_delete"),
    path("<int:pk>/deactivate/", views.hostel_deactivate, name="hostel_deactivate"),
    path("<int:hostel_id>/rooms/add/", views.room_add, name="room_add"),
    path("rooms/<int:room_id>/edit/", views.room_edit, name="room_edit"),
    path("rooms/<int:room_id>/delete/", views.room_delete, name="room_delete"),
    path(
        "<int:hostel_id>/images/upload/",
        views.image_upload,
        name="image_upload",
    ),
    path(
        "images/<int:image_id>/delete/",
        views.image_delete,
        name="image_delete",
    ),
    path(
        "images/<int:image_id>/primary/",
        views.image_set_primary,
        name="image_primary",
    ),
]
