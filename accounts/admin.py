from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from accounts.models import User
from accounts.models import Subscription,Profile

class Admin(UserAdmin):
    """Set admin page for User"""

    model = User
    list_display = (
        "username",
        "first_name",
        "email",
        "is_client",
        "is_superuser",
        "is_active",
        "is_ops_member",
    )
    search_fields = ("email", "username")
    list_filter = ("is_superuser", "is_active", "is_client", "client")
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "first_name",
                    "last_name",
                    "username",
                    "email",
                    "client",
                    "companies",
                    "password",
                )
            },
        ),
        ("Permissions", {"fields": ("is_superuser", "is_active","is_staff",  "is_ops_member", "is_client")}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "first_name",
                    "last_name",
                    "username",
                    "email",
                    "client",
                    "companies",
                    "password1",
                    "password2",
                    "is_superuser",
                    "is_staff",
                    "is_active",
                    "is_client",
                ),
            },
        ),
    )
    readonly_fields = ("is_client",)
    ordering = ("email", "username")

    def save_model(self, request, obj, form, change):
        """Save user model.
        If we associate User with Client ID, is_client field automatically set
        is_client = True and is_superuser = False."""
        if obj.client:
            obj.is_client = True
            obj.is_superuser = False
        obj.save()

class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'full_name', 'phone_number')


class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'client', 'licence_type', 'sign_up_date', 'licence_start_date', 'licence_end_date', 'days_left')
    search_fields = ("user__email", "user__username", "user__client__name")
    autocomplete_fields = ("user",)

    def days_left(self, obj):
        return obj.days_left()

    def client(self, obj):
        if obj.user.client:
            return str(obj.user.client)
        elif obj.user.is_ops_member:
            return "Citemed Operation Team"
        elif obj.user.is_superuser:
            return "Admin"
    
    days_left.short_description = 'Days Left'


admin.site.register(Subscription, SubscriptionAdmin)
admin.site.register(Profile, ProfileAdmin)
admin.site.register(User, Admin)
