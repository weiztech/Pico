import os
import traceback
import json
import time
from typing import Dict, Optional, List
from django.utils import timezone
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from langchain_core.language_models.base import BaseLanguageModel
from langchain_google_genai import ChatGoogleGenerativeAI

from lit_reviews.models import ClinicalLiteratureAppraisal, AppraisalExtractionField
from lit_reviews.models import (
    ClinicalLiteratureAppraisal, 
    AppraisalExtractionField,
    ArticleReview,
    ExclusionReason,
)

import tempfile
import urllib.request
from backend.logger import logger
from accounts.models import Subscription
from lit_reviews.helpers.extraction_fields import add_extraction_ai_prompt
from lit_reviews.helpers.articles import get_or_create_appraisal_extraction_fields
from accounts.models import User

# Our package's main entry points
try:
    from citemed_ai import OrchestrationService, ExtractionService

except ImportError as e:
    logger.warning(f"Critical Import Error: Failed to import 'citemed_ai'. Please ensure it's installed correctly.")
    logger.warning(f"Original error: {e}")


def initialize_llm(config: Dict) -> Optional[BaseLanguageModel]:
    """Initialize LangChain LLM based on configuration."""
    config_id = config.get("config_id", "Unknown")
    provider_id = config.get("provider_id", "").lower()
    init_args = config.get("init_args", {})

    if provider_id != "google":
        logger.error(f"Unsupported provider_id: {provider_id}")
        return None

    try:
        # We'll use Gemini for this demo
        llm = ChatGoogleGenerativeAI(
            model=init_args.get("model"),
            temperature=init_args.get("temperature"), # Low temperature for consistent, predictable output
            google_api_key=init_args.get("google_api_key")
        )
        logger.info("Gemini LLM instance created successfully.")
        
        return llm 
    
    except Exception as e:
        logger.error(f"Failed to initialize LLM. Please check your API key. Error: {e}")


def get_ai_config(api_key: str) -> List[Dict]:
    """Get AI model configuration."""
    return [{
        "config_id": "gemini_flash_",
        "provider_id": "google",
        "init_args": {
            "model": "gemini-2.0-flash-lite",
            "google_api_key": api_key,
            "temperature": 0.0,
        }
    }]

def process_extraction(extraction_service: ExtractionService, pdf_path: str, fields_to_use: Dict, config_id: str) -> Dict:
    """Process PDF extraction with error handling."""
    try:
        start_time = time.time()
        results = extraction_service.extract_from_pdf(pdf_path=pdf_path, fields=fields_to_use)
        # results = processor.process_files(pdf_path, fields_to_use, output_dir=None)
        duration = time.time() - start_time
        successful_items = sum(1 for res in results.values() if res and "__error__" not in res)
        failed_items = len(results or {}) - successful_items

        logger.info("AI Suggestions is completed successfully")
        logger.info(results)
        
        return {
            "config_id": config_id,
            "section": "Extraction",
            "status": "COMPLETED" if failed_items == 0 else "COMPLETED_W_FAILURES",
            "success": successful_items,
            "failed": failed_items,
            "duration_seconds": round(duration, 2),
            "results": results
        }
    except Exception as e:
        logger.error(f"Processing failed for {config_id}: {str(e)}")
        return {
            "config_id": config_id,
            "status": "PROCESSING_FAILED",
            "error": str(e)
        }

def appraisal_ai_extraction_generation(appraisal_id: int, user_id: int) -> List[Dict]:
    """Process a clinical literature appraisal using AI extraction."""
    try:
        # Get appraisal data
        appraisal = ClinicalLiteratureAppraisal.objects.get(id=appraisal_id)

        # create extraction fields if any missing for this appraisal 
        lit_review = appraisal.article_review.search.literature_review
        extraction_fields = lit_review.extraction_fields.all()

        for extraction_field in extraction_fields:
            # create extraction fields if any is missing 
            get_or_create_appraisal_extraction_fields(appraisal, extraction_field, only_default=False)

        # Update AI status to running
        update_appraisal_ai_status(appraisal_id, 'running')

        extraction_fields = AppraisalExtractionField.objects.filter(
            clinical_appraisal=appraisal
        ).select_related('extraction_field')
        

        # Prepare fields
        fields_to_use = {}
        for field in extraction_fields:
            prompt = field.extraction_field.ai_prompte
            if not prompt:
                prompt = add_extraction_ai_prompt(field.extraction_field)
            fields_to_use[field.extraction_field.name] = prompt 

        # Get the absolute file system path of the PDF
        
        if appraisal.article_review.article.full_text:
            s3_url = appraisal.article_review.article.full_text.url
            # Create temp file with .pdf extension
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
                urllib.request.urlretrieve(s3_url, tmp_file.name)
            pdf_path = tmp_file.name
            logger.info(f"Processing appraisal {appraisal_id} with temp PDF path: {pdf_path}")
        else:
            logger.error("No PDF file attached to the article")
            return [{"status": "PDF_NOT_FOUND"}]
        

        # Initialize and run AI
        api_key = os.getenv("GOOGLE_API_KEY")
        ai_config = get_ai_config(api_key)[0]
        llm = initialize_llm(ai_config)
        if not llm:
            return [{"status": "LLM_INIT_FAILED"}]
        
        # Now, we pass the initialized LLM into our main service.
        extraction_service = ExtractionService(llm_instance=llm)

        result = process_extraction(
            extraction_service=extraction_service,
            pdf_path=pdf_path,
            fields_to_use=fields_to_use,
            config_id=ai_config["config_id"]
        )
        logger.info(f"AI extraction results for appraisal {appraisal_id}: {json.dumps(result, indent=2)}")
        # Save the results to the database
        save_status = save_ai_results(appraisal_id, [result], user_id)
        
        # Clean up temporary file
        if os.path.exists(pdf_path):
            os.unlink(pdf_path)

        return [{**result, "save_status": save_status}]

    except ClinicalLiteratureAppraisal.DoesNotExist:
        logger.error(f"Appraisal with ID {appraisal_id} not found")
        return [{"status": "APPRAISAL_NOT_FOUND"}]
    

    except Exception as e:
        # Set AI status to failed
        update_appraisal_ai_status(appraisal_id, 'failed')

        logger.error(f"Error processing appraisal {appraisal_id}: {str(e)}")
        logger.error(str(traceback.format_exc()))
        return [{"status": "ERROR", "error": str(e)}]


def save_ai_results(appraisal_id: int, results: List[Dict], user_id:int=None) -> Dict:
    """Save AI extraction results to AppraisalExtractionField instances."""
    try:
        extraction_fields = AppraisalExtractionField.objects.filter(
            clinical_appraisal_id=appraisal_id
        ).select_related('extraction_field')
        
        updated_count = 0
        failed_count = 0
        simplified_count = 0
        
        # Initialize the processor for simplification
        api_key = os.getenv("GOOGLE_API_KEY")
        ai_config = get_ai_config(api_key)[0]
        llm = initialize_llm(ai_config)
        
        # Now, we pass the initialized LLM into our main service.
        extraction_service = ExtractionService(llm_instance=llm)
        
        # Get the list of extraction field sections
        # You'll need to filter fields from extraction_fields section
        extraction_section_fields = extraction_fields.filter(
            extraction_field__field_section='EF'
        )
        
        # Create a set of field names from extraction section for easy lookup
        extraction_section_field_names = {
            field.extraction_field.name.lower() for field in extraction_section_fields
        }
        
        logger.info(f"Fields to simplify: {extraction_section_field_names}")
        
        for result in results:
            if result.get('status') in ['COMPLETED', 'COMPLETED_W_FAILURES']:
                pdf_results = result.get('results')
                
                # Update each field with its AI prediction
                for field in extraction_fields:
                    field_name = field.extraction_field.name.lower()
                    
                    # Try to find the corresponding result
                    ai_value = pdf_results.get(field_name)
                    if ai_value:
                        try:
                            # Skip if there's an error
                            if isinstance(ai_value, dict) and '__error__' in ai_value:
                                logger.warning(
                                    f"Error in AI prediction for field {field_name}: {ai_value['__error__']}"
                                )
                                failed_count += 1
                                continue
                            
                            # Update the field
                            field.ai_value = str(ai_value)
                            field.ai_value_status = 'not_reviewed'
                            
                            # Apply simplification only for extraction fields
                            if extraction_service and field_name in extraction_section_field_names and ai_value != "Not Found":
                                try:
                                    logger.info(f"Simplifying extraction field {field_name} for appraisal {appraisal_id}")
                                    simplified_value = extraction_service.simplify_field(field_name, str(ai_value))
                                    field.ai_simplified_value = simplified_value
                                    simplified_count += 1
                                    logger.info(f"Simplified value for {field_name}: {simplified_value}")
                                except Exception as e:
                                    logger.error(f"Simplification failed for field {field_name}: {str(e)}")
                                    # Don't count as failure, just log
                            
                            field.save()
                            updated_count += 1
                            
                            logger.info(f"Updated field {field_name} with AI value: {ai_value}")
                            
                        except Exception as e:
                            logger.error(f"Error saving AI value for field {field_name}: {str(e)}")
                            failed_count += 1
                    else:
                        logger.warning(f"No AI value found for field {field_name}")
                        failed_count += 1
        
        # Update the appraisal status
        appraisal = ClinicalLiteratureAppraisal.objects.get(id=appraisal_id)
        appraisal.app_status = 'In Progress'

        # Set AI status based on success/failure
        update_appraisal_ai_status(appraisal_id, 'completed', user_id)

        return {
            "status": "SUCCESS",
            "updated_fields": updated_count,
            "simplified_fields": simplified_count,
            "failed_fields": failed_count
        }
                
    except Exception as e:
        logger.error(f"Error saving AI results for appraisal {appraisal_id}: {str(e)}")
        logger.error(str(traceback.format_exc()))
        # Update AI status to failed
        update_appraisal_ai_status(appraisal_id, 'failed')
        return {
            "status": "ERROR",
            "error": str(e)
        }

def appraisal_ai_extraction_generation_all(literature_review_id: int, user_id:int=None) -> Dict:
    """Process all clinical appraisals in a literature review that aren't complete."""
    from lit_reviews.models import ClinicalLiteratureAppraisal
    
    try:
        # Get all appraisals for this literature review that aren't complete
        # Use the literature_review_id property
        appraisals = ClinicalLiteratureAppraisal.objects.filter(
            article_review__search__literature_review_id=literature_review_id
        ).exclude(
            app_status='Complete' 
        )
        
        logger.info(f"Found {appraisals.count()} incomplete appraisals for literature review {literature_review_id}")
        
        results = []
        successful = 0
        failed = 0
        
        for appraisal in appraisals:
            try:
                # Skip appraisals without a PDF
                if not appraisal.article_review.article.full_text:
                    logger.warning(f"Skipping appraisal {appraisal.id} - no PDF available")
                    result = {
                        "appraisal_id": appraisal.id,
                        "status": "SKIPPED",
                        "reason": "No PDF available"
                    }
                    failed += 1
                else:
                    # Process this appraisal
                    logger.info(f"Processing appraisal {appraisal.id}")
                    appraisal_result = appraisal_ai_extraction_generation(appraisal.id, user_id)
                    
                    # Check if processing was successful
                    if any(r.get('status') in ['COMPLETED', 'COMPLETED_W_FAILURES'] for r in appraisal_result):
                        successful += 1
                        result = {
                            "appraisal_id": appraisal.id,
                            "status": "SUCCESS",
                            "details": appraisal_result
                        }
                    else:
                        failed += 1
                        result = {
                            "appraisal_id": appraisal.id,
                            "status": "FAILED",
                            "details": appraisal_result
                        }
                
                results.append(result)
                
            except Exception as e:
                logger.error(f"Error processing appraisal {appraisal.id}: {str(e)}")
                results.append({
                    "appraisal_id": appraisal.id,
                    "status": "ERROR",
                    "error": str(e)
                })
                failed += 1
        
        return {
            "literature_review_id": literature_review_id,
            "total_processed": len(results),
            "successful": successful,
            "failed": failed,
            "results": results
        }
        
    except Exception as e:
        logger.error(f"Error processing appraisals for literature review {literature_review_id}: {str(e)}")
        return {
            "literature_review_id": literature_review_id,
            "status": "ERROR",
            "error": str(e)
        }

def update_appraisal_ai_status(appraisal_id: int, ai_status: str, user_id:int=None) -> Dict:
    """
    Update the AI generation status of a clinical literature appraisal.
    
    Args:
        appraisal_id: ID of the appraisal to update
        ai_status: AI generation status ('not_started', 'running', 'completed', 'failed')
        
    Returns:
        Dict with status information
    """
    from lit_reviews.tasks import deduct_remaining_license_credits_task

    try:
        appraisal = ClinicalLiteratureAppraisal.objects.get(id=appraisal_id)
        
        # Update AI status
        appraisal.ai_generation_status = ai_status
        appraisal.ai_last_processed_at = timezone.now()
        appraisal.save()

        if user_id:
            user = User.objects.get(id=user_id)
            user_licence = Subscription.objects.filter(user=user).first()
            is_credit_license = user_licence and user_licence.licence_type == "credits"
            # deduct credit
            if ai_status == 'completed' and is_credit_license:
                deduct_remaining_license_credits_task.delay(user.id, 1)
        else:
            logger.warning("AI status update couldn't track user because User is None")
        
        logger.info(f"Appraisal {appraisal_id} AI status updated to '{ai_status}'")
        

        # Send notification for failure and success
        if ai_status == "failed":
            lit_review = appraisal.article_review.search.literature_review
            channel_layer = get_channel_layer()
            room_name = f"review-room-{lit_review.id}"
            group_name = f"group_{room_name}"
            async_to_sync(channel_layer.group_send)(
                group_name,
                {
                    "type": "review_second_pass_ai_fields_completed",
                    "message": {
                        "appraisal_id": appraisal_id,
                        "text": "AI Suggestion for the appraissal extraction fields failed!"
                    },
                }
            )

        elif ai_status == "completed":
            lit_review = appraisal.article_review.search.literature_review
            channel_layer = get_channel_layer()
            room_name = f"review-room-{lit_review.id}"
            group_name = f"group_{room_name}"
            async_to_sync(channel_layer.group_send)(
                group_name,
                {
                    "type": "review_second_pass_ai_fields_completed",
                    "message": {
                        "appraisal_id": appraisal_id,
                        "text": "AI Suggestion for the appraissal extraction fields is completed successfully."
                    },
                }
            )

        return {
            "status": "SUCCESS",
            "message": f"Appraisal {appraisal_id} AI status updated successfully"
        }
        
    except ClinicalLiteratureAppraisal.DoesNotExist:
        logger.error(f"Appraisal with ID {appraisal_id} not found")
        return {
            "status": "ERROR",
            "error": "Appraisal not found"
        }
    except Exception as e:
        logger.error(f"Error updating AI status for appraisal {appraisal_id}: {str(e)}")
        return {
            "status": "ERROR",
            "error": str(e)
        }


def ai_suggest_first_pass_proccessing(article_review):
    """
    Provided an article review ID suggest whether the article should be:
    included or excluded
    """
    from lit_reviews.api.articles.serializers import ArticleReviewSerializer 

    search = article_review.search 
    literature_review = search.literature_review 

    # Initialize and run AI
    api_key = os.getenv("GOOGLE_API_KEY")
    ai_config = get_ai_config(api_key)[0]
    llm = initialize_llm(ai_config)
    # Now, we pass the initialized LLM into our main service.
    orchestrator = None
    if llm:
        try:
            # The OrchestrationService is the main, high-level entry point.
            orchestrator = OrchestrationService(llm_instance=llm)
            logger.info("OrchestrationService initialized successfully.")

        except Exception as e:
            logger.error(f"Failed to initialize OrchestrationService: {e}")
            return
    else:
        logger.error("LLM not initialized, skipping service setup.")
        return
    
    protocol = literature_review.searchprotocol
    device_context = {
        "device_name": literature_review.device.name,
        "review_info": {
            "Device Description": protocol.device_description,
            "Device Intended Purpose": protocol.intended_use,
            "State of the Art Description": protocol.sota_description
        }
    }

    # The pre-defined list of reasons for exclusion.
    # The format is a list of (ID, Reason Text) tuples.
    exclusion_reasons = ExclusionReason.objects.filter(literature_review=literature_review)
    exclusion_reasons = [(reason_obj.id, reason_obj.reason) for reason_obj in exclusion_reasons]

    # The abstract text to be analyzed.
    # This example is an animal study, so we expect it to be excluded with reason #3.
    abstract_to_screen = article_review.article.abstract
    logger.debug("\nRunning screen_abstract...")
    start_time = time.time()

    decision = orchestrator.screen_abstract(
        abstract_text=abstract_to_screen,
        device_name=device_context["device_name"],
        review_info=device_context["review_info"],
        exclusion_criteria=exclusion_reasons
    )

    duration = time.time() - start_time
    logger.debug(f"Screening completed in {duration:.2f} seconds.")
    
    if decision:
        # Example of how to use the result in your application:
        exclusion_decision = decision.get("decision_status")
        if exclusion_decision == "Excluded":
            exclusion_reason = decision.get('exclusion_reason_text')
            article_review.ai_state_decision = "E"
            article_review.ai_exclusion_reason = exclusion_reason
        else:
            article_review.ai_state_decision = "I"

        article_review.save()
        logger.success(f"\nAI suggested article review with ID {article_review.id} to be marked as {exclusion_decision}.")
    else:
        logger.error("\nThe screening process failed to return a decision. Check logs for details.")

    lit_review = article_review.search.literature_review
    channel_layer = get_channel_layer()
    room_name = f"review-room-{lit_review.id}"
    group_name = f"group_{room_name}"
    serializer = ArticleReviewSerializer(article_review)
    async_to_sync(channel_layer.group_send)(
        group_name,
        {
            "type": "article_review_ai_suggestions_completed",
            "message": {
                "article_review_id": article_review.id,
                "article_review": serializer.data,
                "text": "AI Suggestion for 1st pass proccessing completed successfully for the relevent article review."
            },
        }
    )

