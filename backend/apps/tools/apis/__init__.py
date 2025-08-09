from apps.tools.apis.gmaps.api import GMapViewSet
from apps.tools.apis.lucky.api import LuckyViewSet


# Register Tools APIs
TOOLS_APIS = [
    GMapViewSet,
    LuckyViewSet,
]