import datetime
import traceback
import time 
import os 
import uuid
from selenium import webdriver
from django.contrib.auth import get_user_model
from django.core.files import File
from dateutil.relativedelta import relativedelta
from selenium.webdriver.chrome.service import Service

from backend.logger import logger
from backend import settings
from lit_reviews.helpers.generic import create_chrome_driver
from lit_reviews.models import (
    SearchConfiguration,
    SearchParameter,
    SearchProtocol,
    LiteratureSearch,
    ScraperReport,
    LiteratureReview,
)
from lit_reviews.utils.consts import (
    pubmed_age,
    pubmed_article_types,
    clinical_trials_study_results,
    clinical_trials_age_group,
    clinical_trials_expanded_access_status,
    clinical_trials_recruitment_status,
    clinical_trials_api_age_group,
    clinical_trials_api_overall_status,
)
User = get_user_model()

DEFAULT_EXCLUSION_MAX = 3000

class Scraper:
    """
    A Base Class for all database web scrapers and apis we have on place for automating:
    1. Automating article import process "Run Searches - Run Aauto Search"
    2. Getting Expected Results Count - Search Terms View.
    
    Params:
    review_id: Literature Review Object ID.
    search_id: Literature Search Object ID.
    file_format: every database accept different file formats, the correct format should be provided.
    user_id: Who run the search ? or created the search term ?
    date_format: every database accept different date format.
    """
        
    def __init__(self, review_id, search_id, file_format=None, user_id=None, date_format=None):
        # get init data values
        self.DEFAULT_DOWNLOAD_DIRECTORY  = settings.FULL_TMP_ROOT
        self.file_format = file_format
        lit_review = LiteratureReview.objects.get(id=review_id)
        search_protocol = SearchProtocol.objects.get(literature_review=lit_review)
        self.max_results = search_protocol.max_imported_search_results
        self.lit_search = LiteratureSearch.objects.get(id=search_id) 
        self.disable_exclusion = self.lit_search.disable_exclusion if self.lit_search.disable_exclusion else False
        # max results number that can be included even if automatic exclution is disactivated
        self.EXCLUSION_MAX = DEFAULT_EXCLUSION_MAX

        # Get search filters like start date, end date and some other filters that are specific for each database.
        # For most scraper we use initiate_search_params to get those parameters and prepare them
        # except for Pubmed and Clinical Trials we use get_url_filter instead
        # and we use get_api_query_params for the API connection currently onlt available for clinical trials.
        self.initiate_search_params(date_format)
        self.create_file_path()
        user = User.objects.filter(pk=user_id).first()
        report = ScraperReport.objects.create(
            start_date=self.start_date,
            end_date=self.end_date,
            search=self.lit_search,
            search_term=self.lit_search.term,
            database_name=self.lit_search.db.name,
            user=user,
            literature_review=lit_review,
        )
        self.report = report
        logger.info(f"Running Search for {self.lit_search}")

    def capture_error(self, error_msg, driver=None):
        report = self.report
        report.errors = error_msg

        if driver:
            # Take error screenshot
            UUID = str(uuid.uuid4())
            img_name = "error screenshot-{}.png".format(UUID)
            tmp_screenshot_path = os.path.join(settings.TMP_ROOT, img_name)    
            driver.save_screenshot(tmp_screenshot_path)
            local_file = open(tmp_screenshot_path, "rb")
            screenshot_img = File(local_file)
            report.failure_stage_screenshot = screenshot_img
            report.failure_stage_screenshot.save(img_name, screenshot_img)
            local_file.close()
            report.status = "FAILED"
            report.save()
            

    def clear_downloaded_file_path(self, file_name):
        """
        Clear the default file from DEFAULT_DOWNLOAD_DIRECTORY.
        to delete any old/stored file and make sure to use the
        default name for only the new searched term.
        """
        try:
            os.rename(os.path.join(self.DEFAULT_DOWNLOAD_DIRECTORY, file_name), os.path.join(self.DEFAULT_DOWNLOAD_DIRECTORY, "citation-export-{}.txt".format(str(uuid.uuid4()))))
        except:
            pass

    def get_api_query_params(self):
        """
        Generate API URL Query Params
        """
        lit_search = self.lit_search

        try:
            search_config = SearchConfiguration.objects.get(
                database=lit_search.db,
                literature_review=lit_search.literature_review
            )

            if lit_search.db.entrez_enum == "ct_gov":
                if lit_search.literature_review.is_autosearch:
                    start_date = lit_search.start_search_interval.strftime("%Y/%m/%d")
                    end_date = lit_search.end_search_interval.strftime("%Y/%m/%d")
                
                elif lit_search.is_notebook_search:
                    start_date = lit_search.start_search_interval.strftime("%Y/%m/%d")
                    end_date = lit_search.end_search_interval.strftime("%Y/%m/%d")

                else:
                    start_date_str = SearchParameter.objects.get(
                        search_config=search_config, name="Start Date"
                    ).value
                    start_date = datetime.datetime.strptime(start_date_str, "%Y-%m-%d").strftime("%m/%d/%Y")

                    end_date_str = SearchParameter.objects.get(
                        search_config=search_config, name="End Date"
                    ).value
                    end_date = datetime.datetime.strptime(end_date_str, "%Y-%m-%d").strftime("%m/%d/%Y")
                    if not start_date or not end_date:
                        raise Exception("Please ensure that the search parameters for this database are set on the Search Protocol page before running your search. It appears the start or end date is missing for this database.")
                    
                age = SearchParameter.objects.get(
                    search_config=search_config, name="Age Group"
                ).value
                age_list = age.split(",") if age else ""

                status_r = SearchParameter.objects.get(
                    search_config=search_config, name="Recruitment Status"
                ).value
                status_r_list = status_r.split(",") if status_r else ""

                status_e = SearchParameter.objects.get(
                    search_config=search_config, name="Expanded Access Status"
                ).value
                status_e_list = status_e.split(",") if status_e else ""

                study_results = SearchParameter.objects.get(
                    search_config=search_config, name="Study Results"
                ).value

                params = "" 
                dates_filter_param = f"filter.advanced=AREA[ResultsFirstPostDate]RANGE[{start_date}, {end_date}]"
                params += dates_filter_param
                age_params = " AND ("

                if age_list:
                    for age_item in age_list:
                        age_value = clinical_trials_api_age_group[age_item]
                        if age_params == " AND (":
                            age_params +=f" AREA[StdAge]{age_value}"
                        else:
                            age_params +=f" OR AREA[StdAge]{age_value}"

                if age_params != " AND (":
                    age_params += " )"
                    params += age_params
                
                status_params = " AND ("
                if len(status_r_list) and not len(status_e_list):
                    status_params += "AREA[OverallStatus]AVAILABLE OR AREA[OverallStatus]NO_LONGER_AVAILABLE OR AREA[OverallStatus]TEMPORARILY_NOT_AVAILABLE OR AREA[OverallStatus]APPROVED_FOR_MARKETING"
                elif len(status_e_list) and not len(status_r_list):
                    status_params += "AREA[OverallStatus]NOT_YET_RECRUITING OR AREA[OverallStatus]RECRUITING OR AREA[OverallStatus]ENROLLING_BY_INVITATION OR AREA[OverallStatus]ACTIVE_NOT_RECRUITING OR AREA[OverallStatus]SUSPENDED OR AREA[OverallStatus]TERMINATED OR AREA[OverallStatus]COMPLETED OR AREA[OverallStatus]WITHDRAWN OR AREA[OverallStatus]UNKNOWN"   

                if status_r_list:
                    for status_item in status_r_list:
                        status_value = clinical_trials_api_overall_status[status_item]
                        if status_params == " AND (":
                            status_params += f" AREA[OverallStatus]{status_value}"
                        else:
                            status_params += f" OR AREA[OverallStatus]{status_value}"

                if status_e_list:
                    for status_item in status_e_list:
                        status_value = clinical_trials_api_overall_status[status_item]
                        if status_params == " AND (":
                            status_params += f" AREA[OverallStatus]{status_value}"
                        else:
                            status_params += f" OR AREA[OverallStatus]{status_value}"
                
                if status_params != " AND (":
                    status_params += " )"
                    params += status_params

                # if study_results:
                #     study_results_value = clinical_trials_study_results[study_results]
                #     params += f"&rslt={study_results_value}"

                return params 

            logger.warning(f"We have no handler for the provided database: {lit_search.db.name}")
            return None 
            
        except Exception as error:
            error_track = traceback.format_exc()
            logger.error(f"Error wile getting search params for {lit_search.db} error traceback: {error_track}")
            raise Exception("Please ensure that the search parameters for this database are set on the Search Protocol page before running your search. It appears the start or end date is missing for this database.")


    def get_url_filter(self):
        """
        Generate URL Query Params Filters for Trails and Pubmed Scrapers.
        """
        lit_search = self.lit_search
        try:
            search_config = SearchConfiguration.objects.get(
                database=lit_search.db,
                literature_review=lit_search.literature_review
            )
            
            if lit_search.db.entrez_enum == "pubmed":
                if lit_search.literature_review.is_autosearch:
                    start_date = lit_search.start_search_interval.strftime("%Y/%m/%d")
                    end_date = lit_search.end_search_interval.strftime("%Y/%m/%d")
                
                elif lit_search.is_notebook_search:
                    start_date = lit_search.start_search_interval.strftime("%Y/%m/%d")
                    end_date = lit_search.end_search_interval.strftime("%Y/%m/%d")
                
                else:
                    start_date = SearchParameter.objects.get(
                        search_config=search_config, name="Start Date"
                    ).value.replace("-", "/")
                    end_date = SearchParameter.objects.get(
                        search_config=search_config, name="End Date"
                    ).value.replace("-", "/")
                    if not start_date or not end_date:
                        raise Exception("Please ensure that the search parameters for this database are set on the Search Protocol page before running your search. It appears the start or end date is missing for this database.")

                age = SearchParameter.objects.get(
                    search_config=search_config, name="Age"
                ).value
                article_type = SearchParameter.objects.get(
                    search_config=search_config, name="Article Type"
                ).value

                url_params = "" 
                dates = "{}-{}".format(start_date, end_date)
                url_params += f"&filter=dates.{dates}"

                age_list = age.split(",") if age else ""
                article_type_list = article_type.split(",") if article_type else ""

                if article_type_list:
                    for article in article_type_list:
                        article_value = pubmed_article_types[article]
                        url_params += f"&filter=pubt.{article_value}"
                
                if age_list:
                    for age in age_list:
                        age_value = pubmed_age[age]
                        url_params += f"&filter=age.{age_value}"

                return url_params

            if lit_search.db.entrez_enum == "ct_gov":
                if lit_search.literature_review.is_autosearch:
                    start_date = lit_search.start_search_interval.strftime("%Y/%m/%d")
                    end_date = lit_search.end_search_interval.strftime("%Y/%m/%d")
                
                elif lit_search.is_notebook_search:
                    start_date = lit_search.start_search_interval.strftime("%Y/%m/%d")
                    end_date = lit_search.end_search_interval.strftime("%Y/%m/%d")

                else:
                    start_date_str = SearchParameter.objects.get(
                        search_config=search_config, name="Start Date"
                    ).value
                    start_date = datetime.datetime.strptime(start_date_str, "%Y-%m-%d").strftime("%m/%d/%Y")

                    end_date_str = SearchParameter.objects.get(
                        search_config=search_config, name="End Date"
                    ).value
                    end_date = datetime.datetime.strptime(end_date_str, "%Y-%m-%d").strftime("%m/%d/%Y")
                    if not start_date or not end_date:
                        raise Exception("Please ensure that the search parameters for this database are set on the Search Protocol page before running your search. It appears the start or end date is missing for this database.")
                    
                age = SearchParameter.objects.get(
                    search_config=search_config, name="Age Group"
                ).value
                age_list = age.split(",") if age else ""

                status_r = SearchParameter.objects.get(
                    search_config=search_config, name="Recruitment Status"
                ).value
                status_r_list = status_r.split(",") if status_r else ""

                status_e = SearchParameter.objects.get(
                    search_config=search_config, name="Expanded Access Status"
                ).value
                status_e_list = status_e.split(",") if status_e else ""

                study_results = SearchParameter.objects.get(
                    search_config=search_config, name="Study Results"
                ).value

                url_params = "" 
                url_params += f"&rfpd_s={start_date}&rfpd_e={end_date}"
                if age_list:
                    for age_item in age_list:
                        age_value = clinical_trials_age_group[age_item]
                        url_params += f"&age={age_value}"

                if status_r_list:
                    for status_item in status_r_list:
                        status_value = clinical_trials_recruitment_status[status_item]
                        url_params += f"&recrs={status_value}"

                if status_e_list:
                    for status_item in status_e_list:
                        status_value = clinical_trials_expanded_access_status[status_item]
                        url_params += f"&recrs={status_value}"

                if study_results:
                    study_results_value = clinical_trials_study_results[study_results]
                    url_params += f"&rslt={study_results_value}"

                return url_params 

            logger.warning(f"We have no handler for the provided database: {lit_search.db.name}")
            return None 
            
        except Exception as error:
            error_track = traceback.format_exc()
            logger.error(f"Error wile getting search params for {lit_search.db} error traceback: {error_track}")
            raise Exception("Please ensure that the search parameters for this database are set on the Search Protocol page before running your search. It appears the start or end date is missing for this database.")

    def initiate_search_params(self, date_format=None):
        ##############################################################
        # Get Search Params for scrapers start date, end date and extra ones.
        # for Pubmed and Clinical Trials we use get_url_filter instead.
        ##############################################################
        lit_search = self.lit_search
        try:
            protocol = SearchProtocol.objects.get(literature_review=lit_search.literature_review)
            if lit_search.db.is_ae or lit_search.db.is_recall:
                years_back = protocol.ae_years_back
                protocol_start_date = protocol.ae_start_date_of_search
                protocol_end_date = protocol.ae_date_of_search
            else:
                years_back = protocol.years_back
                protocol_start_date = protocol.lit_start_date_of_search
                protocol_end_date = protocol.lit_date_of_search

            AVAILABLE_SCRAPERS = ["pmc", "cochrane", "pubmed", "ct_gov", "scholar"]
            if lit_search.db.entrez_enum in AVAILABLE_SCRAPERS:
                if lit_search.literature_review.is_autosearch:
                    start_date = lit_search.start_search_interval
                    end_date = lit_search.end_search_interval
                
                elif lit_search.is_notebook_search:
                    start_date = lit_search.start_search_interval
                    end_date = lit_search.end_search_interval

                else:
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
                    start_date = datetime.datetime.strptime(start_date_str, "%Y-%m-%d")
                    end_date = datetime.datetime.strptime(end_date_str, "%Y-%m-%d")

            else:   
                if lit_search.literature_review.is_autosearch:
                    start_date = lit_search.start_search_interval
                    end_date = lit_search.end_search_interval
                
                elif lit_search.is_notebook_search:
                    start_date = lit_search.start_search_interval
                    end_date = lit_search.end_search_interval
                
                else:
                    if protocol_start_date:
                        start_date = protocol_start_date
                        end_date = protocol_end_date
                        
                    else:
                        ONE_YEAR_DAYS = 365
                        days = ONE_YEAR_DAYS * years_back
                        if protocol_end_date:
                            end_date = protocol_end_date
                            start_date = protocol_end_date - relativedelta(years=years_back)
                            
                        else:
                            end_date = datetime.datetime.now().date()
                            start_date =  datetime.datetime.now() - datetime.timedelta(days=days)
                            start_date = start_date.date()

                    if date_format:
                        start_date = start_date.strftime(date_format)
                        end_date = end_date.strftime(date_format)

            self.start_date = start_date
            self.end_date = end_date
            return start_date, end_date
    
        except Exception as error:
            error_track = traceback.format_exc()
            logger.error(f"Error wile getting search params for {lit_search.db} error traceback: {error_track}")
            raise Exception("Please ensure that the search parameters for this database are set on the Search Protocol page before running your search. It appears the start or end date is missing for this database.")

    def create_file_path(self):
        """
        Return scraper resuts File name and file path.
        """
        search_term = self.lit_search.term
        db_name = self.lit_search.db.name
        TMP_ROOT = settings.TMP_ROOT
        t = time.localtime()
        timestamp = time.strftime("%b-%d-%Y_%H%M", t)
        search_term =  search_term.replace("/", "").replace("'", "").replace('"', '')
        if len(search_term) > 70:
            search_term  = search_term[0:30] + "..." + search_term[len(search_term)-30:len(search_term)]

        UUID = str(uuid.uuid4())
        file_name = "{}-{}-{}-{}".format(db_name, search_term, timestamp, UUID)
        if self.file_format:
            file_name = file_name + self.file_format
        FILE_PATH = os.path.join(TMP_ROOT, file_name)

        self.FILE_PATH = FILE_PATH
        self.file_name = file_name
        return file_name, FILE_PATH

    def is_excluded(self, result_count):
        NO_RESULTS = result_count < 1
        MAX_LIMIT_REACHED = not self.disable_exclusion and result_count > self.max_results
        EXCLUSION_MAX_LIMIT_REACHED = result_count > self.EXCLUSION_MAX

        # exclude if results are out of range before running the search
        # if NO_RESULTS or MAX_LIMIT_REACHED or EXCLUSION_MAX_LIMIT_REACHED:
        # we need to consider only EXCLUSION_MAX_LIMIT_REACHED since we need to store the file any way 
        # in case the user wants to force the import instead of auto excluding
        if NO_RESULTS or EXCLUSION_MAX_LIMIT_REACHED:
            return True

    def create_browser(self):
        return create_chrome_driver(self.DEFAULT_DOWNLOAD_DIRECTORY)
    

def get_expected_result_count(db, lit_search, lit_review_id, term, user_id=None):
    from lit_reviews.database_scrapers import pubmed, pubmed_central, clinical_trials, cochranelibrary
    expected_result_count = -1

    try:
        if db.entrez_enum == "pubmed":
            pubmed_obj = pubmed.Pubmed(lit_review_id, lit_search.id, user_id)
            expected_result_count = int(str(pubmed_obj.result_count).replace(",", ""))

        elif db.entrez_enum == "pmc":
            scraper = pubmed_central.PubmedCentral(lit_review_id, lit_search.id, user_id)
            result_count =  scraper.get_results_count()
            expected_result_count = result_count

        elif db.entrez_enum == "ct_gov":
            scraper = clinical_trials.ClinicalTrials(lit_review_id, lit_search.id, user_id)
            result_number = scraper.get_results_count()
            expected_result_count = result_number 
        
        elif db.entrez_enum == "cochrane":
            scraper = cochranelibrary.CochraneLibrary(lit_review_id, lit_search.id, user_id)
            result_number = scraper.get_results_count()
            expected_result_count = result_number 

    except Exception as error:
        logger.error("Failed to get expected result count for {} {} with the following error {}".format(term, db, error))
        error_track = traceback.format_exc()
        logger.error(f"error traceback: {error_track}")

    logger.info("expected result count received for {0} : {1}".format(lit_search.db.name, expected_result_count))
    return expected_result_count