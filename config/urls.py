from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView

urlpatterns = [
    # Serves your existing home.html template at the root path '/'
    path('', TemplateView.as_view(template_name='home.html'), name='home'),
    
    path('admin/', admin.site.urls),
    path('accounts/', include(('accounts.urls', 'accounts'), namespace='accounts')),
    path('roommates/', include(('roommates.urls', 'roommates'), namespace='roommates')),
    path('hostels/', include(('hostels.urls', 'hostels'), namespace='hostels')),
]