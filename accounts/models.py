from django.db import models 
from django.db.models import Q
from django.contrib.auth.models import AbstractUser
from django.db.models.deletion import DO_NOTHING
from datetime import date

from accounts.managers import UserManager


class User(AbstractUser):
    """
    An abstract base class implementing a fully featured User model with
    admin-compliant permissions.

    Username, email and password are required. Other fields are optional.
    """

    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = ["email"]

    email = models.EmailField(verbose_name="email", max_length=254, unique=True)
    is_ops_member = models.BooleanField(
        "Operations team member",
        default=False,
        help_text="Designates whether the user is a member of our internal CiteMed operations team.",
    )
    is_client = models.BooleanField(
        "client status",
        default=False,
        help_text="Designates whether the user can log into this client site.",
    )
    client = models.ForeignKey(
        "lit_reviews.Client",
        on_delete=DO_NOTHING,
        verbose_name="Main Company",
        related_name="users",
        null=True,
        blank=True,
    )
    companies = models.ManyToManyField(
        "lit_reviews.Client",
        verbose_name="Secondary companies user is part of",
        related_name="all_users",
        null=True,
        blank=True,
    )
    objects = UserManager()

    def __str__(self):
        return self.username
    
    @property
    def my_companies(self):
        "get all user companies user is part of (main and secondary)"
        from client_portal.models import Client

        if self.is_superuser:
            return Client.objects.all()
        elif self.is_ops_member:
            return Client.objects.filter(is_company=False)

        company_ids = list(self.companies.values_list("id", flat=True))
        if self.client and self.client.id:
            company_ids.append(self.client.id)
        return Client.objects.filter(id__in=company_ids)


    def my_reviews(self):
        "Get list of projects (literature reviews) user has access to"
        from lit_reviews.models import LiteratureReview

        if self.is_superuser:
            return LiteratureReview.objects.all()

        companies_review_ids = list(LiteratureReview.objects.filter(client__in=self.my_companies).values_list("id", flat=True))
        external_review_ids = list(LiteratureReview.objects.filter(authorized_users__in=[self]).values_list("id", flat=True))
        all_review_ids_list = [*companies_review_ids, *external_review_ids]

        if self.is_ops_member:
            ops_team_review_ids = list(LiteratureReview.objects.filter(client__is_company=False).values_list("id", flat=True))
            all_review_ids_list = [*all_review_ids_list, *ops_team_review_ids]

        all_review_ids_set = set(all_review_ids_list)
        return LiteratureReview.objects.filter(id__in=all_review_ids_set)


    class Meta:
        db_table = "auth_user"
        verbose_name = "user"
        verbose_name_plural = "users"

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    full_name = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=15, null=True, blank=True)

    def __str__(self):
        return self.full_name

    class Meta:
        verbose_name = "profile"
        verbose_name_plural = "profiles"


class Subscription(models.Model):
    LICENCE_TYPES = (
        # ('sandbox', 'Sandbox'),
        ('basic', 'Basic'),
        ('credits', 'Credits'),
        ('unlimited', 'Unlimited'),
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='licence')
    sign_up_date = models.DateTimeField(auto_now_add=True)
    licence_type = models.CharField(max_length=255, choices=LICENCE_TYPES, default='credits')
    licence_start_date = models.DateField(null=True, blank=True)
    licence_end_date = models.DateField(null=True, blank=True)
    stripe_id = models.CharField(max_length=255, null=True, blank=True)

    plan_credits = models.IntegerField(null=True, blank=True)
    remaining_credits = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return f"{self.user.username} - {self.licence_type}"

    def days_left(self):
        if not self.licence_start_date or not self.licence_end_date:
            return 0
        
        today = date.today()
        if today >= self.licence_end_date:
            return 0

        return (self.licence_end_date - today).days

    @property
    def is_valid(self):
        if self.licence_type == "unlimited" or self.licence_type == "credits":
            return True 
        elif self.licence_type == "basic" and self.days_left() > 0:
            return True 
        return False 

    class Meta:
        verbose_name = "subscription"
        verbose_name_plural = "subscriptions"
