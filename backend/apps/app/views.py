from collections import namedtuple
from importlib import import_module

from django.conf import settings
from django.shortcuts import get_object_or_404
from django.utils import translation
from drf_spectacular.settings import patched_settings
from drf_spectacular.utils import extend_schema
from drf_spectacular.views import SCHEMA_KWARGS, SpectacularAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import App
from .schema_generators import AppSchemaGenerator


class AppSchemaView(SpectacularAPIView):
    generator_class = AppSchemaGenerator
    permission_classes = [IsAuthenticated]

    def _get_schema_response(self, request, app):
        # version specified as parameter to the view always takes precedence. after
        # that we try to source version through the schema view's own versioning_class.
        version = (
            self.api_version or request.version or self._get_version_parameter(request)
        )
        generator = self.generator_class(
            urlconf=self.urlconf,
            api_version=version,
            patterns=self.patterns,
            app=app,
        )
        return Response(
            data=generator.get_schema(request=request, public=self.serve_public),
            headers={
                "Content-Disposition": f'inline; filename="{self._get_filename(request, version)}"'
            },
        )

    @extend_schema(**SCHEMA_KWARGS)
    def get(self, request, app_id, *args, **kwargs):
        access_app = getattr(request, "access_app", None)
        query = {"app_id": app_id}

        # validate token on using app authentication
        if access_app:
            query["token"] = access_app.token

        app = get_object_or_404(App, **query)

        # continue get object
        if isinstance(self.urlconf, list) or isinstance(self.urlconf, tuple):
            ModuleWrapper = namedtuple("ModuleWrapper", ["urlpatterns"])
            if all(isinstance(i, str) for i in self.urlconf):
                # list of import string for urlconf
                patterns = []
                for item in self.urlconf:
                    url = import_module(item)
                    patterns += url.urlpatterns
                self.urlconf = ModuleWrapper(tuple(patterns))
            else:
                # explicitly resolved urlconf
                self.urlconf = ModuleWrapper(tuple(self.urlconf))

        with patched_settings(self.custom_settings):
            if settings.USE_I18N and request.GET.get("lang"):
                with translation.override(request.GET.get("lang")):
                    return self._get_schema_response(request, app)
            else:
                return self._get_schema_response(request, app)
