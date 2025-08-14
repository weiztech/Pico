from backend.logger import logger
from time import sleep, time
import os
import json
import re
from lit_reviews.database_scrapers.utils import Scraper 
import urllib.parse
from selenium.webdriver.common.by import By

TWO_MINUTES = 60*2

class PubmedCentral(Scraper):
    def __init__(self, review_id, search_id, user_id=None):
        super().__init__(review_id, search_id, file_format=".txt", user_id=user_id)
        self.clear_downloaded_file_path("pmc_result.txt")
        post_url = {
            "url": "https://ncbi.nlm.nih.gov/pmc",
            "term": self.lit_search.term,
            "filters": [{
                "name": "EntrezSystem2.PEntrez.PMC.Facets.FacetsUrlFrag",
                "value": "filters=pubdate_{}_{}".format(self.start_date.strftime("%Y/%m/%d"), self.end_date.strftime("%Y/%m/%d")),
            }]
        }
        self.results_url = json.dumps(post_url)
        try:
            self.driver = self.create_browser()
        except Exception as e:
            error_msg = 'Failed to create browser. ({})'.format(e)
            self.capture_error(error_msg)
            raise Exception(error_msg)

    def get_results_count(self):
        search_term = self.lit_search.term
        start_date_obj = self.start_date
        end_date_obj = self.end_date    
        logger.debug(f"Start Date: {start_date_obj}")
        logger.debug(f"End Date: {end_date_obj}")
        if "&" in search_term or "?" in search_term:
            search_term = urllib.parse.quote(search_term, safe='')

        url = "https://www.ncbi.nlm.nih.gov/pmc/?term={}".format(search_term)
        self.driver.get(url)        
        sleep(2)
        
        # Clicking publication date custom range button
        filters_available = True
        try:
            self.driver.find_element(By.CSS_SELECTOR,"a[id='facet_date_rangepubdate']").click()
        except Exception as e:
            filters_available = False
            error_msg = "An error occurred while choosing range dates. ({})".format(e)
            logger.warning(error_msg)
            self.capture_error(error_msg, self.driver)
            # raise Exception(error_msg)
        
        if filters_available:
            # Start Date Area
            # Set start publication date year
            try:
                self.driver.find_element(By.CSS_SELECTOR,"input[id='facet_date_st_yearpubdate']").send_keys(start_date_obj.year)
            except Exception as e:
                error_msg = "An error occurred while entering the start date year. ({})".format(e)
                self.capture_error(error_msg, self.driver)
                raise Exception(error_msg)
            
            # Clicking empty field to automate filled
            try:
                self.driver.find_element(By.XPATH,"/html/body/div[1]/div[1]/form/div[1]/div[4]/div/ul[3]/li/ul/div/h4").click()
            except Exception as e:
                error_msg = "An error occurred while clicking on the empty field. ({})".format(e)
                self.capture_error(error_msg, self.driver)
                raise Exception(error_msg)
            
            # Clearing the default start month
            try:
                self.driver.find_element(By.CSS_SELECTOR,"input[id='facet_date_st_monthpubdate']").clear()
            except Exception as e:
                error_msg = "An error occurred while clearing the default start month. ({})".format(e)
                self.capture_error(error_msg, self.driver)
                raise Exception(error_msg)
            
            # Set the publication date month
            try:
                self.driver.find_element(By.CSS_SELECTOR,"input[id='facet_date_st_monthpubdate']").send_keys(start_date_obj.month)
            except Exception as e:
                error_msg = "An error occurred while entering the start date month. ({})".format(e)
                self.capture_error(error_msg, self.driver)
                raise Exception(error_msg)
            
            # Clearing the default start day
            try:
                self.driver.find_element(By.CSS_SELECTOR,"input[id='facet_date_st_daypubdate']").clear()
            except Exception as e:
                error_msg = "An error occurred while clearing the default start day. ({})".format(e)
                self.capture_error(error_msg, self.driver)
                raise Exception(error_msg)
            
            # Set the publication date day
            try:
                self.driver.find_element(By.CSS_SELECTOR,"input[id='facet_date_st_daypubdate']").send_keys(start_date_obj.day)
            except Exception as e:
                error_msg = "An error occurred while entering the start date day. ({})".format(e)
                self.capture_error(error_msg, self.driver)
                raise Exception(error_msg)
            # End Date Area

            # Set end publication date year
            try:
                self.driver.find_element(By.CSS_SELECTOR,"input[id='facet_date_end_yearpubdate']").send_keys(end_date_obj.year)
            except Exception as e:
                error_msg = "An error occurred while entering the end date year. ({})".format(e)
                self.capture_error(error_msg, self.driver)
                raise Exception(error_msg)
            
            # Clicking empty field to automate filled
            try:
                self.driver.find_element(By.XPATH,"/html/body/div[1]/div[1]/form/div[1]/div[4]/div/ul[3]/li/ul/div/h4").click()
            except Exception as e:
                error_msg = "An error occurred while clicking on the empty field. ({})".format(e)
                self.capture_error(error_msg, self.driver)
                raise Exception(error_msg)
            
            # Clearing the default end month
            try:
                self.driver.find_element(By.CSS_SELECTOR,"input[id='facet_date_end_monthpubdate']").clear()
            except Exception as e:
                error_msg = "An error occurred while clearing the default end month. ({})".format(e)
                self.capture_error(error_msg, self.driver)
                raise Exception(error_msg)
            
            # Set end publication date month
            try:
                self.driver.find_element(By.CSS_SELECTOR,"input[id='facet_date_end_monthpubdate']").send_keys(end_date_obj.month)
            except Exception as e:
                error_msg = "An error occurred while entering the end date month. ({})".format(e)
                self.capture_error(error_msg, self.driver)
                raise Exception(error_msg)
            
            # Clearing the default end day
            try:
                self.driver.find_element(By.CSS_SELECTOR,"input[id='facet_date_end_daypubdate']").clear()
            except Exception as e:
                error_msg = "An error occurred while clearing the default end day. ({})".format(e)
                self.capture_error(error_msg, self.driver)
                raise Exception(error_msg)
            
            # Set end publication date day
            try:
                self.driver.find_element(By.CSS_SELECTOR,"input[id='facet_date_end_daypubdate']").send_keys(end_date_obj.day)
            except Exception as e:
                error_msg = "An error occurred while entering the end date day. ({})".format(e)
                self.capture_error(error_msg, self.driver)
                raise Exception(error_msg)
            
            # Applying publication date custom range
            try:
                self.driver.find_element(By.CSS_SELECTOR,"button[id='facet_date_range_applypubdate']").click()
            except Exception as e:
                error_msg = "An error occurred while applying publication date custom range. ({})".format(e)
                self.capture_error(error_msg, self.driver)
                raise Exception(error_msg)
        
        # Find the result count text
        try:
            result_count_text = self.driver.find_element(By.CSS_SELECTOR,"h3[class='result_count left']").text
        except Exception as r_count_error:
            try:
                messagearea = self.driver.find_elements(By.ID, "messagearea")
                if len(messagearea) and "No items found" in messagearea[0].text:
                    return 0
                
                else:
                    try:
                        result_count_text = self.driver.find_element(By.CSS_SELECTOR,"a[title='Total Results']").text 

                    except Exception as e:
                        logger.warning(f"Pubmed Central couldn't get the result count for {search_term}, probably no results were found")
                        return 0
                    
            except Exception as e:
                error_msg = "An error occurred while finding the result count text. ({})".format(r_count_error)
                self.capture_error(error_msg, self.driver)
                raise Exception(error_msg)
        
        # Extracting the result count number
        try:
            result_count = int(re.findall(r'\d+', result_count_text)[-1])
            return result_count

        except Exception as e:
            error_msg = "An error occurred while extracting the result count number. ({})".format(e)
            self.capture_error(error_msg, self.driver)
            raise Exception(error_msg)
            

    def search(self, is_preview=False):
        search_term = self.lit_search.term  
        url = "https://www.ncbi.nlm.nih.gov/pmc/?term={}".format(search_term)
        result_count = self.get_results_count()
        self.results_count = result_count
        if self.is_excluded(result_count):
            self.driver.quit()
            return "Results out of range", result_count  
        
        else:
            # Download the file
            try:
                file_path = self.download()
            except Exception as e:
                error_msg = "An error occurred while downloading the file. ({})".format(e)
                self.capture_error(error_msg, self.driver)
                raise Exception(error_msg)
          
            # Adding the url to the file
            try:
                self.line_prepender(file_path, url)
            except Exception as e:
                error_msg = "An error occurred while adding the url to the file. ({})".format(e)
                self.capture_error(error_msg, self.driver)
                raise Exception(error_msg)
            
            # get new file name
            new_file_name = self.file_name
            
            # Renaming the file
            try:
                os.rename(file_path, os.path.join(self.DEFAULT_DOWNLOAD_DIRECTORY, new_file_name))
            except Exception as e:
                error_msg = "An error occurred while renaming the file. ({})".format(e)
                self.capture_error(error_msg, self.driver)
                raise Exception(error_msg)
            
            self.driver.quit()
            return new_file_name, result_count
    
    def download(self):
        # Clicking the send to menu button
        try:
            self.driver.find_element(By.CSS_SELECTOR,"a[sourcecontent='send_to_menu']").click()
        except Exception as e:
            error_msg = "An error occurred while clicking the send to menu button. ({})".format(e)
            self.capture_error(error_msg, self.driver)
            raise Exception(error_msg)
        
        sleep(1)

        # Choosing the 'dest_File' option
        try:
            self.driver.find_element(By.CSS_SELECTOR,"input[id='dest_File']").click()
        except Exception as e:
            error_msg = "An error occurred while choosing the 'dest_File' option. ({})".format(e)
            self.capture_error(error_msg, self.driver)
            raise Exception(error_msg)
        sleep(1)
        
        # Choosing the 'MEDLINE' option
        try:
            self.driver.find_element(By.CSS_SELECTOR,"option[value='MEDLINE']").click()
        except Exception as e:
            error_msg = "An error occurred while choosing the 'MEDLINE' option. ({})".format(e)
            self.capture_error(error_msg, self.driver)
            raise Exception(error_msg)
        
        # Clicking the create file button
        try:
            self.driver.find_element(By.CSS_SELECTOR,"button[name='EntrezSystem2.PEntrez.PMC.Pmc_ResultsPanel.Pmc_DisplayBar.SendToSubmit']").click()
            self.show_download_progress()
        except Exception as e:
            error_msg = "An error occurred while clicking the create file button. ({})".format(e)
            self.capture_error(error_msg, self.driver)
            raise Exception(error_msg)
        
        # Creating file_path
        try:
            file_path = os.path.join(self.DEFAULT_DOWNLOAD_DIRECTORY, "pmc_result.txt")
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
                
        return file_path
    
    def line_prepender(self, filename, line):
        with open(filename, 'r+', encoding="utf8") as f:
            content = f.read()
            f.seek(0, 0)
            f.write(line.rstrip('\r\n') + '\n\n' + content)

    # method to get the downloaded file name
    def show_download_progress(self, waitTime=TWO_MINUTES):
        driver = self.driver
        driver.execute_script("window.open()")
        # switch to new tab
        driver.switch_to.window(driver.window_handles[-1])
        # navigate to chrome downloads
        driver.get('chrome://downloads')
        # define the endTime
        endTime = time() + waitTime
        
        while True:
            try:
                # get latest downloaded item element
                downloaded_item = driver.execute_script(
                    "return document.querySelector('downloads-manager').shadowRoot.querySelector('#downloadsList downloads-item')"
                )     
                if "Show in folder" in downloaded_item.text:
                    downloaded_file_name = driver.execute_script("return document.querySelector('downloads-manager').shadowRoot.querySelector('#downloadsList downloads-item').shadowRoot.querySelector('div#content  #file-link').text")
                    logger.info(f"File {downloaded_file_name} has been downloaded succesfully")
                    break

                # get downloaded percentage
                downloadPercentage = driver.execute_script(
                    "return document.querySelector('downloads-manager').shadowRoot.querySelector('#downloadsList downloads-item').shadowRoot.querySelector('#progress').value"
                )
                logger.info(f"Downloaded file percentage: {downloadPercentage}")
                # check if downloadPercentage is 100 (otherwise the script will keep waiting)
                if downloadPercentage == 100:
                    # return the file name once the download is completed
                    downloaded_file_name = driver.execute_script("return document.querySelector('downloads-manager').shadowRoot.querySelector('#downloadsList downloads-item').shadowRoot.querySelector('div#content  #file-link').text")
                    logger.info(f"File {downloaded_file_name} has been downloaded succesfully")
                    break 
                
            except Exception as e:
                logger.error(f"Error occured while trying to get downloaded file progress : {e}")
                break 

            sleep(1)
            if time() > endTime:
                break