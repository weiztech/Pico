from time import sleep
import os, glob, time, datetime
import zipfile

from backend import settings
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from backend.logger import logger
from lit_reviews.database_scrapers.utils import Scraper
from lit_reviews.utils.consts import (
    PRODUCT_CODE,
    MANUFACTURER,
    MODEL_NUMBER,
    REPORT_NUMBER,
    BRAND_NAME,
)

class MaudeFda(Scraper):
    def __init__(self, review_id, search_id, user_id=None):
        super().__init__(review_id, search_id, file_format=".csv", user_id=user_id)
        self.start_date = self.start_date.strftime("%m/%d/%Y")
        self.end_date = self.end_date.strftime("%m/%d/%Y")
        # devided search due to results > 500 
        self.iterative_search = False

        try:
            self.driver = self.create_browser()
        except Exception as e:
            error_msg = 'Failed to create browser. ({})'.format(e)
            self.capture_error(error_msg)
            raise Exception(error_msg)

    def search_and_get_result(self, start_date=None, end_date=None):
        url = "https://www.accessdata.fda.gov/scripts/cdrh/cfdocs/cfmaude/search.cfm"
        self.driver.get(url)
        sleep(2)
    
        search_term = self.lit_search.term
        start_date = start_date if start_date else self.start_date
        end_date = end_date if end_date else self.end_date
        search_field = self.lit_search.advanced_options and self.lit_search.advanced_options.get("search_field", None)
        
        # Adding Element to the Browser
        try:
            from_date_element = self.driver.find_element(by=By.XPATH,value='//input[@id="ReportDateFrom"]')
            to_date_element= self.driver.find_element(by=By.XPATH,value='//input[@id="ReportDateTo"]')
            product_code_element= self.driver.find_element(by=By.XPATH,value='//input[@id="ProductCode"]')
            search_element= self.driver.find_element(by=By.XPATH,value='//input[@name="Search"]')

            if search_field and search_field == MANUFACTURER:
                manufacturer_element= self.driver.find_element(by=By.XPATH,value='//input[@id="Manufacturer"]')
                manufacturer_element.clear()
                manufacturer_element.send_keys(search_term)

            elif search_field and search_field == MODEL_NUMBER:
                model_number_element = self.driver.find_element(by=By.XPATH,value='//input[@name="ModelNumber"]')
                model_number_element.clear()
                model_number_element.send_keys(search_term)

            elif search_field and search_field == REPORT_NUMBER:
                report_number_element = self.driver.find_element(by=By.XPATH,value='//input[@id="ReportNumber"]')
                report_number_element.clear()
                report_number_element.send_keys(search_term)

            elif search_field and search_field == BRAND_NAME:
                brand_name_element = self.driver.find_element(by=By.XPATH,value='//input[@name="BrandName"]')
                brand_name_element.clear()
                brand_name_element.send_keys(search_term)

            else:
                product_code_element.clear()
                product_code_element.send_keys(search_term)

            from_date_element.clear()
            from_date_element.send_keys(start_date)
            to_date_element.clear()
            to_date_element.send_keys(end_date)
            time.sleep(1)
            search_element.click()
            logger.debug('Searching from {0} to {1}'.format(start_date, end_date))

        except Exception as e:
            error_msg = "An error occurred while choosing range dates. ({})".format(e)
            self.capture_error(error_msg, self.driver)
            raise Exception(error_msg)
        
        try:
            # Waiting for the page to load
            export_excel_element=WebDriverWait(self.driver, 5).until(EC.presence_of_element_located((By.XPATH, '//a[@title="Export to Excel"]')))
        except:
            # # We might not get results even in iterative search so we dont completely stop the function
            # if not iterative_search:
            #     return "No results found.", None
            # pass
            logger.warning("Maude Scraper Failed to get results")
            no_records_found = self.driver.find_elements(by=By.XPATH,value='//td[contains(.,"No records were found with")]')
            if no_records_found:
                self.results_count = 0
            
            return "No results found.", False
        
        # get results count
        if not self.iterative_search:
            try:
                results_count_td = self.driver.find_elements(by=By.XPATH,value='//td[contains(.,"records meeting your search")]')
                if results_count_td:
                    results_count = results_count_td[0].find_element(By.TAG_NAME,"b").text
                    self.results_count = int(results_count)

            except Exception as error:
                logger.warning("Maude Scraper Failed to get results count")
                no_records_found = self.driver.find_elements(by=By.XPATH,value='//td[contains(.,"No records were found with")]')
                if no_records_found:
                    self.results_count = 0
                    return "No results found.", False
        
        results_exceeded_500 = self.driver.find_elements(by=By.XPATH,value='//td[contains(.,"narrow your search")]')
        return export_excel_element, results_exceeded_500
    
        
    def search(self, is_preview=False):
        export_excel_element=None
        monthly_ranges=None
        export_excel_element, results_exceeded_500 = self.search_and_get_result()
        
        # if results are > 500 we should narrow the search dates and do multiple searches
        if results_exceeded_500 and not is_preview:
            try:
                self.iterative_search = True
                download_files = []

                yearly_ranges = self.get_dates_ranges(self.start_date, self.end_date, 'yearly')
                logger.debug("narrowing the search to yearly")
                for i in range(len(yearly_ranges)-1):
                    yearly_range_start_date = yearly_ranges[i]
                    if i != 0:
                        yearly_range_start_date = datetime.datetime.strptime(yearly_range_start_date, '%m/%d/%Y') + datetime.timedelta(days=1)
                        yearly_range_start_date = yearly_range_start_date.strftime('%m/%d/%Y')
                    yearly_range_end_date = yearly_ranges[i+1]

                    export_excel_element, results_exceeded_500 = self.search_and_get_result(yearly_range_start_date, yearly_range_end_date)

                    # if results > 500 do monthly 
                    if results_exceeded_500:
                        monthly_ranges= self.get_dates_ranges(yearly_range_start_date, yearly_range_end_date, 'monthly')
                        logger.debug("narrowing the search to monthly")
                        
                        for j in range(len(monthly_ranges)-1):
                            monthly_range_start_date = monthly_ranges[j]
                            if j != 0:
                                monthly_range_start_date = datetime.datetime.strptime(monthly_range_start_date, '%m/%d/%Y') + datetime.timedelta(days=1)
                                monthly_range_start_date = monthly_range_start_date.strftime('%m/%d/%Y')
                            monthly_range_end_date = monthly_ranges[j+1]
                            export_excel_element, results_exceeded_500 = self.search_and_get_result(monthly_range_start_date, monthly_range_end_date)
                            if export_excel_element != "No results found.":
                                download_file = self.download_results(export_excel_element, monthly_range_start_date, monthly_range_end_date)   
                                self.file_name = self.file_name.replace(".csv", ".zip")
                                self.FILE_PATH = self.FILE_PATH.replace(".csv", ".zip")
                                zip_file_path = self.FILE_PATH.replace(".csv", ".zip")
                                download_files.append(download_file)

                    elif export_excel_element != "No results found.":
                        download_file = self.download_results(export_excel_element, yearly_range_start_date, yearly_range_end_date)   
                        self.file_name = self.file_name.replace(".csv", ".zip")
                        self.FILE_PATH = self.FILE_PATH.replace(".csv", ".zip")
                        zip_file_path = self.FILE_PATH.replace(".csv", ".zip")
                        download_files.append(download_file)

                with zipfile.ZipFile(zip_file_path, 'w') as zipf:
                    for file_name in download_files:
                        file_path = settings.TMP_ROOT + '/' + file_name
                        zipf.write(file_path, file_name)

                self.driver.quit()
                return download_files, self.results_count
            
            except Exception as e:
                error_msg = "An error occurred while Trying to narrow the search and run an iterative search. ({})".format(e)
                self.capture_error(error_msg, self.driver)
                raise Exception(error_msg)
        
        if export_excel_element and export_excel_element != "No results found.":
            download_file = self.download_results(export_excel_element)
            self.driver.quit()
            return download_file, self.results_count
        
        elif export_excel_element == "No results found.":
            self.driver.quit()
            return "Results out of range", 0

    def download_results(self, export_excel_element, start_date=None, end_date=None):
        export_excel_element.click()
        time.sleep(2)
        download_flag = False
        while download_flag != True:
            download_flag, download_file = self.check_download_completed(start_date, end_date)

        logger.debug("Downloaded File : ",download_file)
        return download_file
        
    def get_dates_ranges(self, start, end, how):        
        dates=[]
        # converting back to datetime
        start_date = datetime.datetime.strptime(start, '%m/%d/%Y')
        end_date = datetime.datetime.strptime(end, '%m/%d/%Y')
        
        if how == 'yearly':
            i = 1
            dates.append(end_date.strftime('%m/%d/%Y'))
            year_start_range = (end_date - datetime.timedelta(days=i*366))
            while year_start_range > start_date:
                i += 1                
                dates.append(year_start_range.strftime('%m/%d/%Y'))
                year_start_range = (end_date - datetime.timedelta(days=i*366))
            
            if year_start_range != start_date:
                dates.append(start_date.strftime('%m/%d/%Y'))

            dates=dates[::-1]
            return dates
        
        if how == 'monthly':
            i = 1
            dates.append(end_date.strftime('%m/%d/%Y'))
            month_start_range = (end_date - datetime.timedelta(days=i*31))
            while month_start_range > start_date:
                i += 1                
                dates.append(month_start_range.strftime('%m/%d/%Y'))
                month_start_range = (end_date - datetime.timedelta(days=i*31))
            
            if month_start_range != start_date:
                dates.append(start_date.strftime('%m/%d/%Y'))

            dates=dates[::-1]
            return dates

    def check_download_completed(self, start_date=None, end_date=None):
        list_of_files = glob.glob(self.DEFAULT_DOWNLOAD_DIRECTORY + "/*") # * means all if need specific format then *.
        list_of_files = list(filter(lambda file: "maudeExcelReport" in file, list_of_files))
        latest_file = max(list_of_files, key=os.path.getctime) if len(list_of_files) else ""
        new_file_name = self.file_name
        if self.iterative_search:
            s_date = str(start_date).replace("/", "-")
            e_date = str(end_date).replace("/", "-")
            new_file_name = f"maude-part-{self.lit_search.term}-{s_date}-{e_date}.csv"

        if latest_file and '.crdownload' in latest_file:
            logger.debug('File Downloading...')
            time.sleep(1)
            return False, new_file_name
        
        else:
            time.sleep(1)
            logger.debug('File Download Completed')
            # Renaming the downloaded file 
            try:
                file_path = os.path.join(latest_file)
            except Exception as e:
                error_msg = "An error occurred while creating the file path. ({})".format(e)
                self.capture_error(error_msg, self.driver)
                raise Exception(error_msg)
        
            try:
                new_path = os.path.join(self.DEFAULT_DOWNLOAD_DIRECTORY, new_file_name)

                logger.debug(f"File Path: {file_path}")
                logger.debug(f"New Path: {new_path}")
                os.rename(file_path, new_path)
                
            except Exception as e:
                error_msg = "An error occurred while renaming the file. ({})".format(e)
                self.capture_error(error_msg, self.driver)
                raise Exception(error_msg)
            
            return True, new_file_name
    
    def line_prepender(self, filename, line):
        with open(filename, 'r+', encoding="utf8") as f:
            content = f.read()
            f.seek(0, 0)
            f.write(line.rstrip('\r\n') + '\n\n' + content)