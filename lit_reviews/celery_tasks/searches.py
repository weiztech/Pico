import traceback
import time
import os
import datetime, pytz

from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files import File
from backend.logger import logger

from lit_reviews.helpers.articles import improve_file_styling
from lit_reviews.helpers.generic import create_tmp_file
from lit_reviews.report_builder.utils import validate_search_terms
from client_portal.models import *
from lit_reviews.models import *
from lit_reviews.pmc_api import (
    materialize_search_proposal,
)
from lit_reviews.database_imports import (
    pubmed_pmc,
    cochrane,
    ct_gov,
    embase,
    google_scholar,
    maude_recalls,
    maude,
    pmc_europe,
)
from lit_reviews.helpers.search_terms import (
    validate_input_columns,
)


def run_single_search_task(lit_search_id, expected_result_count=None, user_id=None): 
    from lit_reviews.tasks import remove_duplicate_async
    from lit_reviews.tasks import async_log_action_literature_search_results
    # Get Search ID from Task (passed as parameter)
    lit_search = LiteratureSearch.objects.get(
        id=lit_search_id
    ) 
    lit_search.script_time = datetime.datetime.now(pytz.utc)
    lit_search.save()
    logger.info(f"user_id: {user_id}")
    # if we do have expected_result_count this search will be excluded (0 or > max results)
    if expected_result_count is None:
        # process the search file and write it to /tmp/uuid  so we can pass it to parse_text
        file_name = lit_search.search_file.name.replace("uploads/files/", "")
        fmp_file_content = lit_search.search_file.read()
        tmp_file = create_tmp_file(file_name, fmp_file_content)
        search_file = tmp_file

        # re-style/organize the excel file if it's a maude search
        if lit_search.db.entrez_enum == "maude" or lit_search.db.entrez_enum == "maude_recalls":
            try:
                styled_file_name = lit_search.term + "_" + file_name.replace(".csv", ".xls") 
                styled_file_path = improve_file_styling(tmp_file, styled_file_name)
                with open(styled_file_path, 'rb') as styled_file:
                    lit_search.search_file.save(styled_file_name, File(styled_file), save=True)
                os.remove(styled_file_path)

            except Exception as e:
                logger.warning("Failed to convert csv file to excel and organize it for maude search.")
                logger.warning("Traceback: {0}".format(traceback.format_exc()))
                pass

        # vlidate columns for google scholar db
        db_name = lit_search.db.entrez_enum
        try:
            is_valid = validate_input_columns(search_file, db_name)

        except Exception as e:
            logger.error("Traceback: {0}".format(traceback.format_exc()))
            import_status = "INCOMPLETE-ERROR"
            lit_search.import_status = import_status
            lit_search.error_msg = str(e)
            lit_search.save()
            # Log failure action
            async_log_action_literature_search_results.delay(
                user_id,
                "Failed Literature Search",
                f"The search term '{lit_search.term}' for database '{lit_search.db}'  with error: {lit_search.error_msg}.",
                lit_search.id,
                lit_search.literature_review.id,
            )
            return
        
        if not is_valid: 
            logger.debug("validation issue!")
            import_status = "INCOMPLETE-ERROR"
            lit_search.import_status = import_status
            lit_search.error_msg = """
            The csv file you've uploaded doesn't contain the correct columns, 
            csv file for google scholar should include the following columns: 
            Title, Abstract, Citation MLA, Citation APA.
            """
            lit_search.save()
             # Log failure action
            async_log_action_literature_search_results.delay(
                user_id,
                "Failed Literature Search",
                f"The search term '{lit_search.term}' for database '{lit_search.db}'  with error: {lit_search.error_msg}.",
                lit_search.id,
                lit_search.literature_review.id,
            )

            return 
        
    else:
        search_file = ""  
        tmp_file = ""
    
    # Clear out all ArticleReview objects FK -> Search (because we are re-running this).
    ArticleReview.objects.filter(search=lit_search).delete()
    AdverseEventReview.objects.filter(search=lit_search).delete()
    AdverseRecallReview.objects.filter(search=lit_search).delete()

    # Run proper data import sequence (based on Database type from Search object), with filenamex
    try:
        if lit_search.db.entrez_enum == "pmc" or lit_search.db.entrez_enum == "pubmed":
            if ".xml" in search_file:
                results = pubmed_pmc.parse_xml(
                    search_file,
                    lit_search.term,
                    lit_search.literature_review.id,
                    lit_search.db.entrez_enum,
                    expected_result_count,
                    lit_search_id=lit_search.id,
                )
            else:
                results = pubmed_pmc.parse_text(
                    search_file,
                    lit_search.term,
                    lit_search.literature_review.id,
                    lit_search.db.entrez_enum,
                    expected_result_count,
                    lit_search_id=lit_search.id,
                )

        elif lit_search.db.entrez_enum == "cochrane":
            results = cochrane.parse_text(
                search_file,
                lit_search.term,
                lit_search.literature_review.id,
                expected_result_count,
                lit_search_id=lit_search.id,
            )

        elif lit_search.db.entrez_enum == "ct_gov" or lit_search.db.entrez_enum == "ctgov":
            results = ct_gov.parse_text(
                search_file,
                lit_search.term,
                lit_search.literature_review.id,
                expected_result_count,
                lit_search_id=lit_search.id,
            )

        elif lit_search.db.entrez_enum == "embase":
            results = embase.parse_text(
                search_file,
                lit_search.term,
                lit_search.literature_review.id,
                lit_search_id=lit_search.id,
            )

        if lit_search.db.entrez_enum == "scholar":
            if ".ris" in search_file:
                results = google_scholar.parse_ris(
                    search_file,
                    lit_search.term,
                    lit_search.literature_review.id,
                )
                
            else:
                results = google_scholar.parse_scholar(
                    search_file,
                    lit_search.term,
                    lit_search.literature_review.id,
                )

        elif lit_search.db.entrez_enum == "maude":
            if ".zip" in search_file:
                results = maude.parse_zip(
                    search_file, lit_search.term, lit_search.literature_review.id, lit_search_id=lit_search.id,
                )
            else:    
                results = maude.parse_workbook(
                    search_file, 
                    lit_search.term, 
                    lit_search.literature_review.id, 
                    lit_search_id=lit_search.id, 
                    expected_result_count=expected_result_count,
                )

        elif lit_search.db.entrez_enum == "maude_recalls":
            if ".zip" in search_file:
                results = maude_recalls.parse_zip(
                    search_file, lit_search.term, lit_search.literature_review.id, lit_search_id=lit_search.id,
                )
            else:
                results = maude_recalls.parse_workbook(
                    search_file, 
                    lit_search.term, 
                    lit_search.literature_review.id, 
                    lit_search_id=lit_search.id, 
                    expected_result_count=expected_result_count,
                )

        elif lit_search.db.entrez_enum == "pmc_europe":
            results = pmc_europe.parse_text(
                search_file,
                lit_search.term,
                lit_search.literature_review.id,
                expected_result_count,
                lit_search_id=lit_search.id,
            )

            # TODO Z:
            # Check results of import (number of articles processed vs. number of ArticleReview objects created)
            # example results object   {"processed_articles": 0,  "imported_articles": 0, "import_status": "COMPLETE" }

            ## Note for Z,  you will need to modify EARCH database_import module to count these values properly.
            ## Please start with one... and then we can review it together.

            # Save Search object and update timestamp  + new status fields (success/incomplete)
        
        # refetch literature search in case in updates done inside database imports scripts
        lit_search =  LiteratureSearch.objects.get(id=lit_search_id)
        lit_search.processed_articles = results["processed_articles"]
        lit_search.imported_articles = results["imported_articles"]
        lit_search.import_status = results["import_status"]
        lit_search.duplicate_articles = None
        lit_search.error_msg = None
        lit_search.save()

        results_dups =  results.get("duplicates", None)
        # remove_duplicate_async.delay(lit_search.literature_review.id, lit_search.id, results_dups)
        duplication_report, created = DuplicationReport.objects.get_or_create(literature_review_id=lit_search.literature_review.id)
        duplication_report.needs_update = True
        duplication_report.save()

        if lit_search.limit_excluded:
            # Log exclusion action
            async_log_action_literature_search_results.delay(
                user_id,
                "Excluded Literature Search",
                f"The search term '{lit_search.term}' or database '{lit_search.db}' completed successfully, but all results were excluded.",
                lit_search.id,
                lit_search.literature_review.id,
            )
        else:
            # Log success action
            async_log_action_literature_search_results.delay(
                user_id,
                "Completed Literature Search",
                f"The search term '{lit_search.term}' for database '{lit_search.db}' completed successfully with {lit_search.imported_articles} imported articles.",
                lit_search.id,
                lit_search.literature_review.id,
            )

    except Exception as e:
        error_track = str(traceback.format_exc())
        logger.error("Error inside run single search: {0}".format(error_track))
        import_status = "INCOMPLETE-ERROR"
        lit_search.import_status = import_status
        lit_search.duplicate_articles = None
        if "OSError: Expected start" in error_track:
            lit_search.error_msg = "Error reading the RIS file. Please ensure that the first two comment lines are removed and try again."
        else:
            lit_search.error_msg = str(e)

        lit_search.save()

        # remove_duplicate_async.delay(lit_search.literature_review.id, lit_search.id)
        duplication_report, created = DuplicationReport.objects.get_or_create(literature_review_id=lit_search.literature_review.id)
        duplication_report.needs_update = True
        duplication_report.save()

        # Log failure action
        async_log_action_literature_search_results.delay(
            user_id,
            "Failed Literature Search",
            f"The search term '{lit_search.term}' for database '{lit_search.db}'  with error: {lit_search.error_msg}.",
            lit_search.id,
            lit_search.literature_review.id,
        )
        
    if tmp_file:
        os.remove(tmp_file)


def process_single_prop_task(prop_id, batch_size=200):
    logger.debug("single search prop materialize")
    proposal = LiteratureReviewSearchProposal.objects.get(id=prop_id)
    try:
        search = LiteratureSearch.objects.get(
            term=proposal.term,
            db=proposal.db,
            literature_review=proposal.literature_review,
        )
        search.delete()

    except Exception as e:
        logger.error("no search found, no need to delete: {0}".format(str(e)))

    ars = ArticleReview.objects.filter(
        search__term=proposal.term,
        search__db=proposal.db,
        search__literature_review=proposal.literature_review,
    )
    logger.debug("{0} ArticleReviews to delete".format(len(ars)))
    materialize_search_proposal(proposal, batch_size)


def process_props_task(review_id, batch_size=100):
    proposals = LiteratureReviewSearchProposal.objects.filter(
        literature_review__id=review_id
    )
    logger.debug("Total Searches to Run: {0}".format(str(len(proposals))))
    for index, proposal in enumerate(proposals):
        time.sleep(5)
        materialize_search_proposal(proposal, batch_size)
        logger.debug("search completed run for #: {0}".format(str(index + 1)))

    logger.debug("ALL SEARCHES COMPLETE")
    return True


def validate_search_terms_task(lit_review_id):
    # validate report here.
    lit_review = LiteratureReview.objects.get(id=lit_review_id)
    validator = SearchTermValidator.objects.get_or_create(literature_review=lit_review)[0]
    validator.status = "RUNNING"
    validator.save()

    try:
        validate_search_terms(lit_review_id)
        validator.status = "COMPLETE"
        validator.save()

    except Exception as e:
        logger.error("caught validation error: {0}".format(str(e)))
        validator.status = "INCOMPLETE-ERROR"
        validator.error_msg = "Error in Validating Report \n " + str(e)
        validator.save()
        return None
    

def search_clear_results_task(lit_review_id, searches_ids):
    lit_searchs = LiteratureSearch.objects.filter(id__in=searches_ids, literature_review__id=lit_review_id)
    for search in lit_searchs:
        search.ae_events.clear()
        search.ae_recalls.clear()
        ArticleReview.objects.filter(search=search).all().delete()
        if search.db.is_recall or search.db.is_ae:
            AdverseEventReview.objects.filter(search=search).delete()
            AdverseRecallReview.objects.filter(search=search).delete()

        search.import_status = "NOT RUN"
        search.error_msg = None
        search.imported_articles = None
        search.processed_articles = None
        search.result_count = None
        search.save()