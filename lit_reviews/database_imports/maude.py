import xlrd
import zipfile
import os 
import pandas as pd 

from backend import settings
from backend.logger import logger
from datetime import datetime
from lit_reviews.models import (
    LiteratureReview,
    NCBIDatabase,
    AdverseEventReview,
    LiteratureSearch,
    AdverseEvent,
)
from lit_reviews.database_imports.utils import set_result_count


def retrieve_events(file_path):
    records = []
    wb = xlrd.open_workbook(file_path)
    sh = wb.sheet_by_index(0)

    for rowIndex in range(1, sh.nrows):
        event = {}
        logger.debug(
            "Row: {0}, {1}, {2}, {3}, {4}, {5}, {6}".format(
                sh.cell_value(rowIndex, 0),
                sh.cell_value(rowIndex, 1),
                sh.cell_value(rowIndex, 2),
                sh.cell_value(rowIndex, 3),
                sh.cell_value(rowIndex, 4),
                sh.cell_value(rowIndex, 5),
                sh.cell_value(rowIndex, 6),
            )
        )

        # event_date = datetime.strptime(str(sh.cell_value(rowIndex, 6)).strip(), '%Y/%m/%d')
        event_description = sh.cell_value(rowIndex, -1).replace(
            "Event Description:", ""
        )
        event_manufacturer = sh.cell_value(rowIndex, 5)
        event_product = sh.cell_value(rowIndex, 7)
        event_brand_name = sh.cell_value(rowIndex, 8)
        event_url = sh.cell_value(rowIndex, 1)
        event_type = sh.cell_value(rowIndex, 4)
        
        if event_url.find("https") != -1:
            try:
                event_number_full =  str(sh.cell_value(rowIndex, 2))
                event_number_short = event_number_full.split('-')[0].strip()
                logger.debug("Event Numbers Long and Short {0} - {1}".format(event_number_full, event_number_short))
                if len(event_number_full) <= 2:
                    raise Exception('could not parse event_number_full for Adverse Event' )

            except Exception as e:
                logger.debug("exception adding maude " + str(e))
                event_number_full = False 
                event_number_short = False 

            logger.debug(str(sh.cell_value(rowIndex, 3) ))
            try:
                event_date = datetime(
                    *xlrd.xldate_as_tuple(sh.cell_value(rowIndex, 3), wb.datemode)
                ).date()

            except Exception as e:
                print("error getting event date, most likely blank, try event_reported instead")
                event_date = datetime(
                    *xlrd.xldate_as_tuple(sh.cell_value(rowIndex, 6), wb.datemode)
                ).date()

            report_date = datetime(
                *xlrd.xldate_as_tuple(sh.cell_value(rowIndex, 6), wb.datemode)
            ).date()

            ae_values = {
                "event_uid": event_url,
                "description": event_description,
                "manufacturer": event_manufacturer,
                "brand_name": event_brand_name,
                "event_type": event_type,
                "report_date": report_date,
                "event_date": event_date,
                "event_number_full": event_number_full,
                "event_number_short": event_number_short,
            }
            records.append(ae_values)

    return records


def retrieve_events_from_xlsx_file(file_path):
    records = []
    try:
        df = pd.read_excel(file_path)
    except ValueError:
        df = pd.read_csv(file_path)
    total_rows = len(df)
    for rowIndex in range(1, total_rows):
        event = {}

        # event_date = datetime.strptime(str(sh.cell(row=rowIndex, column=6).value).strip(), '%Y/%m/%d')
        event_description = df.iloc[rowIndex, -1]
        event_description = event_description.replace("Event Description:", "") if not pd.isnull(event_description) else ""
        event_manufacturer = df.iloc[rowIndex, 5]
        event_product = df.iloc[rowIndex, 7]
        event_brand_name = df.iloc[rowIndex, 8]
        event_url = df.iloc[rowIndex, 1]
        event_type = df.iloc[rowIndex, 4]
        
        if event_url.find("https") != -1:
            try:
                event_number_full =  str(df.iloc[rowIndex, 2])
                event_number_short = event_number_full.split('-')[0].strip()
                logger.debug("Event Numbers Long and Short {0} - {1}".format(event_number_full, event_number_short))
                if len(event_number_full) <= 2:
                    raise Exception('could not parse event_number_full for Adverse Event' )

            except Exception as e:
                logger.debug("exception adding maude " + str(e))
                event_number_full = False 
                event_number_short = False 

            try:
                event_date = df.iloc[rowIndex, 3]
                if type(event_date) == datetime:
                    event_date = event_date.date()
                else:
                    event_date = datetime.strptime(event_date, "%Y-%m-%d %H:%M:%S").date()

            except Exception as error:
                logger.debug("error getting event date, most likely blank, try event_reported instead")
                event_date = df.iloc[rowIndex, 6]
                if type(event_date) == datetime:
                    event_date = event_date.date()
                else:
                    event_date = datetime.strptime(event_date, "%Y-%m-%d %H:%M:%S").date()

            report_date = df.iloc[rowIndex, 6]
            if type(report_date) == datetime:
                report_date = report_date.date()
            else:
                report_date = datetime.strptime(report_date, "%Y-%m-%d %H:%M:%S").date()

            ae_values = {
                "event_uid": event_url,
                "description": event_description,
                "manufacturer": event_manufacturer,
                "brand_name": event_brand_name,
                "event_type": event_type,
                "report_date": report_date,
                "event_date": event_date,
                "event_number_full": event_number_full,
                "event_number_short": event_number_short,
            }
            records.append(ae_values)

    return records

def parse_workbook(file_path, search_term, lit_review_id, lit_search_id=None, is_zip=False, expected_result_count=None):
    count = 0
    db = NCBIDatabase.objects.get(entrez_enum="maude")
    ae_review = LiteratureReview.objects.get(id=lit_review_id)
    ae_bulk_list = []
    ae_reviews_bulk = []

    try:
        ae_search = LiteratureSearch.objects.get_or_create(
            literature_review=ae_review, db=db, term=search_term
        )[0]
    except:
        ae_search = LiteratureSearch.objects.get(id=lit_search_id)

    # deleting AE rviews for this search if it's not coming from zip file processing (parse_zip)
    if not is_zip:
        ae_review = AdverseEventReview.objects.filter(search=ae_search).delete()

    # if no results are found exclude search
    if expected_result_count == 0:
        logger.debug("No Results Found for maude imported file")
        set_result_count(ae_search, lit_review_id ,count)
        return {
            "processed_articles": 0,
            "imported_articles": 0,
            "import_status": "COMPLETE",
        }
    
    try:
        records = retrieve_events(file_path)
    except xlrd.biffh.XLRDError as error:
        records = retrieve_events_from_xlsx_file(file_path)

    for record in records:
        count += 1
        record["db"] = db
        ae_obj = AdverseEvent.objects.filter(**record).first()

        # if event with same values already exists don't create
        if not ae_obj:
            obj_entry = AdverseEvent(**record)
            ae_bulk_list.append(obj_entry)
            print("new ae created!")

        else:
            ae_review = AdverseEventReview(ae=ae_obj, search=ae_search)
            ae_reviews_bulk.append(ae_review)

    # bulk create AdverseEvent objects
    try:
        aes = AdverseEvent.objects.bulk_create(ae_bulk_list)

    except Exception as e:
        raise Exception('Error occured while creating AE: ' + e)

    for ae in aes:
        ae_search.ae_events.add(ae)
        ae_review = AdverseEventReview(ae=ae, search=ae_search)
        ae_reviews_bulk.append(ae_review)

    AdverseEventReview.objects.bulk_create(ae_reviews_bulk)

    # TODO Fix query
    import_article = AdverseEventReview.objects.filter(search=ae_search).count()
    return {
        "processed_articles": count,
        "imported_articles": import_article,
        "import_status": "COMPLETE",
    }


def parse_zip(file_path, search_term, lit_review_id, lit_search_id=None):
    db = NCBIDatabase.objects.get(entrez_enum="maude")
    ae_review = LiteratureReview.objects.get(id=lit_review_id)
    try:
        ae_search = LiteratureSearch.objects.get_or_create(
            literature_review=ae_review, db=db, term=search_term
        )[0]
    except:
        ae_search = LiteratureSearch.objects.get(id=lit_search_id)

    # deleting AE rviews for this search if any!
    ae_review = AdverseEventReview.objects.filter(search=ae_search).delete()

    proccessed = 0
    extract_to = settings.TMP_ROOT + "/" + "unarchived_zip_folder"

    with zipfile.ZipFile(file_path, 'r') as zipf:
        # Extract all files in the zip archive to the specified directory    
        zipf.extractall(extract_to)
    
    for filename in os.listdir(extract_to):
        file_path = os.path.join(extract_to, filename)
        results = parse_workbook(file_path, search_term, lit_review_id, lit_search_id, is_zip=True)
        proccessed += results["processed_articles"]

    imported_articles = AdverseEventReview.objects.filter(search=ae_search).count()
    return {
        "processed_articles": proccessed,
        "imported_articles": imported_articles,
        "import_status": "COMPLETE",
    }