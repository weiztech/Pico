import uuid
from datetime import datetime, timedelta

from backend import settings
from backend.logger import logger
from lit_reviews.models import (
    LiteratureReview,
    SearchProtocol,
    LivingReview,
    LiteratureSearch,
    AdverseEventReview,
    AdverseRecallReview,
    LiteratureReviewSearchProposal,
    ExtractionField,
    ArticleReview,
    ClinicalLiteratureAppraisal,
    KeyWord,
    AppraisalExtractionField,
    CustomKeyWord,
    ExclusionReason,
    FinallReportJob,
    AdversDatabaseSummary,
    SearchTermsPropsSummaryReport,
    SearchConfiguration,
    SearchParameter,
    NCBIDatabase,
)
from django.contrib.auth import get_user_model


User = get_user_model()

## For Creating duplicate/test projects from existing projects.
def create_new_test_project_task(project_name="Trial Project", projectid_to_copy=None, device_name=None):
    from client_portal.models import Project
    
    ## create new literature review object
    lit_review = LiteratureReview.objects.get(id=projectid_to_copy)
    
    new_client = lit_review.client
    new_client.name = "Trial Project {0}".format(str(uuid.uuid1()))
    new_client.pk = None
    new_client.save()
    
    new_device = lit_review.device
    new_device.pk = None
    if device_name:
        new_device.name = device_name
    new_device.save()
    
    target_lit_review = LiteratureReview.objects.get(id=projectid_to_copy)

    lit_review.pk= None
    lit_review.client = new_client
    lit_review.device = new_device
    lit_review.save()  ## now we have a clone. 

    # create test project object for the cloned lit review
    project = Project.objects.filter(lit_review = target_lit_review).first()
    if project:
        project_name = str(project.project_name) + ' Trial Project'
        project.project_name = project_name 
        project.id = None 
        project.lit_review = lit_review
        project.save()
        test_project = project

    # search protocol page

    old_searchprotocol = SearchProtocol.objects.filter(literature_review = target_lit_review).first()
    # delete the defualt protocol
    SearchProtocol.objects.filter(literature_review = lit_review).delete()
    new_searchprotocol = old_searchprotocol
    original_s_protocol_id = old_searchprotocol.id
    new_searchprotocol.id = None
    new_searchprotocol.literature_review = lit_review
    new_searchprotocol.save()

    original_s_protocol = SearchProtocol.objects.get(id=original_s_protocol_id)
    for db in original_s_protocol.lit_searches_databases_to_search.all():
        new_searchprotocol.lit_searches_databases_to_search.add(db)
    for db in original_s_protocol.ae_databases_to_search.all():
        new_searchprotocol.ae_databases_to_search.add(db)
    
    new_searchprotocol.save()

    # search Terms page

    # ## TODO modify the name of the project = parameters
    db = NCBIDatabase.objects.get(entrez_enum='pubmed')

    ## create  LiteatureSearch Object
    lit_searches = LiteratureSearch.objects.filter(literature_review=target_lit_review).all()
    for lit_search in lit_searches:
        ae_reviews = AdverseEventReview.objects.filter(search=lit_search)
        recalls = AdverseRecallReview.objects.filter(search=lit_search)

        lit_search.literature_review = lit_review
        # lit_search.import_status = "NOT RUN"
        lit_search.pk = None
        lit_search.save()

        ## copy all related AdverseEventReview && AdverseRecallReview
        for ae in ae_reviews:
            new_ae = ae.ae
            new_ae.pk = None 
            new_ae.save()
            ae.ae = new_ae
            ae.search = lit_search
            ae.pk = None 
            ae.save()


        for recall in recalls:
            new_recall_ae = recall.ae
            new_recall_ae.pk = None 
            new_recall_ae.save()
            recall.ae = new_recall_ae
            recall.search = lit_search
            recall.pk = None 
            recall.save()

    ## create LiteratureReviewSearchProposal objects 
    proposals = LiteratureReviewSearchProposal.objects.filter(literature_review=target_lit_review)
    for proposal in proposals:
        try:
            duplicate_search = LiteratureSearch.objects.get(
                term=proposal.term,
                literature_review=lit_review,
                db=proposal.db,
            )
            proposal.literature_search = duplicate_search
            proposal.literature_review = lit_review
            proposal.pk = None
            proposal.save()
        except:
            logger.error("Search not found for: " + proposal.term)
            pass 


    # ExtractionField
    extractions = ExtractionField.objects.filter(literature_review=target_lit_review)
    for field in extractions:
        if not ExtractionField.objects.filter(literature_review=lit_review, name=field.name).exists():
            field.literature_review = lit_review
            field.pk = None
            field.save()

    ## find project to copy (which id?)
    ## loop through all ArticleReview objects of target project
    ars = ArticleReview.objects.filter(search__literature_review=target_lit_review)

    ## for each, create new ArticleReview with same data, except the SearchObject is the new one.
    for article_review in ars:
        target_appraisal = ClinicalLiteratureAppraisal.objects.filter(article_review=article_review).first()
        logger.debug("target appraisal: {0}".format(target_appraisal))

        article_review.search = lit_search
        article_review.pk = None
        article_review.save()
        article_review.status = 'U'
        article_review.exclusion_reason = None
        article_review.save()
    
        # add apparsials
        if target_appraisal:
            # delete the defualt created one
            old_clinical_lit = ClinicalLiteratureAppraisal.objects.filter(article_review=article_review).first()
            if old_clinical_lit:
                old_clinical_lit.delete()
            # duplicate the target one
            clinical_app_extraction_fields = AppraisalExtractionField.objects.filter(clinical_appraisal=target_appraisal)
            target_appraisal.pk = None
            target_appraisal.article_review = article_review
            target_appraisal.save()
            
            for field in clinical_app_extraction_fields:
                if field.extraction_field:
                    field.pk = None 
                    field.clinical_appraisal = target_appraisal
                    duplicate_extraction_field = ExtractionField.objects.get(
                        literature_review=lit_review,
                        name=field.extraction_field.name,
                    )
                    field.extraction_field = duplicate_extraction_field
                    field.save()

    # add all authorized users 
    for user in target_lit_review.authorized_users.all():
        lit_review.authorized_users.add(user)

    # copy all KeyWord
    kws = KeyWord.objects.filter(literature_review=target_lit_review)
    KeyWord.objects.filter(literature_review=lit_review).delete()
    for kw in kws:
        kw.literature_review = lit_review
        kw.pk = None 
        kw.save()
    custome_kws = CustomKeyWord.objects.filter(literature_review=target_lit_review)
    for kw in custome_kws:
        kw.literature_review = lit_review
        kw.pk = None 
        kw.save()

    # copy all ExclusionReason
    ExclusionReason.objects.filter(literature_review=lit_review).delete()
    ex_reasons = ExclusionReason.objects.filter(literature_review=target_lit_review)
    for reason in ex_reasons:
        reason.literature_review = lit_review
        reason.pk = None 
        reason.save()  

    # copy all FinallReportJob
    reports = FinallReportJob.objects.filter(literature_review=target_lit_review)
    for report in reports:
        report.literature_review = lit_review
        report.pk = None 
        report.save()  

    # copy all AdversDatabaseSummary
    summaries = AdversDatabaseSummary.objects.filter(literature_review=target_lit_review)
    for summary in summaries:
        summary.literature_review = lit_review
        summary.pk = None 
        summary.save() 

    # copy all SearchTermsPropsSummaryReport
    reports = SearchTermsPropsSummaryReport.objects.filter(literature_review=target_lit_review)
    for report in reports:
        report.literature_review = lit_review
        report.pk = None 
        report.save() 

    # duplicate default configs
    d_configs = SearchConfiguration.objects.filter(literature_review=lit_review)
    for d_config in d_configs:
        d_config.delete()

    # Search Terms Configurations
    configs = SearchConfiguration.objects.filter(literature_review=target_lit_review)
    for config in configs:
        original_config_id = config.id
        config.id = None
        config.literature_review = lit_review
        config.save()

        original_config = SearchConfiguration.objects.get(id=original_config_id)
        parameters = SearchParameter.objects.filter(search_config=original_config)
        for param in parameters:
            param.id = None 
            param.search_config = config
            param.save()


def create_living_reviews_projects_task():
    from lit_reviews.helpers.project import create_periodic_review, get_end_date_for_living_review_project

    living_reviews = LivingReview.objects.all()
    for living_item in living_reviews:
        living_projects = living_item.projects.all()
        if living_projects.count():
            latest_created_project = living_projects.order_by("searchprotocol__lit_start_date_of_search").last()
            start_date = latest_created_project.searchprotocol.lit_date_of_search # end date of previous run
            logger.debug(str(latest_created_project))
            start_date += timedelta(days=1)

            end_date = get_end_date_for_living_review_project(living_item, start_date)
            today = datetime.now()
            one_day_after_end_date = end_date + timedelta(days=1)

            periodic_project = LiteratureReview.objects.filter(parent_living_review=living_item, searchprotocol__lit_start_date_of_search=start_date)
            # create a living review project if it doesn't exists
            if today.date() == one_day_after_end_date and not periodic_project.exists():
                create_periodic_review(start_date, end_date, living_item, latest_created_project)
                

        else:
            today = datetime.now()
            start_date = living_item.start_date 

            while start_date < today.date():
                end_date = get_end_date_for_living_review_project(living_item, start_date)

                periodic_project = LiteratureReview.objects.filter(parent_living_review=living_item, searchprotocol__lit_start_date_of_search=start_date)
                # create a living review project if it doesn't exists
                if not periodic_project.exists() and today.date() > end_date:
                    create_periodic_review(start_date, end_date, living_item, living_item.project_protocol)
                
                start_date = end_date + timedelta(days=1)

                
def create_sample_project_on_register_task(user_id):
    from lit_reviews.tasks import clone_project_task
    from client_portal.models import Project
    
    user = User.objects.filter(id=user_id).first()
    if user:
        # check if user has any created projects
        if user.my_reviews().count() == 0 and user.client:
            copy_from_lit_id = settings.TEMPATE_PROJECT_ID if settings.TEMPATE_PROJECT_ID else 207
            literature_review_copied = LiteratureReview.objects.filter(id=copy_from_lit_id).first()
            literature_review = literature_review_copied
            literature_review.id = None
            literature_review.client = user.client 
            literature_review.save()

            literature_review_copied = LiteratureReview.objects.filter(id=copy_from_lit_id).first()
            Project.objects.create(
                project_name="INTRO 01",
                client=user.client,
                lit_review = literature_review
            )

            literature_review.cloned_from = literature_review_copied
            literature_review.is_cloning_completed = False
            literature_review.save()
            clone_project_task.delay(literature_review_copied.id, literature_review.id)

            return literature_review