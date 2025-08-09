from django.contrib import admin
from .models import App, RequestAccessTier
from .forms import AppAdminForm


@admin.register(RequestAccessTier)
class RequestAccessTierAdmin(admin.ModelAdmin):
    list_display = ('name', 'rps', 'created_at', 'updated_at')
    search_fields = ('name',)
    readonly_fields = ('created_at', 'updated_at')


@admin.register(App)
class AppAdmin(admin.ModelAdmin):
    """Admin configuration for App model."""
    form = AppAdminForm
    list_display = ('app_id', 'user', 'tier', 'tools', 'last_used_at', 'created_at', 'updated_at')
    search_fields = ('app_id', 'user__email')
    list_filter = ('created_at', 'tier')

    def get_fieldsets(self, request, obj=None):
        if obj:  # obj is not None, so this is an edit form.
            return (
                (None, {'fields': ('app_id', 'user', 'tier', 'token', 'tools')}),
                ('Timestamps', {'fields': ('created_at', 'updated_at', 'last_used_at')}),
            )
        else:  # obj is None, so this is an add form.
            return (
                (None, {'fields': ('tools',)}),
            )

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return 'app_id', 'user', 'token', 'created_at', 'updated_at', 'last_used_at'
        return 'app_id', 'token', 'created_at', 'updated_at', 'last_used_at'

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.user = request.user
            obj.tier_id = RequestAccessTier.objects.order_by('-rps').values_list('id', flat=True).first()
        super().save_model(request, obj, form, change)
