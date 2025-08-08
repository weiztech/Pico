from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    RegisterView,
    LoginView,
    logout_view,
    ProfileView,
    ProfileDetailView,
    ChangePasswordView
)

app_name = 'auth'

urlpatterns = [
    # Authentication
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', logout_view, name='logout'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # User Profile
    path('profile/', ProfileView.as_view(), name='profile'),
    path('profile/detail/', ProfileDetailView.as_view(), name='profile_detail'),
    path('change-password/', ChangePasswordView.as_view(), name='change_password'),
]
