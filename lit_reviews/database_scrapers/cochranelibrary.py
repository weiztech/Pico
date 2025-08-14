from selenium import webdriver
from datetime import date
from backend.logger import logger
from time import sleep, time
import uuid
import os
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.by import By
import traceback

from lit_reviews.database_scrapers.utils import Scraper 
from backend.settings import (
    COCHRANE_LOGIN_EMAIL,
    COCHRANE_LOGIN_PASS,
)

TWO_MINUTES = 60*2

class CochraneLibrary(Scraper):
    def __init__(self, review_id, search_id, user_id=None):
        super().__init__(review_id, search_id, file_format=".txt", user_id=user_id)
        self.clear_downloaded_file_path("citation-export.txt")
        
        try:
            self.driver = self.create_browser()
            
        except Exception as e:
            error_msg = 'Failed to create browser. ({})'.format(e)
            self.capture_error(error_msg)
            raise Exception(error_msg)
        
    def click_btn(self, ele, error_msg):
        # sometimes page take too long to load which would prevent clocking html elements
        for i in range(5):
            try:
                # ele.click()
                self.driver.execute_script("arguments[0].click();", ele)
                return 

            except Exception as e:
                sleep(2)
                error = e
                pass
            
        error_track = str(traceback.format_exc())
        logger.error("Cochrane scraper clicking btn error, error track: {}".format(error_track))
        self.capture_error(error_msg, self.driver)
        raise Exception("{}. ({})".format(error_msg, error))

    def get_results_count(self, requires_login=False):
        search_term = self.lit_search.term
        self.driver.get("https://www.cochranelibrary.com/advanced-search")
        sleep(2)

        # Enable Signing in when needed
        if requires_login:
            self.login()
            sleep(2)
            
            self.driver.get("https://www.cochranelibrary.com/advanced-search")
            sleep(2)

        # Filled the search bar
        try:
            self.driver.find_element(By.ID, 'searchText0').send_keys(search_term)
        except Exception as e:
            error_msg = "An error occurred while searching. ({})".format(e)
            self.capture_error(error_msg, self.driver)
            raise Exception(error_msg)
        
        # Clicking search limit setting button
        search_limit_btn = self.driver.find_element(By.ID, "addSearchLimit")
        self.click_btn(search_limit_btn, "An error occurred while setting the limits.")
        sleep(1)
        
        # click Cochrane Reviews Only
        try:
            cochrane_review_checkbox = self.driver.find_element(By.CSS_SELECTOR,"input[type='checkbox'][value='review']")
            cochrane_review_checkbox.click()
        except Exception as e:
            error_msg = "An error occurred while trying to click Cochrane Reviews Checkbox filter"
            self.capture_error(error_msg, self.driver)
        
        # Selected between filter option 
        radio_btn = self.driver.find_element(By.CSS_SELECTOR,"input[type='radio'][value='between']")
        self.click_btn(radio_btn, "An error occurred while choosing between dates.")

        # Set start publication date year
        try:
            self.driver.find_element(By.ID, "startPublicationDateYear").send_keys(str(self.start_date.year))
        except Exception as e:
            error_msg = "An error occurred while entering start date year. ({})".format(e)
            self.capture_error(error_msg, self.driver)
            raise Exception(error_msg)

        # Set start publication date month
        try:
            select_1 = Select(self.driver.find_element(By.ID, "startPublicationDateMonth"))
            select_1.select_by_value(str(self.start_date.month))
        except Exception as e:
            error_msg = "An error occurred while entering start date month. ({})".format(e)
            self.capture_error(error_msg, self.driver)
            raise Exception(error_msg)
        
        # Set end publication date year
        try:
            self.driver.find_element(By.ID,"endPublicationDateYear").send_keys(str(self.end_date.year))
        except Exception as e:
            error_msg = "An error occurred while entering end date year. ({})".format(e)
            self.capture_error(error_msg, self.driver)
            raise Exception(error_msg)  
        sleep(1)
        
        # Set end publication date month
        try:
            select_2 = Select(self.driver.find_element(By.ID,"endPublicationDateMonth"))
            select_2.select_by_value(str(self.end_date.month))
        except Exception as e:
            error_msg = "An error occurred while entering end date month. ({})".format(e)
            self.capture_error(error_msg, self.driver)
            raise Exception(error_msg)  
        sleep(1)

        # Click apply limit button
        apply_btn = self.driver.find_element(By.CLASS_NAME, 'apply-limits')
        self.click_btn(apply_btn, "An error occurred while clicking the apply limit button.")
        sleep(1)
        
        # Click the run search button
        search_btn = self.driver.find_element(By.XPATH,'//*[@id="advancedSearchForm"]/div[5]/div/button[3]')
        self.click_btn(search_btn, "An error occurred while clicking the run search button.")
        
        # Waiting until page is loaded
        self.wait_until_page_is_loaded()
        
        try:
            result_number = int(self.driver.find_element(By.CLASS_NAME, "results-number").text)
            return result_number
        except Exception as e:
            error_msg = "An error occurred while getting results number. ({})".format(e)
            logger.error(error_msg)
            return 0
            # raise Exception("An error occurred while getting results number. ({})".format(e))
        
    def search(self, is_preview=False):
        try:
            result_number = self.get_results_count()
            self.results_count = result_number
            logger.info(f"We get result  number of: {result_number}")
            if self.is_excluded(result_number):
                return "Results out of range", result_number     

            sleep(2)
            # Click select all button to select all 
            # print(self.driver.page_source)
            select_all_btn = self.driver.find_element(By.ID,"_scolarissearchresultsportlet_WAR_scolarissearchresults_selectAll")
            self.click_btn(select_all_btn, "An error occurred while clicking the select all button")
            
            # Click 'Export selected citation(s)' button
            export_btn = self.driver.find_element(By.XPATH,"//button[@data-modal-title='Export selected citation(s)']")
            self.click_btn(export_btn, "An error occurred while clicking the 'Export selected citations' button.")
            sleep(1)
            
            # We don't need to click the 'Include abstract' button as it is clicked by default
            # # Click 'Include abstract' button
            # try:
            #     self.driver.find_element(By.XPATH,'/html/body/div[1]/div[6]/div[2]/div/div[3]/div/div[4]/form/div/label/input').click()
            # except Exception as e:
            #     raise Exception("An error occurred while clicking the 'Include abstract' button. ({})".format(e))

            # the download button should be selected by the absolute xpath otherwise selenium will fail to click it
            xpath = '//form[@class="download-citation-form"]//button'
            # download_button = self.driver.find_element(By.XPATH,"/html/body/div[2]/div[6]/div[2]/div/div[3]/div/div[4]/form/button")
            download_buttons = self.driver.find_elements(By.XPATH, xpath)
            btn_clicked = False
            for download_button in download_buttons:
                if download_button.text == "Download":
                    self.click_btn(download_button, "An error occurred while clicking the download button.")
                    btn_clicked = True 
                

            if not btn_clicked:
                raise Exception("Failed to find download button")
            
            # Waiting for the file to be prepared
            logger.debug("Waiting for the file to be prepared")
            self.wait_until_page_is_loaded(1)
            sleep(1)

            # Renaming the downloaded file 
            try:
                file_path = os.path.join(self.DEFAULT_DOWNLOAD_DIRECTORY, "citation-export.txt")
            except Exception as e:
                error_msg = "An error occurred while creating the file path. ({})".format(e)
                self.capture_error(error_msg, self.driver)
                raise Exception(error_msg)

            sleep(1)
            self.show_download_progress()            
            # Waiting for the file to be downloaded
            ONE_MINUTE = 60
            break_time = time() + (3 * ONE_MINUTE)

            while True:
                if os.path.isfile(file_path):
                    break
                elif time() > break_time:
                    error_msg = "Error while downloading the file TIME OUT"
                    self.capture_error(error_msg, self.driver)
                    raise Exception(error_msg)
                
                else:
                    logger.debug("Waiting for file to be downloaded")
                    sleep(1)

            # Renaming the downloaded file  
            new_file_name = self.file_name
            
            try:
                os.rename(file_path, os.path.join(self.DEFAULT_DOWNLOAD_DIRECTORY, new_file_name))
            except Exception as e:
                error_msg = "An error occurred while renaming the file. ({})".format(e)
                self.capture_error(error_msg, self.driver)
                raise Exception(error_msg)
            
            self.driver.quit()
            return new_file_name, result_number
        
        except Exception as error:
            error_track = str(traceback.format_exc())
            error_msg = "An error occurred while searching Cochrane. ({}) with the following error track {}".format(error, error_track)
            self.capture_error(error_msg, self.driver)
            self.driver.quit()
            raise Exception(error_msg) 
    
    def wait_until_page_is_loaded(self, spinner_index=0):
        init_time = time()
        ONE_MINUTE =  60
        THREE_MINUTES = 180

        while True:
            try:
                spinner_div = self.driver.find_elements(By.CLASS_NAME, 'spinner')[spinner_index]
                spinner_class_name = spinner_div.get_attribute("class")
            except Exception as e:
                error_msg = "Spinner animation error ({})".format(e)
                self.capture_error(error_msg, self.driver)
                raise Exception(error_msg)
            
            if "loaded" in spinner_class_name:
                break
            elif spinner_class_name == "spinner spin-animation":
                logger.debug("loading page...")
                sleep(1)
            else:
                error_msg = "Unknown spinner class name"
                self.capture_error(error_msg, self.driver)
                raise Exception(error_msg)

            if (init_time + ONE_MINUTE) < time() and not spinner_div.is_displayed():
                log_error_msg = "No spinner loader showed either there might be an error with the search term text formating, Please contact support for help!"
                logger.error(log_error_msg)
                self.capture_error(log_error_msg, self.driver)
                raise Exception(log_error_msg)

            if (init_time + THREE_MINUTES) < time():
                log_error_msg = "Results were not loaded in cochrane website loading forever there might be an error with the search term text formating, Please contact support for help!"
                logger.error(log_error_msg)
                self.capture_error(log_error_msg, self.driver)
                raise Exception(log_error_msg)

    
    def login(self):
        driver = self.driver
        login_tag = self.driver.find_element(By.XPATH,'//a[@class="auxiliary-menu-item signin last"]')
        login_link = login_tag.get_attribute("href")
        self.driver.get(login_link)
        email_input = driver.find_element(By.ID,"_58_login")
        password_input = driver.find_element(By.ID,"_58_password")

        email_input.send_keys(COCHRANE_LOGIN_EMAIL)
        password_input.send_keys(COCHRANE_LOGIN_PASS)

        submit_btn = driver.find_element(By.XPATH,'//div[@class="pull-left"]/button')
        self.driver.execute_script("arguments[0].click();", submit_btn)

    # Check download progress and Get downloaded file name 
    def show_download_progress(self, waitTime=TWO_MINUTES):
        driver = self.driver
        driver.execute_script("window.open()")
        # switch to new tab
        driver.switch_to.window(driver.window_handles[-1])
        # navigate to chrome downloads
        driver.get('chrome://downloads')
        # define the endTime
        endTime = time()+waitTime

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

        # switch back to main tab
        self.driver.switch_to.window(self.driver.window_handles[0])