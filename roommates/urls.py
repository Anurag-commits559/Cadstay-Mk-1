from django.urls import path
from . import views

app_name = 'roommates'

urlpatterns = [
    path('', views.roommate_list, name='roommate_list'),
    path('index/', views.roommate_list, name='index'),
    path('create/', views.create_roommate_request, name='create_roommate_request'),
    path('create-profile/', views.create_roommate_request, name='create_profile'),
    path('<int:pk>/', views.roommate_detail, name='roommate_detail'),
    path('<int:pk>/edit/', views.edit_roommate_request, name='edit_roommate_request'),
    path('<int:pk>/delete/', views.delete_roommate_request, name='delete_roommate_request'),
]