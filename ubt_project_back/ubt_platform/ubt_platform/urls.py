from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from django.conf.urls.static import static
from django.conf import settings, Settings

# router = DefaultRouter()
# router.register(r'subjects', SubjectViewSet)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('tests.urls')),
    path('summernote/', include('django_summernote.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
