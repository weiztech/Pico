from django import forms

from apps.tools.functions import get_tool_choices

from .models import App


class AppAdminForm(forms.ModelForm):
    tools = forms.MultipleChoiceField(
        choices=get_tool_choices, widget=forms.SelectMultiple, required=False
    )

    class Meta:
        model = App
        fields = "__all__"
