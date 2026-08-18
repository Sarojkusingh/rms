from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # App Routing
    path('', include('accounts.urls')),
    path('', include('tenants.urls')),
    path('', include('academics.urls')),
    path('', include('students.urls')),
    path('', include('faculty.urls')),
    path('', include('examinations.urls')),
    path('', include('marks.urls')),
    path('', include('results.urls')),
    path('', include('reports.urls')),
    path('', include('subscriptions.urls')),
    path('', include('support.urls')),
    path('', include('notifications.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
