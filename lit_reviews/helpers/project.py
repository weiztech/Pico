import os
import json 
import traceback
import datetime 
import requests 
from dotenv import load_dotenv
from datetime import timedelta
from dateutil.relativedelta import relativedelta
from django.db.models.fields.files import FileField, ImageField
from lit_reviews.models import (
    ArticleReview,
    LiteratureReviewSearchProposal,
    LiteratureSearch,
    ExtractionField,
    SearchProtocol,
    ExclusionReason,
    KeyWord,
    CustomKeyWord,
    SearchConfiguration,
    SearchParameter,
    ClinicalLiteratureAppraisal,
    AppraisalExtractionField,
    LiteratureReview,
    Client,
    Manufacturer,
    Device,
    NCBIDatabase,
    Article,
    AdverseEvent,
    AdverseRecall,
    AdverseEventReview,
    AdverseRecallReview,
    AdversDatabaseSummary,
    FinallReportJob,
    ArticleTag,
)
from backend.logger import logger
from backend import settings
from django.forms.models import model_to_dict
from lit_reviews.helpers.generic import create_tmp_file
from decimal import Decimal
from django.core.files.base import ContentFile
from django.core.files import File
from lit_reviews.helpers.aws_s3 import generate_fetch_presigned_url, s3_direct_file_uplaod


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH_TO_DOT_ENV_FILE = os.path.join(BASE_DIR, ".env")
if os.path.exists(PATH_TO_DOT_ENV_FILE):
    load_dotenv(PATH_TO_DOT_ENV_FILE)
    logger.info(".env read successfully")
else:
    logger.warning(".env not found")
    
def custom_model_to_dict(instance):
    data = model_to_dict(instance)

    for field in instance._meta.get_fields():
        if not field.is_relation:
            value = getattr(instance, field.name)
            if isinstance(value, datetime.datetime):
                data[field.name] = value.strftime('%Y-%m-%d %H:%M:%S')
            elif isinstance(value, datetime.date):
                data[field.name] =value.strftime('%Y-%m-%d')
            elif isinstance(field, (FileField, ImageField)):
                data[field.name] = value.url if value else None
            elif isinstance(value, Decimal):
                data[field.name] = str(value)

    return data


def download_file(url):
    # Get aws object key
    logger.debug(f"Downloading File : {url}")
    object_key = url.split('/')[4:] # Extract the file path/name from the URL
    object_key = "/".join(object_key)
    object_key = object_key.split("?")[0] # get rid of any aws keys / signitures
    bucket_name = os.getenv("SOURCE_EXPORT_BUCKET_NAME", settings.AWS_STORAGE_BUCKET_NAME) # This should be changed based on the source bucket.
    signed_url = generate_fetch_presigned_url(object_key, bucket_name)
    
    response = requests.get(signed_url)
    if response.status_code == 200:
        content_file = ContentFile(response.content)
        logger.debug(f"Done!")
        return File(content_file, name=object_key)

    else:
        logger.debug(f"Done!")
        return None


def get_database(db_name):
    db = NCBIDatabase.objects.filter(entrez_enum=db_name).first()
    if db:
        return db
    
    if db_name == "maude_recalls2":
        return NCBIDatabase.objects.filter(entrez_enum="maude_recalls").first()
    if db_name == "cochrane_library":
        return NCBIDatabase.objects.filter(entrez_enum="cochrane").first()

    logger.error(f"Database named {db_name} couldn't be found!")
    return None 

def convert_data(data):
    """
    Convert some fields like files and decimals ...etc.
    to be accepted by the django models.
    """
    file_fields = [
        "report", "prisma", "condensed_report","appendix_e2","terms_summary_report",
        "vigilance_report","protocol","second_pass_articles","second_pass_word","verification_zip",
        "fulltext_zip","full_text","search_report","search_file","manual_pdf",
        "second_pass_ris", "article_reviews_ris", "verification_zip", "duplicates_report",
        "audit_tracking_logs", "missing_clinical_appraisals", "all_articles_review", "appendix_a",
        "appendix_b_all", "appendix_b_retinc", "appendix_c_all", "appendix_c_retinc", "appendix_d", "appendix_e",
    ]
    for key, value in data.items():
        if value and isinstance(value ,str):
            is_file_field = key in file_fields 
            is_file_link = "AWSAccessKeyId=" in value
            if is_file_field or is_file_link:
                data[key] = download_file(data[key])

    return data

def export_project_backup(client_name):
    from client_portal.models import Project

    client = Client.objects.get(name=client_name)
    logger.info(f"###### COPYING {client.name} CLIENT PROJECTS #########")
    # 
    reviews_dict = []
    client_reviews = LiteratureReview.objects.filter(client=client)

    for review in client_reviews:
        review_dict = {}
        literature_dict = custom_model_to_dict(review)
        literature_dict.pop("id")
        literature_dict.pop("client")
        literature_dict.pop("authorized_users")
        logger.info(f"Copying Review Data {str(review)}")
        review_dict["review"] = literature_dict

        literature_dict.pop("device")
        device = review.device 
        device_dict = custom_model_to_dict(device)
        device_dict.pop("id")
        device_dict.pop("manufacturer")
        review_dict["device"] = device_dict

        manufacturer = review.device.manufacturer
        manufacturer_dict = custom_model_to_dict(manufacturer)
        manufacturer_dict.pop("id")
        review_dict["manufacturer"] = manufacturer_dict

        protocol = review.searchprotocol
        protocol_dict = custom_model_to_dict(protocol)
        protocol_dict.pop("id")
        protocol_dict.pop("literature_review")
        protocol_dict["lit_searches_databases_to_search"] = [db.entrez_enum for db in protocol.lit_searches_databases_to_search.all()]
        protocol_dict["ae_databases_to_search"] = [db.entrez_enum for db in protocol.ae_databases_to_search.all()]
        review_dict["searchprotocol"] = protocol_dict

        project = Project.objects.filter(lit_review=review).first()
        if project:
            project_dict =  custom_model_to_dict(project)
            project_dict.pop("id")
            project_dict.pop("client")
            project_dict.pop("lit_review")
            project_dict.pop("most_recent_project")
            
            review_dict["project"] = project_dict

        logger.info(f"Copying Exclusion Reasons FOR Review {str(review)}")
        exclusions = ExclusionReason.objects.filter(literature_review=review)
        review_dict["exclusions"] = [exclusion.reason for exclusion in exclusions]
        
        logger.info(f"Copying Database Summaries FOR Review {str(review)}")
        summaries = AdversDatabaseSummary.objects.filter(literature_review=review)
        summaries_dict = []
        for summary in summaries:
            summary_dict = custom_model_to_dict(summary)
            summary_dict.pop("id")
            summary_dict.pop("literature_review")
            summary_dict["database"] = summary.database.entrez_enum
            summaries_dict.append(summary_dict)

        review_dict["aes_summaries"] = summaries_dict

        # Reports 
        logger.info(f"Copying Reports LITR/LITP FOR Review {str(review)}")
        reports_dict = []
        reports = FinallReportJob.objects.filter(literature_review=review)
        for report in reports:
            report_dict = custom_model_to_dict(report)
            report_dict.pop("id")
            report_dict.pop("literature_review")
            reports_dict.append(report_dict)

        review_dict["reports"] = reports_dict
        searches = LiteratureSearch.objects.filter(literature_review=review)
        searches_dict = []

        logger.info(f"Copying Search Terms FOR Review {str(review)}")
        for search in searches:
            search_dict = custom_model_to_dict(search)
            search_dict.pop("id")
            search_dict.pop("literature_review")
            search_dict.pop("ae_events")
            search_dict.pop("ae_recalls")
            search_dict["db"] = search.db.entrez_enum
            # logger.info(f"Copying search {search_dict}")

            search_articles_reviews = ArticleReview.objects.filter(search=search)
            # article_reviews_dict = []
            search_dict["reviews"] = []
            search_dict["events"] = []
            search_dict["recalls"] = []

            logger.info(f"Copying Article Reviews FOR Review {str(review)}")
            for article_review in search_articles_reviews:
                article = article_review.article 
                article_review_dict = custom_model_to_dict(article_review)
                article_review_dict.pop("id")
                article_review_dict.pop("search")
                article_dict = custom_model_to_dict(article)
                article_dict.pop("id")
                article_review_dict["article"] = article_dict
                #
                review_app = ClinicalLiteratureAppraisal.objects.filter(article_review=article_review).first()
                if review_app:
                    review_app_dict = custom_model_to_dict(review_app)
                    review_app_dict.pop("id")
                    review_app_dict.pop("article_review")
                    review_app_dict["extraction_field"] = []
                    
                    # Clinical Appraisal Fields
                    app_extraction_fields = AppraisalExtractionField.objects.filter(clinical_appraisal=review_app)
                    for app_extraction in app_extraction_fields:
                        app_extraction_field_dict = custom_model_to_dict(app_extraction)
                        app_extraction_field_dict.pop("id")
                        app_extraction_field_dict.pop("clinical_appraisal")
                        app_extraction_field_dict["extraction_field"] = app_extraction.extraction_field.name
                        review_app_dict["extraction_field"].append(app_extraction_field_dict)
                    
                    article_review_dict["appraisal"] = review_app_dict
                #
                # article_reviews_dict.append(article_review_dict)
                search_dict["reviews"].append(article_review_dict) 
                # logger.info(f"Copying article review {article_reviews_dict}")                        

            adverse_events_reviews = AdverseEventReview.objects.filter(search=search)
            adverse_recall_reviews = AdverseRecallReview.objects.filter(search=search)

            logger.info(f"Copying Adverse Events FOR Review {str(review)}")
            for event_review in adverse_events_reviews:
                event_review_dict = custom_model_to_dict(event_review)
                event_review_dict.pop("id")
                event_review_dict.pop("search")
                event = event_review.ae 
                event_dict = custom_model_to_dict(event)
                event_dict.pop("id")
                event_dict["db"] = event.db.entrez_enum 
                event_review_dict["ae"] = event_dict
                search_dict["events"].append(event_review_dict)

            for recall_review in adverse_recall_reviews:
                recall_review_dict = custom_model_to_dict(recall_review)
                recall_review_dict.pop("id")
                recall_review_dict.pop("search")
                recall = recall_review.ae 
                recall_dict = custom_model_to_dict(recall)
                recall_dict.pop("id")
                recall_dict["db"] = recall.db.entrez_enum 
                recall_review_dict["ae"] = recall_dict
                search_dict["recalls"].append(recall_review_dict)

            # logger.info(f"Copying search {search_dict}")
            searches_dict.append(search_dict)
        #
        review_dict["searches"] = searches_dict
        
        # Proposals 
        review_dict["proposals"] = []
        proposals = LiteratureReviewSearchProposal.objects.filter(literature_review=review)
        for proposal in proposals:
            proposal_dict = custom_model_to_dict(proposal)
            proposal_dict.pop("id")
            proposal_dict.pop("literature_review")
            proposal_dict.pop("literature_search")
            proposal_dict["db"] = proposal.db.entrez_enum
            review_dict["proposals"].append(proposal_dict)

        logger.info(f"Copying Keywords FOR Review {str(review)}")
        kws = KeyWord.objects.filter(literature_review=review)
        kws_dict = []
        for kw in kws:
            kw_dict = custom_model_to_dict(kw)
            kw_dict.pop("id")
            kw_dict.pop("literature_review")
            kws_dict.append(kw_dict)

        review_dict["kws"] = kws_dict
        
        custom_kws = CustomKeyWord.objects.filter(literature_review=review)
        custom_kws_dict = []

        for kw in custom_kws:
            kw_dict = custom_model_to_dict(kw)
            kw_dict.pop("id")
            kw_dict.pop("literature_review")
            custom_kws_dict.append(kw_dict)

        review_dict["custom_kws"] = custom_kws_dict

        logger.info(f"Copying Database Configurations FOR Review {str(review)}")
        # database confifurations
        db_configurations = SearchConfiguration.objects.filter(literature_review=review)
        configs_dict = []
        for config in db_configurations:
            config_dict = custom_model_to_dict(config)
            config_dict.pop("id")
            config_dict.pop("literature_review")
            config_dict["database"] = config.database.entrez_enum
            config_dict["params"] = []
            parameters = SearchParameter.objects.filter(search_config=config)
            for param in parameters:
                param_dict = custom_model_to_dict(param)
                param_dict.pop("id")
                param_dict.pop("search_config")
                config_dict["params"].append(param_dict)
            #
            configs_dict.append(config_dict)
        #
        review_dict["configs"] = configs_dict
        reviews_dict.append(review_dict)

        # figure out a way to deal with custom_model_to_dict not converting foriegn keys and m2m
        string_content =  json.dumps(review_dict)
        content = string_content.encode()
        file_name = str(review) + ".json"
        tmp_file = create_tmp_file(file_name, content)
        
        ### UPLOAD EXPORT FILE TO AWS S3 BUCKET ###
        object_key = "client_projects_dump/"+file_name
        s3_direct_file_uplaod(tmp_file, object_key, settings.AWS_STORAGE_BUCKET_NAME)

    return None

def import_project_backup(dump_file_aws_key, client_name):
    from client_portal.models import Project

    client = Client.objects.get(name=client_name)
    bucket_name = os.getenv("SOURCE_IMPORT_BUCKET_NAME", settings.AWS_STORAGE_BUCKET_NAME) # This should be changed on your env vars (which bucket your dump file lives ?).
    signed_url = generate_fetch_presigned_url(dump_file_aws_key, bucket_name)
    data_file_path = ""
    logger.debug(f"Downloading Dump File : {dump_file_aws_key}...")

    try:
        response = requests.get(signed_url)
        if response.status_code == 200:
            data_file_path = create_tmp_file("review_temp.json", response.text.encode())
            logger.debug("File Downloaded! Importing Data Now")

        else:
            logger.debug(f"Error while trying to retrieve dump file {str(response.text)}")

    except Exception as error:
        logger.debug(f"Error while trying to retrieve dump file {str(error)}")
        return None

    with open(data_file_path, "rb") as data_file:
        # content = data_file.read()
        content_json = json.load(data_file)
        client = Client.objects.get(name=client_name)

        manufacturer_values = content_json["manufacturer"]
        manufacturer = Manufacturer.objects.get_or_create(**manufacturer_values)[0]
        device_values = content_json["device"]
        device = Device.objects.get_or_create(manufacturer=manufacturer, **device_values)[0]
        literature_dict = content_json["review"] 
        review = LiteratureReview.objects.create(
            client=client,
            device=device,
            **literature_dict,
        )
        logger.info(f"Exporting Review {str(review)}")

        ### DELETE DEFAULT VALUES 
        review.searchprotocol.delete()
        ExclusionReason.objects.filter(literature_review=review).delete()
        KeyWord.objects.filter(literature_review=review).delete()
        
        logger.info(f"Exporting Protocol For Review {str(review)}")
        protocol_values = content_json["searchprotocol"]        
        searches_dbs = protocol_values.pop("lit_searches_databases_to_search")
        aes_dbs = protocol_values.pop("ae_databases_to_search")
        protocol = SearchProtocol.objects.create(**protocol_values, literature_review=review)
        for db_name in searches_dbs:
            db = get_database(db_name)
            protocol.lit_searches_databases_to_search.add(db)

        for db_name in aes_dbs:
            db = get_database(db_name)
            protocol.ae_databases_to_search.add(db)

        project = content_json.get("project", None)
        if project:
            Project.objects.create(
                **project,
                client=client,
                lit_review=review,
            )

        logger.info(f"Exporting Exclusion Reasons For Review {str(review)}")
        exclusions = content_json["exclusions"] 
        for reason in exclusions:
            ExclusionReason.objects.create(literature_review=review, reason=reason)
        
        logger.info(f"Exporting DB SUmmaries For Review {str(review)}")
        aes_summaries = content_json["aes_summaries"]
        for summary in aes_summaries:
            database = get_database(summary.pop("database")) 
            AdversDatabaseSummary.objects.create(
                literature_review=review, 
                database=database,
                **summary,
            )

        # Reports 
        logger.info(f"Exporting Reports For Review {str(review)}")
        reports = content_json["reports"]
        for report_values in reports:
            FinallReportJob.objects.create(
                **convert_data(report_values),
                literature_review=review,
            )

        logger.info(f"Exporting Search Terms For Review {str(review)}")
        searches = content_json["searches"]
        for search_values in searches:
            article_reviews = search_values.pop("reviews")
            events = search_values.pop("events")
            recalls = search_values.pop("recalls")
            if search_values.get("proposal"):
                search_values.pop("proposal") 

            db_name = search_values.pop("db")
            db = get_database(db_name)
            search = LiteratureSearch.objects.create(
                **convert_data(search_values), 
                literature_review=review, 
                db=db
            )
            
            logger.info(f"Exporting Article Reviews For Review {str(review)}")
            for article_review_values in article_reviews:
                article_values = article_review_values.pop("article")
                article_review_appraisal = article_review_values.get("appraisal", None)
                if article_review_appraisal:
                    article_review_values.pop("appraisal")

                article = None 
                pubmed_uid = article_values["pubmed_uid"]
                pmc_uid = article_values["pmc_uid"]

                if pubmed_uid:
                    article = Article.objects.filter(pubmed_uid=pubmed_uid, literature_review=review).first()
                if not article and pmc_uid:
                    article = Article.objects.filter(pmc_uid=pmc_uid, literature_review=review).first()
                if not article:
                    if "literature_review" in article_values.keys():
                        article_values.pop("literature_review")
                    article = Article.objects.create(**convert_data(article_values), literature_review=review)

                article_review = ArticleReview.objects.create(**article_review_values, search=search, article=article)

                if article_review_appraisal:
                    app_extractions = article_review_appraisal.pop("extraction_field")
                    # review_app = 
                    if ClinicalLiteratureAppraisal.objects.filter(article_review=article_review).exists():
                        ClinicalLiteratureAppraisal.objects.get(article_review=article_review).delete()

                    review_app = ClinicalLiteratureAppraisal.objects.create(
                        article_review=article_review,
                        **article_review_appraisal
                    )

                    for extraction in app_extractions:
                        extraction_field = ExtractionField.objects.get(
                            name=extraction.pop("extraction_field"),
                            literature_review=review,
                        )
                        AppraisalExtractionField.objects.create(
                            **extraction,
                            clinical_appraisal=review_app,
                            extraction_field=extraction_field,
                        )

            logger.info(f"Exporting Adverse Events For Review {str(review)}")
            for event_review in events:
                ae_values = event_review.pop("ae")
                ae_obj = AdverseEvent.objects.filter(**ae_values).first()
                # if event with same values already exists don't create
                if not ae_obj:
                    db_name = ae_values.pop("db")
                    db = get_database(db_name) 
                    ae_obj = AdverseEvent.objects.create(db=db, **convert_data(ae_values))

                AdverseEventReview.objects.create(
                    ae=ae_obj,
                    search=search,
                    **event_review,
                )

            for recall_review in recalls:
                ae_values = recall_review.pop("ae")
                recall_obj = AdverseRecall.objects.filter(**ae_values).first()
                if not recall_obj:
                    db_name = ae_values.pop("db")
                    db = get_database(db_name) 
                    recall_obj = AdverseRecall.objects.create(db=db, **convert_data(ae_values))

                AdverseRecallReview.objects.create(
                    ae=recall_obj,
                    search=search,
                    **recall_review,
                )

        # Proposals 
        proposals = content_json["proposals"]
        for proposal_values in proposals:
            db_name = proposal_values["db"]
            db = get_database(db_name)
            lit_search = LiteratureSearch.objects.filter(
                literature_review=review,
                db=db,
                term=proposal_values["term"],
            ).first()
            if lit_search:
                proposal = LiteratureReviewSearchProposal.objects.create(
                    literature_review=review,
                    db=db,
                    literature_search=lit_search,
                    term=proposal_values["term"],
                    is_sota_term=proposal_values["is_sota_term"],
                )
            else:
                proposal = LiteratureReviewSearchProposal.objects.create(
                    literature_review=review,
                    db=db,
                    term=proposal_values["term"],
                    is_sota_term=proposal_values["is_sota_term"],
                )

        logger.info(f"Exporting Keywords For Review {str(review)}")
        kws = content_json["kws"]
        for kw in kws:
            KeyWord.objects.create(literature_review=review, **kw)

        custom_kws = content_json["custom_kws"]
        for kw in custom_kws:
            CustomKeyWord.objects.create(literature_review=review, **kw)
        
        logger.info(f"Exporting Database Configurations For Review {str(review)}")
        db_configs = content_json["configs"]
        for config in db_configs:
            db_name = config["database"]
            database = get_database(db_name)
            configuration = SearchConfiguration.objects.get(
                literature_review=review,
                database=database,
            )
            for param in config["params"]:
                paramater = SearchParameter.objects.get(
                    search_config=configuration, 
                    name=param["name"]
                )
                paramater.value = param["value"]
                paramater.save()


def combine_two_projects(p1, p2, duplicate):
    from client_portal.models import Project

    logger.info("###### COPYING PROJECT #########")
    logger.info("Cloning Search Protocol...")
    # Search Protocol
    duplicate.searchprotocol.delete()
    s_protocol = p1.searchprotocol
    p1_s_protocol_id = s_protocol.id
    s_protocol.id = None
    s_protocol.literature_review = duplicate
    s_protocol.save()
    p1_s_protocol = SearchProtocol.objects.get(id=p1_s_protocol_id)
    for db in p1_s_protocol.lit_searches_databases_to_search.all():
        s_protocol.lit_searches_databases_to_search.add(db)
    for ae_db in p1_s_protocol.ae_databases_to_search.all():
        s_protocol.ae_databases_to_search.add(ae_db)

    # p2_s_protocol = p2.searchprotocol
    # for db in p2_s_protocol.lit_searches_databases_to_search.all():
    #     s_protocol.lit_searches_databases_to_search.add(db)
    # for ae_db in p2_s_protocol.ae_databases_to_search.all():
    #     s_protocol.ae_databases_to_search.add(ae_db)

    logger.info("Cloning Project...")
    # Project
    cloned_project = Project.objects.get(lit_review=duplicate)
    original_project = Project.objects.get(lit_review=p1)

    cloned_project.max_terms = original_project.max_terms
    cloned_project.max_hits = original_project.max_hits
    cloned_project.max_results = original_project.max_results
    cloned_project.save()

    logger.info("Cloning Project...")
    # Search Terms #P1
    searches1 = LiteratureSearch.objects.filter(literature_review=p1)
    for search in searches1:
        article_reviews1 = ArticleReview.objects.filter(search=search)
        search.literature_review = duplicate
        search.pk = None 
        search.save()

        for article_review in article_reviews1:
            origina_article_review_id = article_review.id
            article_review.search = search 
            article_review.pk = None 
            article_review.save()
            # clinical appraisals
            app = ClinicalLiteratureAppraisal.objects.filter(article_review__id=origina_article_review_id).first()
            if app:
                ClinicalLiteratureAppraisal.objects.filter(article_review=article_review).delete()
                app.article_review = article_review
                app.pk = None
                app.save()


    proposals1 = LiteratureReviewSearchProposal.objects.filter(literature_review=p1)
    for proposal in proposals1:
        duplicate_search = LiteratureSearch.objects.get(
            term=proposal.term,
            literature_review=duplicate,
            db=proposal.db,
        )
        proposal.literature_search = duplicate_search
        proposal.literature_review = duplicate
        proposal.pk = None
        proposal.save()

    # Search Terms #P2
    searches2 = LiteratureSearch.objects.filter(literature_review=p2)
    for search in searches2:
        article_reviews2 = ArticleReview.objects.filter(search=search)
        lit_search = LiteratureSearch.objects.filter(literature_review=duplicate, term=search.term, db=search.db)
        if not lit_search.exists():
            search.literature_review = duplicate
            search.pk = None 
            search.save()
        else:
            search = lit_search.first()

        for article_review2 in article_reviews2:
            origina_article_review_id2 = article_review2.id
            article_review2.search = search 
            article_review2.pk = None 
            article_review2.save()

            # clinical appraisals
            app = ClinicalLiteratureAppraisal.objects.filter(article_review__id=origina_article_review_id2).first()
            if app:
                ClinicalLiteratureAppraisal.objects.filter(article_review=article_review2).delete()
                app.article_review = article_review2
                app.pk = None
                app.save()

    proposals2 = LiteratureReviewSearchProposal.objects.filter(literature_review=p2)
    for proposal in proposals2:
        duplicate_search = LiteratureSearch.objects.get(
            term=proposal.term,
            literature_review=duplicate,
            db=proposal.db,
        )
        proposal.literature_search = duplicate_search
        if not LiteratureReviewSearchProposal.objects.filter(literature_review=duplicate, literature_search=duplicate_search).exists():
            proposal.literature_review = duplicate
            proposal.pk = None
            proposal.save()


    logger.info("Cloning Exclusion Reasons...")
    # Exclusion Reasons
    ExclusionReason.objects.filter(literature_review=duplicate).delete()
    reasons = ExclusionReason.objects.filter(literature_review=p1)
    for reason in reasons:
        reason.literature_review = duplicate
        reason.pk = None
        reason.save()
        

    logger.info("Cloning Keywords...")
    KeyWord.objects.filter(literature_review=duplicate).delete()
    keywords = KeyWord.objects.filter(literature_review=p1)
    for keyword in keywords:
        keyword.pk = None 
        keyword.literature_review = duplicate 
        keyword.save()

    CustomKeyWord.objects.filter(literature_review=duplicate).delete()
    keywords = CustomKeyWord.objects.filter(literature_review=p1)
    for keyword in keywords:
        keyword.pk = None 
        keyword.literature_review = duplicate 
        keyword.save()

    logger.info("Search Terms Configuration...")

    # duplicate default configs
    d_configs = SearchConfiguration.objects.filter(literature_review=duplicate)
    for d_config in d_configs:
        d_config.delete()

    # Search Terms Configurations
    configs = SearchConfiguration.objects.filter(literature_review=p1)
    for config in configs:
        original_config_id = config.id
        config.id = None
        config.literature_review = duplicate
        config.save()

        original_config = SearchConfiguration.objects.get(id=original_config_id)
        parameters = SearchParameter.objects.filter(search_config=original_config)
        for param in parameters:
            param.id = None 
            param.search_config = config
            param.save()


def clone_project(original, duplicate):
    from client_portal.models import Project

    logger.info("###### COPYING PROJECT #########")
    logger.debug(f"Original Project searches: {LiteratureSearch.objects.filter(literature_review=original).count()}")
    logger.debug(f"Original Project proposals: {LiteratureReviewSearchProposal.objects.filter(literature_review=original).count()}")
    logger.debug(f"Original Project exclusion reasons: {ExclusionReason.objects.filter(literature_review=original).count()}")
    logger.debug(f"Original Project articles: {ArticleReview.objects.filter(search__literature_review=original).count()}")
    logger.debug(f"Original Project keywords: {KeyWord.objects.filter(literature_review=original).count()}")
    logger.debug(f"Original Project custom keywords: {CustomKeyWord.objects.filter(literature_review=original).count()}")

    try:
        logger.info("Cloning Search Protocol...")
        # Search Protocol
        duplicate.searchprotocol.delete()
        s_protocol = original.searchprotocol
        original_s_protocol_id = s_protocol.id
        s_protocol.id = None
        s_protocol.literature_review = duplicate
        s_protocol.save()
        original_s_protocol = SearchProtocol.objects.get(id=original_s_protocol_id)
        for db in original_s_protocol.lit_searches_databases_to_search.all():
            s_protocol.lit_searches_databases_to_search.add(db)
        for ae_db in original_s_protocol.ae_databases_to_search.all():
            s_protocol.ae_databases_to_search.add(ae_db)

        logger.info("Cloning Project...")
        # Project
        cloned_project = Project.objects.get(lit_review=duplicate)
        original_project = Project.objects.get(lit_review=original)

        cloned_project.max_terms = original_project.max_terms
        cloned_project.max_hits = original_project.max_hits
        cloned_project.max_results = original_project.max_results
        cloned_project.save()

        # Article Tags
        tags = ArticleTag.objects.filter(literature_review=original)
        for tag in tags:
            tag.literature_review = duplicate
            tag.pk = None
            tag.creator = None
            tag.save()

            tag.article_reviews.clear()

        logger.info("Cloning Search Terms...")
        # Search Terms
        searches = LiteratureSearch.objects.filter(literature_review=original)
        for search in searches:
            article_reviews = ArticleReview.objects.filter(search=search)
            search.literature_review = duplicate
            search.pk = None 
            search.save()

            for article_review in article_reviews:
                article_review.search = search
                new_related_tags = []
                for tag in article_review.tags.all():
                    new_tag = ArticleTag.objects.filter(name=tag.name, literature_review=duplicate).first()
                    new_related_tags.append(new_tag)
                
                if article_review.state != "D":
                    article_review.state = "U"
                article_review.exclusion_reason = None
                article_review.pk = None 
                article_review.save()

                article_review.tags.clear()
                for tag in new_related_tags:
                    article_review.tags.add(tag)

        proposals = LiteratureReviewSearchProposal.objects.filter(literature_review=original)
        for proposal in proposals:
            duplicate_search = LiteratureSearch.objects.filter(
                term=proposal.term.strip(),
                literature_review=duplicate,
                db=proposal.db,
            ).first()
            if not duplicate_search:
                duplicate_search = LiteratureSearch.objects.create(
                    term=proposal.term.strip(),
                    literature_review=duplicate,
                    db=proposal.db,
                    is_sota_term=proposal.is_sota_term,
                )

            proposal.literature_search = duplicate_search
            proposal.literature_review = duplicate
            proposal.pk = None
            proposal.save()


        logger.info("Cloning Exclusion Reasons...")
        # Exclusion Reasons
        ExclusionReason.objects.filter(literature_review=duplicate).delete()
        reasons = ExclusionReason.objects.filter(literature_review=original)
        for reason in reasons:
            reason.literature_review = duplicate
            reason.pk = None
            reason.save()
            

        logger.info("Cloning Keywords...")
        KeyWord.objects.filter(literature_review=duplicate).delete()
        keywords = KeyWord.objects.filter(literature_review=original)
        for keyword in keywords:
            keyword.pk = None 
            keyword.literature_review = duplicate 
            keyword.save()

        CustomKeyWord.objects.filter(literature_review=duplicate).delete()
        keywords = CustomKeyWord.objects.filter(literature_review=original)
        for keyword in keywords:
            keyword.pk = None 
            keyword.literature_review = duplicate 
            keyword.save()


        logger.debug(f"Original Project searches: {LiteratureSearch.objects.filter(literature_review=original).count()}")
        logger.debug(f"Original Project proposals: {LiteratureReviewSearchProposal.objects.filter(literature_review=original).count()}")
        logger.debug(f"Original Project exclusion reasons: {ExclusionReason.objects.filter(literature_review=original).count()}")
        logger.debug(f"Original Project articles: {ArticleReview.objects.filter(search__literature_review=original).count()}")
        logger.debug(f"Original Project keywords: {KeyWord.objects.filter(literature_review=original).count()}")
        logger.debug(f"Original Project custom keywords: {CustomKeyWord.objects.filter(literature_review=original).count()}")

        logger.info("###### COPYING PROJECT COMPLETED #########")
        logger.debug(f"Duplicate Project searches: {LiteratureSearch.objects.filter(literature_review=duplicate).count()}")
        logger.debug(f"Duplicate Project proposals: {LiteratureReviewSearchProposal.objects.filter(literature_review=duplicate).count()}")
        logger.debug(f"Duplicate Project exclusion reasons: {ExclusionReason.objects.filter(literature_review=duplicate).count()}")
        logger.debug(f"Duplicate Project articles: {ArticleReview.objects.filter(search__literature_review=duplicate).count()}")  
        logger.debug(f"Duplicate Project keywords: {KeyWord.objects.filter(literature_review=duplicate).count()}")
        logger.debug(f"Duplicate Project custom keywords: {CustomKeyWord.objects.filter(literature_review=duplicate).count()}")
        
        logger.info("Search Terms Configuration...")

        # duplicate default configs
        d_configs = SearchConfiguration.objects.filter(literature_review=duplicate)
        for d_config in d_configs:
            d_config.delete()

        # ExtractionField
        extractions = ExtractionField.objects.filter(literature_review=original)
        for field in extractions:
            if not ExtractionField.objects.filter(literature_review=duplicate, name=field.name).exists():
                field.literature_review = duplicate
                field.pk = None
                field.save()

        # Search Terms Configurations
        configs = SearchConfiguration.objects.filter(literature_review=original)
        for config in configs:
            original_config_id = config.id
            config.id = None
            config.literature_review = duplicate
            config.save()

            original_config = SearchConfiguration.objects.get(id=original_config_id)
            parameters = SearchParameter.objects.filter(search_config=original_config)
            for param in parameters:
                param.id = None 
                param.search_config = config
                param.save()

        duplicate.is_cloning_completed = True
        duplicate.save()

    except Exception as errors:
        logger.error(f"Cloning for project {str(duplicate)} failed with the below error {str(traceback.format_exc())}")
        duplicate.cloning_errors = str(errors)
        duplicate.is_cloning_completed = True
        duplicate.save()


def create_periodic_review(start_date, end_date, living_review_parent, copy_data_from_review):
    from lit_reviews.tasks import clone_project_task, run_auto_search, process_article_review_device_mentions_async
    from client_portal.models import Project

    logger.info(f"creating periodic project for {str(living_review_parent)} start date : {str(start_date)} end date : {str(end_date)}")
    periodic_project = LiteratureReview.objects.create(
        device=living_review_parent.device,
        client=living_review_parent.project_protocol.client,
        cloned_from=copy_data_from_review,
        is_cloning_completed= False,
        parent_living_review=living_review_parent,
        is_living_review=True,
    )
    total_created_projects = living_review_parent.projects.count()
    Project.objects.create(
        lit_review=periodic_project, 
        project_name=f"LRP {total_created_projects+1}",
        client=living_review_parent.project_protocol.client,
    )

    # copy data search protocol and search terms from latest run project
    clone_project_task(copy_data_from_review.id, periodic_project.id)
    periodic_project.refresh_from_db()
    periodic_project.searchprotocol.lit_date_of_search = end_date # End date of search
    periodic_project.searchprotocol.ae_date_of_search = end_date # End date of search
    periodic_project.searchprotocol.lit_start_date_of_search = start_date
    periodic_project.searchprotocol.ae_start_date_of_search = start_date
    periodic_project.searchprotocol.save()

    # updata start/end dates for all databases if they have custome config
    search_configs = SearchConfiguration.objects.filter(
        literature_review=periodic_project
    )
    for search_config in search_configs:
        start_date_parameter = SearchParameter.objects.get(search_config=search_config, name="Start Date")
        start_date_parameter.value = start_date
        start_date_parameter.save()

        end_date_parameter = SearchParameter.objects.get(search_config=search_config, name="End Date")
        end_date_parameter.value = end_date
        end_date_parameter.save() 

    # Run automated searches 
    searches = LiteratureSearch.objects.filter(literature_review=periodic_project)
    for search in searches:
        if search.db.auto_search_available:
            logger.info(f"Running auto search for {str(search)}")
            run_auto_search(periodic_project.id, search.id)
        else:
            logger.warning(f"Run auto search is not available for {search.db}")

    ## detect article mentions for under , similar and competitor devices
    process_article_review_device_mentions_async.delay(periodic_project.id)


def get_end_date_for_living_review_project(living_review, start_date):
    end_date = None 
    
    if living_review.interval == "weekly":
        end_date = start_date + timedelta(days=7)
    if living_review.interval == "monthly":
        end_date = start_date + relativedelta(months=1) - timedelta(days=1)
    if living_review.interval == "quarterly":
        end_date = start_date + relativedelta(months=3) - timedelta(days=1)
    if living_review.interval == "annually":
        end_date = start_date.replace(month=12, day=31)

    return end_date