from bs4 import BeautifulSoup
import requests
import re
import traceback
import urllib.parse

from backend.logger import logger 
from lit_reviews.database_scrapers.utils import Scraper

class Pubmed(Scraper):
    def __init__(self, review_id, search_id, user_id=None):
        super().__init__(review_id, search_id, file_format=".txt", user_id=user_id)
        # clear special characters
        search_term = self.lit_search.term
        if "“" in search_term or "”" in search_term:
            search_term = search_term.replace("“", '"').replace("”", '"')
        if "&" in search_term or "?" in search_term:
            search_term = urllib.parse.quote(search_term, safe='')

        self.original_term = self.lit_search.term
        self.search_term = search_term 
        self.url_filter = self.get_url_filter()
        # save filters to the report
        self.report.applied_filters = self.url_filter
        self.report.save()
        logger.debug(f"URL FIlter: {self.url_filter}")
        
        # Create a session object
        self.session = self.create_session()
    
        # Make a listing url
        listing_url = f"https://pubmed.ncbi.nlm.nih.gov/?term={search_term}{self.url_filter}"
        # https://pubmed.ncbi.nlm.nih.gov/?term=term&filter=pubt.booksdocs&filter=age.newborn
        self.results_url = listing_url
        logger.debug("url : " + listing_url)

        # Get csrf-token and cookie from website html and return headers
        self.csrf_token, cookie, self.results_count = self.get_configs(listing_url)

        # Set cookie and referer to session's header
        self.session.headers["cookie"] = cookie
        self.session.headers["referer"] = listing_url.encode("utf-8")

        
    def search(self, is_preview=False):
        result_count = int(str(self.results_count).replace(",", ""))
        self.results_count = result_count
        if self.is_excluded(result_count):
            return "Results out of range", result_count  

        else:
            # Make a post request to download the results
            try:
                filters = self.url_filter.split("&filter=")
                # remove empty filter
                filters.pop(0)

                req = self.session.post("https://pubmed.ncbi.nlm.nih.gov/results-export-search-data/",
                        data={
                            "csrfmiddlewaretoken": self.csrf_token,
                            "results-format": "pubmed-text",
                            "term":self.original_term.encode("utf-8"),
                            "filter": filters,
                        }
                    )

                if req.status_code != 200:
                    error_msg = "status_code is {}".format(req.status_code)
                    self.capture_error(error_msg)
                    raise Exception(error_msg)
                
            except Exception as e:
                print("Error : {}".format(e))
                raise e
        return req.content, result_count
        
    def create_session(self):
        # Creating a session object
        session = requests.Session()
        
        # Set initial headers
        session.headers = {
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.4951.67 Safari/537.36 OPR/87.0.4390.45"
        }
        
        return session
    
    def get_response(self, listing_url):
        # Make a get request to term listing_url
        try:
            req = self.session.get(listing_url)
            if req.status_code != 200:
                error_msg = "status_code is {}".format(req.status_code)
                self.capture_error(error_msg)
                raise Exception(error_msg)
            
            else:
                return req

        except Exception as e:
            logger.error("Error : {}".format(str(e)))
            error_msg = "Error : {}".format(e)
            self.capture_error(error_msg)
            raise Exception(error_msg)
        
    def get_configs(self, listing_url):
        reponse = self.get_response(listing_url)

        # Create a BeautifulSoup object
        soup = BeautifulSoup(reponse.text, "lxml")
        try:
            # Get result count
            results_amount = soup.find("div", attrs={"class": "results-amount"})
            if not results_amount:
                # if there is no such a div than it could be the case that there is only one result
                no_results_msg = soup.find("span", attrs={"class": "single-result-redirect-message"})
                if no_results_msg and "1" in str(no_results_msg):
                    result_count = 1

            elif "No results were found" in str(results_amount):
                result_count = 0
            else:
                result_count = results_amount.find("span", attrs={"class": "value"}).text
                
        except Exception as e:
            error_msg = str(traceback.format_exc())
            logger.error("Couldn't get result count : " + error_msg)
            result_count = -1
            # raise Exception("Error while trying to get result count : {}".format(e))

        # Extract csrf_token from page source (html)
        csrf_token = soup.find("input", attrs={"name": "csrfmiddlewaretoken"}).get("value")
        
        # Extract key and value from cookie
        cookies_dict = {key:value for key, value in re.findall(r'(.*?)=(.*?); ', reponse.headers["Set-Cookie"].replace("Secure, ", ""))}

        # Create cookie with necessary params 
        cookie = ""
        required_params = ["pm-csrf", "pm-sessionid", "ncbi_sid", "pm-sid", "pm-adjnav-sid"]
        for required_param in required_params:
            try:
                param_value = cookies_dict[required_param]
            except KeyError:
                print(required_params, "not found in cookie.")
                continue
            
            cookie += "{}={}; ".format(required_param, param_value)
     
        return csrf_token, cookie, result_count
