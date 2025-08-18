import boto3
import pandas as pd
import datetime
from dateutil.relativedelta import relativedelta

from django.conf import settings
from lit_reviews.helpers.generic import generate_number_from_text
from lit_reviews.models import (
    LiteratureReviewSearchProposal,
    LiteratureReviewSearchProposalReport,
    LiteratureSearch,
    SearchConfiguration,
    SearchParameter,
    LiteratureReview,
    ArticleReview,
    NCBIDatabase,
    SearchTermPreview,
)
from lit_reviews.api.search_terms.serializers import SearchTermSerializer, LiteratureReviewSearchProposalReportSerializer
from backend.logger import logger
import boto3



def validate_input_columns(file, db_name):
    if db_name == "scholar" and not ".ris" in file:
        scholar_header_columes = ['Title', 'Abstract', 'Citation MLA', 'Citation APA']
        df = pd.read_csv(file, delimiter=',', encoding='unicode_escape')
        column_names = list(df.columns)
        if scholar_header_columes != column_names:    
            return False
        
    return True

def upload_file_to_aws_s3(file_path ,upload_to):
    session = boto3.Session(aws_access_key_id=settings.AWS_ACCESS_KEY_ID,aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY)
    s3 = session.resource('s3')
    s3.meta.client.upload_file(Filename=file_path , Bucket=settings.AWS_STORAGE_BUCKET_NAME, Key=upload_to)
    BUCKET_NAME = settings.AWS_STORAGE_BUCKET_NAME
    file_url = "https://s3.amazonaws.com/" + BUCKET_NAME + "/" + upload_to
    return file_url


def get_search_protocol_scope_field_label(years_back):
    return f"""The scope of the literature search includes a query of select adverse event report databases as well as scientific databases for the past {years_back} years. This period of time is felt to provide sufficient clinical experience with these devices from both a safety and performance perspective. Performance assessments include reports designed to....[ finish the paragraph below ]"""


def create_init_search_params_litreview(lit_review):
    init_search_configs = SearchConfiguration.objects.filter(is_template=True)

    for s_config in init_search_configs:
        s_config_id = s_config.id
        s_config_copy = s_config
        s_config_copy.id = None
        s_config_copy.literature_review = lit_review
        s_config_copy.is_template = False
        s_config_copy.save()
        s_config = SearchConfiguration.objects.get(id=s_config_id)

        for param in s_config.params.all():
            param_copy = param
            param_copy.id = None
            param_copy.search_config = s_config_copy
            param_copy.save()

    logger.info(f"Configuration parameters created for {lit_review} successfuly")



def link_proposal_with_literature_search():
    """
    Link each SearchProposal object with a LiteratureSearch
    and a SearchProposalReport.  
    """
    LiteratureReviewSearchProposalReport.objects.all().delete()
    props = LiteratureReviewSearchProposal.objects.all()   
    for  prop in props:
        try:
            search = LiteratureSearch.objects.get_or_create(term=prop.term, db=prop.db, literature_review=prop.literature_review)[0]
            prop.literature_search = search
            prop.save()

        except Exception as e:
            logger.error("No Serach Object Found: {0}".format(str(e)))

        report = LiteratureReviewSearchProposalReport.objects.get_or_create(term=prop.term, literature_review=prop.literature_review)[0]
        prop.report = report  
        prop.save()
        logger.debug("Literature Search is Updated for: {0}".format(prop))


def get_search_date_ranges(lit_search):
    if lit_search.literature_review.is_autosearch or lit_search.is_notebook_search:
        start_date = lit_search.start_search_interval
        end_date = lit_search.end_search_interval
        return start_date, end_date    
        
    protocol = lit_search.literature_review.searchprotocol
    configurable_dbs = ["pmc", "cochrane", "pubmed", "ct_gov"]
    if lit_search.db.entrez_enum in configurable_dbs:
        search_config = SearchConfiguration.objects.get(
            database=lit_search.db,
            literature_review=lit_search.literature_review
        )
        
        start_date_str = SearchParameter.objects.get(
            search_config=search_config, name="Start Date"
        ).value
        end_date_str = SearchParameter.objects.get(
            search_config=search_config, name="End Date"
        ).value
        if "00:00:00" in start_date_str:
            start_date_str = start_date_str.replace("00:00:00", "").strip()
        if "00:00:00" in end_date_str:
            end_date_str = end_date_str.replace("00:00:00", "").strip()

        print("start_date_str : "+start_date_str)
        start_date = datetime.datetime.strptime(start_date_str, "%Y-%m-%d")
        end_date = datetime.datetime.strptime(end_date_str, "%Y-%m-%d")

    elif lit_search.db.is_ae or lit_search.db.is_recall:
        end_date = protocol.ae_date_of_search
        if protocol.ae_start_date_of_search:
            start_date = protocol.ae_start_date_of_search
        else:
            start_date = protocol.ae_date_of_search - relativedelta(years=protocol.ae_years_back)

    else:
        end_date = protocol.lit_date_of_search
        if protocol.lit_start_date_of_search:
            start_date = protocol.lit_start_date_of_search
        else:
            start_date = protocol.lit_date_of_search - relativedelta(years=protocol.years_back)

    return start_date, end_date


def construct_search_terms_list(search_proposals, total_start=0):
    """
    This function construct the search terms list to be used inside Search Terms View.
    It serves more like a Serailizer.
    """
    terms = {}
    for prop in search_proposals:
        expected_result_count = prop.literature_search.expected_result_count if prop.literature_search else -1
        is_search_file = prop.literature_search and prop.literature_search.search_file != None and prop.literature_search.search_file != ""
        preview = None
        scraper_error = ""
        search_label = ""
        pico_category = None
        if prop.literature_search:
            preview = SearchTermPreview.objects.filter(literature_search=prop.literature_search).first()
            scraper_error = prop.literature_search.error_msg
            search_label = prop.literature_search.search_label
            pico_category = prop.literature_search.pico_category

        if expected_result_count == 0:
            expected_count_str = str(0)
        elif expected_result_count and expected_result_count > -1:
            expected_count_str = str(expected_result_count)
            # for maude if there are more than 500 results we should display warning to users to narrow the search
            if expected_result_count == 500 and prop.db.entrez_enum == "maude":
                # expected_count_str = "Warning"
                expected_count_str = "500+"
            # expected for scholar right now always 100+    
            if prop.db.entrez_enum == "scholar":
                expected_count_str += "+"

        elif prop.db.auto_search_available:
            expected_count_str = "Failed"
        else:
            expected_count_str = "Not Available"

        if prop.literature_search and prop.literature_search.advanced_options:
            search_field = prop.literature_search.advanced_options.get("search_field", None)
        else:
            search_field= None

        search_report = prop.report
        if not search_report:
            search_report = LiteratureReviewSearchProposalReport.objects.create(term=prop.term, literature_review=prop.literature_review)
            prop.report = search_report 
            prop.save()

        row = {
            "proposal": prop, 
            "expected_result_count": expected_result_count,  
            "count": expected_count_str,
            "report": search_report, 
            "is_search_file": is_search_file,
            "preview": preview,
            "scraper_error": scraper_error,
            "search_field": search_field,
            "term_type": search_label,
            "pico_category": pico_category,
        }
        prop_ser = SearchTermSerializer(row).data
        if terms.get(prop.term):
            terms[prop.term].append(prop_ser)
        else:
            terms[prop.term] = [prop_ser]

    total_terms = total_start
    terms_list = []
    for key, value in terms.items():
        is_search_file = any([item["is_search_file"] for item in value])
        value.sort(key=lambda row: row.get('proposal').get("db"))
        terms_list.append({
            "is_search_file": is_search_file,
            "term": key,
            "value": value,
            "id": value[0].get('proposal').get("id"),
            # "index": total_terms + 1,
            "index": generate_number_from_text(key),
            "term_type": search_label,
            "pico_category": value[0].get('pico_category'),
        })
        total_terms += 1

    return terms_list, total_terms


def update_search_terms(
        prop_id, 
        lit_review_id, 
        term, 
        is_sota_term, 
        entrez_enums, 
        user_id=None, 
        clinical_trials_search_field=None, 
        maude_search_field=None,
        term_type=None,
    ):
    """
    Update Review Terms given a Lit Review and a Search Term. 
    the function takes a term and get all the searches and than update accordignly by either:
    - deleting the search if the database was no longer selected
    - updating the search term text / the type ...etc
    - creating new searches if a new databases were selected
    """
    from lit_reviews.tasks import fetch_preview_and_expected_results
    
    prop_item = LiteratureReviewSearchProposal.objects.get(
        id=prop_id,
    )
    lit_review = LiteratureReview.objects.get(id=lit_review_id)
    props = LiteratureReviewSearchProposal.objects.filter(
        term=prop_item.term, 
        literature_review=lit_review
    )
    report = LiteratureReviewSearchProposalReport.objects.filter(term=term, literature_review=lit_review).order_by("id").first()
    if not report:
        report = LiteratureReviewSearchProposalReport.objects.create(term=term, literature_review=lit_review)
    entrez_enums = [entrez_enum.strip() for entrez_enum in entrez_enums]

    # Delete
    for prop in props:
        lit_search = LiteratureSearch.objects.filter(
            literature_review=prop.literature_review,
            db=prop.db,
            term=prop.term,
        ).first()

        # delete LiteratureSearch && LiteratureReviewSearchProposal if not related db is selected anymore
        if prop.db.entrez_enum not in entrez_enums:
            prop.delete()
            if lit_search:
                lit_search.delete()


    # Update/Create props after we deleted the unselected ones
    props = LiteratureReviewSearchProposal.objects.filter(term=prop_item.term, literature_review=lit_review)
    
    # Update 
    for prop  in props:
        update_search_proposal(
            report,
            prop,
            term, 
            is_sota_term, 
            clinical_trials_search_field=clinical_trials_search_field, 
            maude_search_field=maude_search_field,
            term_type=term_type,
        )

    # create new LiteratureReviewSearchProposal && LiteratureReview if new db has been added
    for entrez_enum in entrez_enums:
        db = NCBIDatabase.objects.get(entrez_enum=entrez_enum)
        lit_review = LiteratureReview.objects.get(id=lit_review_id)
        prop = LiteratureReviewSearchProposal.objects.filter(db=db, term=term, literature_review=lit_review).first()
        update_result_count = False 

        if not prop:
            update_result_count =True
            new_prop = LiteratureReviewSearchProposal(
                literature_review=lit_review,
                term=term,
                db=db,
                is_sota_term=is_sota_term,
                search_label = term_type
            )
            search = LiteratureSearch(
                literature_review=lit_review,
                db=db,
                is_sota_term=is_sota_term,
                term=term,
                search_label = term_type
            )
            search.save() 
            new_prop.report = report
            new_prop.literature_search = search
            new_prop.save()
            
            # update report with correct term
            report.term = new_prop.term 
            report.save()

        else:
            search, created = LiteratureSearch.objects.get_or_create(
                literature_review=prop.literature_review, db=prop.db, term=prop.term,
            )
            if created:
                update_result_count = True 
                
            if not prop.literature_search:
                prop.literature_search = search 
                prop.save()

                # update report with correct term
                report.term = prop.term 
                report.save()

        # udpating search field
        if clinical_trials_search_field and search.db.entrez_enum == "ct_gov":
            search.advanced_options = {"search_field" : clinical_trials_search_field}
            search.save()
        elif maude_search_field and search.db.entrez_enum == "maude":
            search.advanced_options = {"search_field" : maude_search_field} 
            search.save()

    report.status = "FETCHING_PREVIEW"
    report.save()
    fetch_preview_and_expected_results.delay(term, lit_review_id, user_id=user_id)
    return "Success"


def update_search_proposal(
        report,
        prop,
        term, 
        is_sota_term, 
        clinical_trials_search_field=None, 
        maude_search_field=None,
        term_type=None,
    ):
    """
    Update a single search directly by updating the search term text ...etc. 
    """    
    prop.report = report
    prop.save()
    
    lit_search = LiteratureSearch.objects.get_or_create(
        literature_review=prop.literature_review,
        db=prop.db,
        term=prop.term,
    )[0]
    logger.debug("sota term {0} {1}".format(is_sota_term, type(is_sota_term)))
    
    ## If term text changed mark it as not run yet
    if lit_search.term != term:
        lit_search.import_status       =  "NOT RUN"
        lit_search.processed_articles  =  None
        lit_search.imported_articles   =  None
        lit_search.duplicate_articles  =  None
        lit_search.result_count        =  None
        article_reviews = ArticleReview.objects.filter(search=lit_search)
        logger.warning(f"Delete {article_reviews.count()} article reviews for search {str(lit_search)}")
        article_reviews.delete()
    
    ## update term
    prop.term = term
    lit_search.term = term
    prop.is_sota_term = is_sota_term
    lit_search.is_sota_term = is_sota_term
    lit_search.search_label= term_type
    prop.search_label = term_type
    
    # udpating search field
    if clinical_trials_search_field and lit_search.db.entrez_enum == "ct_gov":
        lit_search.advanced_options = {"search_field" : clinical_trials_search_field}
    elif maude_search_field and lit_search.db.entrez_enum == "maude":
        lit_search.advanced_options = {"search_field" : maude_search_field} 

    prop.save()
    lit_search.save()

    # update report with correct term
    report.term = prop.term 
    report.save()