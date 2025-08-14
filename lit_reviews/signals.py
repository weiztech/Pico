from django.db.models.signals import pre_save,post_save, pre_delete, post_delete
from django.dispatch import receiver
from django.db import transaction

from backend.logger import logger
from accounts.models import Subscription
from lit_reviews.models import (
    ClinicalLiteratureAppraisal,
    ArticleReview,
    ArticleReview,
    ClinicalLiteratureAppraisal,
    LiteratureReview,
    LiteratureSearch,
    SearchProtocol,
)
from lit_reviews.helpers.user import getCurrentUser


@receiver(pre_save, sender=ClinicalLiteratureAppraisal)
def update_clinical_appraisal_review_status(sender, instance, *args, **kwargs):
    instance.app_status = instance.status


@receiver(pre_save, sender=ArticleReview)
def article_review_modified(sender, instance, **kwargs):
    from .tasks import async_log_action_article_review_modified
    
    # Create Activity Action
    try:
        user = getCurrentUser()
        if not user:
            logger.warning("Article Review State Modified Action couldn't be created because User is None")
            return

        logger.debug(f"{user} User detected")

        # Check if the instance already exists (i.e., it's an update, not a creation)
        try:
            existing_instance = sender.objects.get(id=instance.id)
            old_state = existing_instance.get_state_display()
            new_state = instance.get_state_display()

            if old_state != new_state:
                verb='Article Review State Modified'
                literature_review_id = instance.literature_review_id
                if new_state == "Excluded":
                    exclusion_reason = instance.exclusion_reason
                    description = f'Article Review titled "{instance}" marked as "Excluded" with the the following reason: "{exclusion_reason}".'
                else:
                    description = f'Article Review titled "{instance}" marked as "{new_state}".'
                async_log_action_article_review_modified.delay(user.id, verb, description, instance.id, literature_review_id)
        
        except sender.DoesNotExist:
            # Instance is being created, not modified
            pass

    except Exception as e:
        logger.warning(f"Article Review State Modified Action couldn't be created because of an error: {e}")

    
    # Reduce The User's Credits if he does have a credit based subscription
    try:
        from lit_reviews.tasks import deduct_remaining_license_credits_task

        existing_instance = sender.objects.get(id=instance.id)
        old_state = existing_instance.state
        new_state = instance.state
        user = getCurrentUser()
        user_licence = Subscription.objects.filter(user=user).first()
        is_credit_license = user_licence and user_licence.licence_type == "credits"
        if old_state in ["U", "D"] and new_state not in ["U", "D"] and is_credit_license:
            # deduct from remaining credits
            deduct_remaining_license_credits_task.delay(user.id, 1)

    except sender.DoesNotExist:
        # Instance is being created, not modified
        pass
    

@receiver(post_delete, sender=ArticleReview)
def article_review_deleted(sender, instance, **kwargs):
    from .tasks import async_log_action_article_review_deleted
    
    try:
        user = getCurrentUser()
        if not user:
            logger.warning("Article Review Deleted Action couldn't be created because User is None")
            return

        logger.debug(f"{user} User detected")

        # Log the action asynchronously
        verb = 'Article Review Deleted'
        description = f'Article Review labeled "{instance}" with ID "#{instance.id}" was deleted.'
        literature_review_id = instance.literature_review_id

        async_log_action_article_review_deleted.delay(user.id, verb, description, literature_review_id)
        
    except Exception as e:
        logger.warning(f"Article Review Deleted Action couldn't be created because of an error: {e}")


@receiver(post_save, sender=ClinicalLiteratureAppraisal)
def clinical_literature_appraisal_created(sender, instance, created, **kwargs):
    from .tasks import async_log_action_clinical_literature_appraisal_created
    try:
        user = getCurrentUser()
        if not user:
            logger.warning("Clinical Literature Appraisal Created Action couldn't be created because User is None")
            return

        logger.debug(f"{user} User detected")

        if created:
            verb = 'Clinical Literature Appraisal Created'
            description = f'Clinical Literature Appraisal labeled "{instance}" with ID "#{instance.id}" was Created.'
            literature_review_id = instance.literature_review_id

            transaction.on_commit(
                lambda: async_log_action_clinical_literature_appraisal_created.delay(user.id, verb, description, instance.id, literature_review_id)
            )
            
    except Exception as e:
        logger.warning(f"Clinical Literature Appraisal Created Action couldn't be created because of an error: {e}")

        
@receiver(pre_save, sender=ClinicalLiteratureAppraisal)
def clinical_literature_appraisal_modified(sender, instance, **kwargs):
    from .tasks import async_log_action_clinical_literature_appraisal_modified
    try:
        user = getCurrentUser()
        if not user:
            logger.warning("Clinical Literature Appraisal Modified Action couldn't be created because User is None")
            return

        logger.debug(f"{user} User detected")

        try:
            verb = 'Clinical Literature Appraisal Modified'
            literature_review_id = instance.literature_review_id

            old_instance = sender.objects.get(id=instance.id)
            old_sota_article = old_instance.is_sota_article
            new_sota_article = instance.is_sota_article
            old_included = old_instance.included
            new_included = instance.included

            if old_sota_article != new_sota_article:
                if new_sota_article:
                    description = f'Article Review titled "{instance.article_review}" marked as "Sota Article".'
                else:
                    description = f'Article Review titled "{instance.article_review}" marked as "Excluded".'
                async_log_action_clinical_literature_appraisal_modified.delay(user.id, verb, description, instance.id, literature_review_id)

            if old_included != new_included:
                if new_included:
                    description = f'Article Review titled "{instance.article_review}" marked as "Included".'
                else:
                    description = f'Article Review titled "{instance.article_review}" marked as "Device Article".'
                async_log_action_clinical_literature_appraisal_modified.delay(user.id, verb, description, instance.id, literature_review_id)

        except sender.DoesNotExist:
            # Instance is being created, not modified, so do nothing
            pass

    except Exception as e:
        logger.warning(f"Clinical Literature Appraisal Modified Action couldn't be created because of an error: {e}")


@receiver(post_delete, sender=ClinicalLiteratureAppraisal)
def clinical_literature_appraisal_deleted(sender, instance, **kwargs):
    from .tasks import async_log_action_clinical_literature_appraisal_deleted
    try:
        user = getCurrentUser()
        if not user:
            logger.warning("Clinical Literature Appraisal Deleted Action couldn't be created because User is None")
            return

        logger.debug(f"{user} User detected")

        verb = 'Clinical Literature Appraisal Deleted'
        description = f'Clinical Literature Appraisal labeled "{instance}" with ID "#{instance.id}" was deleted.'
        literature_review_id = instance.literature_review_id

        # Log the action asynchronously
        async_log_action_clinical_literature_appraisal_deleted.delay(user.id, verb, description, literature_review_id)

    except Exception as e:
        logger.warning(f"Clinical Literature Appraisal Deleted Action couldn't be created because of an error: {e}")


@receiver(post_save, sender=LiteratureReview)
def literature_review_created(sender, instance, created, **kwargs):
    from .tasks import async_log_action_literature_review_created
    try:
        user = getCurrentUser()
        if not user:
            logger.warning("Literature Review Created Action couldn't be created because User is None")
            return

        logger.debug(f"{user} User detected")

        if created:
            verb = 'Literature Review Created'
            description = f'Literature Review labeled "{instance}" with ID "#{instance.id}" was Created.'

            transaction.on_commit(
                lambda: async_log_action_literature_review_created.delay(user.id, verb, description, instance.id)
            )

    except Exception as e:
        logger.warning(f"Literature Review Created Action couldn't be created because of an error: {e}")


@receiver(pre_save, sender=LiteratureReview)
def literature_review_modified(sender, instance, **kwargs):
    from .tasks import async_log_action_literature_review_modified
    try:
        user = getCurrentUser()
        if not user:
            logger.warning("Literature Review Modified Action couldn't be created because User is None")
            return

        logger.debug(f"{user} User detected")

        # Check if the instance already exists (i.e., it's an update, not a creation)
        try:
            existing_instance = sender.objects.get(id=instance.id)
            old_is_archived = existing_instance.is_archived
            new_is_archived = instance.is_archived

            if old_is_archived != new_is_archived:
                if new_is_archived:
                    verb = 'Literature Review Archived'
                    description = f'Literature Review titled "{instance}" with ID "#{instance.id}" was archived.'
                else:
                    verb = 'Literature Review Unarchived'
                    description = f'Literature Review titled "{instance}" with ID "#{instance.id}" was unarchived.'
                
                async_log_action_literature_review_modified.delay(user.id, verb, description, instance.id)
        
        except sender.DoesNotExist:
            # Instance is being created, not modified
            pass

    except Exception as e:
        logger.warning(f"Literature Review Modified Action couldn't be created because of an error: {e}")


@receiver(post_delete, sender=LiteratureReview)
def literature_review_deleted(sender, instance, **kwargs):
    from .tasks import async_log_action_literature_review_deleted
    try:
        user = getCurrentUser()
        if not user:
            logger.warning("Literature Review Deleted Action couldn't be created because User is None")
            return

        logger.debug(f"{user} User detected")

        verb = 'Literature Review Deleted'
        description = f'Literature Review labeled "{instance}" with ID "#{instance.id}" was deleted.'

        async_log_action_literature_review_deleted.delay(user.id, verb, description)

    except Exception as e:
        logger.warning(f"Literature Review Deleted Action couldn't be created because of an error: {e}")


@receiver(post_save, sender=LiteratureSearch)
def literature_search_created(sender, instance, created, **kwargs):
    from .tasks import async_log_action_literature_search_created
    try:
        user = getCurrentUser()
        if not user:
            logger.warning("Literature Search Created Action couldn't be created because User is None")
            return

        logger.debug(f"{user} User detected")

        literature_review_id = str(instance.literature_review.id)

        if created:
            verb = 'Literature Search Created'
            description = f'Literature Search labeled "{instance}" with ID "#{instance.id}" was created.'

            transaction.on_commit(
                lambda: async_log_action_literature_search_created.delay(user.id, verb, description, instance.id, literature_review_id)
            )

    except Exception as e:
        logger.warning(f"Literature Search Created Action couldn't be created because of an error: {e}")


@receiver(post_delete, sender=LiteratureSearch)
def literature_search_deleted(sender, instance, **kwargs):
    from .tasks import async_log_action_literature_search_deleted
    try:
        user = getCurrentUser()
        if not user:
            logger.warning("Literature Search Deleted Action couldn't be created because User is None")
            return

        logger.debug(f"{user} User detected")

        verb = 'Literature Search Deleted'
        description = f'Literature Search labeled "{instance}" with ID "#{instance.id}" was deleted.'
        lit_review = str(instance.literature_review.id)

        # Log the action asynchronously
        async_log_action_literature_search_deleted.delay(user.id, verb, description, lit_review)

    except Exception as e:
        logger.warning(f"Literature Search Deleted Action couldn't be created because of an error: {e}")


@receiver(pre_save, sender=SearchProtocol)
def search_protocol_modified(sender, instance, **kwargs):
    from .tasks import async_log_action_search_protocol_modified
    try:
        user = getCurrentUser()
        if not user:
            logger.warning("Search Protocol Modified Action couldn't be created because User is None")
            return

        logger.debug(f"{user} User detected")

        try:
            verb = 'Search Protocol Modified'
            literature_review_id = instance.literature_review_id

            old_instance = sender.objects.get(id=instance.id)

            # List to collect the changes
            modifications = []

            # Check each field for changes and log accordingly
            fields_to_check = [
                'device_description', 'intended_use', 'indication_of_use',
                'lit_date_of_search', 'ae_date_of_search',
                'lit_start_date_of_search', 'ae_start_date_of_search',
                'years_back', 'ae_years_back',
                'max_imported_search_results',
                'comparator_devices', 'sota_description', 'sota_product_name',
                'safety_claims', 'performance_claims', 'other_info',
                'scope', 'preparer',
            ]

            # Compare fields and log changes
            for field in fields_to_check:
                old_value = getattr(old_instance, field)
                new_value = getattr(instance, field)
                if old_value != new_value:
                    modifications.append(f'Field "{field}" changed from "{old_value}" to "{new_value}".')

            # Only log an action if there are modifications
            if modifications:
                # Join the modifications into a single description
                description = "Changes: " + "; ".join(modifications)

                # Log the action once with the list of all modifications
                async_log_action_search_protocol_modified.delay(
                    user.id, verb, description, instance.id, literature_review_id
                )

        except sender.DoesNotExist:
            # Instance is being created, not modified, so do nothing
            pass

    except Exception as e:
        logger.warning(f"Search Protocol Modified Action couldn't be created because of an error: {e}")

from django.db.models.signals import m2m_changed

@receiver(m2m_changed, sender=SearchProtocol.lit_searches_databases_to_search.through)
@receiver(m2m_changed, sender=SearchProtocol.ae_databases_to_search.through)
def databases_to_search_changed(sender, instance, action, reverse, model, pk_set, **kwargs):
    from .tasks import async_log_action_db_modification
    # Prepare lists to store changes
    changes = {
        'lit_added': [],
        'lit_removed': [],
        'ae_added': [],
        'ae_removed': [],
    }

    # Detect which field triggered the signal
    if sender == SearchProtocol.lit_searches_databases_to_search.through:
        field_type = 'lit'
    elif sender == SearchProtocol.ae_databases_to_search.through:
        field_type = 'ae'
    else:
        return  # Not one of the tracked fields

    if action == 'post_add':
        added_dbs = model.objects.filter(pk__in=pk_set)
        for db in added_dbs:
            if field_type == 'lit':
                changes['lit_added'].append(db.name)
            elif field_type == 'ae':
                changes['ae_added'].append(db.name)

    elif action == 'post_remove':
        removed_dbs = model.objects.filter(pk__in=pk_set)
        for db in removed_dbs:
            if field_type == 'lit':
                changes['lit_removed'].append(db.name)
            elif field_type == 'ae':
                changes['ae_removed'].append(db.name)

    # Combine all changes into one description
    description_parts = []
    if changes['lit_added']:
        description_parts.append(f'Added to Lit Searches Databases: {", ".join(changes["lit_added"])}.')
    if changes['lit_removed']:
        description_parts.append(f'Removed from Lit Searches Databases: {", ".join(changes["lit_removed"])}.')
    if changes['ae_added']:
        description_parts.append(f'Added to AE Searches Databases: {", ".join(changes["ae_added"])}.')
    if changes['ae_removed']:
        description_parts.append(f'Removed from AE Searches Databases: {", ".join(changes["ae_removed"])}.')

    # Log the action if there are any changes
    if description_parts:
        user = getCurrentUser()
        if user:
            verb = 'Search Protocol Database Modification'
            description = ' '.join(description_parts)
            async_log_action_db_modification.delay(user.id, verb, description, instance.id, instance.literature_review_id)
        else:
            logger.warning("Could not log database changes because User is None")