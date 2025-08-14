import xlrd
import os
import pandas as pd
import zipfile
from backend import settings
from datetime import datetime

from lit_reviews.models import *
from lit_reviews.database_imports.utils import set_result_count

def retrieve_recalls(file_path):
    wb = xlrd.open_workbook(file_path)
    sh = wb.sheet_by_index(0)
    records = []

    for rowIndex in range(1, sh.nrows):
        obj = {}
        obj["event_uid"] = sh.cell_value(rowIndex, 1)
        obj["product_description"] = sh.cell_value(rowIndex, 2)
        obj["trade_name"] = sh.cell_value(rowIndex, 3)
        
        # ignore recall class if it's a letter to be updated asap
        try:
            recall_class = sh.cell_value(rowIndex, 4)
            recall_class = int(recall_class)
        except ValueError:
            recall_class = None 

        obj["recall_class"] = recall_class          
        obj["firm_name"] = sh.cell_value(rowIndex, 9)
        obj["recall_reason"] = sh.cell_value(rowIndex, 10)

        if sh.cell_value(rowIndex, 6):
            obj["event_date"] = datetime(
                *xlrd.xldate_as_tuple(sh.cell_value(rowIndex, 6), wb.datemode)
            )
        records.append(obj)

    return records


def retrieve_events_from_xlsx_file(file_path):
    records = []
    try:
        df = pd.read_excel(file_path)
    except ValueError:
        df = pd.read_csv(file_path)
            
    total_rows = len(df)
    for rowIndex in range(1, total_rows):
        obj = {}
        obj["event_uid"] = df.iloc[rowIndex, 1] if not pd.isnull(df.iloc[rowIndex, 1]) else ""
        obj["product_description"] = df.iloc[rowIndex, 2] if not pd.isnull(df.iloc[rowIndex, 2]) else ""
        obj["trade_name"] = df.iloc[rowIndex, 3] if not pd.isnull(df.iloc[rowIndex, 3]) else ""
        obj["recall_class"] = df.iloc[rowIndex, 4] if not pd.isnull(df.iloc[rowIndex, 4]) else ""
        obj["firm_name"] = df.iloc[rowIndex, 9] if not pd.isnull(df.iloc[rowIndex, 9]) else ""
        obj["recall_reason"] = df.iloc[rowIndex, 10] if not pd.isnull(df.iloc[rowIndex, 10]) else ""
        obj["event_date"] = df.iloc[rowIndex, 6] if not pd.isnull(df.iloc[rowIndex, 6]) else ""
        records.append(obj)

    return records


def parse_workbook(file_path, search_term, lit_review_id, lit_search_id=None, expected_result_count=None):
    db = NCBIDatabase.objects.get(entrez_enum="maude_recalls")
    ae_review = LiteratureReview.objects.get(id=lit_review_id)

    try:
        ae_search = LiteratureSearch.objects.get_or_create(
            literature_review=ae_review, db=db, term=search_term
        )[0]
    except:
        ae_search = LiteratureSearch.objects.get(id=lit_search_id)

    # if no results are found exclude search
    if expected_result_count == 0:
        logger.debug("No Results Found for maude imported file")
        set_result_count(ae_search, lit_review_id ,expected_result_count)

        return {
            "processed_articles": 0,
            "imported_articles": 0,
            "import_status": "COMPLETE",
        }
    
    count = 0
    try:
        records = retrieve_recalls(file_path)
    except xlrd.biffh.XLRDError as error:
        records = retrieve_events_from_xlsx_file(file_path)

    for obj in records:
        obj["db"] = db
        try:
            ae = AdverseRecall.objects.filter(**obj).first()
            if not ae:
                ae = AdverseRecall.objects.create(**obj)
                
            ae_search.ae_recalls.add(ae)
            logger.debug("obj created {0} - Search {1}".format(ae, ae_search))
            ae_review = AdverseRecallReview(ae=ae, search=ae_search)
            ae_review.save()
            count = count+1

        except Exception as e:
            raise Exception("Failed creating record with error: " + str(e))
        
    # TODO Fix query
    import_article = AdverseRecallReview.objects.filter(search=ae_search).count()
    return {
        "processed_articles": count,
        "imported_articles": import_article,
        "import_status": "COMPLETE",
    }


def parse_zip(file_path, search_term, lit_review_id, lit_search_id=None):
    db = NCBIDatabase.objects.get(entrez_enum="maude_recalls")
    ae_review = LiteratureReview.objects.get(id=lit_review_id)
    try:
        ae_search = LiteratureSearch.objects.get_or_create(
            literature_review=ae_review, db=db, term=search_term
        )[0]
    except:
        ae_search = LiteratureSearch.objects.get(id=lit_search_id)

    # deleting recall rviews for this search if any!
    recalls = AdverseRecallReview.objects.filter(search=ae_search).delete()

    proccessed = 0
    extract_to = settings.TMP_ROOT + "/" + "unarchived_zip_folder"

    with zipfile.ZipFile(file_path, 'r') as zipf:
        # Extract all files in the zip archive to the specified directory    
        zipf.extractall(extract_to)
    
    for filename in os.listdir(extract_to):
        file_path = os.path.join(extract_to, filename)
        results = parse_workbook(file_path, search_term, lit_review_id, lit_search_id)
        proccessed += results["processed_articles"]

    imported_articles = AdverseRecallReview.objects.filter(search=ae_search).count()
    return {
        "processed_articles": proccessed,
        "imported_articles": imported_articles,
        "import_status": "COMPLETE",
    }