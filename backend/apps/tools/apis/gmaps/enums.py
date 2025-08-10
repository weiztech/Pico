from enum import Enum


class GeoCodingAction(str, Enum):
    GEOCODING = "geocoding"
    REVERSE_GEOCODING = "reverse_geocoding"

    @classmethod
    def choices(cls) -> list[tuple[str, str]]:
        return [(action.value, action.value) for action in cls]


class EmbedUrlType(str, Enum):
    place = "place"
    direction = "direction"
