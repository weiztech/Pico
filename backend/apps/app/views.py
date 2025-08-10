from collections import namedtuple
from importlib import import_module

from drf_spectacular.settings import patched_settings
from drf_spectacular.views import SpectacularAPIView, SCHEMA_KWARGS
from drf_spectacular.utils import extend_schema

from django.conf import settings
from django.utils import translation

from .models import App


class AppSchemaView(SpectacularAPIView):

    @extend_schema(**SCHEMA_KWARGS)
    def get(self, request, *args, **kwargs):
        # continue get object
        if isinstance(self.urlconf, list) or isinstance(self.urlconf, tuple):
            ModuleWrapper = namedtuple('ModuleWrapper', ['urlpatterns'])
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
            if settings.USE_I18N and request.GET.get('lang'):
                with translation.override(request.GET.get('lang')):
                    return self._get_schema_response(request)
            else:
                return self._get_schema_response(request)