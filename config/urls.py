"""
Root URL configuration.

Only the home page lives here directly. Everything related to
authentication/user management is delegated to accounts.urls.
Future team members will add their own app URLs here, e.g.:
    path("hostels/", include("listings.urls")),
    path("roommates/", include("roommates.urls")),
"""

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
    path("", include("roommates.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
