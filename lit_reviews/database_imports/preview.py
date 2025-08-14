import os
import json
from Bio import Medline
import pandas 
from pathlib import Path
from copy import deepcopy
import rispy
from tempfile import NamedTemporaryFile
from django.core.files import File
from backend import settings

from lit_reviews.pmc_api import medline_json_to_citemed_article
from lit_reviews.database_imports.cochrane import process_file_lines
from lit_reviews.helpers.articles import process_ris_file
from lit_reviews.models import ArticlePreview, SearchTermPreview
from lit_reviews.database_imports.ct_gov import process_file_row
from lit_reviews.database_imports.maude_recalls import retrieve_recalls
from lit_reviews.database_imports.maude import retrieve_events

def proccess_preview(search, preview, s_results):
    # if results are a file:    
    if isinstance(s_results, str) and  (".txt" in s_results or ".text" in s_results or ".ris" in s_results or ".csv" in s_results):
        filepath = os.path.join(settings.TMP_ROOT, s_results)
    else:
        file_temp = NamedTemporaryFile(delete=True)
        file_temp.write(s_results) 
        file_temp.flush()
        filepath = file_temp.name # File(file_temp)

    articles = []
    if search.db.entrez_enum == "pubmed" or search.db.entrez_enum == "pmc":
        fetch_handle = open(filepath, "r", encoding="utf8")
        file_articles = Medline.parse(fetch_handle)
        for article in file_articles:
            if len(article.keys()) < 2:
                # ignore file line if it's not an article
                continue
            
            article = medline_json_to_citemed_article(article)
            articles.append(article)

    elif search.db.entrez_enum == "cochrane":
        articles = process_file_lines(filepath)

    elif search.db.entrez_enum == "ct_gov":
        f = pandas.read_csv(filepath, delimiter=",")
        count = 0 
        for index, row in f.iterrows():
            result = process_file_row(row, search)

            if result:
                count += 1
                article = {"title": result["title"], "abstract": result["abstract"], "citation": result["citation"]}
                articles.append(article)

        # update expected search count since in clinical trails we exclude automatically non completed studies 
        search.expected_result_count = count
        search.save()

    elif search.db.entrez_enum == "pmc_europe":
        results = process_ris_file(filepath, search.db)
        articles = results.get("entries")

    elif search.db.entrez_enum == "maude":
        records = retrieve_events(filepath)
        for article in records:
            article.pop("event_date")
            article.pop("report_date")
            articles.append(article)

    elif search.db.entrez_enum == "maude_recalls":
        records = retrieve_recalls(filepath)
        for article in records:
            article.pop("event_date")
            articles.append(article)

    if len(articles) > 50:
        articles = articles[0:50]
        
    previewObj = SearchTermPreview.objects.get(id=preview)
    previewObj.results = json.dumps(articles)
    previewObj.status = "COMPLETED"
    previewObj.save()