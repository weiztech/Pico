from accounts.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

from backend.logger import logger
from accounts.helpers import subscribe_email_to_active_campaign
from lit_reviews.tasks import create_sample_project_on_register_async

@receiver(post_save, sender=User)
def user_created_signal(sender, instance, created, **kwargs):
    if created:
        # create pproject sample for the user
        create_sample_project_on_register_async.delay(instance.id)

        # Extract first and last name
        first_name = instance.first_name
        last_name = instance.last_name
        email = instance.email 

        # subscribe the email to ActiveCampaign (will not affect user creation if it fails)
        try:
            subscribe_result = subscribe_email_to_active_campaign(email, first_name, last_name)
            if not subscribe_result.get("success"):
                logger.warning(f"Failed to subscribe user {email} to ActiveCampaign: {subscribe_result.get('message')}")
        except Exception as e:
            logger.error(f"Error subscribing user {email} to ActiveCampaign: {str(e)}")