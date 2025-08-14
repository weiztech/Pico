import inspect
import threading
import os
from lit_reviews.middleware import CurrentUserMiddleware
from backend.logger import logger
from functools import lru_cache

# Thread-local cache
_request_cache = threading.local()

def getCurrentUser():
    # Check if we already cached the user for this request
    if hasattr(_request_cache, 'current_user'):
        return _request_cache.current_user

    try:
        user = None
        # Try to get user using middleware function
        user = CurrentUserMiddleware.get_current_user()
        if not user:
            # If not found, fall back to inspecting the call stack
            for entry in reversed(inspect.stack()):
                if os.path.basename(entry.filename) == 'views.py':
                    try:
                        user = entry.frame.f_locals['request'].user
                    except KeyError:
                        user = None
                    break

        _request_cache.current_user = user
        return user
    
    except Exception as e:
        logger.warning(f"Error getting current user: {e}")
        return None