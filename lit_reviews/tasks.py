from celery import shared_task
from lit_reviews.helpers.articles import check_full_article_link
from lit_reviews.models import (
    LiteratureReview,
    ArticleReview,
    ClinicalLiteratureAppraisal,
    LiteratureSearch,
    SearchProtocol
)
from lit_reviews.helpers.project import clone_project, import_project_backup
from lit_reviews.database_imports.utils import parse_one_off_ris
from lit_reviews.helpers.articles import remove_duplicate, retained_articles
from django.contrib.auth import get_user_model
from actstream import action
from backend.settings import CELERY_DEDUPLICATION_QUEUE
from backend.logger import logger
from backend.celery import app
from lit_reviews.celery_tasks import (
    emails, 
    searches, 
    articles, 
    reports, 
    projects, 
    scrapers,
    generics
)
from lit_reviews.helpers.ai import (
    appraisal_ai_extraction_generation_all, 
    appraisal_ai_extraction_generation
)

User = get_user_model()


@shared_task()
def send_email_when_comment_created(lit_review_id, comment_id, domain_name):
    return emails.send_email_when_comment_created_task(lit_review_id, comment_id, domain_name)
    

@app.task(queue=CELERY_DEDUPLICATION_QUEUE)
def remove_duplicate_async(lit_review_id, lit_search_id=None, default_dups=None):
    duplicate_articles = remove_duplicate(lit_review_id)
    if default_dups:
        duplicate_articles = duplicate_articles + default_dups
    if lit_search_id:
        lit_search = LiteratureSearch.objects.get(id=lit_search_id)
        lit_search.duplicate_articles = duplicate_articles
        lit_search.save()
    

@shared_task
def parse_one_off_ris_async(file_path, lit_review_id, search_id, is_retained=False):
    return parse_one_off_ris(file_path, lit_review_id, search_id, is_retained)


@app.task(queue=CELERY_DEDUPLICATION_QUEUE)
def retain_articles_async(lit_search_id):
    return retained_articles(lit_search_id)


@shared_task
def run_single_search(lit_search_id, expected_result_count=None, user_id=None):
    return searches.run_single_search_task(lit_search_id, expected_result_count, user_id)


@shared_task
def process_single_prop_async(prop_id, batch_size=200):
    return searches.process_single_prop_task(prop_id, batch_size)


@shared_task
def process_props_async(review_id, batch_size=100):
    return searches.process_props_task(review_id, batch_size)


@shared_task
def state_change_task_async(id, selected_state, user_id):
    return articles.state_change_task(id, selected_state, user_id)


@shared_task
def bulk_article_review_update_async(lit_review_id, review_ids, state, note, exclusion_reason, exclusion_comment, tag_ids, user_id=None):
    return articles.bulk_article_review_update_task(lit_review_id, review_ids, state, note, exclusion_reason, exclusion_comment, tag_ids, user_id)


@shared_task
def build_protocol(review_id, is_simple=False):
    return reports.build_protocol_task(review_id, is_simple)


@shared_task
def build_report(review_id, is_simple=False):
    return reports.build_report_task(review_id, is_simple)


@shared_task
def build_abbott_report(review_id):
    return reports.build_abbott_report_task(review_id)


@shared_task
def build_prisma(review_id):
    return reports.build_prisma_task(review_id)


@shared_task
def build_second_pass_word_report(review_id):
    return reports.build_second_pass_word_report_task(review_id)


@shared_task
def export_article_reviews_ris_report(review_id):
    return reports.export_article_reviews_ris_report_task(review_id)


@shared_task
def generate_ae_report(review_id):
    reports.generate_ae_report_task(review_id)


@shared_task
def generate_search_term_report(search_id):
    return reports.generate_search_term_report_task(search_id)


@shared_task
def generate_fulltext_zip_async(id, user_id=None):
    return reports.generate_fulltext_zip_report_task(id, user_id)


## For Creating duplicate/test projects from existing projects.
@shared_task
def new_test_project(project_name="Trial Project", projectid_to_copy=None, device_name=None):
    return projects.create_new_test_project_task(project_name, projectid_to_copy, device_name)


@shared_task
def create_living_reviews_projects_async():
    return projects.create_living_reviews_projects_task()


@shared_task
def generate_search_zip(review_id):
    return reports.generate_search_zip_report_task(review_id)


@shared_task
def generate_search_terms_summary(litreview_id):
    return reports.generate_search_terms_summary_report_task(litreview_id)
        

def process_abstract_kw(abstract, literature_review_id, article_kws=None):
    return articles.process_abstract_kw_task(abstract, literature_review_id, article_kws)


@shared_task
def process_abstract_text(literature_review_id, review_id=None):
    return articles.process_abstract_text_task(literature_review_id, review_id)


@shared_task 
def validate_search_terms_async(lit_review_id):
    return searches.validate_search_terms_task(lit_review_id)


@shared_task 
def search_clear_results_async(lit_review_id, searches_ids):
    return searches.search_clear_results_task(lit_review_id, searches_ids)
    

@shared_task 
def fetch_preview_and_expected_results(term, lit_review_id, user_id=None):
    return scrapers.fetch_preview_and_expected_results(term, lit_review_id, user_id)


@shared_task
def generate_appendix_e2_report(review_id):
    return reports.generate_appendix_e2_report_task(review_id)


@shared_task
def run_auto_search(lit_review_id, lit_search_id, user_id=None, preview=None):
    return scrapers.run_auto_search_task(lit_review_id, lit_search_id, user_id, preview)
    

@shared_task
def send_error_email(report, project, client_name, client_email, error_track):
    return emails.send_error_email_task(report, project, client_name, client_email, error_track)


@shared_task
def send_email(subject, message, to=[], link=None, is_error=False ,error="", from_email=None):
    return emails.send_email_task(subject, message, to, link, is_error, error, from_email)


@shared_task
def export_2nd_pass_extraction_articles(review_id):
    return reports.export_2nd_pass_extraction_articles_task(review_id)


@shared_task
def export_2nd_pass_extraction_articles_ris(review_id):
    return reports.export_2nd_pass_extraction_articles_ris_task(review_id)


@shared_task
def generate_search_terms_summary_excel(review_id):
    return reports.generate_search_terms_summary_excel_report_task(review_id)


@shared_task
def generate_appendix_e2_report_excel(review_id):
    return reports.generate_appendix_e2_report_excel_task(review_id)
    

@shared_task
def export_article_reviews(review_id):
    return reports.export_article_reviews_report_task(review_id)


@shared_task
def generate_condense_report(review_id):
    return reports.generate_condense_report_task(review_id)


@shared_task
def generate_duplicates_report(review_id):
    return reports.generate_duplicates_report_task(review_id)


@shared_task
def generate_audit_tracking_logs_report(review_id):
    return reports.generate_audit_tracking_logs_report_task(review_id)


@shared_task
def generate_device_history_report(review_id, user_id):
    return reports.generate_device_history_report_task(review_id, user_id)


@shared_task
def generate_cumulative_report(review_id, user_id):
    return reports.generate_cumulative_report_task(review_id, user_id)


@shared_task()
def send_scrapers_report():
    return scrapers.send_scrapers_report_task()



@shared_task
def check_full_article_link_async(article_id, article_review_id, user_id):
    return check_full_article_link(article_id, article_review_id, user_id)


@shared_task
def recalculate_second_pass_appraisals_status_task(lit_review_id):
    articles.recalculate_second_pass_appraisals_status_task(lit_review_id)


@shared_task
def import_project_backup_task(dump_file_aws_key, client_name):
    return import_project_backup(dump_file_aws_key, client_name)


@shared_task
def deduct_remaining_license_credits_task(user_id, deducted_credits):
    return articles.deduct_remaining_license_credits(user_id, deducted_credits)


@shared_task
def clone_project_task(copied_project_lit_review__id, literature_review__id):
    copied_project_lit_review = LiteratureReview.objects.get(id=copied_project_lit_review__id)
    literature_review = LiteratureReview.objects.get(id=literature_review__id)
    return clone_project(copied_project_lit_review, literature_review)


@shared_task
def async_log_action_article_review_modified(user, verb, description, action_id, target_object_id):
    user = User.objects.get(pk=user)
    action_object = ArticleReview.objects.get(pk=action_id)
    target_object = LiteratureReview.objects.get(pk=target_object_id)
    action.send(user, verb=verb, description=description, action_object=action_object, target=target_object)


@shared_task
def async_log_action_article_review_deleted(user, verb, description, target_object_id):
    user = User.objects.get(pk=user)
    target_object = LiteratureReview.objects.get(pk=target_object_id)
    action.send(user, verb=verb, description=description, target=target_object)

@shared_task
def async_log_action_clinical_literature_appraisal_created(user, verb, description, action_id, target_object_id):
    user = User.objects.get(pk=user)
    action_object = ClinicalLiteratureAppraisal.objects.get(pk=action_id)
    target_object = LiteratureReview.objects.get(pk=target_object_id)
    action.send(user, verb=verb, description=description, action_object=action_object, target=target_object)

@shared_task
def async_log_action_clinical_literature_appraisal_modified(user, verb, description, action_id, target_object_id):
    user = User.objects.get(pk=user)
    action_object = ClinicalLiteratureAppraisal.objects.get(pk=action_id)
    target_object = LiteratureReview.objects.get(pk=target_object_id)
    action.send(user, verb=verb, description=description, action_object=action_object, target=target_object)

@shared_task
def async_log_action_clinical_literature_appraisal_deleted(user, verb, description, target_object_id):
    user = User.objects.get(pk=user)
    target_object = LiteratureReview.objects.get(pk=target_object_id)
    action.send(user, verb=verb, description=description, target=target_object)



@shared_task
def async_log_action_literature_review_created(user, verb, description, action_id):
    user = User.objects.get(pk=user)
    action_object = LiteratureReview.objects.get(pk=action_id)
    action.send(user, verb=verb, description=description, action_object=action_object, target=action_object, public=False)
    

@shared_task
def async_log_action_literature_review_modified(user, verb, description, action_id):
    user = User.objects.get(pk=user)
    action_object = LiteratureReview.objects.get(pk=action_id)
    action.send(user, verb=verb, description=description, action_object=action_object, target=action_object, public=True)


@shared_task
def async_log_action_literature_review_deleted(user, verb, description):
    user = User.objects.get(pk=user)
    action.send(user, verb=verb, description=description, public=False)


@shared_task
def async_log_action_literature_search_created(user, verb, description, action_id, target_object_id):
    user = User.objects.get(pk=user)
    action_object = LiteratureSearch.objects.get(pk=action_id)
    target_object = LiteratureReview.objects.get(pk=target_object_id)

    action.send(user, verb=verb, description=description, action_object=action_object, target=target_object)
    

@shared_task
def async_log_action_literature_search_deleted(user, verb, description,target_object_id):
    user = User.objects.get(pk=user)
    target_object = LiteratureReview.objects.get(pk=target_object_id)
    action.send(user, verb=verb, description=description, target=target_object)


@shared_task
def async_log_action_search_protocol_modified(user, verb, description, action_id, target_object_id):
    logger.info("Will verb: {}", verb)
    user = User.objects.get(pk=user)
    action_object = SearchProtocol.objects.get(pk=action_id)
    target_object = LiteratureReview.objects.get(pk=target_object_id)
    action.send(user, verb=verb, description=description, action_object=action_object, target=target_object)


@shared_task
def async_log_action_db_modification(user_id, verb, description, action_id, target_object_id):
    try:
        user = User.objects.get(pk=user_id)
        action_object = SearchProtocol.objects.get(pk=action_id)
        target_object = LiteratureReview.objects.get(pk=target_object_id)
        action.send(user, verb=verb, description=description, action_object=action_object, target=target_object)
    except Exception as e:
        logger.error(f"Error logging database modification action: {e}")


@shared_task
def async_log_action_literature_search_results(user, verb, description, action_id, target_object_id):
    user = User.objects.get(pk=user)
    action_object = LiteratureSearch.objects.get(pk=action_id)
    target_object = LiteratureReview.objects.get(pk=target_object_id)
    
    action.send(user, verb=verb, description=description, action_object=action_object, target=target_object)


@shared_task
def appraisal_ai_extraction_generation_all_async(literature_review_id, user_id):
    appraisal_ai_extraction_generation_all(literature_review_id, user_id)


@shared_task
def appraisal_ai_extraction_generation_async(appraisal_id, user_id):
    appraisal_ai_extraction_generation(appraisal_id, user_id)

    
@shared_task()
def delete_temp_files_async():
    return generics.delete_temp_files_task()
    

@shared_task 
def generate_ai_suggestionss_first_pass_async(article_review_ids, sorting):
    return articles.generate_ai_suggestionss_first_pass_task(article_review_ids, sorting)


@shared_task()
def calculate_clinical_appraisal_status_async(appraisal_id):
    return articles.calculate_clinical_appraisal_status_task(appraisal_id)


@shared_task
def generate_highlighted_pdf_async(review_id, article_id):
    return articles.generate_highlighted_pdf_task(review_id, article_id)


@shared_task
def create_sample_project_on_register_async(user_id):
    return projects.create_sample_project_on_register_task(user_id)


def process_article_review_device_mentions_async(review_id):
    return generics.process_article_review_device_mentions_task(review_id)

