from rest_framework.permissions import BasePermission


class AppPermission(BasePermission):
    """
    Check if the app has permission to access the tool.
    The app is authenticated by AppTokenAuthentication.
    """

    def has_permission(self, request, view):
        """
        Check if the app has permission to access the tool.
        """
        app = getattr(request, "access_app", None)

        # admin site user always allow access for easier testing purpose
        if request.user and request.user.has_admin_access and not app:
            return True

        if not app:
            return False

        api_basename = getattr(view, "api_basename", None)
        if not api_basename:
            return False

        # Check if the api_basename is in the app's tools
        return api_basename in app.tools
