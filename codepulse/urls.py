
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(('blog.api_urls', 'blog_api'), namespace='blog_api')),
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    path('', include('blog.urls')),
    path('blog/', include('blog.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)