from enum import Enum
from typing import List, Tuple


class GeoCodingAction(str, Enum):
    GEOCODING = 'geocoding'
    REVERSE_GEOCODING = 'reverse_geocoding'

    @classmethod
    def choices(cls) -> List[Tuple[str, str]]:
        return [(action.value, action.value) for action in cls]


class EmbedUrlType(str, Enum):
    place = 'place'
    direction = 'direction'
