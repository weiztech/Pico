from backend.logger import logger 

from bs4 import BeautifulSoup
import requests
import re

from lit_reviews.database_scrapers.utils import Scraper 

##################################################
##  BELOW SCRAPER NO LONGER USED WE'RE USING  ####
##  INSTEAD WE'RE USING API check below folder ###
##  lit_reviews.database_apis.clinical_trails.py #
##################################################
class ClinicalTrials(Scraper):
    def __init__(self, review_id, search_id, user_id=None):
        super().__init__(review_id, search_id, file_format=".csv", user_id=user_id)
        self.url_filter = self.get_url_filter()
        # save filters to the report
        self.report.applied_filters = self.url_filter
        self.report.save()

        # form the search url
        self.search_term = self.lit_search.term
        self.url = f"https://classic.clinicaltrials.gov/ct2/results?cond=&term={self.search_term}{self.url_filter}"
        logger.debug(f"ct_gov url: {self.url}")
        
        # Creating the session
        try:
            self.session = self.create_session()
        except Exception as e:
            error_msg = "An error occurred while creating the session. ({})".format(e)
            self.capture_error(e)
            raise Exception(error_msg)

    def get_results_count(self):
        url =  self.url

        # Request to session
        try:
            req = self.session.get(url)
        except Exception as e:
            error_msg = "An error occurred while request to url. ({})".format(e)
            self.capture_error(error_msg)
            raise Exception(error_msg)
        
        # Creating BeautifulSoup object
        try:
            soup = BeautifulSoup(req.content, "lxml")
        except Exception as e:
            error_msg = "An error occurred while creating bs4 object. ({})".format(e)
            self.capture_error(error_msg)
            raise Exception(error_msg)
        
        # Getting message text from website
        try:
            message = soup.find("div", "ct-inner_content_wrapper").text.strip()

        except Exception as e:
            error_msg = """
            An error occurred while trying to extract the results message, please check your search query maybe it cannot be searched as given.
            because either the term is too long or the synntax format is wrong.
            """
            self.capture_error(error_msg)
            raise Exception(error_msg)

        
        # Extract the message for result_number
        try:
            if "No Studies found for" in message:
                result_number = 0       
            else:
                result_number = int(re.findall(r'(\d+).*?found for', message)[0])
            return result_number
        except Exception as e:
            error_msg = "An error occurred while extracting the message for result_number. ({})".format(e)
            self.capture_error(error_msg)
            raise Exception(error_msg)
        
    def search(self, is_preview=False):
        result_number = self.get_results_count()
        self.results_count = result_number
        url =  self.url
        
        # stop processing if results are out of range
        if self.is_excluded(result_number):
            return "Results out of range", result_number 
            
        # Request to session
        try:
            req = self.session.get(url)
        except Exception as e:
            error_msg = "An error occurred while request to url. ({})".format(e)
            self.capture_error(error_msg)
            raise Exception(error_msg)
        
        # Creating BeautifulSoup object
        try:
            soup = BeautifulSoup(req.content, "lxml")
        except Exception as e:
            error_msg = "An error occurred while creating bs4 object. ({})".format(e)
            self.capture_error(error_msg)
            raise Exception(error_msg)
        
        # Getting message text from website
        try:
            message = soup.find("div", "ct-inner_content_wrapper").text.strip()
        except Exception as e:
            error_msg = "An error occurred while extracting the message text. ({})".format(e)
            self.capture_error(error_msg)
            raise Exception(error_msg)
        
        # Extract the message for result_number
        try:
            if "No Studies found for" in message:
                result_number = 0       
            else:
                result_number = int(re.findall(r'(\d+).*?found for', message)[0])
        except Exception as e:
            error_msg = "An error occurred while extracting the message for result_number. ({})".format(e)
            self.capture_error(error_msg)
            raise Exception(error_msg)
        
        if result_number >= 1:            
            download_url = "https://classic.clinicaltrials.gov/ct2/results/download_fields?down_count=10000&down_flds=all&down_fmt=csv&term={SEARCH_TERM}{URL_FILTERS}&flds=a&flds=b&flds=y"
            download_url = download_url.format(
                SEARCH_TERM=self.search_term,
                URL_FILTERS=self.url_filter,
            )
            logger.debug(f"Download URL: {download_url}")

            # Request to download url
            try:
                req_download = self.session.get(download_url)
            except Exception as e:
                error_msg = "An error occurred while request to download url. ({})".format(e)
                self.capture_error(error_msg)
                raise Exception(error_msg)
        
            # Getting downloaded content
            try:
                content = req_download.content
            except Exception as e:
                error_msg = "An error occurred while getting the content. ({})".format(e)
                self.capture_error(error_msg)
                raise Exception(error_msg)
        
        else:
            content = None
 
        return content, result_number
                 
    def create_session(self):
        # Creating a session
        try:
            session = requests.Session()
        except Exception as e:
            error_msg = "An error occurred while creating the session. ({})".format(e)
            self.capture_error(error_msg)
            raise Exception(error_msg)
        
        # Setting the session headers
        try:
            session.headers = {"user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.5005.115 Safari/537.36 OPR/88.0.4412.53"}
        except Exception as e:
            error_msg = "An error occurred while setting session headers. ({})".format(e)
            self.capture_error(error_msg)
            raise Exception(error_msg)
        
        return session