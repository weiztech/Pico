import os 
from django.contrib.auth.views import (
    LogoutView,
    LoginView,
    PasswordResetView,
    PasswordResetDoneView,
    PasswordResetConfirmView,
    PasswordResetCompleteView,
)
from django.urls import reverse_lazy
from .forms import (
    LogInForm,
    ResetPasswordForm,
    PasswordSetForm,
    UserRegistrationForm,
)
from django.shortcuts import render, redirect

from .models import Subscription
from django.conf import settings
from lit_reviews.tasks import send_email

from lit_reviews.models import Client
from django.utils import timezone

from django.contrib.auth import login, authenticate
from backend.logger import logger


def subscription_required(request):
    return render(request, 'accounts/subscription_required.html')

class BaseLogin(LoginView):
    form_class = LogInForm

class Login(BaseLogin):
    template_name = "accounts/login.html"


class LoginV2(BaseLogin):
    template_name = "accounts/login_v2.html"


class LogOut(LogoutView):
    template_name = "accounts/logout.html"


class ResetPassword(PasswordResetView):
    form_class = ResetPasswordForm
    success_url = reverse_lazy("accounts:reset_password_done")
    template_name = "accounts/reset_password.html"
    email_template_name = "accounts/reset_password_email.html"
    subject_template_name = "accounts/reset_password_subject.txt"


class ResetPasswordDone(PasswordResetDoneView):
    template_name = "accounts/reset_password_done.html"


class ResetPasswordConfirm(PasswordResetConfirmView):
    form_class = PasswordSetForm
    success_url = reverse_lazy("accounts:reset_password_complete")
    template_name = "accounts/reset_password_confirm.html"


class ResetPasswordComplete(PasswordResetCompleteView):
    template_name = "accounts/reset_password_complete.html"

def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            try:
                user = form.save(commit=False)

                # Collect user info from the form
                full_name = form.cleaned_data.get('full_name')
                company_name = form.cleaned_data.get('company_name')
                phone_number = form.cleaned_data.get('phone_number')

                # create a client
                client_info = company_name if company_name else full_name
                
                # Check if a client with the same name exists
                clients = Client.objects.filter(name=client_info)
                if clients.exists():
                    # Append current time to client_info to make it unique
                    current_time = timezone.now().strftime("%Y%m%d%H%M%S")
                    client_info += f"_{current_time}"

                # Create the client
                client = Client.objects.create(
                    name=client_info,
                    short_name=client_info,
                    long_name=client_info,
                    full_address_string=client_info,
                )
                client.save()

                if client:
                    user.client = client
                    user.is_client = True
                    user.save()

                    # create subscriprion 
                    subscription = Subscription.objects.create(
                        user=user,
                        licence_type='credits',
                        plan_credits=500,
                        remaining_credits=500,
                    )
                    subscription.save()


                    # Send admin email
                    CELERY_DEFAULT_QUEUE = settings.CELERY_DEFAULT_QUEUE
                    subject = "New User Registration in Citemed"
                    message = f"""
                        A new user has registered in Citemed {CELERY_DEFAULT_QUEUE} environment.
                        \n
                        \n Username: {user.username}
                        \n Email: {user.email}
                        \n Full Name: {full_name}
                        \n Company Name: {company_name}
                        \n Phone Number: {phone_number}
                    """
                    SUPPORT_EMAILS = os.getenv("SUPPORT_EMAILS", "").split(",")
                    logger.info(f"sending email notificaiton to: {SUPPORT_EMAILS}")
                    send_email.delay(subject, message, to=SUPPORT_EMAILS)
                    
                    # Authenticate and log in the user
                    raw_password = form.cleaned_data.get('password1')
                    user = authenticate(username=user.username, password=raw_password)
                    if user is not None:
                        login(request, user)                            
                        return redirect("/literature_reviews/")
                    
                    return redirect('accounts:login')
                
                else:
                    form.add_error(None, 'There was an error creating your account. Please try again.')
                    logger.error(f"Error during user registration: {e}")
                    return render(request, 'accounts/register.html', {'form': form})

            except Exception as e:
                form.add_error(None, 'There was an error creating your account. Please try again.')
                logger.error(f"Error during user registration: {e}")
                return render(request, 'accounts/register.html', {'form': form})
        else:
            return render(request, 'accounts/register.html', {'form': form})

    else:
        form = UserRegistrationForm()
    
    return render(request, 'accounts/register.html', {'form': form})

