from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('accounts.urls')),
    path('hostels/', include('hostels.urls')),
    path('requests/', include('requests_module.urls')),
    path('roommates/', include('roommates.urls')),
]