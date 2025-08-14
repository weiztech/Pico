from backend.logger import logger 
import requests

from lit_reviews.database_scrapers.utils import Scraper 
from lit_reviews.utils.consts import (
    OTHER_TERMS,
    CONDITION_AND_DISEASE,
    INTERVENTIOO_TREAMENT,
    LOCATION,
)

class ClinicalTrials(Scraper):
    def __init__(self, review_id, search_id, user_id=None):
        super().__init__(review_id, search_id, file_format=".csv", user_id=user_id)

        self.url_filter = self.get_api_query_params()
        # save filters to the report
        self.report.applied_filters = self.url_filter
        self.report.save()
        # form the search url
        self.search_term = self.lit_search.term
        # build search URL
        root = f"https://clinicaltrials.gov/api/v2/studies?"
        search_expr = f"query.term={self.search_term}"
        search_field = self.lit_search.advanced_options and self.lit_search.advanced_options.get("search_field", None)
        if search_field and search_field != OTHER_TERMS:
            if search_field == CONDITION_AND_DISEASE:
                search_expr = f"query.cond={self.search_term}"
            elif search_field == INTERVENTIOO_TREAMENT:
                search_expr = f"query.intr={self.search_term}"
            elif search_field ==  LOCATION:
                search_expr = f"query.locn={self.search_term}"

        self.url = f"{root}{search_expr}&{self.url_filter}"
        logger.debug(f"ct_gov API URL: {self.url}")


    def get_results_count(self):
        getCountURL =  self.url + "&countTotal=true&pageSize=1"

        # Request to session
        try:
            res = requests.get(getCountURL)
            if res.status_code == 200:
                resDict = res.json()
                results_count = resDict.get("totalCount")
                return int(results_count)

            else:
                error_msg = "An error occurred while request API url to get results total count ({})".format(str(res.text))
                self.capture_error(error_msg)
                raise Exception(error_msg)
           
        except Exception as e:
            error_msg = "An error occurred while request to url. ({})".format(e)
            self.capture_error(error_msg)
            raise Exception(error_msg)
        
    def search(self, is_preview=False):
        result_number = self.get_results_count()
        logger.debug("CT Gove API Response Total Count: " + str(result_number))
        self.results_count = result_number
        url =  self.url + "&format=csv&pageSize=1000"
        
        # stop processing if results are out of range
        if self.is_excluded(result_number):
            return "Results out of range", result_number 
            
        # Request to session
        try:
            res = requests.get(url)
        except Exception as e:
            error_msg = "An error occurred while request to url. ({})".format(e)
            self.capture_error(error_msg)
            raise Exception(error_msg)
    
        # Getting downloaded content
        try:
            content = res.text.encode()
        except Exception as e:
            error_msg = "An error occurred while getting the content. ({})".format(e)
            self.capture_error(error_msg)
            raise Exception(error_msg)
 
        return content, result_number