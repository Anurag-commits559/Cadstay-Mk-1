from django.urls import path
from . import views

app_name = "roommates"

urlpatterns = [
    path("", views.index, name="roommate_list"),
]
