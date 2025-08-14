from django.core.management.base import BaseCommand
from accounts.helpers import subscribe_all_users_to_active_campaign

class Command(BaseCommand):
    """
    Add all registered users to active compagin.
    """

    help = "Add all registered users to active compagin."

    def handle(self, *args, **kwargs):
        subscribe_all_users_to_active_campaign()
