import requests
import json
import os
from backend.logger import logger


def subscribe_email_to_active_campaign(email, first_name, last_name, list_id=24):
    try:
        api_url = os.getenv("ACTIVE_CAMPAIGN_API_URL")
        api_key = os.getenv("ACTIVE_CAMPAIGN_API_KEY")
        if not api_url or not api_key:
            logger.error("ActiveCampaign API URL or API Key not set in environment variables.")
            return {"success": False, "message": "API credentials not found."}

        headers = {
            "Api-Token": api_key,
            "Content-Type": "application/json"
        }

        # Step 1: First check if the contact already exists
        logger.info(f"Checking if contact exists for email: {email}")
        search_endpoint = f"{api_url}/api/3/contacts?email={email}"
        search_response = requests.get(search_endpoint, headers=headers)

        contact_id = None

        if search_response.status_code == 200:
            contacts = search_response.json().get("contacts", [])
            if contacts:
                # Contact exists, get the ID
                contact_id = contacts[0].get("id")
                logger.info(f"Found existing contact with ID: {contact_id}")

                # Update the existing contact
                update_endpoint = f"{api_url}/api/3/contacts/{contact_id}"
                update_data = {
                    "contact": {
                        "email": email,
                        "firstName": first_name,
                        "lastName": last_name
                    }
                }

                logger.info(f"Updating existing contact for email: {email}")
                update_response = requests.put(update_endpoint, headers=headers, data=json.dumps(update_data))

                if update_response.status_code not in [200, 201]:
                    logger.error(f"Failed to update contact: {update_response.text}")
                    return {"success": False, "message": f"Failed to update contact: {update_response.text}"}

                logger.info(f"Successfully updated contact with ID: {contact_id}")

        # If contact doesn't exist, create a new one
        if not contact_id:
            # Step 1: Create new contact
            create_endpoint = f"{api_url}/api/3/contacts"
            contact_data = {
                "contact": {
                    "email": email,
                    "firstName": first_name,
                    "lastName": last_name
                }
            }

            logger.info(f"Creating new contact for email: {email}")
            response = requests.post(create_endpoint, headers=headers, data=json.dumps(contact_data))

            if response.status_code not in [200, 201]:
                logger.error(f"Failed to create contact: {response.text}")
                return {"success": False, "message": f"Failed to create contact: {response.text}"}

            # Get contact ID from response
            contact_id = response.json().get("contact", {}).get("id")
            if not contact_id:
                logger.error(f"Could not retrieve contact ID from API response: {response.text}")
                return {"success": False, "message": "Could not retrieve contact ID from API response"}

            logger.info(f"Successfully created new contact with ID: {contact_id}")

        # Step 2: Add contact to list (whether it's a new or existing contact)
        list_endpoint = f"{api_url}/api/3/contactLists"

        list_data = {
            "contactList": {
                "list": list_id,
                "contact": contact_id,
                "status": 1
            }
        }

        logger.info(f"Attempting to add contact {contact_id} to list {list_id}")
        list_response = requests.post(list_endpoint, headers=headers, data=json.dumps(list_data))

        # If the response indicates the contact is already on the list, treat as success
        if list_response.status_code == 422 and "already exists" in list_response.text.lower():
            logger.info(f"Contact {contact_id} is already on list {list_id}")
            return {"success": True, "message": "Contact is already subscribed"}

        if list_response.status_code not in [200, 201]:
            logger.error(f"Failed to add contact to list: {list_response.text}")
            return {"success": False, "message": f"Failed to add contact to list: {list_response.text}"}

        logger.info(f"Successfully subscribed {email} to list {list_id}")
        return {"success": True, "message": "Successfully subscribed", "data": list_response.json()}

    except requests.exceptions.RequestException as e:
        logger.error(f"Request error while subscribing {email}: {str(e)}")
        return {"success": False, "message": f"API request error: {str(e)}"}
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error while subscribing {email}: {str(e)}")
        return {"success": False, "message": f"JSON decode error: {str(e)}"}
    except Exception as e:
        logger.error(f"Unexpected error while subscribing {email}: {str(e)}")
        return {"success": False, "message": f"Unexpected error: {str(e)}"}


def subscribe_all_users_to_active_campaign():
    """
    Function to subscribe all existing users to the ActiveCampaign list.
    This can be run as a one-time operation
    """
    from django.contrib.auth import get_user_model
    User = get_user_model()

    users = User.objects.filter(is_active=True)
    logger.info(f"Starting bulk subscription for {users.count()} users")

    users_data = []
    for user in users:
        users_data.append({
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name
        })

    results = {
        "total": len(users_data),
        "successful": 0,
        "failed": 0,
        "failures": []
    }

    for user in users_data:
        email = user.get("email")
        first_name = user.get("first_name", "")
        last_name = user.get("last_name", "")

        if not email:
            results["failed"] += 1
            results["failures"].append({"email": None, "reason": "Missing email"})
            continue

        result = subscribe_email_to_active_campaign(email, first_name, last_name)

        if result.get("success"):
            results["successful"] += 1
        else:
            results["failed"] += 1
            results["failures"].append({
                "email": email,
                "reason": result.get("message", "Unknown error")
            })

    logger.info(f"Bulk subscription complete. Summary: {results}")
    return f"Bulk subscription task finished. Summary: {results}"