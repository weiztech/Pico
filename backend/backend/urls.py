from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView


from apps.tools.constants import API_TOOLS_URL_PREFIX


urlpatterns = [
    path('admin/', admin.site.urls),
    # path('api/auth/', include('apps.auth.urls')),
    path(API_TOOLS_URL_PREFIX, include('apps.tools.urls')),
    path('api/app/', include('apps.app.urls')),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]
