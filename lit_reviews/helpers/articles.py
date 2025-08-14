import fitz
import os 
import requests
import rispy
import csv
import datetime, pytz
import pandas as pd
import re
import uuid
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time
import shutil
from selenium.webdriver.common.by import By
from django.db.models import Q

from pathlib import Path
from copy import deepcopy
from django.core.files.base import ContentFile
from django.conf import settings
from fuzzywuzzy import fuzz
from django.urls import reverse
from django.utils import timezone

from lit_reviews.models import (
    Article,
    ArticleReview,
    LiteratureReview,
    AdverseEventReview,
    NCBIDatabase,
    ClinicalLiteratureAppraisal,
    AppraisalExtractionField,
    ExtractionField,
    KeyWord,
    CustomKeyWord,
    LiteratureSearch,
    DuplicationReport,
    DuplicatesGroup,
    CustomerSettings
)
from backend.logger import logger
from lit_reviews.helpers.generic import get_customer_settings, create_chrome_driver
from django.contrib.auth import get_user_model


User = get_user_model()

def retrieve_matches(target_article_id, lit_review_id):
    """
    Given a target article with a list of articles
    retrieve all potentail matches.
    """
    embase_article_review = ArticleReview.objects.get(id=target_article_id)
    matches = [embase_article_review]
    potential_matches = []
    articles = ArticleReview.objects.filter(
        search__literature_review_id=lit_review_id
    ).exclude(state='D')
    for article_review in articles:
        # check if I'm comparing the same article, in this case pass to next
        if embase_article_review.id == article_review.id:
            continue 

        citation_fuzzy = fuzz.token_set_ratio(embase_article_review.article.citation, article_review.article.citation)
        abstract_fuzzy =  fuzz.token_set_ratio(embase_article_review.article.abstract, article_review.article.abstract)
        title_fuzzy = fuzz.token_set_ratio(embase_article_review.article.title, article_review.article.title)

        # ## to look for the default 'no citaiton found or abstract text' 
        if article_review.article.abstract.strip().lower().find("citemed") != -1:
            abstract_fuzzy = 0

        if citation_fuzzy > 70 and abstract_fuzzy > 90 and title_fuzzy > 95:
            matches.append(article_review)
            logger.info(f"Potential Match found: {article_review.id}")

        elif citation_fuzzy > 50 and abstract_fuzzy > 70 and title_fuzzy > 80:
            potential_matches.append(article_review)
            logger.info(f"Potential match found: {article_review.id}")
    
    return matches, potential_matches

### ML remove duplicates for embase.
def check_embase_duplicates(lit_review_id):
    ## get all article reviews for the project
    embase_db = NCBIDatabase.objects.get(entrez_enum='embase')

    all_article_reviews = ArticleReview.objects.filter(
        search__literature_review_id=lit_review_id
    ).exclude(state='D')

    embase_article_reviews = ArticleReview.objects.filter(
        search__literature_review_id=lit_review_id, search__db=embase_db 
    ).exclude(state='D')

    logger.debug("Article Reviews (Non Embase): {0} \n Embase Reviews: {1}".format(len(all_article_reviews), len(embase_article_reviews) ))
    dupes = []

    for embase_article_review in embase_article_reviews:
        matches, potential_matches  = retrieve_matches(embase_article_review.id, lit_review_id)

        # matches should be more than 2 (because we are including original article)
        if len(matches) > 1:
            unclassified_matches = [match for match in matches if match.state == "U"]
            non_unclassified_non_duplicate_matches = [match for match in matches if ( match.state != "U" and match.state != "D")]
            
            if len(non_unclassified_non_duplicate_matches) > 0:
                to_mark_as_duplicate = unclassified_matches
                original_artical = non_unclassified_non_duplicate_matches[0]

            elif len(unclassified_matches) > 1:
                to_mark_as_duplicate = unclassified_matches[1:]
                original_artical = unclassified_matches[0]

            else:
                to_mark_as_duplicate = []
                original_artical = unclassified_matches[0]
            
            if len(to_mark_as_duplicate) > 0:
                for d_match in to_mark_as_duplicate:
                    d_match.state = 'D'
                    d_match.save()

                    # create dupes group 
                    try:
                        duplicates_group, created = DuplicatesGroup.objects.get_or_create(original_article_review=original_artical)
                    except:
                        duplicates_group = DuplicatesGroup.objects.filter(original_article_review=original_artical).first()
                    
                    duplicates_group.duplicates.add(d_match)
                    dupes.append(d_match.id)

            logger.warning(f"{str(len(to_mark_as_duplicate))} Duplicates found for {embase_article_review.article.title}")
        
        else:
            original_artical = matches[0]
        

        if len(potential_matches) > 0:
            for d_match in potential_matches:
                d_match.potential_duplicate_for = original_artical
                d_match.save()

            logger.warning(f"{str(len(potential_matches))} Potential Duplicates found for {embase_article_review.article.title}")

    ### TODOO Update project de-duplicate run with timestamp and verification that duplicates were process (only if all searches uploaded check.)
    # logger.debug("Duplicate Article Reviews: {0}".format(dupes))

    return dupes

def remove_ae_duplicates(lit_review_id):
    logger.debug("no more AE deduplication")
    return 0
    dupes_removed = 0
    ## first attempt at reglar deduplication (exact article match)
    ae_reviews = AdverseEventReview.objects.filter(search__literature_review_id=lit_review_id, state="UN",
                    search__db__entrez_enum='maude', ).exclude(is_duplicate=True).prefetch_related('ae').values_list('ae', 'id', 'ae__event_number_short')
    tup_list = list(ae_reviews)
    tup_list2 = list(ae_reviews)

    for row in tup_list:
        #tup_list.remove(row)
        ## now loop through the rest of them.
        #count = 0      
        for row2 in tup_list2:
            if  row != row2 and (row[0] == row2[0]  or (row[2] == row2[2] and (row[2] not in [None, '', ' '] and row2[2] not in [None, '', ' '])  )) :
                adverse_review = AdverseEventReview.objects.get(id=row2[1])
                adverse_review.is_duplicate = True
                adverse_review.save()
                #print("ae review marked as duplicate {0}".format(adverse_review))

    ae_reviews_dupes = AdverseEventReview.objects.filter()
    return dupes_removed

def retained_articles(lit_search_id):
    # we make article review as retained
    lit_search = LiteratureSearch.objects.get(id=lit_search_id)
    # remove dups first 
    remove_duplicate(lit_search.literature_review.id)
    final_articles_review = ArticleReview.objects.filter(search__id=lit_search_id).exclude(state='D')
    finale_search_articles_retained = final_articles_review.count()
    logger.info(f"Marking all non duplicate articles as Retained: {str(finale_search_articles_retained)} articles.")
    for article_review in final_articles_review:
        article_review.state = "I"
        article_review.save() 
    
    lit_search.processed_articles = finale_search_articles_retained
    lit_search.import_status = "COMPLETE"
    lit_search.save()

def remove_duplicate(lit_review_id):
    # Update duplication report to running
    duplication_report, created = DuplicationReport.objects.get_or_create(literature_review_id=lit_review_id)
    duplication_report.status = "RUNNING"
    duplication_report.needs_update = False
    duplication_report.save()

    ae_dupes_removed = remove_ae_duplicates(lit_review_id)
    # logger.warning("AE Duplicates Removed: {0}".format(ae_dupes_removed))

    logger.debug("Processing for EMBASE Duplicates...")
    embase_dupes_found = check_embase_duplicates(lit_review_id)
    logger.warning("Embase Duplicates  Completed! Duplicates Found: {0}".format(len(embase_dupes_found)))
    logger.debug("Embase duplicates completed, Now processing all")

    lit_review = LiteratureReview.objects.get(id=lit_review_id)
    article_reviews = ArticleReview.objects.filter(search__literature_review=lit_review)
    dups_removed = len(embase_dupes_found) + ae_dupes_removed

    for article_review in article_reviews:
        article = article_review.article
        if article.pubmed_uid:
            reviews = ArticleReview.objects.filter(
                Q(search__literature_review=lit_review),
                Q(article=article) | 
                Q(article__pubmed_uid=article.pubmed_uid)
            ).exclude(state="D")
        elif article.pmc_uid:
            reviews = ArticleReview.objects.filter(
                Q(search__literature_review=lit_review),
                Q(article=article) | 
                Q(article__pmc_uid=article.pmc_uid)
            ).exclude(state="D")
        else:
            reviews = ArticleReview.objects.filter(search__literature_review=lit_review, article=article).exclude(state="D")

        # original_artical is the article that should be left for review all the rest (similar articles) should be marked as duplicate
        # Ex: if we have 5 similar articles 1 article should be left for review (original) the rest (4) should be marked as duplicate
        if len(reviews) > 1:
            unclassifiedd_reviews = reviews.filter(state="U")
            non_unclassifiedd_reviews = reviews.exclude(state="U")

            if non_unclassifiedd_reviews.count():
                duplicate_reviews = unclassifiedd_reviews  
                original_article = non_unclassifiedd_reviews.first()
            else: 
                duplicate_reviews = unclassifiedd_reviews[1:]
                original_article = unclassifiedd_reviews[0]

            for item in duplicate_reviews:
                item.state = "D"
                item.save()
                dups_removed += 1

                try:
                    duplicates_group, created = DuplicatesGroup.objects.get_or_create(original_article_review=original_article)
                except:
                    duplicates_group = DuplicatesGroup.objects.filter(original_article_review=original_article).first()
                duplicates_group.duplicates.add(item)

            logger.warning(f"{str(duplicate_reviews.count())} Duplicate Found for article: {article_review.article.title}")
            
    logger.warning("duplicates for Non-Embase Completed! Duplicates Removed: " + str(dups_removed))

    # Update duplication report to completed
    duplication_report.status = "COMPLETED"
    duplication_report.duplicates_count = dups_removed
    duplication_report.save()

    return dups_removed


def get_article_redirect_url(article_state,lit_review_id):
    URL = reverse("lit_reviews:article_reviews_list", args=[str(lit_review_id)])
    if article_state == "U":
        return  URL + "?state=U"
    elif article_state == "I":
        return  URL + "?state=I"
    elif article_state == "M":
        return  URL + "?state=M"
    elif article_state == "E":
        return  URL + "?state=E"
    elif article_state == "D":
        return  URL + "?state=D"
    

def get_clinical_appraisal_status_report(appraisals, force_status_recalculation=False):
    """
    calculate status and store it for each clinical appraisal in the given list
    """

    app_list = []
    completed = []
    in_completed = []

    app_status_counts = {
        "Total": 0,
        "Missing full text pdf/Incomplete": 0,
        "Full text uploaded/Ready for Review": 0,
        "Needs Suitability/Outcomes Dropdowns": 0,
        "Incomplete Sota": 0,
        "Incomplete Device Review": 0,
        "Missing Excl. Justification": 0,
        "Incomplete Extraction Fields": 0,
        "Complete": 0,
        "Complete SoTa Reviews": 0,
        "Complete Device Reviews": 0,
    }
    
    for app in appraisals:        
        # check if app has authors in meta_data
        from lit_reviews.helpers.reports import extract_authors
        article = app.article_review.article
        current_meta_data = article.meta_data
        has_authors = current_meta_data and current_meta_data.get("authors", None)

        if app.article_review.search.db.entrez_enum != "ct_gov" and not has_authors:
            authors = extract_authors(article.citation)
            authors = (", ").join(authors)
            if current_meta_data:
                current_meta_data["authors"] = authors
            else:
                current_meta_data = {"authors": authors}

            article.meta_data = current_meta_data
            article.save()
            
        # calculate status and store it
        app_status = app.app_status
        if (not app_status) or (app_status == "Missing full text pdf/Incomplete" and app.article_review.article.full_text) or force_status_recalculation:
            app_status = app.status
            app.app_status = app_status
            app.save()

        if app_status == "Missing full text pdf/Incomplete":
            in_completed.append(app)
            app_status_counts["Missing full text pdf/Incomplete"] += 1

        if app_status == "Full text uploaded/Ready for Review":
            in_completed.append(app)
            app_status_counts["Full text uploaded/Ready for Review"] += 1

        elif app_status == "Needs Suitability/Outcomes Dropdowns":
            in_completed.append(app)
            app_status_counts["Needs Suitability/Outcomes Dropdowns"] += 1

        elif app_status == "Incomplete Sota":
            in_completed.append(app)
            app_status_counts["Incomplete Sota"] += 1

        elif app_status == "Incomplete Extraction Fields":
            in_completed.append(app)
            app_status_counts["Incomplete Extraction Fields"] += 1

        elif "Incomplete Device Review" in app_status:
            in_completed.append(app)
            app_status_counts["Incomplete Device Review"] += 1

        elif app_status == "Missing Excl. Justification":
            in_completed.append(app)
            app_status_counts["Missing Excl. Justification"] += 1

        elif app_status == "Complete":
            completed.append(app)
            app_status_counts["Complete"] += 1
            if app.is_sota_article:
                app_status_counts["Complete SoTa Reviews"] += 1
            else:
                app_status_counts["Complete Device Reviews"] += 1

        app_status_counts["Total"] += 1
        app_list.append({"app": app, "message": app_status})

    app_status_counts["Uncomplete"] = app_status_counts["Total"] - app_status_counts["Complete"]
    app_status_counts["UncompleteExceptExtractions"] = app_status_counts["Uncomplete"] - app_status_counts["Incomplete Extraction Fields"]
    return app_list, app_status_counts, completed, in_completed, 


def create_missing_clinical_appraisals_file(lit_review_id,report_job):
    appraisals = ClinicalLiteratureAppraisal.objects.filter(
            article_review__search__literature_review__id=lit_review_id, article_review__state="I"
        )
    app_list, app_status_counts, completed, in_completed = get_clinical_appraisal_status_report(appraisals) 

    if len(in_completed):
        document_name_csv = "Missing_Clinical_Appraisals_" + str(report_job.id) + "_" + datetime.datetime.now(pytz.utc).strftime("%Y-%m-%d") + ".csv"
        document_name_excel = "Missing_Clinical_Appraisals_" + str(report_job.id) + "_" + datetime.datetime.now(pytz.utc).strftime("%Y-%m-%d") + ".xlsx"
        # csv_file = os.path.join(settings.TMP_ROOT, document_name_csv)
        # excel_file = os.path.join(settings.TMP_ROOT, document_name_excel)
        csv_file = f"tmp/${document_name_csv}"
        excel_file = f"tmp/${document_name_excel}"
        

        logger.debug("Creating Missing Appraisals File")

        with open(csv_file, 'w', newline='') as file:
            writer = csv.writer(file)
            header_row = ["ID", "Title", "Citation"]
            writer.writerow(header_row)
            for app in appraisals:
                status = app.status
                if status != "Complete":
                    id =  app.id
                    title = app.article_review.article.title
                    citation = app.article_review.article.citation
                    body_row = [id, title, citation]
                    writer.writerow(body_row)

        # conver csv file to excel file
        read_file = pd.read_csv(csv_file)
        read_file.to_excel(excel_file, index = None, header=True)
        return excel_file
            
    else:
        return None


def check_library_entry_objects():
    """
    We should have a LibraryEntry for each Article.
    This script will check if All Articles already have a LibraryEntry object, 
    if not it will create one.
    """
    from client_portal.models import LibraryEntry
    articles = Article.objects.all()
    for article in articles:
        if not LibraryEntry.objects.filter(article=article).exists():
            logger.info(f"Article with ID {article.id} doesn't have a LibraryEntry, creating One...")
            LibraryEntry.objects.create(article=article)


def get_or_create_appraisal_extraction_fields(apprailsal, extra_extraction, only_default=True, sub_extraction_number=None):
    values = {
        "extraction_field": extra_extraction, 
        "clinical_appraisal": apprailsal,
    }
    if only_default:
        appraisal_extraction_fields = AppraisalExtractionField.objects.filter(**values, extraction_field_number=1).order_by("id")
        appraisal_extraction_field = appraisal_extraction_fields.first()

        if not appraisal_extraction_field:
            appraisal_extraction_field = AppraisalExtractionField.objects.create(**values)
        elif appraisal_extraction_fields.count() > 1:
            # just in case if there are any duplicates we delete them
            duplicate_extraction = appraisal_extraction_fields.last()
            if not duplicate_extraction.value:
                duplicate_extraction.delete()

        return appraisal_extraction_field

    elif sub_extraction_number:
        appraisal_extraction_field = AppraisalExtractionField.objects.filter(**values, extraction_field_number=sub_extraction_number).first()
        return appraisal_extraction_field
    
    else:
        appraisal_extraction_fields = AppraisalExtractionField.objects.filter(**values)
        if not appraisal_extraction_fields.count():
            AppraisalExtractionField.objects.create(**values)
            appraisal_extraction_fields = AppraisalExtractionField.objects.filter(**values)
        return appraisal_extraction_fields

def check_extraction_section_completion(app, field_section):
    """
    Check if a given extraction section is completed for an appraisal.
    """
    section_extractions = ExtractionField.objects.filter(
        literature_review=app.article_review.search.literature_review,
        field_section=field_section
    )
    section_values = []
    for extraction in section_extractions:
        app_extraction = get_or_create_appraisal_extraction_fields(app, extraction)
        section_values.append(app_extraction.value)
    
    logger.debug(f"section_values : {section_values}")
    return any(value == None or value == "" for value in section_values)


def wait_pdf_to_download_and_it_save_to_article(article, article_review_id, tmp_download_folder, user_id):
    from lit_reviews.tasks import appraisal_ai_extraction_generation_async

    files = [f for f in os.listdir(tmp_download_folder) if os.path.isfile(os.path.join(tmp_download_folder, f))]
    started_at = datetime.datetime.now()
    is_file_being_downloaded =  (not files) or ("com.google.Chrome" in files[0]) or (".crdownload" in files[0])

    while is_file_being_downloaded:
        logger.info("waiting for full text pdf to be downloaded!")
        time.sleep(1)
        files = [f for f in os.listdir(tmp_download_folder) if os.path.isfile(os.path.join(tmp_download_folder, f))]
        is_file_being_downloaded =  (not files) or ("com.google.Chrome" in files[0]) or (".crdownload" in files[0])

        if (started_at + datetime.timedelta(minutes=1)) < datetime.datetime.now():
            logger.warning(f"Auto full text pdf download failed for {article.title}")
            break 

    if files:
        with open(f"{tmp_download_folder}/{files[0]}", "rb") as full_text_file:
            # Download the PDF using requests
            full_text_file_name = name_article_full_text_pdf(article)
            article.full_text.save(full_text_file_name, full_text_file, save=True) 
            logger.success(f"Full text downloaded for {article.title}")

            if article_review_id:
                article_review = ArticleReview.objects.filter(id=article_review_id).first()
                appraisal = ClinicalLiteratureAppraisal.objects.filter(article_review=article_review).first()
                ## recalculate appraisal status
                if appraisal: 
                    appraisal.app_status = appraisal.status
                    user = User.objects.filter(id=user_id).first()
                    customer_settings = get_customer_settings(user)

                    logger.info(f"customer_settings {customer_settings.pk}")                     
                    if customer_settings and customer_settings.automatic_ai_extraction:
                        logger.info("Automatic AI extraction is enabled - processing appraisal asynchronously")
                        appraisal_ai_extraction_generation_async.delay(appraisal.id, user_id)
                    else:
                        logger.info("Automatic AI extraction is disabled - skipping AI processing")


def check_full_article_link(article_id, article_review_id, user_id):
    article = Article.objects.filter(id=article_id).first()
    if article_review_id:
        article_review = ArticleReview.objects.filter(id=article_review_id).first()
        if article.url and article_review.search.db.entrez_enum == "pmc_europe":
            tmp_download_folder = f"{settings.FULL_TMP_ROOT}/pdf-{uuid.uuid4()}" 
            os.makedirs(tmp_download_folder, exist_ok=True)
            driver = create_chrome_driver(tmp_download_folder)
            driver.get(article.url)
            time.sleep(3)  # you can fine-tune this delay

            try:           
                driver.find_element(By.ID,"open_pdf").find_element(By.CLASS_NAME, "action").click()
                time.sleep(2)
                wait_pdf_to_download_and_it_save_to_article(article, article_review_id, tmp_download_folder, user_id)
                driver.quit()
                shutil.rmtree(tmp_download_folder)

                return 
            except:
                logger.warning("Failed to download full text PDF from europe pmc")
                driver.quit()


    if article.pmc_uid:
        url = "https://www.ncbi.nlm.nih.gov/pmc/articles/"+article.pmc_uid+"/pdf"
    elif article.pubmed_uid:
        url = "https://www.ncbi.nlm.nih.gov/pmc/articles/"+article.pubmed_uid+"/pdf"
    else:
        # we just keep the full text empty to show the message to the user
        url = ""

    if url and not article.full_text:
        # check if there is a pdf first with requests 
        session = requests.Session()
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Referer': 'https://www.example.com',
            'Accept-Language': 'en-US,en;q=0.9',
        }
        response = session.get(url, headers=headers)

        if response.status_code == 200: 
            tmp_download_folder = f"{settings.FULL_TMP_ROOT}/pdf-{uuid.uuid4()}" 
            os.makedirs(tmp_download_folder, exist_ok=True)
            driver = create_chrome_driver(tmp_download_folder)
            driver.get(url)
            # Wait for the challenge to complete and redirection to happen
            time.sleep(2)  # you can fine-tune this delay
            # Load the page – this will trigger the JavaScript PoW
            driver.get(url)

            wait_pdf_to_download_and_it_save_to_article(article, article_review_id, tmp_download_folder, user_id)

            driver.quit()
            shutil.rmtree(tmp_download_folder)
        
        else:
            logger.warning(f"Auto full text pdf download failed for {article.title}")

    
def improve_file_styling(file_path, file_name):
    """
    Improve styling for excel files. 
    Some uploaded excel files for maude are messy
    """
    # conver csv file to excel file
    df = pd.read_excel(file_path, na_values=['NaN'])
    # Create an empty DataFrame with the same columns as the original DataFrame
    df_empty = pd.DataFrame(columns=df.columns)

    styled_tmp_file = os.path.join(settings.TMP_ROOT, file_name)

    # Concatenate the empty DataFrame with the original DataFrame to ensure at least one row of data
    df = pd.concat([df_empty, df])
    writer = pd.ExcelWriter(styled_tmp_file, engine='xlsxwriter')
    df.to_excel(writer, sheet_name='sheetName', index = False, header=True)
    for column in df:
        column_data = df[column].astype(str)
        if len(column_data) > 0:
            column_length = max(df[column].astype(str).map(len).max(), len(column))
            col_idx = df.columns.get_loc(column)
            if column_length < 15:
                column_length = 15
            
            # max cell width is 30
            if column_length > 30:
                column_length = 30

            writer.sheets['sheetName'].set_column(col_idx, col_idx, column_length)

    writer.close()
    return styled_tmp_file

def process_ris_file(file_path, database=None):
    """
    Extract Articles data from RIS file.
    RIS Format: https://en.wikipedia.org/wiki/RIS_(file_format)
    """
    from lit_reviews.database_imports.utils import form_citation

    if database:
        if database.entrez_enum == "pmc_europe":
            clear_ris_file(file_path)

    p = Path(file_path)
    mapping = deepcopy(rispy.TAG_KEY_MAPPING)
    mapping["U2"] = "identifier"
    entries = rispy.load(p, encoding="utf8", mapping=mapping)
    results = {
        "count": len(entries),
        "entries": [],
    }

    for entry in entries:
        obj = {}
        # Extract title 
        title = entry.get("title", None)
        if not title:
            title = entry.get("primary_title", None)
        if not title:
            title = entry.get("secondary_title", None)
        if not title:
            logger.warning("No title found")
            title = "Title wasn't found or could not be processed. If you think this is a mistake please contact support." 
        obj["title"] = title 

        # Extract Abstract
        abstract = entry.get("abstract", None)
        if not abstract:
            abstract = entry.get("notes_abstract", None)

        if not abstract:
            logger.warning("No abstract found")
            abstract = "Abstract wasn't found or could not be processed. If you think this is a mistake please contact support." 
        obj["abstract"] = abstract 
        
        # Extract Identifier 
        accession_number = entry.get('accession_number', None)

        # Extract Pub Date
        year = entry.get("year", "")
        if not year:
            year = entry.get("publication_year", "")
        if not year:
            year = entry.get("access_date", "")
        obj["pub_date"] = year 


        # Extract DOI
        DOI = entry.get("doi", None)
        if not DOI:
            logger.warning("No DOI found")
                    
        # Extract URL
        url = entry.get("url", None)

        # Extract Citation Details like: authors, journal name ... 
        
        authors = entry.get("authors", [])
        if len(authors):
            authors = ",".join(authors)
        else:
            a1_authors = entry.get("first_authors", [])
            a2_authors = entry.get("secondary_authors", [])
            a3_authors = entry.get("tertiary_authors", [])
            a4_authors = entry.get("subsidiary_authors", [])

            authors = [*a1_authors, *a2_authors, *a3_authors, *a4_authors]
            authors = ",".join(authors)
        
        journal_name = entry.get("journal_name", "")
        volume = entry.get("volume", "")
        number = entry.get("number", "")
        start_page = entry.get("start_page", "")
        end_page = entry.get("end_page", "")
        unique_identifier = entry.get("identifier", "")
        keywords = entry.get("keywords", [])
        meta_data = {
            "volume": volume,
            "volume_number": number,
            "start_page": start_page,
            "end_page": end_page,
            "authors": authors,
        }
        if len(keywords):
            keywords = ",".join(keywords)

        range = ""
        if start_page:
            range = f"{start_page}-{end_page}"
        
        obj["title"] = title
        obj["abstract"] = abstract
        obj["publication_year"] = year
        if accession_number and "PMC" in accession_number:
            obj['pmc_uid'] = accession_number
        elif accession_number:
            obj["pubmed_uid"] = accession_number

        obj["citation"] = form_citation(authors, title, journal_name, year, volume, number, DOI, range)
        obj["journal"] = journal_name
        obj["url"] = url
        obj["doi"] = DOI
        obj["keywords"] = keywords
        obj["meta_data"] = meta_data
        # obj["pubmed_uid"] = unique_identifier if unique_identifier else DOI
        results["entries"].append(obj)

    return results

def hex_to_rgb(hex: str):
    if hex.startswith("#") :
        hex = hex[1:]
        
    return tuple(int(hex[i:i+2], 16) for i in (0, 2, 4)) 

def get_ai_search_texts(doc):
### this can be a slow request, so we should be running it from a celery task.
    # Extract text from each page
    text = ""
    for page in doc:
        text += page.get_text()

    data = {'context': text}

    # with open('extract_ft_text.txt', 'w') as f:
    #     f.write(str(data))
    # Send the request to the ai web service
    url = os.getenv("AI_API_URL", "http://citemed.ethandrower.com/extract_ft/")
    try:
        response = requests.post(url, json=data, timeout=50)
        if response.status_code == 200:
            try:
                response_data = response.json()
                ## should be a list of tuples containning ('keyword', 'label') label = [population, safety...]')

                if isinstance(response_data, list):
                    return response_data  # Assuming the data is
                else:
                    raise ValueError("Response data is not a list")

            except ValueError as e:
                print("Error parsing response:", e)
                return []
        else:
            print(f"Error: Received response code {response.status_code}")
            return []

    except requests.RequestException as e:
        print("Error sending request to the web service:", e)
        return []


def highlight_full_text_pdf(pdf_path, output_path, search_texts):
    # search_texts is a list of tuples of (search text, color in hex format) example [('Vein', "#aec2d0")]
    pdf = fitz.open(pdf_path)

    for item in search_texts:
        search_text = item[0]
        color = item[1]
        # convert to float by dividing each value by 255
        color_rgbf = tuple( list( map( lambda x: x/255, hex_to_rgb(color))))

        for page_number in range(len(pdf)):
            page = pdf[page_number]
            text_instances = page.search_for(search_text)
            if text_instances and len(text_instances):
                for inst in text_instances:
                    annot = page.add_highlight_annot(inst)
                    annot.set_colors(stroke=color_rgbf)
                    annot.update()

    pdf.save(output_path)
    pdf.close()

def get_default_kw_color(kw):
    if kw == "population":
        return "#ebe4c2"
    elif kw == "intervention":
        return "#d5cad0"
    elif kw == "comparison":
        return "#c7d7cf"
    elif kw == "outcome":
        return "#aec2d0"
    elif kw == "exclusion":
        return "#ff0000"

def form_review_search_kw(review_id):
    kws = []
    kw = KeyWord.objects.get(literature_review__id=review_id)
    labels = ["population", "intervention", "comparison", "outcome", "exclusion"]
    for label in labels:
        label_color = getattr(kw, f"{label}_color") 
        color = label_color if label_color else get_default_kw_color(kw)
        label_kws_obj = getattr(kw, f"{label}") 
        label_kws = label_kws_obj.split(",")
        kws = [*kws, *[(item, color) for item in label_kws]]


    custom_keywords = CustomKeyWord.objects.filter(literature_review__id=review_id)
    for kw_obj in custom_keywords:
        custom_kw_list = kw_obj.custom_kw.split(",")
        color = kw_obj.custom_kw_color
        kws = [*kws, *[(item, color) for item in custom_kw_list]]

    return kws


def get_unclassified_and_duplicate_for_article(review, all_reviews):
    article_dups_plus_original = [review]
    for compared_review in all_reviews:
        if review.id != compared_review.id:
            title_fuzzy = fuzz.token_set_ratio(review.article.title, compared_review.article.title)
            citation_fuzzy = fuzz.token_set_ratio(review.article.citation, compared_review.article.citation)
            abstract_fuzzy = fuzz.token_set_ratio(review.article.abstract, compared_review.article.abstract)
            if citation_fuzzy > 70 and abstract_fuzzy > 90 and title_fuzzy > 95:
                article_dups_plus_original.append(compared_review)

    unclassified = [article for article in article_dups_plus_original if article.state == "U"]
    duplicated = [article for article in article_dups_plus_original if article.state == "D"]

    return article_dups_plus_original, unclassified, duplicated

def generate_url_article_reviews(article , db_name):
    logger.info('db name : {}',db_name)

    if db_name == "pubmed" and article.pubmed_uid: 
            article_link = "https://pubmed.ncbi.nlm.nih.gov/" + article.pubmed_uid
    elif db_name == "pmc" and article.pmc_uid:
        article_link = "https://www.ncbi.nlm.nih.gov/pmc/articles/" + article.pmc_uid
    elif db_name == "cochrane":
        article_link = "Not Available"
    elif db_name == "embase":
        article_link = "Not Available"
    elif db_name == "ct_gov" and article.pubmed_uid:
        article_link = "https://clinicaltrials.gov/study/" + article.pubmed_uid
    else:
        article_link = "Not Available"

    if not article.url and article_link != "Not Available":
        article.url = article_link
        article.save()
        
    return article_link

def name_article_full_text_pdf(article, user_id=None):
    from lit_reviews.helpers.reports import extract_authors

    authors = extract_authors(article.citation)
    first_author = ""
    if len(authors):
        first_author = authors[0]

    short_title = article.title[:40]
    current_timestamp = timezone.now().strftime("%d-%m-%Y %H")
    pub_year = article.publication_year if article.publication_year else ""

    if not user_id:
        article_name = f"{first_author}_{pub_year}_{short_title}_{current_timestamp}.pdf"
    else:
        customer = User.objects.get(id=user_id)
        settings = get_customer_settings(customer)
        ft__foramt = settings.full_texts_naming_format  
        
        if ft__foramt == "A":
            article_name = f"{first_author}_{pub_year}_{short_title}.pdf"
        elif ft__foramt == "B":
            article_name = f"{short_title}_{first_author}_{pub_year}.pdf"
        else:
            article_name = f"{pub_year}_{first_author}_{short_title}.pdf"

    article_name = article_name.replace(" ", "-")
    # get rid of spacial characters
    article_name = article_name.replace("\\", "").replace("\/", "").replace("\n","")
    article_name = re.sub(r'[^a-zA-Z0-9\-_.]', '', article_name)
    return article_name


def clear_ris_file(ris_file):
    # europe pmc sometimes comes with a header that should be removed cant be processed as a ris entry 
    cleaned_file = Path(ris_file)
    with open(cleaned_file, 'r+') as fp:
        # read an store all lines into list
        lines = fp.readlines()
        # move file pointer to the beginning of a file
        fp.seek(0)
        # truncate the file
        fp.truncate()
        # start writing lines except the first line
        i=0
        for line in lines:
            if "JOUR" in line:
                start_line = i
                break
            else:
                i = i + 1  
        fp.writelines(lines[start_line:])


def create_unique_article_identifier(article):
    client_id = ""
    if article.literature_review and article.literature_review.client:
        client_id = article.literature_review.client.id

    article_uuid = None 
    if article.pubmed_uid and len(article.pubmed_uid) < 200:
        article_uuid = article.pubmed_uid
    elif article.pmc_uid and len(article.pmc_uid) < 200:
        article_uuid = article.pmc_uid
    elif article.doi and len(article.doi) < 200:
        article_uuid = article.doi
    else:
        article_uuid = article.id

    return f"{article_uuid}_{client_id}"


def calculate_full_text_status(article_reviews):
    for article_review in article_reviews:
        status = article_review.calculate_full_text_status()    
        if article_review.full_text_status != status:
            article_review.full_text_status = status
            article_review.save()

    return article_reviews