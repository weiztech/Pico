import re
import boto3
import os 
import hashlib
import uuid
from selenium import webdriver
from selenium.webdriver.chrome.service import Service

from backend import settings
from backend.logger import logger 
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.conf import settings

from botocore.exceptions import ClientError
from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.core.files.base import ContentFile
from lit_reviews.models import CustomerSettings


User = get_user_model()

def get_server_env():
    if settings.CELERY_DEFAULT_QUEUE == "MAIN_PROD":
        return "Prod"
    elif settings.CELERY_DEFAULT_QUEUE == "DEMO_ENV":
        return "Demo"
    elif settings.CELERY_DEFAULT_QUEUE == "PUBLIC":
        return "Public"
    else:
        return "Staging"
    

def construct_report_error(err_msg, err_track, report_job, RT, lit_review, version_number=None):
    from lit_reviews.tasks import send_error_email
    logger.error(err_track)
    report_job.status = "INCOMPLETE-ERROR"
    report_job.error_msg = err_msg 
    if version_number and version_number > Decimal("1.0"):
        version_number = Decimal(version_number) - Decimal('.1')
        report_job.version_number = version_number
    report_job.save()
    user = User.objects.filter(client=lit_review.client).first()
    user_username = user.username if user else "Unknown"
    user_email = user.email if user else "Unknown"
    send_error_email.delay(RT, str(lit_review), user_username, user_email, err_track)
    return err_msg


def create_presigned_url(bucket_name, object_name, expiration=60):
    """Generate a presigned URL to share an S3 object

    :param bucket_name: string
    :param object_name: string -> s3 bucket object name
    :param expiration: Time in seconds for the presigned URL to remain valid
    :return: Presigned URL as string. If error, returns None.
    """

    # Generate a presigned URL for the S3 object
    s3_client = boto3.client('s3')
    try:
        response = s3_client.generate_presigned_url('get_object',
                                                    Params={'Bucket': bucket_name,
                                                            'Key': object_name},
                                                    ExpiresIn=expiration)
    except ClientError as e:
        logger.error(e)
        return None

    # The response contains the presigned URL
    return response


def calculte_years_back(start_date, end_date):
    if start_date is None or end_date is None:
        return 0
    
    difference = end_date - start_date
    return round((difference.days + difference.seconds / 86400) / 365.2425)

def create_tmp_file(file_name, content):
    """
    Create temporary file to extract info / manipulates files on the local machine.
    :param: file_name: you can give it a random file name
    :param: content: file content in text format
    """
    unique_id = uuid.uuid4()
    temp_folder = f"tmp/{unique_id}"
    os.makedirs(temp_folder, exist_ok=True)
    file_name = file_name.replace("/", "")
    tmp_file = os.path.join(temp_folder, file_name)
    fout = open(tmp_file, "wb+")
    file_content = ContentFile(content)
    for chunk in file_content.chunks():
        fout.write(chunk)
    fout.close()
    return tmp_file


def generate_number_from_text(text):
    # Generate a SHA-256 hash of the input text
    hash_object = hashlib.sha256(text.encode())
    # Convert the hash to an integer
    hash_int = int(hash_object.hexdigest(), 16)
    # Ensure the number is within 3 digits
    number = hash_int % 1000
    return number

def get_customer_settings(user):
    if user.client:
        customer_settings = CustomerSettings.objects.filter(client=user.client).first()
        if not customer_settings:
            customer_settings = CustomerSettings.objects.create(client=user.client)

        return customer_settings
    else:
        default_settings = CustomerSettings.objects.filter(client__isnull=True).first()
        if not default_settings:
            default_settings = CustomerSettings.objects.create()

        return default_settings


def create_chrome_driver(download_directory):
    options = webdriver.ChromeOptions()
    if not settings.DISABLE_HEADLESS_SCRAPER:
        options.headless = True
        options.add_argument("--headless=new")
        options.add_argument("--disable-gpu")
        
    options.add_argument("--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")
    options.add_argument("--no-sandbox")
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('log-level=3')
    options.add_argument("start-maximized")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    options.add_experimental_option("prefs", {
        "plugins.always_open_pdf_externally": True,  # Forces download
        "download.default_directory": download_directory,
    })
    
    if not settings.DISABLE_CHROME_OPTIONS:
        # Please activate to this section when you deployment

        try:
            chrome_bin_path = os.environ.get("GOOGLE_CHROME_BIN")
            print("Cchrome bin localtion: " + str(chrome_bin_path))
        except Exception as e:
            raise Exception("An error occurred while getting the GOOGLE_CHROME_BIN from environ. ({})".format(e))
        
        if chrome_bin_path == None:
            raise Exception("Please set GOOGLE_CHROME_BIN as environment variable. ")

        try:
            options.binary_location = chrome_bin_path
        except Exception as e:
            raise Exception("An error occurred while setting the GOOGLE_CHROME_BIN from environ. ({})".format(e))
            
        try:
            driver_path = os.environ.get("CHROMEDRIVER_PATH")
            print("chromedriver path: " + str(driver_path))
        except Exception as e:
            raise Exception("An error occurred while getting the CHROMEDRIVER_PATH from environ. ({})".format(e))
        
        if driver_path == None:
            raise Exception("Please set CHROMEDRIVER_PATH as environment variable. ")

        service = Service(executable_path=driver_path)
        driver = webdriver.Chrome(service=service, options=options)
        # driver = webdriver.Chrome(executable_path=driver_path, chrome_options=options)

    else:
        driver = webdriver.Chrome(options=options)
        
    return driver


def count_word_occurrences(text, word):
    pattern = rf'\b{re.escape(word)}\b'
    matches = re.findall(pattern, text, flags=re.IGNORECASE)
    return len(matches)