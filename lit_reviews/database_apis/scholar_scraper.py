
from scholarly import scholarly, ProxyGenerator
### TODO install this slightly modified package from ethan's forked repo
### with python3 pip install -e   (for local testing)
### pip install git+https://github.com/ethandrower/scholarly.git
import traceback
import uuid
import os
from backend.logger import logger
import requests
from lit_reviews.helpers.generic import create_tmp_file
from lit_reviews.database_scrapers.utils import Scraper
from lit_reviews.models import (
    SearchConfiguration,
    SearchParameter,
    NCBIDatabase,
)
from backend.settings import (
    PROXY_USER,
    PROXY_PASS,
    PROXY_PORT,
    PROXY_HOST,
    PROXY_API_KEY,
)

class GoogleScholarApi(Scraper):
    def __init__(self, review_id, search_id, user_id=None, max_results=50):
        super().__init__(review_id, search_id, file_format=".ris", user_id=user_id, date_format="%Y")
        # form the search url
        self.search_term = self.lit_search.term
        
        self.max_results = self.get_max_results_limit()  ## TODO get from search protocol parameters
        self.results_count = self.get_results_count()
        self.results_url = f"https://scholar.google.com/scholar?q={self.search_term}&as_ylo={self.start_date}&as_yhi={self.end_date}"
        
        # Set Up Proxy
        self.pg = ProxyGenerator()  ## to add proxy info later from ENV

        ### not sure if this should be in constructor or not.
        # self.pg.Luminati(
        #     usr=PROXY_USER, 
        #     passwd=PROXY_PASS, 
        #     proxy_port=PROXY_PORT, 
        #     host=PROXY_HOST,
        # )

    def get_max_results_limit(self):
        try:
            search_config = SearchConfiguration.objects.get(
                database=NCBIDatabase.objects.get(entrez_enum="scholar"),
                literature_review=self.lit_search.literature_review
            )
            max_results_str = SearchParameter.objects.get(
                search_config=search_config, name="Max Results"
            ).value
            return int(max_results_str)
        
        except:
            logger.warning("No Max Results Limit Parameter was found. Setting 50 as default")
            return 50

    def get_results_count(self):
        ## TODO not sure if we should do this??
        # I don't think there is a way to get the results count using the scholar package so it might be a bit hard to get
        # I say we just leave it for now if it doesn't matter much. we return a FIXED 100+ 
        return 100


    def generate_ris_file(self, items):
        with open(self.FILE_PATH, 'w') as f:
            for item in items:
                f.write("TY  - JOUR\n")  # Type of reference, "JOUR" means journal article
                f.write(f"TI  - {item['bib']['title']}\n")  # Title
                authors = item['bib']['author']
                for author in authors:
                    f.write(f"AU  - {author}\n")  # Author

                f.write(f"PY  - {item['bib']['pub_year']}\n")  # Publication year
                f.write(f"AB  - {item['bib']['abstract']}\n")  # Abstract
                f.write(f"JO  - {item['bib']['venue']}\n")  # Journal name (venue)
                f.write(f"UR  - {item.get('pub_url')}\n")  # URL
                f.write(f"DO  - {item.get('eprint_url')}\n")  # DOI
                f.write("ER  - \n\n")  # End of reference
        
        return self.FILE_PATH

    def search(self):
        #scholarly._SESSION = session
        ## need to modify this for the filters as well (years specifically)
        
        try:    
            self.pg.ScraperAPI(PROXY_API_KEY)
            scholarly.use_proxy(self.pg)  ## TODO test this if we should put in instance variable.
        except Exception as error:
            err_track = str(traceback.format_exc())
            logger.warning("Failed to use proxy please make sure you have an env variable for PROXY_API_KEY and you're using the correct key")
            logger.warning(f"warning traceback: {err_track}")
    
        ### TODO get the years from instance variables?
        try:
            search_query = scholarly.search_pubs('{}'.format(self.search_term), year_low=self.start_date, year_high=self.end_date)
        except Exception as error:
            logger.warning("Proxy not working try again without a proxy")
            # desactivate proxy
            self.pg = ProxyGenerator()
            scholarly.use_proxy(self.pg)
            search_query = scholarly.search_pubs('{}'.format(self.search_term), year_low=self.start_date, year_high=self.end_date)

        items = []
        while True:
            if len(items) >= self.max_results:
                break
            try:
                items.append(next(search_query))

            except StopIteration: ## THis is when we run out of items
                break

        ris_file_output = self.generate_ris_file(items)
        # the second returned value is for results count to be updated
        return ris_file_output, None

