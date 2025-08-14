from selenium import webdriver
from time import sleep, time
import os
import re
from selenium.webdriver.common.by import By

from backend.logger import logger
from lit_reviews.database_scrapers.utils import Scraper

class EuropePMC(Scraper):
    def __init__(self, review_id, search_id, user_id=None):
        super().__init__(review_id, search_id, file_format=".ris", user_id=user_id)
        self.clear_downloaded_file_path("europepmc.ris")
        try:
            self.driver = self.create_browser()
        except Exception as e:
            error_msg = 'Failed to create browser. ({})'.format(e)
            self.capture_error(error_msg)
            raise Exception(error_msg)

    def search(self, is_preview=False):
        search_term = self.lit_search.term
        start_date_obj = self.start_date
        end_date_obj = self.end_date
        url = "https://europepmc.org/"
        self.driver.get(url)
        sleep(2) 

        # prepare the search query
        search_term_query = "{} AND (FIRST_PDATE:[{} TO {}])".format(search_term, start_date_obj.strftime("%Y-%m-%d"), end_date_obj.strftime("%Y-%m-%d"))
        
        # Set the Search Query
        try:
            self.driver.find_element(By.ID,"banner--search-input").send_keys(search_term_query)
            sleep(1)
        except Exception as e:
            error_msg = "An error occurred while setting the search query. ({})".format(e)
            self.capture_error(error_msg, self.driver)
            raise Exception(error_msg)
        
        # Click the search button
        try:
            self.driver.find_element(By.ID,"banner--search-button").click()
        except Exception as e:
            error_msg = "An error occurred while clicking the search button. ({})".format(e)
            self.capture_error(error_msg, self.driver)
            raise Exception(error_msg)
        
        # Waiting until page is loaded
        try:
            self.wait_until_page_is_loaded("//img[@src='/img/content-loading-indicator.961a7bab.gif']")
        except Exception as e:
            error_msg = "An error occurred while loading the page. ({})".format(e)
            self.capture_error(error_msg, self.driver)
            raise Exception(error_msg)
        
        # Accept the cookie aceept button
        try:
            self.driver.find_element(By.ID,"data-protection-agree").click()
        except Exception as e:
            pass
        
        # Extracting result_number
        try:
            if "There are no citations matching your query." in self.driver.find_element(By.CLASS_NAME, "search-results").text:
                self.driver.quit()
                return "Results out of range", 0
            else:
                result_number = int(float(self.driver.find_element(By.ID,"search-results--results--details--top").find_element(By.CLASS_NAME, "semi-bold").text.strip().replace(",","")))
        except Exception as e:
            error_msg = "An error occurred while extracting result_number. ({})".format(e)
            self.capture_error(error_msg, self.driver)
            raise Exception(error_msg)
        
        self.results_count = result_number

        if self.is_excluded(result_number):
            self.driver.quit()
            return "Results out of range", result_number    

        else:
            file_path, first_max = self.download()
            # Renaming the downloaded file 
            new_file_name = self.file_name
            
            try:
                os.rename(file_path, os.path.join(self.DEFAULT_DOWNLOAD_DIRECTORY, new_file_name))
            except Exception as e:
                error_msg = "An error occurred while renaming the file. ({})".format(e)
                self.capture_error(error_msg, self.driver)
                raise Exception(error_msg)
        
            message = "successfully downloaded."
            if first_max >= 50000:
                message += " WARNING : downloaded first {} results".format(first_max)
            
            self.driver.quit()
            return new_file_name, result_number 

    def download(self):
        # Click the export button
        try:
            self.driver.find_element(By.ID,"get_citation").click()
            sleep(1)
        except Exception as e:
            error_msg = "An error occurred while clicking the export button. ({})".format(e)
            self.capture_error(error_msg, self.driver)
            raise Exception(error_msg)
        
        # Get download message
        try:
            download_message = self.driver.find_element(By.ID,"export-number-input").text
        except Exception as e:
            error_msg = "An error occurred while getting the download message. ({})".format(e)
            self.capture_error(error_msg, self.driver)
            raise Exception(error_msg)
        
        # Extracting the first max value
        try:
            first_max =  int(re.findall(r'up.*?to.*?(\d+)', download_message)[0])
        except Exception as e:
            error_msg = "An error occurred while extracting the first max value. ({})".format(e)
            self.capture_error(error_msg, self.driver)
            raise Exception(error_msg)
        
        

        # Get export max input element
        try:
            max_export = self.driver.find_element(By.ID,"export-number-input").find_element(By.TAG_NAME,"input")
        except Exception as e:
            error_msg = "An error occurred while trying to get the export max number element. ({})".format(e)
            self.capture_error(error_msg, self.driver)
            raise Exception(error_msg)
        
        # Clear export max number
        try:
            max_export.clear()
        except Exception as e:
            error_msg = "An error occurred while clearing the default export max number. ({})".format(e)
            self.capture_error(error_msg, self.driver)
            raise Exception(error_msg)
        
        # Set export max number
        try:
            max_export.send_keys(first_max)
        except Exception as e:
            error_msg = "An error occurred while setting export max number. ({})".format(e)
            self.capture_error(error_msg, self.driver)
            raise Exception(error_msg)
        
        # Click Select format: RIS button
        try:
            self.driver.find_element(By.XPATH,'//input[@id="export--text--format-RIS"]').click()
        except Exception as e:
            error_msg = "An error occurred while clicking the RIS filter button. ({})".format(e)
            self.capture_error(error_msg, self.driver)
            raise Exception(error_msg)
        
        # Click download button
        try:
            self.driver.find_element(By.XPATH,'//input[@id="export--start--download"]').click()
        except Exception as e:
            error_msg = "An error occurred while clicking the download button. ({})".format(e)
            self.capture_error(error_msg, self.driver)
            raise Exception(error_msg)
              
        # Waiting for the file to be prepared
        try:
            file_path = os.path.join(self.DEFAULT_DOWNLOAD_DIRECTORY, "europepmc.ris")
        except Exception as e:
            error_msg = "An error occurred while creating the file path. ({})".format(e)
            self.capture_error(error_msg, self.driver)
            raise Exception(error_msg)
        
        ONE_MINUTE = 60
        break_time = time() + (3 * ONE_MINUTE)
        while True:
            if os.path.exists(file_path):
                break
            elif time() > break_time:
                error_msg = "Error while downloading the file TIME OUT"
                self.capture_error(error_msg, self.driver)
                raise Exception(error_msg)
            else:
                print("waiting for file to download")
                sleep(1)

        return file_path, first_max

    def wait_until_page_is_loaded(self, spinner_xpath):
        while True:
            try:
                item = self.driver.find_element(By.XPATH,spinner_xpath)
                print("item",item)
                sleep(1)
            except:
                break