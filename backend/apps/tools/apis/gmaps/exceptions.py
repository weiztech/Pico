class GoogleMapsError(Exception):
    """Base exception class for Google Maps API errors."""
    pass


class QuotaExceededError(GoogleMapsError):
    """Raised when API quota is exceeded."""
    def __init__(self, message="Google Maps API quota has been exceeded"):
        self.message = f"QuotaExceededError - {message}"
        super().__init__(self.message)


class GMapUnexpectedError(GoogleMapsError):
    """Raised when an unexpected error occurs."""
    def __init__(self, message="Google Maps API unexpected error occurred"):
        self.message = f"GMapUnexpectedError - {message}"
        super().__init__(self.message)
