from drf_spectacular.plumbing import alpha_operation_sorter
from drf_spectacular.settings import spectacular_settings
from drf_spectacular.generators import  EndpointEnumerator

from apps.tools.constants import API_TOOLS_URL_PREFIX


class CustomEndpointEnumerator(EndpointEnumerator):

    def __init__(self, patterns, urlconf, app):
        super().__init__(patterns, urlconf)
        self.app = app

    def get_api_endpoints(self, patterns=None, prefix=''):
        raw_api_endpoints = self._get_api_endpoints(patterns, prefix)
        # filter tools endpoints
        api_endpoints = []
        for endpoint in raw_api_endpoints:
            endpoint_path = endpoint[0][1:]
            if not endpoint_path.startswith(API_TOOLS_URL_PREFIX):
                continue

            url_prefix = endpoint_path.split(API_TOOLS_URL_PREFIX)[1].split("/")[0]
            if self.app.allow_tool_by_url_prefix(url_prefix):
                api_endpoints.append(endpoint)

        for hook in spectacular_settings.PREPROCESSING_HOOKS:
            api_endpoints = hook(endpoints=api_endpoints)

        api_endpoints_deduplicated = {}
        for path, path_regex, method, callback in api_endpoints:
            if (path, method) not in api_endpoints_deduplicated:
                api_endpoints_deduplicated[path, method] = (path, path_regex, method, callback)

        api_endpoints = list(api_endpoints_deduplicated.values())

        if callable(spectacular_settings.SORT_OPERATIONS):
            return sorted(api_endpoints, key=spectacular_settings.SORT_OPERATIONS)
        elif spectacular_settings.SORT_OPERATIONS:
            return sorted(api_endpoints, key=alpha_operation_sorter)
        else:
            return api_endpoints

class AppSchemaGenerator(spectacular_settings.DEFAULT_GENERATOR_CLASS):
    endpoint_inspector_cls = CustomEndpointEnumerator

    def __init__(self, *args, **kwargs):
        self.app = kwargs.pop("app")
        if not self.app:
            raise Exception("App is required")

        super().__init__(*args, **kwargs)

    def _initialise_endpoints(self):
        if self.endpoints is None:
            self.inspector = self.endpoint_inspector_cls(self.patterns, self.urlconf, app=self.app)
            self.endpoints = self.inspector.get_api_endpoints()

    def get_schema(self, request=None, public=False):
        output = super().get_schema(request, public)
        if self.app.schema_title:
            output["info"]["title"] = self.app.schema_title

        if self.app.schema_description:
            output["info"]["description"] = self.app.schema_description
        return output
