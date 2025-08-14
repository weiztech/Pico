from django import forms
from django.contrib.auth.forms import (
    AuthenticationForm,
    PasswordResetForm,
    SetPasswordForm,
    UserCreationForm
)
from .models import User, Profile

class LogInForm(AuthenticationForm):
    '''LogIn form.'''
    username = forms.CharField(
        label="Username or Email",
        widget=forms.TextInput(
            attrs={
                "class": "input",
                "placeholder": "",
            }
        ),
    )
    password = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(
            attrs={
                "class": "input",
                "placeholder": "",
            }
        ),
    )

    def confirm_login_allowed(self, user):
        if not user.is_active:
            raise forms.ValidationError(
                "Your sandbox access has ended. Please contact ethan@citemed.io to update your license and restore your account.",
                code="inactive",
            )
        
    def __init__(self, *args, **kwargs):
        super(LogInForm, self).__init__(*args, **kwargs)


class ResetPasswordForm(PasswordResetForm):
    '''Reset password form.'''
    email = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(
            attrs={
                "class": "input",
                "placeholder": "Enter your email",
            }
        ),
    )


class PasswordSetForm(SetPasswordForm):
    '''Password set form.s'''
    new_password1 = forms.CharField(
        label="New password",
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "placeholder": "Enter new password",
            }
        ),
    )
    new_password2 = forms.CharField(
        label="Password confirmation",
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "placeholder": "Confirm new password",
            }
        ),
    )

class UserRegistrationForm(UserCreationForm):
    full_name = forms.CharField(
        label="Full Name",
        max_length=255,
        widget=forms.TextInput(
            attrs={
                "class": "input",
                "placeholder": "Enter your full name",
            }
        )
    )
    company_name = forms.CharField(
        label="Company Name",
        max_length=255,
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "input",
                "placeholder": "Enter your company name (optional)",
            }
        )
    )
    phone_number = forms.CharField(
        label="Phone Number",
        max_length=15,
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "input",
                "placeholder": "Enter your phone number (optional)",
            }
        )
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2', 'full_name', 'company_name', 'phone_number']

    def save(self, commit=True):
        user = super(UserRegistrationForm, self).save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
            profile = Profile.objects.create(
                user=user,
                full_name=self.cleaned_data['full_name'],
                phone_number=self.cleaned_data['phone_number'],
            )
        return user