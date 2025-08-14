import traceback
import datetime

from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.conf import settings
from backend.logger import logger

from lit_reviews.database_imports.preview import proccess_preview
from client_portal.models import *
from lit_reviews.models import *
from lit_reviews.helpers.search_terms import upload_file_to_aws_s3
from django.contrib.auth import get_user_model

from lit_reviews.database_scrapers import (
    pubmed,
    cochranelibrary,
    pubmed_central,
    maude_scraper,
    maude_recalls_scraper,
)
from lit_reviews.database_apis import (
    clinical_trails as clinical_trails_api,
    europe_pmc as europe_pmc_api,
    scholar_scraper as scholar_api,
)

User = get_user_model()


def fetch_preview_and_expected_results(term, lit_review_id, user_id=None):
    from lit_reviews.tasks import run_auto_search

    # run search 
    lit_review = LiteratureReview.objects.get(id=lit_review_id)
    props = LiteratureReviewSearchProposal.objects.filter(term=term, literature_review=lit_review)
    report = props[0].report
    error = ""
    
    # Expected Result Count 
    # Legacy expected results count get_expected_result_count(search.db, search, lit_review_id, search.term, user_id=user_id)
    for prop in props:
        try:
            search = LiteratureSearch.objects.get_or_create(
                literature_review=prop.literature_review,
                db=prop.db,
                term=prop.term,
            )[0]

            if prop.db.auto_search_available:
                active_user = User.objects.get(id=user_id)
                preview = SearchTermPreview.objects.filter(literature_search=search).order_by("-created_at").first()
                if preview:
                    preview.status = "RUNNING"
                    preview.user = active_user
                    preview.save()
                else:
                    preview = SearchTermPreview.objects.create(status="RUNNING", literature_search=search, user=active_user)
                
                results, expected_results_count = run_auto_search(lit_review_id, search.id, user_id, preview=preview.id)
                
                # expected count for some databases are calculated during building the preview
                COUNT_RETRIEVED_WITH_PREVIEW_DBS = ["ct_gov"]
                if search.db.entrez_enum not in COUNT_RETRIEVED_WITH_PREVIEW_DBS or expected_results_count == 0:
                    search.expected_result_count = expected_results_count
                    search.save() 
            else:
                search.expected_result_count = -1 
                search.save()

        except Exception as err:
            err_track = str(traceback.format_exc())
            logger.error(err_track)
            if error == "":
                error = f"Fetching Preview and Expected Results Count wasn't successfull for the following databases: '{prop.db.name}',"
            else:
                error += f" '{prop.db.name}',"
        
    if error:
        error += " Please reach out to our support team to get more help!"
        report.status = "FAILED"
        report.errors = error
        report.save()
        return "Failed"
    else:
        report.status = "UPDATED"
        report.save()
        return "success"
    

def run_auto_search_task(lit_review_id, lit_search_id, user_id=None, preview=None): 
    """
    Run our scrapers to programatically search the specific database and download the results
    ** params
    lit_review_id: review id.
    lit_search_id: search id the search object includes the search database, search paramaters, search term.
    user_id: current active user responsible for triggering the search.
    preview: object if this auto search is just to preview the results and not to download/process them.
    """
    from lit_reviews.tasks import run_single_search

    try:
        lit_search = LiteratureSearch.objects.get(
            id=lit_search_id
        ) 

        ################### SCRAPER SET UP ######################
        if lit_search.db.entrez_enum == "pubmed":
            scraper = pubmed.Pubmed(lit_review_id, lit_search.id, user_id)
            if preview:
                previewObj = SearchTermPreview.objects.get(id=preview)
                previewObj.status = "COMPLETED"
                previewObj.results_url = scraper.results_url
                previewObj.save()
                return scraper.results_url,  int(str(scraper.results_count).replace(",", ""))
            
        elif lit_search.db.entrez_enum == "cochrane":
            scraper = cochranelibrary.CochraneLibrary(lit_review_id, lit_search.id, user_id)

        elif lit_search.db.entrez_enum == "pmc":
            scraper = pubmed_central.PubmedCentral(lit_review_id, lit_search.id, user_id)
            if preview:
                previewObj = SearchTermPreview.objects.get(id=preview)
                previewObj.status = "COMPLETED"
                previewObj.results_url = scraper.results_url
                previewObj.save()
                results_count = scraper.get_results_count()
                return scraper.results_url, results_count
                
        elif lit_search.db.entrez_enum == "ct_gov":
            # scraper = clinical_trials.ClinicalTrials(lit_review_id, lit_search.id, user_id)
            scraper = clinical_trails_api.ClinicalTrials(lit_review_id, lit_search.id, user_id)

        elif lit_search.db.entrez_enum == "pmc_europe":
            scraper = europe_pmc_api.EuropePMC(lit_review_id, lit_search.id, user_id)

        elif lit_search.db.entrez_enum == "maude":
            scraper = maude_scraper.MaudeFda(lit_review_id, lit_search.id, user_id)

        elif lit_search.db.entrez_enum == "scholar":
            scraper = scholar_api.GoogleScholarApi(lit_review_id, lit_search.id, user_id)
            if preview:
                previewObj = SearchTermPreview.objects.get(id=preview)
                previewObj.status = "COMPLETED"
                previewObj.results_url = scraper.results_url
                previewObj.save()
                return scraper.results_url,  scraper.results_count
            
        elif lit_search.db.entrez_enum == "maude_recalls":
            scraper = maude_recalls_scraper.MaudeRecalls(lit_review_id, lit_search.id, user_id)


        ################### SCRAPING AND RETURNING RESULTS ######################
        # file_name, FILE_PATH = scraper.file_name, scraper.FILE_PATH
        if preview:
            scraper_results, result_count = scraper.search(is_preview=True)
        else:
            scraper_results, result_count = scraper.search()
        scraper_report = scraper.report

        ########################### PREVIEW RESULTS #############################
        if preview:
            # if preview auto search no need to import the search file just create preview articles
            if scraper_results == "No results found." or scraper_results == "Results out of range":
                previewObj = SearchTermPreview.objects.get(id=preview)
                previewObj.status = "COMPLETED"
                previewObj.save()
            else:
                proccess_preview(lit_search, preview, scraper_results)
                
            return None, scraper.results_count
        
        ################### IMPORTING SCRAPER SEARCH RESULTS ####################
        if scraper_results == "500 records meeting your search criteria returned. The results are incomplete - please narrow your search.":
            import_status = "INCOMPLETE-ERROR"
            lit_search.import_status = import_status
            lit_search.error_msg = f"{scraper_results}" 
            lit_search.save()
            scraper_report.status = "FAILED"
            scraper_report.result_count = result_count
            scraper_report.save()
            return "No results found."
        
        if scraper_results == "Results out of range" or scraper_results == "No results found.":
            lit_search.search_file_url = None
            lit_search.search_file = None
            lit_search.save()
            scraper_report.status = "EXCLUDED"
            scraper_report.result_count = result_count
            scraper_report.save()
            run_single_search(lit_search_id, result_count)
            return "Results out of range"

        if lit_search.db.entrez_enum in ["pubmed", "ct_gov"]:
            with open(scraper.FILE_PATH, 'wb') as f:
                f.write(scraper_results)

        # upload file aws s3
        # django accept max 100 character for file name 
        simplified_file_name = scraper.file_name 
        if len(scraper.file_name) > 80:
            file_format = simplified_file_name.split(".")[-1]
            simplified_file_name = scraper.file_name[:80]
            simplified_file_name = f"{simplified_file_name}.{file_format}"
            logger.debug("Simplified File Name: {0}".format(simplified_file_name))

        upload_to = "uploads/files/" + simplified_file_name
        file_url = upload_file_to_aws_s3(scraper.FILE_PATH, upload_to)
        lit_search.search_file = upload_to
        lit_search.save()
        logger.debug("lit url: {0}".format(lit_search.search_file_url))

        # Update scraper report
        scraper_report.status = "SUCCESS"
        scraper_report.results_file = file_url
        scraper_report.result_count = result_count
        logger.debug("results_file url length: " + str(len(file_url)))
        scraper_report.save()

        # Run search and import records
        run_single_search(lit_search_id)        
        return "success"
    
    except Exception as e:
        error_msg = str(traceback.format_exc())
        logger.error("error inside {} auto search scraper: {}".format(lit_search.db.entrez_enum, error_msg))
        lit_search = LiteratureSearch.objects.get(
            id=lit_search_id
        ) 
        import_status = "INCOMPLETE-ERROR"
        lit_search.import_status = import_status
        lit_search.error_msg = str(e)
        lit_search.save()
        return "error"
    

def send_scrapers_report_task():
    subject = 'Daily Run Auto Search Scrapers Summary'
    template = "email/scrapers_summary.html"
    today =  datetime.datetime.now().date()
    reports = ScraperReport.objects.filter(script_timestamp__date=today)
    context = {
        "reports": reports,
    }
    context = {'reports': reports}
    if settings.SUPPORT_EMAILS:
        recipient_email = settings.SUPPORT_EMAILS
    else:
        recipient_email = [settings.DEFAULT_FROM_EMAIL]
    
    # Render the email template with the given context
    email_body = render_to_string(template, context)

    # Create the EmailMessage object
    email = EmailMessage(subject, email_body, to=recipient_email)
    email.content_subtype = 'html'  # Set the content type to HTML
    
    # Optionally, you can attach files or set additional headers
    
    # Send the email
    email.send()