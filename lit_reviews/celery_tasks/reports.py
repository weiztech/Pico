import traceback
from zipfile import ZipFile, ZIP_DEFLATED
import os
import urllib

import requests
import zipfile
from pathlib import Path
import datetime, pytz
from datetime import date, timedelta
import io
import uuid
import shutil

from decimal import Decimal
from tempfile import NamedTemporaryFile
from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files import File
from backend.logger import logger

from client_portal.models import *
from lit_reviews.models import *

from lit_reviews.helpers.search_terms import (
    get_search_date_ranges,
)
from lit_reviews.helpers.reports import (
    create_excel_file, 
    create_full_text_folder, 
    get_company_logo 
)
from lit_reviews.helpers.generic import construct_report_error
from lit_reviews.helpers.articles import name_article_full_text_pdf
from lit_reviews.report_builder.appendices import vigilance_report
from lit_reviews.report_builder.protocol_context_builder import *
from lit_reviews.report_builder.appendix_e_tables import (
    all_maude_aes, 
    all_maude_recalls, 
    all_manual_aes, 
    all_manual_recalls 
)
from lit_reviews.report_builder.second_pass_articles import second_pass_articles_context, second_pass_articles_ris
from lit_reviews.report_builder.all_articles_reviews import get_article_reviews_ris
from lit_reviews.report_builder.search_terms_summary import search_terms_summary_context
from lit_reviews.report_builder.appendix_e2_report import appendix_e2_report_context
from lit_reviews.report_builder.all_articles_reviews import (
    all_articles_reviews_context,
    generate_article_duplicates_content,
)
from lit_reviews.report_builder.build_report_output import (
    build_report_output,
    build_prisma_output,
    build_second_pass_word_output,
)
from lit_reviews.report_builder.prisma import (
    prisma_summary_excel_context,
    prisma_excluded_articles_summary_context,
    prisma_article_tags_summary_context,
)

from lit_reviews.report_builder.audit_tracking_logs import (
    audit_tracking_logs_context
)

from docxtpl import DocxTemplate
from django.contrib.auth import get_user_model

User = get_user_model()
READ_BUF_SIZE = 4096

########## Helpers #########

def create_report_object(lit_review, REPORT_TYPE, is_simple=False):
    """
    Create the report objects, based on provided type
    """
    logger.debug("{0} for {1}".format(REPORT_TYPE, str(lit_review)))

    try:
        prev_job = FinallReportJob.objects.filter(literature_review=lit_review, report_type=REPORT_TYPE).latest('timestamp')
        version_number = prev_job.version_number + Decimal('.1')
    except Exception as e:
        logger.warning("exception incrementing version number  {0}".format(str(e)))
        version_number = 1.0

    report_job = FinallReportJob(
        literature_review=lit_review,
        status="RUNNING",
        job_started_time=datetime.datetime.now(pytz.utc),
        version_number=version_number,
        report_type=REPORT_TYPE,
    )
    report_job.save()
    logger.debug("Report Job Status {0}".format(report_job.status))

    if is_simple:
        report_job.is_simple = True
        report_job.save()

    return report_job, version_number


def form_report_name(lit_review, report, file_type, default_report_type=None):
    """
    Generate the report unique name based on the provided type
    """
    REPORT_TYPE = report.report_type 
    if REPORT_TYPE == "PROTOCOL":
        REPORT_TYPE = "LITP"
    elif REPORT_TYPE == "REPORT":
        REPORT_TYPE = "LITR"

    if default_report_type:
        REPORT_TYPE = default_report_type

    output_path = "/tmp/Project_{0}/".format(lit_review.id)
    Path(output_path).mkdir(parents=True, exist_ok=True)
    today = datetime.datetime.now(pytz.utc).strftime("%Y-%m-%d %H:%M")
    device_name = lit_review.device.__str__().replace("/", "")
    client_name = lit_review.client.name
    document_name = f"{client_name}_{device_name}_{REPORT_TYPE}_V{report.version_number}_{today}.{file_type}"
    document_path = output_path + document_name
    return document_path, document_name

########## TASKS #############

def build_protocol_task(review_id, is_simple=False):
    lit_review = LiteratureReview.objects.get(id=review_id)
    report_job, version_number = create_report_object(lit_review, "PROTOCOL", is_simple=is_simple)

    try:
        logger.debug("TODO: validate protocol")

    except Exception as e:
        err_track = str(traceback.format_exc())
        error_msg = "Error in Validating Protocol \n " + str(e)
        return construct_report_error(error_msg, err_track, report_job, "LITP Report", lit_review, version_number)

    try:    
        context = build_protocol_context(lit_review, report_job)      
        document_path, document_name = form_report_name(lit_review, report_job, "docx")

    except Exception as e:
        err_track = str(traceback.format_exc())
        error_msg = "Error in protocol context generation \n " + str(e)
        return construct_report_error(error_msg, err_track, report_job, "LITP Report", lit_review, version_number)
    
    try:
        ## generate output document
        document_template = "SimpleProtocolTemplate.docx" if is_simple else "ProtocolTemplate.docx" 
        doc = DocxTemplate("report_templates/"+document_template)
        logger.debug("full context rendered: {0}".format(context))

        image_link = context['company_logo_link']
        company_logo = get_company_logo(image_link, doc)
        context['company_logo'] = company_logo
        doc.render(context, autoescape=True)
        doc.save(document_path)
        f = open(document_path, "rb")
        protocol_file = File(f, name=document_name)
        report_job.protocol = protocol_file
        report_job.status = "COMPLETE"
        report_job.save()

    except Exception as e:
        error_msg = "Error in protocol field saving  \n " + str(e)
        err_track = str(traceback.format_exc())
        return construct_report_error(error_msg, err_track, report_job, "LITP Report", lit_review, version_number)
    

def build_report_task(review_id, is_simple=False):
    lit_review = LiteratureReview.objects.get(id=review_id)
    report_job, version_number = create_report_object(lit_review, "REPORT", is_simple=is_simple)

    # Validate Report
    try:
        logger.debug("SKIPPING VALIDATION")
        #validate_report(review_id)
    except Exception as e:
        err_track = str(traceback.format_exc())
        error_msg = "Error in Validating Report \n " + str(e)
        return construct_report_error(error_msg, err_track, report_job, "LITR Report", lit_review, version_number)


    # Create Report Outputs
    document_path, document_name = form_report_name(lit_review, report_job, "docx")
    # Build Report Outputs
    logger.debug("building report schemas now...")
    doc = build_report_output(review_id, report_job, "REPORT", document_path, is_simple=is_simple)

    # if doc is not an object and rather an exception or an error message string => report building failed no need to continue 
    if isinstance(doc, Exception) or isinstance(doc, str):
        return doc 
    
    # Generate Final Files
    try:
        doc.save(document_path)
        f = open(document_path, "rb")
        report_file = File(f, name=document_name)
        report_job.report = report_file
        report_job.status = "COMPLETE"
        report_job.save()

    except Exception as e:
        err_track = str(traceback.format_exc())
        error_msg = "Error in report file saving  \n " + str(e)
        return construct_report_error(error_msg, err_track, report_job, "LITR Report", lit_review, version_number)

    return None


def build_abbott_report_task(review_id):
    lit_review = LiteratureReview.objects.get(id=review_id)
    report_job, version_number = create_report_object(lit_review, "ABBOTT_REPORT")

    # Create Report Outputs
    document_path, document_name = form_report_name(lit_review, report_job, "docx")
    # Build Report Outputs
    logger.debug("building report schemas now...")
    context =  build_protocol_context(lit_review, report_job)

    try:
        study_outcomes_field = ExtractionField.objects.get(name="study outcomes", literature_review=lit_review)
        study_info_field = ExtractionField.objects.get(name="study info", literature_review=lit_review)
        study_population_field = ExtractionField.objects.get(name="study population", literature_review=lit_review)
        article_summary_field = ExtractionField.objects.get(name="article summary", literature_review=lit_review)

    except:
        err_track = str(traceback.format_exc())
        error_msg = "Please make sure you've added these extraction fields in order for this report to be generated successfully. the required fields are study outcomes, study info, study population, article summary."
        return construct_report_error(error_msg, err_track, report_job, "LITR Report", lit_review, version_number)

    appraisals = ClinicalLiteratureAppraisal.objects.filter(article_review__search__literature_review=lit_review)
    appraisals_context = []
    table_index = 1
    for appraisal in appraisals:

        AppraisalExtractionField.objects.filter(
            extraction_field__name="study outcomes",
            extraction_field__literature_review=lit_review
        ).first()
        appraisal_context_record = {
            "title": appraisal.article_review.article.title,
            "abstract": appraisal.article_review.article.abstract,
            "citation": appraisal.article_review.article.citation,
            "study_info": AppraisalExtractionField.objects.get(clinical_appraisal=appraisal, extraction_field=study_info_field).value,
            "study_population": AppraisalExtractionField.objects.get(clinical_appraisal=appraisal, extraction_field=study_population_field).value,
            "study_outcomes": AppraisalExtractionField.objects.get(clinical_appraisal=appraisal, extraction_field=study_outcomes_field).value,
            "article_summary": AppraisalExtractionField.objects.get(clinical_appraisal=appraisal, extraction_field=article_summary_field).value,
            "table_number": table_index
        }
        appraisals_context.append(appraisal_context_record)
        table_index += 1

    context["appraisals"] = appraisals_context
    context["summary_table_index"] = len(appraisals) + 1
    doc = DocxTemplate("report_templates/AbbottTemplate.docx")
    # adding logo image
    image_link = context['company_logo_link']
    company_logo = get_company_logo(image_link, doc)
    context['company_logo'] = company_logo
    doc.render(context, autoescape=True)
    
    # Generate Final Files
    try:
        doc.save(document_path)
        f = open(document_path, "rb")
        report_file = File(f, name=document_name)
        report_job.abbot_report = report_file
        report_job.status = "COMPLETE"
        report_job.save()

    except Exception as e:
        err_track = str(traceback.format_exc())
        error_msg = "Error in report file saving  \n " + str(e)
        return construct_report_error(error_msg, err_track, report_job, "LITR Report", lit_review, version_number)

    return None


def build_second_pass_word_report_task(review_id):
    lit_review = LiteratureReview.objects.get(id=review_id)
    report_job, version_number = create_report_object(lit_review, "SECOND_PASS_WORD")

    # Validate Report
    try:
        logger.debug("SKIPPING VALIDATION")
        #validate_report(review_id)
    except Exception as e:
        err_track = str(traceback.format_exc())
        error_msg = "Error in Validating Report \n " + str(e)
        return construct_report_error(error_msg, err_track, report_job, "LITR Report", lit_review, version_number)
    
    # Setup output path
    document_path, document_name = form_report_name(lit_review, report_job, "docx")
    logger.debug("building report schemas now...")
    doc = build_second_pass_word_output(review_id, report_job, "SECOND_PASS_WORD")

    # Generate Final Files
    try:
        doc.save(document_path)
        f = open(document_path, "rb")
        report_file = File(f, name=document_name)
        report_job.second_pass_word = report_file
        logger.debug("Generating 2nd Pass Extraction Word Completed!")
        report_job.status = "COMPLETE"
        report_job.save()

    except Exception as e:
        err_track = str(traceback.format_exc())
        error_msg = "Error in report file saving  \n " + str(e)
        return construct_report_error(error_msg, err_track, report_job, "LITR Report", lit_review, version_number)
    
    return None


def build_prisma_task(review_id):
    lit_review = LiteratureReview.objects.get(id=review_id)
    # Generate Final Report and Version Number
    report_job, version_number = create_report_object(lit_review, "PRISMA")

    # Validate Report
    try:
        logger.debug("SKIPPING VALIDATION")
        #validate_report(review_id)
    except Exception as e:
        err_track = str(traceback.format_exc())
        error_msg = "Error in Validating Report \n " + str(e)
        return construct_report_error(error_msg, err_track, report_job, "LITR Report", lit_review, version_number)
    
    # Build Prisma Outputs
    logger.debug("building report schemas now...")
    doc = build_prisma_output(review_id, report_job, "REPORT")

    # Generate Prisma Chart Dox File
    try:
        document_path, document_name = form_report_name(lit_review, report_job, "docx")
        doc.save(document_path)

    except Exception as e:
        err_track = str(traceback.format_exc())
        error_msg = "Error in report file saving  \n " + str(e)
        return construct_report_error(error_msg, err_track, report_job, "LITR Report", lit_review, version_number)

    # Generate Prisma Summary Excel File 
    try:
        ## generate output document
        prisma_row_list = prisma_summary_excel_context(review_id)
        today = datetime.datetime.now(pytz.utc).strftime("%Y-%m-%d %H:%M") 
        prisma_summary_document_name_csv = "{}_PRISMA_SUMMARY_{}.csv".format(str(lit_review).replace("/", "-"), today)
        prisma_summary_document_name_excel = "{}_PRISMA_SUMMARY_{}.xlsx".format(str(lit_review).replace("/", "-"), today)
        prisma_summary_report_path = create_excel_file(
            review_id, 
            report_job.id, 
            prisma_summary_document_name_csv, 
            prisma_summary_document_name_excel,
            prisma_row_list,
        )

    except Exception as e:
        error_msg = "Error in Prisma Zip Generation - Prisma Summary File  \n " + str(e)
        err_track = str(traceback.format_exc())
        return construct_report_error(error_msg, err_track, report_job, "Prisma Report", lit_review, version_number)
    
    # General Excluded Articles Summary Excel File 
    try:
        ## generate output document
        prisma_exclusions_row_list = prisma_excluded_articles_summary_context(review_id) 
        today = datetime.datetime.now(pytz.utc).strftime("%Y-%m-%d %H:%M")
        prisma_exclusions_summary_document_name_csv = "{}_PRISMA_EXCLUSIONS_SUMMARY_{}.csv".format(str(lit_review).replace("/", "-"), today)
        prisma_exclusions_summary_document_name_excel = "{}_PRISMA_EXCLUSIONS_SUMMARY_{}.xlsx".format(str(lit_review).replace("/", "-"), today)
        prisma_exclusions_summary_report_path = create_excel_file(
            review_id, 
            report_job.id, 
            prisma_exclusions_summary_document_name_csv, 
            prisma_exclusions_summary_document_name_excel,
            prisma_exclusions_row_list,
        )

    except Exception as e:
        error_msg = "Error in Prisma Zip Generation - Excluded Articles Summary File  \n " + str(e)
        err_track = str(traceback.format_exc())
        return construct_report_error(error_msg, err_track, report_job, "Prisma Report", lit_review, version_number)
    
    # General Article Tags Summary Excel File 
    try:
        ## generate output document
        prisma_article_tags_row_list = prisma_article_tags_summary_context(review_id) 
        today = datetime.datetime.now(pytz.utc).strftime("%Y-%m-%d %H:%M")
        prisma_article_tags_summary_document_name_csv = "{}_PRISMA_ARTICLE_TAGS_SUMMARY_{}.csv".format(str(lit_review).replace("/", "-"), today)
        prisma_article_tags_summary_document_name_excel = "{}_PRISMA_ARTICLE_TAGS_SUMMARY_{}.xlsx".format(str(lit_review).replace("/", "-"), today)
        prisma_article_tags_summary_report_path = create_excel_file(
            review_id, 
            report_job.id, 
            prisma_article_tags_summary_document_name_csv, 
            prisma_article_tags_summary_document_name_excel,
            prisma_article_tags_row_list,
        )

    except Exception as e:
        error_msg = "Error in Prisma Zip Generation - Article Tags Summary File  \n " + str(e)
        err_track = str(traceback.format_exc())
        return construct_report_error(error_msg, err_track, report_job, "Prisma Report", lit_review, version_number)
    
    # Open zip file
    with NamedTemporaryFile() as temp_zip_file:
        zip_file = ZipFile(temp_zip_file.file, mode="w", compression=ZIP_DEFLATED)
        zip_file.write(filename=document_path, arcname="Prisma Chart.docx")
        zip_file.write(filename=prisma_summary_report_path, arcname="Prisma Summary.xlsx")
        zip_file.write(filename=prisma_exclusions_summary_report_path, arcname="Excluded Articles Summary.xlsx")
        zip_file.write(filename=prisma_article_tags_summary_report_path, arcname="Article Tags Summary.xlsx")
        zip_file.close()

        with open(temp_zip_file.name, "rb") as file:
            # Create Report Outputs
            document_path, document_name = form_report_name(lit_review, report_job, "zip")

            # Save zip output 
            report_job.prisma = File(file, name=document_name)
            logger.debug("Prisma File Generation Completed!")
            report_job.status = "COMPLETE"
            report_job.save()

    return None


def generate_ae_report_task(review_id):
    ### do we need to change this model to a new one, or just add fields to it?
    # report_config = FinalReportConfig.objects.get_or_create(literature_review=review_id)[0]
    lit_review = LiteratureReview.objects.get(id=review_id)

    date_of_search =  date(2021, 12, 31) ## manual overrids
    YS_BACK = 1
    days = 365 * YS_BACK
    date_end =  date_of_search - timedelta(days=days)
    logger.debug("Date End: {0}".format(date_end))

    report_job = FinallReportJob(
        literature_review=lit_review,
        status="RUNNING",
        job_started_time=datetime.datetime.now(pytz.utc),
    )
    report_job.save()
    logger.debug("Report Job Status: {0}".format(report_job.status))
    output_path = f"tmp/{str(uuid.uuid4())}/"
    ## vigilance_report()  (doesn't exist yet, new Vigilance report template)

    try:
        vig_path = vigilance_report(output_path, review_id, date_of_search=date_of_search, date_end=date_end)
        e = open(vig_path, "rb")
        document_path, document_name = form_report_name(lit_review, report_job, "docx")
        vig_file = File(e, name=document_name)
        report_job.vigilance_report = vig_file 
        report_job.save()
        logger.debug("vigilance report complete!")

    except Exception as e:
        error_msg = "Error in Vigilance Report \n " + str(e)
        err_track = str(traceback.format_exc())
        return construct_report_error(error_msg, err_track, report_job, "AE Report", lit_review)


        #raise Exception('need to make sure vigilance report and things are getting saved properly')

    # validate report here.
    try:
        logger.debug("SKIPPING Validate_report method")
        #validate_report(review_id)

    except Exception as e:
        error_msg = "Error in Validating Report \n " + str(e)
        err_track = str(traceback.format_exc())
        return construct_report_error(error_msg, err_track, report_job, "AE Report", lit_review)

    try:        
        report_job.status = "COMPLETE"
        report_job.save()

    except Exception as e:
        error_msg = "Error Saving Final Files " + str(e)
        err_track = str(traceback.format_exc())
        return construct_report_error(error_msg, err_track, report_job, "AE Report", lit_review)

   ### vigilance report to go here


def generate_search_term_report_task(search_id):
    search = LiteratureSearch.objects.get(pk=search_id)
    
    try:
        date_now = datetime.datetime.now(pytz.utc).strftime("%Y-%m-%d %H:%M")
        file_name = search.literature_review.device.__str__() + "__SearchTermReport__" + date_now

        TMP_ROOT = settings.TMP_ROOT
        FILE_PATH = TMP_ROOT + "/" + str(file_name) + ".zip"
        
        with zipfile.ZipFile(FILE_PATH, 'w') as zp:
            if search.search_file:
                res = requests.get(search.search_file.url)
                file_name = search.search_file.name.split("/")[-1]
                zp.writestr(file_name, res.content)
            
                start_date, end_date = get_search_date_ranges(search)
                
                start_date = start_date.date() if isinstance(start_date, datetime.datetime) else start_date
                end_date = end_date.date() if isinstance(end_date, datetime.datetime) else end_date
                years_back = relativedelta(end_date, start_date).years
                rows_list = [
                    ["Search Term", "Years Back", "Start Date", "End Date"],
                    [str(search.term), years_back, start_date, end_date],
                ]
            
                xlsx_csv_file_path = create_excel_file(
                    search.id ,
                    search.id , 
                    "Search_Term_Parameters.csv", 
                    "Search_Term_Parameters.xlsx",
                    rows_list
                )
                with open(xlsx_csv_file_path, 'rb') as excel_file:
                    zp.writestr("Search_Term_Parameters.xlsx", excel_file.read())

            else:
                search.search_report_failing_msg = """
                    The report file generation failed due to the absence of the results file within the search. 
                    This is commonly observed when a search is excluded. It's important to note that when a search is excluded, 
                    the file will not be downloaded, particularly if the Auto Search Feature has been utilized. 
                    Thereby the articles will not be imported into the application at all.
                """
                search.save()
                return "Failed"

        search.search_report = File(open(FILE_PATH, "rb"))
        search.save()
        logger.debug(f"Report has been generated successfully for SEARCH ID {search.id}")

    except Exception as e:
        err_msg = str(traceback.format_exc())
        search.search_report_failing_msg = e
        search.save()
        logger.error(f"Error while generating search term report for SEARCH ID {search.id} : {err_msg}")

    return search 


def generate_fulltext_zip_report_task(literature_review_id, user_id=None):
    from lit_reviews.tasks import send_error_email

    try:
        article_reviews = (
            ArticleReview.objects.filter(search__literature_review_id=literature_review_id, state='I')
            .prefetch_related("article")
        )
        lt_review = LiteratureReview.objects.get(id=literature_review_id)
        error_msg = ""
        report_job, version_number = create_report_object(lt_review, "FULL_TEXT_ZIP")

        logger.debug("Generating FullText Zip...")
        TMP_ROOT = "tmp/"
        FOLDER_PATH = TMP_ROOT + "output_folder/"
        os.mkdir(FOLDER_PATH)
        RETAINED_FOLDER = FOLDER_PATH + "Included Articles/"
        EXCLUDED_FOLDER = FOLDER_PATH + "Excluded Articles/"
        os.mkdir(RETAINED_FOLDER)
        os.mkdir(EXCLUDED_FOLDER)
        ZIP_FILE_NAME = lt_review.device.__str__() + "__Full_Text_PDFs_" + datetime.datetime.now(pytz.utc).strftime("%Y-%m-%d %H:%M")

        for review in article_reviews:
            article = review.article
            logger.debug(f"Full text for Article ID : {article.id}")
            if article.full_text:
                r = requests.get(article.full_text.url)
                # bytes(r.content, encoding= 'utf-8')
                file_name = name_article_full_text_pdf(article, user_id)

                # get rid of any / in the name might break the file creation
                if "/tmp" in file_name:
                    file_name = file_name.replace("/tmp", "")
                if "/ft" in file_name:
                    file_name = file_name.replace("/ft", "")
                if "/" in file_name:
                    file_name = file_name.replace("/", "")

                appraisal = ClinicalLiteratureAppraisal.objects.filter(article_review=review).first()
                DESTINATION_FOLDER = RETAINED_FOLDER if appraisal.included else EXCLUDED_FOLDER
                with open(DESTINATION_FOLDER + file_name, "wb+") as file:
                    file.write(r.content)

            else:
                appraisal = ClinicalLiteratureAppraisal.objects.filter(article_review=review).first()
                if appraisal.included != False:
                    upload_full_text_link = reverse('lit_reviews:full_text_upload', kwargs={'id': lt_review.id})
                    error_msg = f"""
                    <p>
                        No full text found for this Article:
                        <br />
                        Article ID: {article.id}
                        <br />
                        Article Title: {article.title}

                        <br />
                        Please Navigate to <a href="{upload_full_text_link}"> Upload Full Text </a> and upload The Article Full Text PDF.
                        <br />
                        To Get instant help from our team Please submit a ticket <a href="https://share.hsforms.com/1jqB4CJx9RxyvGL3qQYo2rgcq0hk"> Here </a>.
                    </p>
                    """

        FILE_PATH = TMP_ROOT + ZIP_FILE_NAME + ".zip"
        if os.path.exists(FILE_PATH):
            os.remove(FILE_PATH)
        logger.debug(f"File Path: {FILE_PATH}")
        # archive to a zip file
        shutil.make_archive(TMP_ROOT + ZIP_FILE_NAME, 'zip', FOLDER_PATH) 
        with open(FILE_PATH, "rb") as zp_file:
            zp_file = File(zp_file)
            
            report_job.fulltext_zip = zp_file
            if error_msg:
                report_job.error_msg = error_msg
                report_job.status = "INCOMPLETE-ERROR" 
                report_job.version_number = version_number
            else:
                report_job.error_msg = None
                report_job.status = "COMPLETE" 

            report_job.save()
            logger.info("FT Zip generated and saved ")
            shutil.rmtree(FOLDER_PATH)
            return "success"    
    
    except Exception as error:
        logger.info('Error to generate file')
        err_track = str(traceback.format_exc())
        error_msg = "Error in report file saving  \n " + str(error)
        logger.error("caught error generating full text zips : {0}".format(err_track))
        shutil.rmtree(FOLDER_PATH)
        user = User.objects.filter(client=lt_review.client).first()
        if user:
            send_error_email.delay("Full Text Zip Report", str(lt_review), user.username, user.email, err_track)
        return construct_report_error(error_msg, err_track, report_job, "LITR Report", lt_review, version_number)
    

def generate_search_zip_report_task(review_id):
    lit_review = LiteratureReview.objects.get(id=review_id)

    try:
        report_job, version_number = create_report_object(lit_review, "SEARCH_VALIDATION_ZIP")

        searches: list[LiteratureSearch] = LiteratureSearch.objects.filter(
            literature_review_id=review_id
        )
        # Open zip file
        with NamedTemporaryFile() as temp_zip_file:
            zip_file = ZipFile(temp_zip_file.file, mode="w", compression=ZIP_DEFLATED)
            for search in searches:
                if not search.search_file:
                    continue
                search_file = File(search.search_file)
                with NamedTemporaryFile() as temp_file:
                    bin_data = search_file.read(READ_BUF_SIZE)
                    while bin_data:
                        temp_file.write(bin_data)
                        bin_data = search_file.read(READ_BUF_SIZE)
                    temp_file.flush()
                    zip_file.write(filename=temp_file.name, arcname=search_file.name)
            # report_job: FinallReportJob = (
            #     FinallReportJob.objects.filter(literature_review_id=review_id)
            #     .order_by("-timestamp")
            #     .first()
            # )
            zip_file.close()

            with open(temp_zip_file.name, "rb") as file:
                document_path, document_name = form_report_name(lit_review, report_job, "zip")              
                report_job.verification_zip = File(file, name=document_name)
                logger.debug("verification zip complete!")
                report_job.status = "COMPLETE"
                report_job.save()

    except Exception as e:
        err_track = str(traceback.format_exc())
        error_msg = "Search validation Zip {0}".format(e)
        return construct_report_error(error_msg, err_track, report_job, "Search Validation Zip Report", lit_review, version_number)
    

def generate_search_terms_summary_report_task(litreview_id):
    try:
        lit_review = LiteratureReview.objects.get(id=litreview_id)
        report_job, version_number = create_report_object(lit_review, "TERMS_SUMMARY")
        document_path, document_name = form_report_name(lit_review, report_job, "docx")

        context = build_protocol_context(lit_review, report_job)
        search_terms = {}
        props = LiteratureReviewSearchProposal.objects.filter(
            literature_review=lit_review
        ).order_by("id")
        for prop in props:
            if prop.literature_search:
                if prop.term in search_terms:
                    search_terms[prop.term]["dbs"] = [*search_terms[prop.term]["dbs"], prop.db.name]
                    start_date, end_date = get_search_date_ranges(prop.literature_search)
                    start_date = start_date.date() if isinstance(start_date, datetime.datetime) else start_date
                    end_date = end_date.date() if isinstance(end_date, datetime.datetime) else end_date 
                    search_terms[prop.term]["date_ranges"] = [*search_terms[prop.term]["date_ranges"], f"{start_date} to {end_date}"]

                else:
                    start_date, end_date = get_search_date_ranges(prop.literature_search)
                    start_date = start_date.date() if isinstance(start_date, datetime.datetime) else start_date
                    end_date = end_date.date() if isinstance(end_date, datetime.datetime) else end_date 
                    search_terms[prop.term] = {
                        "dbs": [prop.db.name],
                        "date_ranges": [f"{start_date} to {end_date}"]
                    }

        for key, value in search_terms.items():
            search_terms[key] = {"dbs": ", ".join(value["dbs"]) , "date_ranges": ", ".join(value["date_ranges"])}

        context["terms"] = search_terms
        ## generate output document
        doc = DocxTemplate("report_templates/TermsSummaryTemplate.docx")

        # adding logo image
        image_link = context['company_logo_link']
        company_logo = get_company_logo(image_link, doc)
        context['company_logo'] = company_logo

        doc.render(context, autoescape=True)
        doc.save(document_path)
        f = open(document_path, "rb")
        report_file = File(f, name=document_name)
        report_job.terms_summary_report = report_file
        report_job.status = "COMPLETE"
        report_job.save()

    except Exception as e:
        error_msg = "Error in report file saving  \n " + str(e)
        err_track = str(traceback.format_exc())
        return construct_report_error(error_msg, err_track, report_job, "Search Term Summary Report", lit_review, version_number)
    

def generate_appendix_e2_report_task(review_id):
    lit_review = LiteratureReview.objects.get(id=review_id)
    report_job, version_number = create_report_object(lit_review, "APPENDIX_E2")

    # validate report here.
    try:
        logger.debug("SKIPPING VALIDATION")
        #validate_report(review_id)
    except Exception as e:
        error_msg = "Error in Validating Report \n " + str(e)
        err_track = str(traceback.format_exc())
        return construct_report_error(error_msg, err_track, report_job, "Appendix E2 Report", lit_review, version_number)
    review = {
        "appendix_e": {
            "maude_tables": {
                "maude_aes": {
                    "E2_maude_aes": {} 
                } 
            }
        }
    }
    #review.appendix_e.maude_tables.maude_aes.E2_maude_aes.rows 
    review["appendix_e"]["maude_tables"]["maude_aes"]['E2_maude_aes']['rows'] = all_maude_aes(review_id)
    review["appendix_e"]["maude_recalls"] = {}
    review["appendix_e"]["maude_recalls"]['rows'] =  all_maude_recalls(review_id)
    review["appendix_e"]["manual_aes"] = {}
    review["appendix_e"]["manual_aes"]['rows'] = all_manual_aes(review_id)
    review["appendix_e"]["manual_recalls"] = {}
    review["appendix_e"]["manual_recalls"]['rows'] = all_manual_recalls(review_id)

    context = {}
    context =  build_protocol_context(lit_review, report_job)

    context["review"] = review
    logger.debug("full context rendered: {0}".format(context))

    try:
        ## generate output document
        doc = DocxTemplate("report_templates/AppendixE2Tempalte.docx")

        # adding logo image
        image_link = context['company_logo_link']
        company_logo = get_company_logo(image_link, doc)
        context['company_logo'] = company_logo

        document_path, document_name = form_report_name(lit_review, report_job, "docx")
        doc.render(context, autoescape=True)
        doc.save(document_path)
        f = open(document_path, "rb")
        report_file = File(f, name=document_name)
        report_job.appendix_e2 = report_file
        report_job.status = "COMPLETE"
        report_job.save()

    except Exception as e:
        error_msg = "Error in report file saving  \n " + str(e)
        err_track = str(traceback.format_exc())
        return construct_report_error(error_msg, err_track, report_job, "Appendix E2 Report", lit_review, version_number)

    return None


def export_2nd_pass_extraction_articles_task(review_id):
    lit_review = LiteratureReview.objects.get(id=review_id)
    report_job, version_number = create_report_object(lit_review, "SECONDPASS")

    try:
        document_path_csv, document_name_csv = form_report_name(lit_review, report_job, "csv")
        document_path_excel, document_name_excel = form_report_name(lit_review, report_job, "xlsx")        
        row_list = second_pass_articles_context(review_id)

    except Exception as e:
        error_msg = "Error in 2nd Pass Extrection Context Generation \n " + str(e)
        err_track = str(traceback.format_exc())
        return construct_report_error(error_msg, err_track, report_job, "Second Pass Excel Report", lit_review, version_number)

    try:
        ## generate output document
        document_path_final_excel = create_excel_file(
            review_id,
            report_job.id,
            document_name_csv,
            document_name_excel,
            row_list
        )
        f = open(document_path_final_excel, "rb")
        second_pass_articles_file = File(f)
        report_job.second_pass_articles = second_pass_articles_file
        report_job.status = "COMPLETE"
        report_job.save()

    except Exception as e:
        error_msg = "Error in 2nd Pass Extrection Exporting  \n " + str(e)
        err_track = str(traceback.format_exc())
        return construct_report_error(error_msg, err_track, report_job, "Second Pass Excel Report", lit_review, version_number)
    

def export_2nd_pass_extraction_articles_ris_task(review_id):
    lit_review = LiteratureReview.objects.get(id=review_id)
    report_job, version_number = create_report_object(lit_review, "SECOND_PASS_RIS")

    try:
        document_path, document_name = form_report_name(lit_review, report_job, "ris")
        temp_ris_file = second_pass_articles_ris(review_id, document_name)

    except Exception as e:
        error_msg = "Error in 2nd Pass Extrection RIS Context Generation \n " + str(e)
        err_track = str(traceback.format_exc())
        return construct_report_error(error_msg, err_track, report_job, "Second Pass RIS Report", lit_review, version_number)

    # generate full text files
    try:
        logger.debug("Generating FullText Zip...")
        TMP_ROOT, FOLDER_PATH = create_full_text_folder(lit_review)
        # ZIP_FILE_NAME = lit_review.device.__str__() + "__Full_Text__" + datetime.datetime.now(pytz.utc).strftime("%Y-%m-%d %H:%M")
        ZIP_FILE_NAME = document_name
        shutil.move(temp_ris_file, FOLDER_PATH + document_name)
        FILE_PATH = TMP_ROOT + ZIP_FILE_NAME + ".zip"
        if os.path.exists(FILE_PATH):
            os.remove(FILE_PATH)
        logger.debug(f"File Path: {FILE_PATH}")
        # archive to a zip file
        shutil.make_archive(TMP_ROOT + ZIP_FILE_NAME, 'zip', FOLDER_PATH) 
    
    except Exception as e:
        error_msg = "Error in 2nd Pass Extrection RIS Full text pdfs Generation \n " + str(e)
        err_track = str(traceback.format_exc())
        return construct_report_error(error_msg, err_track, report_job, "Second Pass RIS Report", lit_review, version_number)

    try:
        f = open(FILE_PATH, "rb")
        second_pass_articles_file = File(f)
        report_job.second_pass_ris = second_pass_articles_file
        report_job.status = "COMPLETE"
        report_job.save()
        shutil.rmtree(FOLDER_PATH)

    except Exception as e:
        error_msg = "Error in 2nd Pass Extrection Exporting  \n " + str(e)
        err_track = str(traceback.format_exc())
        return construct_report_error(error_msg, err_track, report_job, "Appendix E2 Report", lit_review, version_number)


def generate_search_terms_summary_excel_report_task(review_id):
    lit_review = LiteratureReview.objects.get(id=review_id)
    report_job, version_number = create_report_object(lit_review, "TERMS_SUMMARY_EXCEL")
    
    try:
        document_path_csv, document_name_csv = form_report_name(lit_review, report_job, "csv")
        document_path_excel, document_name_excel = form_report_name(lit_review, report_job, "xlsx")
        row_list = search_terms_summary_context(review_id)

    except Exception as e:
        error_msg = "Error in 2nd Pass Extrection Context Generation \n " + str(e)
        err_track = str(traceback.format_exc())
        return construct_report_error(error_msg, err_track, report_job, "Search Term Summary Report", lit_review, version_number)

    try:
        ## generate output document
        document_path_final_excel = create_excel_file(
            review_id,
            report_job.id,
            document_name_csv,
            document_name_excel,
            row_list
        )
        f = open(document_path_final_excel, "rb")
        search_terms_summary_file = File(f)
        report_job.terms_summary_report = search_terms_summary_file
        report_job.status = "COMPLETE"
        report_job.save()

    except Exception as e:
        error_msg = "Error in Generating Search Term Summary  \n " + str(e)
        err_track = str(traceback.format_exc())
        return construct_report_error(error_msg, err_track, report_job, "Search Term Summary Report", lit_review , version_number)
    

def generate_appendix_e2_report_excel_task(review_id):
    lit_review = LiteratureReview.objects.get(id=review_id)
    report_job, version_number = create_report_object(lit_review, "APPENDIX_E2")

    try:
        _, document_name_csv = form_report_name(lit_review, report_job, "csv")
        _, document_name_excel = form_report_name(lit_review, report_job, "xlsx")

        row_list_maude_aes = appendix_e2_report_context(review_id)
        row_list_maude_recalls = appendix_e2_report_context(review_id, "maude_recalls")
        row_list_manual_aes = appendix_e2_report_context(review_id, "manual_aes")
        row_list_manual_recalls = appendix_e2_report_context(review_id, "manual_recalls")

    except Exception as e:
        error_msg = "Error in 2nd Pass Extrection Context Generation \n " + str(e)
        err_track = str(traceback.format_exc())
        return construct_report_error(error_msg, err_track, report_job, "Appendix E2 Excel Report", lit_review, version_number)

    try:
        ## generate output document
        add_to_excel = create_excel_file(
            review_id, 
            report_job.id, 
            document_name_csv, 
            document_name_excel, 
            row_list_maude_aes, 
            set_column_limit=False, 
            sheet_name="Maude Adverse Events"
        )
        create_excel_file(
            review_id, 
            report_job.id, 
            document_name_csv, 
            document_name_excel, 
            row_list_maude_recalls, 
            set_column_limit=False, 
            sheet_name="Maude Recalls", 
            is_append=True,
            add_to_excel=add_to_excel,
        )
        create_excel_file(
            review_id, 
            report_job.id, 
            document_name_csv, 
            document_name_excel, 
            row_list_manual_aes, 
            set_column_limit=False, 
            sheet_name="Manual Adverse Evetns", 
            is_append=True,
            add_to_excel=add_to_excel,
        )
        document_path_final_excel = create_excel_file(
            review_id, 
            report_job.id,
            document_name_csv, 
            document_name_excel, 
            row_list_manual_recalls, 
            set_column_limit=False, 
            sheet_name="Manual Recalls", 
            is_append=True,
            add_to_excel=add_to_excel,
        )

        f = open(document_path_final_excel, "rb")
        appendix_e2_file = File(f)
        report_job.appendix_e2 = appendix_e2_file
        report_job.status = "COMPLETE"
        report_job.save()

    except Exception as e:
        error_msg = "Error in 2nd Pass Extrection Exporting  \n " + str(e)
        err_track = str(traceback.format_exc())
        return construct_report_error(error_msg, err_track, report_job, "Appendix E2 Excel Report", lit_review, version_number)
    

def export_article_reviews_report_task(review_id):
    lit_review = LiteratureReview.objects.get(id=review_id)
    report_job, version_number = create_report_object(lit_review, "ARTICLE_REVIEWS")

    try:
        _, document_name_csv = form_report_name(lit_review, report_job, "csv")
        _, document_name_excel = form_report_name(lit_review, report_job, "xlsx")
        row_list = all_articles_reviews_context(review_id)

    except Exception as e:
        error_msg = "Error in Export All Articles Reviews Context Generation \n " + str(e)
        err_track = str(traceback.format_exc())
        return construct_report_error(error_msg, err_track, report_job, "Article Reviews Report", lit_review, version_number)

    try:
        ## generate output document
        document_path_final_excel = create_excel_file(
            review_id,
            report_job.id,
            document_name_csv,
            document_name_excel,
            row_list
        )
        f = open(document_path_final_excel, "rb")
        second_pass_articles_file = File(f)
        report_job.second_pass_articles = second_pass_articles_file
        report_job.status = "COMPLETE"
        report_job.save()

    except Exception as e:
        error_msg = "Error in Export All Articles Reviews Exporting   \n " + str(e)
        err_track = str(traceback.format_exc())
        return construct_report_error(error_msg, err_track, report_job, "Article Reviews Report", lit_review, version_number)
    

def export_article_reviews_ris_report_task(review_id):
    lit_review = LiteratureReview.objects.get(id=review_id)
    report_job, version_number = create_report_object(lit_review, "ARTICLE_REVIEWS_RIS")

    try:
        document_path, document_name = form_report_name(lit_review, report_job, "ris")
        temp_ris_file = get_article_reviews_ris(review_id, document_name)

    except Exception as e:
        error_msg = "Error in Article Reviews RIS Context Generation \n " + str(e)
        err_track = str(traceback.format_exc())
        return construct_report_error(error_msg, err_track, report_job, "Article Reviews RIS Report", lit_review, version_number)

    # generate full text files
    try:
        logger.debug("Generating FullText Zip...")
        TMP_ROOT, FOLDER_PATH = create_full_text_folder(lit_review)
        # ZIP_FILE_NAME = lit_review.device.__str__() + "__FullTexts__" + datetime.datetime.now(pytz.utc).strftime("%Y-%m-%d %H:%M")
        ZIP_FILE_NAME = document_name
        shutil.move(temp_ris_file, FOLDER_PATH + document_name)
        FILE_PATH = TMP_ROOT + ZIP_FILE_NAME + ".zip"
        if os.path.exists(FILE_PATH):
            os.remove(FILE_PATH)
        logger.debug(f"File Path: {FILE_PATH}")
        # archive to a zip file
        shutil.make_archive(TMP_ROOT + ZIP_FILE_NAME, 'zip', FOLDER_PATH) 
    
    except Exception as e:
        error_msg = "Error in 2nd Pass Extrection RIS Full text pdfs Generation \n " + str(e)
        err_track = str(traceback.format_exc())
        return construct_report_error(error_msg, err_track, report_job, "Article Reviews RIS Report", lit_review, version_number)
    
    try:
        f = open(FILE_PATH, "rb")
        artilce_reviews_ris = File(f)
        report_job.article_reviews_ris = artilce_reviews_ris
        report_job.status = "COMPLETE"
        report_job.save()

    except Exception as e:
        error_msg = "Error in Article Reviews RIS Exporting  \n " + str(e)
        err_track = str(traceback.format_exc())
        return construct_report_error(error_msg, err_track, report_job, "Article Reviews RIS Report", lit_review, version_number)


def generate_condense_report_task(review_id):
    lit_review = LiteratureReview.objects.get(id=review_id)
    report_job, version_number = create_report_object(lit_review, "CONDENSED_REPORT")
 
    # Validate Report
    try:
        logger.debug("SKIPPING VALIDATION")
        #validate_report(review_id)
    except Exception as e:
        error_msg = "Error in Validating Report \n " + str(e)
        err_track = str(traceback.format_exc())
        return construct_report_error(error_msg, err_track, report_job, "LITR Condense Report", lit_review, version_number)

    document_path, document_name = form_report_name(lit_review, report_job, "docx")
    appendix_path, appendix_document_name = form_report_name(lit_review, report_job, "docx", "Appendix_A")

    # Build Report Outputs
    logger.debug("building report schemas now...")
    doc1, doc2 = build_report_output(
        review_id,
        report_job,
        "CONDENSED_REPORT",
        document_path,
        appendix_path
    )

    # Generate Final Files
    try:
        # Condensed Report File
        doc1.save(document_path)
        f1 = open(document_path, "rb") 
        condensed_report_file = File(f1, name=document_name)
        # Appendix B File  
        doc2.save(appendix_path)
        f2 = open(appendix_path, "rb")
        appendix_b_file = File(f2, name=appendix_document_name)
        # Create Final ZIP File
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w') as zip_file:
            zip_file.writestr(document_name, condensed_report_file.read())
            zip_file.writestr(appendix_document_name, appendix_b_file.read())

        _, condensed_report_name = form_report_name(lit_review, report_job, "zip")
        report_job.condensed_report.save(condensed_report_name, ContentFile(zip_buffer.getvalue()))
        report_job.status = "COMPLETE"
        report_job.save()

    except Exception as e:
        error_msg = "Error in report file saving  \n " + str(e)
        err_track = str(traceback.format_exc())
        return construct_report_error(error_msg, err_track, report_job, "LITR Condense Report", lit_review, version_number)

    return None


def generate_duplicates_report_task(review_id):
    lit_review = LiteratureReview.objects.get(id=review_id)
    report_job, version_number = create_report_object(lit_review, "DUPLICATES")

    try:
        _, document_name_csv = form_report_name(lit_review, report_job, "csv")
        _, document_name_excel = form_report_name(lit_review, report_job, "xlsx")
        rows_data = generate_article_duplicates_content(review_id, include_all_if_no_dups=False)
        logger.info("Number of duplicates: " + str(ArticleReview.objects.filter(state="D").count()))

        ## generate output document
        document_path_final_excel = create_excel_file(
            review_id, 
            report_job.id, 
            document_name_csv, 
            document_name_excel, 
            rows_data, 
            set_column_limit=True
        )
        f = open(document_path_final_excel, "rb")
        duplicates_file = File(f)
        report_job.duplicates_report = duplicates_file
        report_job.status = "COMPLETE"
        report_job.save()

    except Exception as e:
        error_msg = "Error in Export All Articles Reviews Exporting   \n " + str(e)
        err_track = str(traceback.format_exc())
        return construct_report_error(error_msg, err_track, report_job, "Article Reviews Report", lit_review, version_number)
    

def generate_audit_tracking_logs_report_task(review_id):
    lit_review = LiteratureReview.objects.get(id=review_id)
    report_job, version_number = create_report_object(lit_review, "AUDIT_TRACKING_LOGS")    

    try:
        _, document_name_csv = form_report_name(lit_review, report_job, "csv")
        _, document_name_excel = form_report_name(lit_review, report_job, "xlsx")
        row_list = audit_tracking_logs_context(review_id)


    except Exception as e:
        error_msg = "Error in Audit Tracking Logs Context Generation \n " + str(e)
        err_track = str(traceback.format_exc())
        return construct_report_error(error_msg, err_track, report_job, "Audit Tracking Logs Report", lit_review, version_number)

    try:
        ## generate output document
        document_path_final_excel = create_excel_file(
            review_id,
            report_job.id,
            document_name_csv,
            document_name_excel,
            row_list
        )
        f = open(document_path_final_excel, "rb")
        audit_tracking_logs_file = File(f)
        report_job.audit_tracking_logs = audit_tracking_logs_file
        report_job.status = "COMPLETE"
        report_job.save()

    except Exception as e:
        error_msg = "Error in Audit Tracking Logs Exporting  \n " + str(e)
        err_track = str(traceback.format_exc())
        return construct_report_error(error_msg, err_track, report_job, "Audit Tracking Logs Report", lit_review, version_number)


def generate_cumulative_report_task(literature_review_id, user_id):
    from lit_reviews.tasks import send_error_email
    user = User.objects.get(id=user_id)

    lt_review = LiteratureReview.objects.get(id=literature_review_id)
    error_msg = ""
    report_job, version_number = create_report_object(lt_review, "CUMULATIVE_REPORT")
    device = lt_review.device
    device_literature_reviews = LiteratureReview.objects.filter(device=device)
    _, REPORT_NAME = form_report_name(lt_review, report_job, "zip")

    TMP_ROOT = "tmp/"
    timestamp = time.time()
    FOLDER_PATH = TMP_ROOT + f"{device.name} Cumulative Report {str(timestamp)}/"
    os.mkdir(FOLDER_PATH)    
    
    for literature_review in device_literature_reviews:
        if user.client and lt_review.device.client != user.client:
            # jump to next review if the user doesn't have access
            continue 
        
        project_name = f'{str(literature_review.id)} {str(literature_review).replace("/", " ")}'      
        PROJECT_FOLDER = f"{FOLDER_PATH}{project_name}/"
        os.mkdir(PROJECT_FOLDER)

        # generate full articles report
        try:
            _, document_name_csv = form_report_name(literature_review, report_job, "csv", default_report_type="Full Articles Report")
            _, document_name_excel = form_report_name(literature_review, report_job, "xlsx", default_report_type="Full Articles Report")
            row_list = all_articles_reviews_context(literature_review.id, add_project_name=True)
        except Exception as e:
            error_msg = "Error in Export All Articles Reviews Context Generation \n " + str(e)
            err_track = str(traceback.format_exc())
            return construct_report_error(error_msg, err_track, report_job, "Article Reviews Report", literature_review, version_number)

        full_articles_report_path = create_excel_file(
            literature_review.id,
            report_job.id,
            document_name_csv,
            document_name_excel,
            row_list
        )
        shutil.move(full_articles_report_path, f"{PROJECT_FOLDER}{document_name_excel}")      

        # generate second pass report
        try:
            document_path_csv, document_name_csv = form_report_name(literature_review, report_job, "csv", default_report_type="Second Pass Articles Report")
            document_path_excel, document_name_excel = form_report_name(literature_review, report_job, "xlsx", default_report_type="Second Pass Articles Report")        
            row_list = second_pass_articles_context(literature_review.id, add_project_name=True)

        except Exception as e:
            error_msg = "Error in 2nd Pass Extrection Context Generation \n " + str(e)
            err_track = str(traceback.format_exc())
            return construct_report_error(error_msg, err_track, report_job, "Second Pass Excel Report", literature_review, version_number)

        ## generate output document
        second_pass_report_path = create_excel_file(
            literature_review.id,
            report_job.id,
            document_name_csv,
            document_name_excel,
            row_list
        )
        shutil.move(second_pass_report_path, f"{PROJECT_FOLDER}{document_name_excel}")

        # Search Terms Report 
        try:
            document_path_csv, document_name_csv = form_report_name(literature_review, report_job, "csv", default_report_type="Search Terms Report")
            document_path_excel, document_name_excel = form_report_name(literature_review, report_job, "xlsx", default_report_type="Search Terms Report")
            row_list = search_terms_summary_context(literature_review.id, add_project_name=True)

        except Exception as e:
            error_msg = "Error in 2nd Pass Extrection Context Generation \n " + str(e)
            err_track = str(traceback.format_exc())
            return construct_report_error(error_msg, err_track, report_job, "Search Term Summary Report", literature_review, version_number)

        ## generate output document
        search_terms_summary_report_path = create_excel_file(
            literature_review.id,
            report_job.id,
            document_name_csv,
            document_name_excel,
            row_list
        )
        shutil.move(search_terms_summary_report_path, f"{PROJECT_FOLDER}{document_name_excel}")

    FILE_PATH = TMP_ROOT + REPORT_NAME
    if os.path.exists(FILE_PATH):
        os.remove(FILE_PATH)
    logger.debug(f"File Path: {FILE_PATH}")
    # archive to a zip file
    REPORT_FILE_WITHOUT_EXTENTION = TMP_ROOT + REPORT_NAME.replace(".zip", "")
    shutil.make_archive(REPORT_FILE_WITHOUT_EXTENTION, 'zip', FOLDER_PATH) 
    with open(FILE_PATH, "rb") as zp_file:
        zp_file = File(zp_file)
        
        report_job.cumulative_report = zp_file
        if error_msg:
            report_job.error_msg = error_msg
            report_job.status = "INCOMPLETE-ERROR" 
            report_job.version_number = version_number
        else:
            report_job.error_msg = None
            report_job.status = "COMPLETE" 

        report_job.save()
        logger.info("FT Zip generated and saved ")
        shutil.rmtree(FOLDER_PATH)
        return "success"    


def generate_device_history_report_task(literature_review_id, user_id):
    user = User.objects.get(id=user_id)

    lt_review = LiteratureReview.objects.get(id=literature_review_id)
    error_msg = ""
    report_job, version_number = create_report_object(lt_review, "DEVICE_HISTORY")
    device = lt_review.device
    device_literature_reviews = LiteratureReview.objects.filter(device=device)
    _, REPORT_NAME = form_report_name(lt_review, report_job, "zip")

    TMP_ROOT = "tmp/"
    timestamp = time.time()
    FOLDER_PATH = TMP_ROOT + f"{device.name} Device History {str(timestamp)}/"
    os.mkdir(FOLDER_PATH)    

    _, all_reviews_report_name_csv = form_report_name(device_literature_reviews.first(), report_job, "csv", default_report_type="Full Review Data")  
    _, second_pass_report_name_csv = form_report_name(device_literature_reviews.first(), report_job, "csv", default_report_type="Second Pass Appraisals")  
    _, search_terms_report_name_csv = form_report_name(device_literature_reviews.first(), report_job, "csv", default_report_type="Search Terms")
    _, all_reviews_report_name = form_report_name(device_literature_reviews.first(), report_job, "xlsx", default_report_type="Full Review Data")  
    _, second_pass_report_name = form_report_name(device_literature_reviews.first(), report_job, "xlsx", default_report_type="Second Pass Appraisals")  
    _, search_terms_report_name = form_report_name(device_literature_reviews.first(), report_job, "xlsx", default_report_type="Search Terms")

    all_reviews_rows = []
    second_pass_rows = []
    search_terms_rows = []

    for literature_review in device_literature_reviews:
        if user.client and lt_review.device.client != user.client:
            # jump to next review if the user doesn't have access
            continue 
        
        # generate full articles report
        try:
            row_list = all_articles_reviews_context(literature_review.id, add_project_name=True)
            if len(all_reviews_rows):
                # remove headers
                row_list = row_list[1:]
                
            all_reviews_rows = [*all_reviews_rows, *row_list]

        except Exception as e:
            error_msg = "Error in Export All Articles Reviews Context Generation \n " + str(e)
            err_track = str(traceback.format_exc())
            return construct_report_error(error_msg, err_track, report_job, "Article Reviews Report", literature_review, version_number)   

        # generate second pass report
        try:      
            row_list = second_pass_articles_context(literature_review.id, add_project_name=True)
            if len(second_pass_rows):
                # remove headers
                row_list = row_list[1:]

            second_pass_rows = [*second_pass_rows, *row_list]

        except Exception as e:
            error_msg = "Error in 2nd Pass Extrection Context Generation \n " + str(e)
            err_track = str(traceback.format_exc())
            return construct_report_error(error_msg, err_track, report_job, "Second Pass Excel Report", literature_review, version_number)

        # Search Terms Report 
        try:
            row_list = search_terms_summary_context(literature_review.id, add_project_name=True)
            if len(search_terms_rows):
                # remove headers
                row_list = row_list[1:]
            search_terms_rows = [*search_terms_rows, *row_list]

        except Exception as e:
            error_msg = "Error in 2nd Pass Extrection Context Generation \n " + str(e)
            err_track = str(traceback.format_exc())
            return construct_report_error(error_msg, err_track, report_job, "Search Term Summary Report", literature_review, version_number)


    full_articles_report_path = create_excel_file(
        device_literature_reviews.first().id,
        report_job.id,
        all_reviews_report_name_csv,
        all_reviews_report_name,
        all_reviews_rows,
        skip_headless_lines=True,
    )
    shutil.move(full_articles_report_path, f"{FOLDER_PATH}{all_reviews_report_name}")   

    ## generate output document
    second_pass_report_path = create_excel_file(
        device_literature_reviews.first().id,
        report_job.id,
        second_pass_report_name_csv,
        second_pass_report_name,
        second_pass_rows,
        skip_headless_lines=True,
    )
    shutil.move(second_pass_report_path, f"{FOLDER_PATH}{second_pass_report_name}")

    ## generate output document
    search_terms_summary_report_path = create_excel_file(
        device_literature_reviews.first().id,
        report_job.id,
        search_terms_report_name_csv,
        search_terms_report_name,
        search_terms_rows,
        skip_headless_lines=True,
    )
    shutil.move(search_terms_summary_report_path, f"{FOLDER_PATH}{search_terms_report_name}")


    FILE_PATH = TMP_ROOT + REPORT_NAME
    if os.path.exists(FILE_PATH):
        os.remove(FILE_PATH)
    logger.debug(f"File Path: {FILE_PATH}")

    # archive to a zip file
    REPORT_FILE_WITHOUT_EXTENTION = TMP_ROOT + REPORT_NAME.replace(".zip", "")
    shutil.make_archive(REPORT_FILE_WITHOUT_EXTENTION, 'zip', FOLDER_PATH) 
    with open(FILE_PATH, "rb") as zp_file:
        zp_file = File(zp_file)
        
        report_job.device_history_zip = zp_file
        if error_msg:
            report_job.error_msg = error_msg
            report_job.status = "INCOMPLETE-ERROR" 
            report_job.version_number = version_number
        else:
            report_job.error_msg = None
            report_job.status = "COMPLETE" 

        report_job.save()
        logger.info("FT Zip generated and saved ")
        shutil.rmtree(FOLDER_PATH)
        return "success"    