from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from accounts import views as accounts_views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", accounts_views.home, name="home"),
    path("", include("accounts.urls")),
    path("hostels/", include("hostels.urls")),
    path("roommates/", include("roommates.urls")),  # <-- Updated to include "roommates/"
    path("", include("requests_module.urls")), 
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
