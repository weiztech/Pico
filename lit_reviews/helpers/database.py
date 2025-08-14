import boto3
import os 
import time

from django.conf import settings
from django.core.files import File
from django.utils import timezone

from lit_reviews.utils.consts import (
    pubmed_article_types,
    pubmed_age,
    clinical_trials_age_group,
    clinical_trials_recruitment_status,
    clinical_trials_expanded_access_status,
    clinical_trials_study_results,
)
from lit_reviews.models import (
    NCBIDatabase,
    DataBaseDump,
    SearchConfiguration,
    SearchParameter,
)
from django.conf import settings
from django.core.files import File
from backend.logger import logger

from backend.logger import logger
from django.utils import timezone
import boto3
import os 
import time


def cleanup_old_dump_files():
    """
    Delete database dumpfiels older than 1 month.
    """
    TODAY = timezone.now()
    TWO_MONTHS_EARLIER = TODAY - timezone.timedelta(days=60)
    old_db_dumps = DataBaseDump.objects.filter(timestamp__lt=TWO_MONTHS_EARLIER)
    for instance in old_db_dumps:
        session = boto3.Session(aws_access_key_id=settings.AWS_ACCESS_KEY_ID,aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY)
        s3 = session.client('s3')
        s3.delete_object(Bucket=settings.AWS_STORAGE_BUCKET_NAME, Key=str(instance.file))
        
    old_db_dumps.delete()

def create_essentials():
    db_name = os.getenv("db_name")
    db_user = os.getenv("db_user")
    db_password = os.getenv("db_password")
    db_host = os.getenv("db_host")
    db_port = os.getenv("db_port")
    filename = "citemed_backup" + "-" + time.strftime("%Y%m%d") + ".backup"
    pssword_cmd = f"PGPASSWORD='{db_password}' "
    command_str = str(db_host)+" -p "+str(db_port)+" -d "+db_name+" -U "+db_user
    return command_str, filename, pssword_cmd

def create_tmp_backup_file(filename):
    project_path = os.path.abspath(os.path.dirname(__name__))
    output_path = "/tmp/{0}".format(filename)
    backup_path = os.path.join(project_path, output_path)
    return backup_path

def backup_database():
    """
    Create a buckup file for the current database,
    This Script works only on Linux serevrs.
    """
    cleanup_old_dump_files()

    from lit_reviews.tasks import send_email
    command_str,filename,pssword_cmd = create_essentials()
    backup_path = create_tmp_backup_file(filename)
    command_str = pssword_cmd + "pg_dump -h " + command_str
    command_str = command_str + " -F c -b -v -f "+backup_path
    try:
        os.system(command_str)
        logger.debug("Backup Completed")
        opened_file = open(backup_path, "rb")
        db_dump = DataBaseDump.objects.create()
        t = time.localtime()
        timestamp = time.strftime("%b-%d-%Y_%H%M", t)
        file_name = "db_dump-" + timestamp + ".backup"
        db_dump.file.save(file_name , File(opened_file))
        opened_file.close()
        # send_email(subject, message, to=[], link=None, is_error=False ,error="")
        subject = "Auto Generate Prod Database Dump File"
        message = f"The database dump file has been generated successfuly at {timestamp}, Please check below link toget the file!"
        send_email.delay(subject, message, to=[settings.DEFAULT_FROM_EMAIL], link=db_dump.file.url)
        logger.debug("Email Message Send: {0}".format(message))

    except Exception as e:
        logger.error("!!Problem occured!!: {0}".format(str(e)))
        subject = "Auto Generate Prod Database Dump File"
        message = f"Error occured while trying to generate a database dump file, Below is the error message"
        send_email.delay(subject, message, to=[settings.DEFAULT_FROM_EMAIL], is_error=True, error=e)


def restore_database():
    command_str,filename,pssword_cmd = create_essentials()
    backup_path = create_tmp_backup_file(filename)
    command_str = pssword_cmd+ "pg_restore -h " + command_str
    command_str = command_str + " -v '"+backup_path+"/"+filename+"'"
    command_str = command_str + " -F c -b -v -f '"+backup_path

    try:
        os.system(command_str)
        logger.debug("Restore completed")

    except Exception as e:
        logger.error("!!Problem occured!!: {0}".format(str(e)))




def create_init_search_params_templates():
    ####### PUBMED #########
    pubmed_search_config = SearchConfiguration.objects.create(
        database=NCBIDatabase.objects.get(entrez_enum="pubmed"),
        is_template=True
    )
    pubmed_age_choices = ",".join(list(pubmed_age.keys()))
    SearchParameter.objects.create(
        search_config=pubmed_search_config,
        name="Age",
        type="CK",
        options=pubmed_age_choices,
    )
    pubmed_article_types_choices = ",".join(list(pubmed_article_types.keys()))
    SearchParameter.objects.create(
        search_config=pubmed_search_config,
        name="Article Type",
        type="CK",
        options=pubmed_article_types_choices,
    )
    SearchParameter.objects.create(
        search_config=pubmed_search_config,
        name="Start Date",
        type="DT",
    )
    SearchParameter.objects.create(
        search_config=pubmed_search_config,
        name="End Date",
        type="DT",
    )

    ####### CLINICAL TRAILAS #########
    ctgove_search_config = SearchConfiguration.objects.create(
        database=NCBIDatabase.objects.get(entrez_enum="ct_gov"),
        is_template=True
    )
    clinical_trials_age_choices = ",".join(list(clinical_trials_age_group.keys()))
    SearchParameter.objects.create(
        search_config=ctgove_search_config,
        name="Age Group",
        type="CK",
        options=clinical_trials_age_choices,
    )

    clinical_trials_recruitment_status_choices = ",".join(list(clinical_trials_recruitment_status.keys()))
    SearchParameter.objects.create(
        search_config=ctgove_search_config,
        name="Recruitment Status",
        type="CK",
        options=clinical_trials_recruitment_status_choices,
    )

    clinical_trials_expanded_access_status_choices = ",".join(list(clinical_trials_expanded_access_status.keys()))
    SearchParameter.objects.create(
        search_config=ctgove_search_config,
        name="Expanded Access Status",
        type="CK",
        options=clinical_trials_expanded_access_status_choices,
    )

    clinical_trials_study_results_choices = ",".join(list(clinical_trials_study_results.keys()))
    SearchParameter.objects.create(
        search_config=ctgove_search_config,
        name="Study Results",
        type="DP",
        options=clinical_trials_study_results_choices,
        value="Studies With Results"
    )

    SearchParameter.objects.create(
        search_config=ctgove_search_config,
        name="Start Date",
        type="DT",
    )
    SearchParameter.objects.create(
        search_config=ctgove_search_config,
        name="End Date",
        type="DT",
    )


    ####### PMC #########
    pmc_config = SearchConfiguration.objects.create(
        database=NCBIDatabase.objects.get(entrez_enum="pmc"),
        is_template=True
    )
    SearchParameter.objects.create(
        search_config=pmc_config,
        name="Start Date",
        type="DT",
    )
    SearchParameter.objects.create(
        search_config=pmc_config,
        name="End Date",
        type="DT",
    )

    ####### Cochrane #########
    cochrane_config = SearchConfiguration.objects.create(
        database=NCBIDatabase.objects.get(entrez_enum="cochrane"),
        is_template=True
    )
    SearchParameter.objects.create(
        search_config=cochrane_config,
        name="Start Date",
        type="DT",
    )
    SearchParameter.objects.create(
        search_config=cochrane_config,
        name="End Date",
        type="DT",
    )

    ####### Google Scholar #########
    scholar_config = SearchConfiguration.objects.create(
        database=NCBIDatabase.objects.get(entrez_enum="scholar"),
        is_template=True
    )
    SearchParameter.objects.create(
        search_config=scholar_config,
        name="Start Date",
        type="DT",
    )
    SearchParameter.objects.create(
        search_config=scholar_config,
        name="End Date",
        type="DT",
    )
    SearchParameter.objects.create(
        search_config=scholar_config,
        name="Max Results",
        type="NB",
    )

