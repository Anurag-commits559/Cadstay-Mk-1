from django.urls import path

from . import views

app_name = 'roommates'

urlpatterns = [
    path('', views.index, name='roommate_list'),
    path('create/', views.create_request, name='create_roommate_request'),
    path('delete/<int:pk>/', views.delete_request, name='delete_roommate_request'),
]