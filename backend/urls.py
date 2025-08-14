from django.contrib import admin
from django.urls import include, path
from django.conf.urls.static import static
import debug_toolbar
from .views import redirect_view
from .settings import DEBUG, STATIC_URL, STATIC_ROOT
from django.conf.urls import handler404, handler500

urlpatterns = [
    path("", redirect_view),
    path(
        "",
        include("accounts.urls", namespace="accounts"),
    ),
    path(
        "literature_reviews/",
        include("lit_reviews.urls", namespace="literature_reviews"),
    ),
    path(
        "client_portal/",
        include("client_portal.urls", namespace="client_portal"),
    ),
    path(
        "admin_monitoring/",
        include(("admin_side.urls" , "admin_side"), namespace="admin_side"),
    ),
    # path('s3upload/', include('s3upload.urls')),
    path('s3direct/', include('s3direct.urls')),
    path("admin/", admin.site.urls),
] + static(STATIC_URL, document_root=STATIC_ROOT)


if DEBUG:
    urlpatterns.insert(0, path("__debug__/", include(debug_toolbar.urls)))

# error pages
handler404 = 'lit_reviews.views.error_404'
handler500 = 'lit_reviews.views.error_500'
handler403 = 'lit_reviews.views.error_403'
