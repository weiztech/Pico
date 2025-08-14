import requests
import os
import json
import time

from backend.logger import logger
from lit_reviews.database_scrapers.utils import Scraper

class EuropePMC(Scraper):
    def __init__(self, review_id, search_id, user_id=None):
        super().__init__(review_id, search_id, file_format=".ris", user_id=user_id)
        self.clear_downloaded_file_path("europepmc.ris")
        self.base_url = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"

    def search(self, is_preview=False):
        search_term = self.lit_search.term
        start_date_obj = self.start_date
        end_date_obj = self.end_date
        
        # Prepare the search query
        search_term_query = "({}) AND (FIRST_PDATE:[{} TO {}])".format(
            search_term, 
            start_date_obj.strftime("%Y-%m-%d"), 
            end_date_obj.strftime("%Y-%m-%d")
        )
        logger.info("Search term query: {}".format(search_term_query))
        
        try:
            # Get initial results to check hit count
            initial_params = {
                'query': search_term_query,
                'resultType': 'core',
                'pageSize': 1,
                'cursorMark': '*',
                'format': 'json'
            }
            
            response = requests.get(self.base_url, params=initial_params)
            response.raise_for_status()
            
            # Parse JSON to get hit count
            data = response.json()
            
            if 'hitCount' not in data:
                return "Results out of range", 0
                
            result_number = int(data['hitCount'])
            self.results_count = result_number
            
            # Check if no results found
            if result_number == 0:
                return "Results out of range", 0
                
        except Exception as e:
            error_msg = "An error occurred while getting initial results. ({})".format(e)
            self.capture_error(error_msg)
            raise Exception(error_msg)

        if self.is_excluded(result_number):
            return "Results out of range", result_number    
        else:
            file_path = self.download_all_results(search_term_query)
            
            # Renaming the downloaded file 
            new_file_name = self.file_name
            
            try:
                os.rename(file_path, os.path.join(self.DEFAULT_DOWNLOAD_DIRECTORY, new_file_name))
            except Exception as e:
                error_msg = "An error occurred while renaming the file. ({})".format(e)
                self.capture_error(error_msg)
                raise Exception(error_msg)
        
            message = "successfully downloaded."
            if result_number >= 50000:
                message += " WARNING : downloaded first 50000 results"
            
            return new_file_name, result_number

    def download_all_results(self, search_query):
        """Download all results using pagination"""
        try:
            # Create combined results structure
            combined_data = {
                'version': '6.9',
                'hitCount': 0,
                'resultList': {'result': []}
            }
            
            cursor_mark = "*"
            total_results = 0
            max_results = 50000  # Limit to prevent excessive downloads
            
            while cursor_mark and total_results < max_results:
                params = {
                    'query': search_query,
                    'resultType': 'core',
                    'pageSize': 1000,
                    'cursorMark': cursor_mark,
                    'format': 'json'
                }
                
                response = requests.get(self.base_url, params=params)
                response.raise_for_status()
                
                # Parse current page
                page_data = response.json()
                
                # Get hit count from first page
                if total_results == 0:
                    combined_data['hitCount'] = page_data.get('hitCount', 0)
                
                # Add results to combined data
                if 'resultList' in page_data and 'result' in page_data['resultList']:
                    for result in page_data['resultList']['result']:
                        combined_data['resultList']['result'].append(result)
                        total_results += 1
                        
                        if total_results >= max_results:
                            break
                
                # Get next cursor mark
                if 'nextCursorMark' in page_data and page_data['nextCursorMark'] != cursor_mark:
                    cursor_mark = page_data['nextCursorMark']
                else:
                    cursor_mark = None
                
                logger.info("Downloaded {} results so far".format(total_results))
                time.sleep(0.1)  # Small delay to be respectful to the API
            
            # Convert JSON to RIS format
            ris_content = self.json_to_ris(combined_data)
            
            # Save RIS file
            file_path = os.path.join(self.DEFAULT_DOWNLOAD_DIRECTORY, "europepmc.ris")
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(ris_content)
            
            return file_path
            
        except Exception as e:
            error_msg = "An error occurred while downloading results. ({})".format(e)
            self.capture_error(error_msg)
            raise Exception(error_msg)

    def json_to_ris(self, json_data):
        """Convert JSON results to RIS format"""
        ris_content = []

        # Add provider header
        ris_content.append("Provider: Europe PMC")
        ris_content.append("Content: text/plain; charset=\"UTF-8\"")
        ris_content.append("")  # Empty line

        if 'resultList' not in json_data or 'result' not in json_data['resultList']:
            return "\n".join(ris_content)

        for result in json_data['resultList']['result']:
            ris_entry = []
            ris_entry.append("TY  - EJOUR")

            pmid = result.get("pmid", "")
            doi = result.get("doi", "")
            pub_year = result.get("pubYear", "")
            abstract = result.get("abstractText", "")
            title = result.get("title", "").strip()
            page = result.get("pageInfo", "")
            language = result.get("language", "eng")

            # Identifiers
            if pmid:
                ris_entry.append(f"AN  - {pmid}")
            ris_entry.append("DB  - PubMed")

            if doi:
                ris_entry.append(f"DO  - {doi}")

            if title:
                ris_entry.append(f"TI  - {title}")

            # Authors
            for author in result.get("authorList", {}).get("author", []):
                full_name = author.get("fullName")
                if full_name:
                    ris_entry.append(f"AU  - {full_name.strip()}")

            # Journal info
            journal_info = result.get("journalInfo", {})
            journal = journal_info.get("journal", {})
            if journal.get("title"):
                ris_entry.append(f"T2  - {journal['title'].strip()}")
            if journal.get("medlineAbbreviation"):
                ris_entry.append(f"J2  - {journal['medlineAbbreviation'].strip()}")
            if journal.get("issn"):
                ris_entry.append(f"SN  - {journal['issn'].strip()}")

            if journal_info.get("issue"):
                ris_entry.append(f"IS  - {journal_info['issue'].strip()}")
            if journal_info.get("volume"):
                ris_entry.append(f"VL  - {journal_info['volume'].strip()}")
            if journal_info.get("printPublicationDate"):
                ris_entry.append(f"DA  - {journal_info['printPublicationDate'].strip()}")

            if pub_year:
                ris_entry.append(f"PY  - {pub_year}")

            # Abstract
            if abstract:
                ris_entry.append(f"AB  - {abstract.strip()}")

            # Page
            if page:
                ris_entry.append(f"SP  - {page.strip()}")

            # Address (first author only)
            for author in result.get("authorList", {}).get("author", []):
                affs = author.get("authorAffiliationDetailsList", {}).get("authorAffiliation", [])
                if affs:
                    first_aff = affs[0].get("affiliation")
                    if first_aff:
                        ris_entry.append(f"AD  - {first_aff.strip()}")
                    break  # Only one AD tag

            # Language
            if language:
                ris_entry.append(f"LA  - {language}")

            # Keywords
            for kw in result.get("keywordList", {}).get("keyword", []):
                ris_entry.append(f"KW  - {kw}")

            # URLs
            if pmid:
                ris_entry.append(f"UR  - http://europepmc.org/abstract/MED/{pmid}")
            if doi:
                ris_entry.append(f"UR  - https://doi.org/{doi}")
            for link in result.get("fullTextUrlList", {}).get("fullTextUrl", []):
                url = link.get("url")
                if url:
                    ris_entry.append(f"UR  - {url}")

            # End record
            ris_entry.append("ER  - ")
            ris_entry.append("")  # Space between entries

            ris_content.extend(ris_entry)

        return "\n".join(ris_content)
