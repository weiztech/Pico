import pandas as pd
import csv
import os
import requests
import shutil
import urllib
import uuid
import re

from pathlib import Path
from rispy import TAG_KEY_MAPPING
from docxtpl import InlineImage
from docx.shared import Mm

from backend.logger import logger
from lit_reviews.helpers.generic import generate_number_from_text
from lit_reviews.helpers.articles import get_unclassified_and_duplicate_for_article, name_article_full_text_pdf
from lit_reviews.models import CustomerSettings, ArticleReview

def create_excel_file(review_id, report_job_id, document_name_csv, document_name_excel, row_list, set_column_limit=False, sheet_name="Sheet", is_append=False, skip_headless_lines=False, add_to_excel=None):
    output_path = f"tmp/{str(uuid.uuid4())}/"
    Path(output_path).mkdir(parents=True, exist_ok=True)

    document_path_csv = output_path + document_name_csv
    # add to an existing excel file no need to create a new one
    if add_to_excel:
        document_path_final_excel = add_to_excel
    else:
        document_path_final_excel = output_path + document_name_excel

    # create a csv file
    with open(document_path_csv, "w", newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerows(row_list)

    if skip_headless_lines:
        # conver csv file to excel file
        df = pd.read_csv(document_path_csv, keep_default_na=False, na_values=['NaN'], on_bad_lines='skip')
    else:
        # conver csv file to excel file
        df = pd.read_csv(document_path_csv, keep_default_na=False, na_values=['NaN'])
    # Create an empty DataFrame with the same columns as the original DataFrame
    df_empty = pd.DataFrame(columns=df.columns)

    # Concatenate the empty DataFrame with the original DataFrame to ensure at least one row of data
    df = pd.concat([df_empty, df])
    if is_append:
        writer = pd.ExcelWriter(document_path_final_excel, engine='openpyxl', mode='a')
    else:
        writer = pd.ExcelWriter(document_path_final_excel, engine='xlsxwriter')

    df.to_excel(writer, sheet_name=sheet_name, index = False, header=True)
    for column in df:
        column_data = df[column].astype(str)
        if len(column_data) > 0:
            column_length = max(df[column].astype(str).map(len).max(), len(column))
            col_idx = df.columns.get_loc(column)
            MAX_LENGTH = 100
            if column_length < 15:
                column_length = 15
            elif column_length > MAX_LENGTH and set_column_limit:
                column_length = MAX_LENGTH

            if not is_append:
                writer.sheets[sheet_name].set_column(col_idx, col_idx, column_length)

    writer.close()
    return document_path_final_excel


def list_specail_character(context, chart_list):
    """
    This script detect all special characters whithin a giver dictionary.  
    """

    value = context
    if isinstance(value, dict):
        for key in context:
            value = context[key]
            list_specail_character(value, chart_list)
    elif isinstance(value, list):
        for v in value:
            list_specail_character(v, chart_list)
    elif isinstance(value, str):
        reg_expresion = '[^a-zA-Z0-9.!:\-\*\?_,();  *]+'
        specail_chars = re.findall(reg_expresion, value)
        for group in specail_chars:
            for char in group:
                if chart_list.get(char):
                    chart_list[char] += 1
                else:
                    chart_list[char] = 1


def extract_authors(text):
    # First, handle the case where names are in the format "Last, F."
    names = re.findall(r'\b[A-Z][a-z]+,? [A-Z]\.?', text)
    
    # If no names were found in the first format, assume they're in the format "Last"
    if not names:
        names = text.split(',')

    # Clean up extra spaces and return the list of names
    return [name.strip() for name in names]


def form_ris_entry(article_review, article_reviews):
    """
    form a ris entry for a ris file based on user settings and available data in the article
    """

    client = article_review.search.literature_review.client 
    if client.is_company:
        settings = CustomerSettings.objects.filter(client=client).first()
        if not settings:
            settings = CustomerSettings.objects.create(client=client)
    else:
        settings = CustomerSettings.objects.first()
        if not settings:
            settings = CustomerSettings.objects.create()

    article = article_review.article
    keywords = article.keywords.split(",") if article.keywords else ""
    authors = article.citation.split(article.title)[0]
    authors = extract_authors(authors) if authors else ""

    main_search_index = generate_number_from_text(article_review.search.term)
    indexes = [main_search_index]
    article_dups_plus_original, unclassified, duplicated = get_unclassified_and_duplicate_for_article(article_review, article_reviews)
    for dup in article_dups_plus_original:
        index = generate_number_from_text(dup.search.term)
        if index not in indexes:
            indexes.append(index)
    
    search_indexes = "/".join(["P"+str(index) for index in indexes])
    
    entry = {
        'type_of_reference': 'JOUR', 
        'id': article_review.id,
        TAG_KEY_MAPPING[settings.ris_article_title]: article.title,
        TAG_KEY_MAPPING[settings.ris_article_abstract]: article.abstract,
        TAG_KEY_MAPPING[settings.ris_article_search_term_index]: search_indexes,
        TAG_KEY_MAPPING[settings.ris_article_state]: article_review.get_state_display(),
    }

    if article_review.notes:
        entry[TAG_KEY_MAPPING[settings.ris_article_notes]] = article_review.notes
    if article.doi:
        entry[TAG_KEY_MAPPING[settings.ris_article_doi]] = article.doi
    if keywords:
        entry[TAG_KEY_MAPPING[settings.ris_article_keywords]] = keywords
    if article.publication_year:
        entry[TAG_KEY_MAPPING[settings.ris_article_publication_year]] = article.publication_year
    if article.journal:
        entry[TAG_KEY_MAPPING[settings.ris_article_journal_name]] = article.journal
    if article.url:
        entry[TAG_KEY_MAPPING[settings.ris_article_urls]] = article.url
    if authors:
        entry[TAG_KEY_MAPPING[settings.ris_articles_authors]] = authors
    # file attachment for full text pdf
    if article_review.state == "I" and article.full_text:
        full_text_file_name = name_article_full_text_pdf(article)
        entry["file_attachments1"] = f"full_text_pdfs/{full_text_file_name}"

    return entry


def create_full_text_folder(lit_review):
    """
    Create a temp full text pdfs folder to include all the articles 
    full texts for a specific project / literature review.
    """

    TMP_ROOT = "tmp/"
    FOLDER_PATH = TMP_ROOT + "ris_output/"
    # clear folder location if there is already a file there
    try:
        shutil.rmtree(FOLDER_PATH)
    except:
        pass

    os.mkdir(FOLDER_PATH)
    FULL_TEXT_FOLDER_PATH = FOLDER_PATH + "full_text_pdfs/"
    os.mkdir(FULL_TEXT_FOLDER_PATH)
    article_reviews = ArticleReview.objects.filter(search__literature_review=lit_review, state="I")

    for review in article_reviews:
        article = review.article
        logger.debug(f"Full text for Article ID : {article.id}")
        if article.full_text:
            r = requests.get(article.full_text.url)
            # bytes(r.content, encoding= 'utf-8')
            file_name = name_article_full_text_pdf(article)

            # get rid of any / in the name might break the file creation
            if "/tmp" in file_name:
                file_name = file_name.replace("/tmp", "")
            if "/ft" in file_name:
                file_name = file_name.replace("/ft", "")
            if "/" in file_name:
                file_name = file_name.replace("/", "")

            with open(FULL_TEXT_FOLDER_PATH + file_name, "wb+") as file:
                file.write(r.content)

    return TMP_ROOT, FOLDER_PATH


def get_company_logo(image_link, doc):
    # test if the image is valid
    if image_link:
        response = requests.get(image_link)
        if response.status_code == 200:
            # adding image to the document
            file_name = str(uuid.uuid4())+'_image.jpeg'
            project_path = os.path.abspath(os.path.dirname(__name__))
            output_path = "/tmp/images/{0}".format(file_name)
            path = os.path.join(project_path, output_path)
            os.makedirs(path)
            file_path = os.path.join(path, file_name)
            urllib.request.urlretrieve(image_link, file_path)
            company_logo = InlineImage(doc, image_descriptor= file_path, height=Mm(27), width=Mm(40))

            return company_logo
    
    else:
        return ""
    logger.warning("Comapny logo file not found")
 