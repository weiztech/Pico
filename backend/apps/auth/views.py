from drf_spectacular.utils import extend_schema
from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenRefreshView

from .models import Users
from .serializers import (
    PasswordChangeSerializer,
    UserLoginSerializer,
    UserRegistrationSerializer,
    UserSerializer,
    UserProfileSerializer,
)


@extend_schema(description='Register a new user', tags=['Auth'])
class RegisterView(generics.CreateAPIView):
    """User registration endpoint."""

    queryset = Users.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)

        return Response(
            {
                'user': UserSerializer(user).data,
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            },
            status=status.HTTP_201_CREATED,
        )


@extend_schema(description='Login a user', tags=['Auth'])
class LoginView(generics.GenericAPIView):
    """User login endpoint."""

    serializer_class = UserLoginSerializer
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']

        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)

        return Response(
            {
                'user': UserSerializer(user).data,
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }
        )


@extend_schema(description='Logout a user', tags=['Auth'])
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_view(request):
    """User logout endpoint."""
    try:
        refresh_token = request.data['refresh']
        token = RefreshToken(refresh_token)
        token.blacklist()
        return Response(
            {'message': 'Successfully logged out'}, status=status.HTTP_205_RESET_CONTENT
        )
    except Exception:
        return Response({'error': 'Invalid token'}, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(description='Refresh an access token', tags=['Auth'])
class CustomTokenRefreshView(TokenRefreshView):
    """
    Custom token refresh view to include it in the spectacular schema.
    """

    pass


@extend_schema(description='Retrieve or update user profile', tags=['Profile'])
class UserProfileView(generics.RetrieveUpdateAPIView):
    """User profile endpoint."""

    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user


@extend_schema(description='Change user password', tags=['Profile'])
class ChangePasswordView(generics.GenericAPIView):
    """Change password endpoint."""

    serializer_class = PasswordChangeSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = request.user
        user.set_password(serializer.validated_data['new_password'])
        user.save()

        return Response({'message': 'Password changed successfully'})
