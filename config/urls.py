from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView

urlpatterns = [
    path('', TemplateView.as_view(template_name='home.html'), name='home'),

    path('admin/', admin.site.urls),
    path('accounts/', include(('accounts.urls', 'accounts'), namespace='accounts')),
    path('roommates/', include(('roommates.urls', 'roommates'), namespace='roommates')),
    path('hostels/', include(('hostels.urls', 'hostels'), namespace='hostels')),
    path('requests/', include(('requests_module.urls', 'requests_module'), namespace='requests_module')),
]

# Serve media files locally during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)