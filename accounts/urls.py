from django.urls import path
from . import views

app_name = "accounts"
urlpatterns = [
    path("join-citemed-io/", views.register, name="register"),
    path("login/", views.Login.as_view(), name="login"),
    path("login/abbott/", views.LoginV2.as_view(), name="login_v2"),
    path("logout/", views.LogOut.as_view(), name="logout"),
    path("admin/login/", views.Login.as_view(), name="admin_login"),
    path("admin/logout/", views.LogOut.as_view(), name="admin_logout"),
    path("reset_password/", views.ResetPassword.as_view(), name="reset_password"),
    path("subscription_required/", views.subscription_required, name="subscription_required"),
    path(
        "reset_password_done/",
        views.ResetPasswordDone.as_view(),
        name="reset_password_done",
    ),
    path(
        "reset_password_complete/",
        views.ResetPasswordComplete.as_view(),
        name="reset_password_complete",
    ),
    path(
        "reset_password_confirm/$<uidb64>/<token>/",
        views.ResetPasswordConfirm.as_view(),
        name="reset_password_confirm",
    ),
]
