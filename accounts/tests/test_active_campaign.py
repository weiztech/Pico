from django.test import TestCase
import os
import time
from dotenv import load_dotenv

load_dotenv()

class ActiveCampaignIntegrationTest(TestCase):

    def setUp(self):
        self.api_url = os.getenv("ACTIVE_CAMPAIGN_API_URL")
        self.api_key = os.getenv("ACTIVE_CAMPAIGN_API_KEY")

        # Skip tests if credentials are not available
        if not self.api_url or not self.api_key:
            self.skipTest("ActiveCampaign API credentials not found in environment")

        # Import the function directly from accounts app
        from accounts.helpers import subscribe_email_to_active_campaign
        self.subscribe_func = subscribe_email_to_active_campaign

        self.test_email = "bensoltane.mohammed.amine@gmail.com"

    def test_subscribe_new_contact(self):
        """Test creating a new contact and subscribing to ActiveCampaign"""
        result = self.subscribe_func(
            email=self.test_email,
            first_name="Test",
            last_name="User"
        )

        self.assertTrue(result.get("success"), f"Failed to create contact: {result.get('message')}")
        print(f"✅ Successfully created new contact with email: {self.test_email}")

        # Store contact data for the update test
        self.contact_data = result.get("data", {})

    def test_update_existing_contact(self):
        """Test updating an existing contact in ActiveCampaign"""
        # First create a contact
        self.test_subscribe_new_contact()

        # Wait to ensure the first operation completed
        time.sleep(2)

        # Now update the same contact
        result = self.subscribe_func(
            email=self.test_email,
            first_name="Updated",
            last_name="Name"
        )

        self.assertTrue(result.get("success"), f"Failed to update contact: {result.get('message')}")
        print(f"✅ Successfully updated existing contact with email: {self.test_email}")