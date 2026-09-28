from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect

urlpatterns = [
    path('', lambda request: redirect('roommates/')),
    path('admin/', admin.site.urls),
    path('roommates/', include('roommates.urls', namespace='roommates')),
    path('hostels/', include('hostels.urls', namespace='hostels')),  # <-- Add or verify this line
]