import pandas

from lit_reviews.database_scrapers.utils import DEFAULT_EXCLUSION_MAX
from backend.logger import logger
from lit_reviews.database_imports.utils import set_result_count, insert_article
from lit_reviews.models import (
    ArticleReview,
    NCBIDatabase,
    LiteratureSearch,
    LiteratureReview,
    SearchProtocol,
    SearchConfiguration,
    SearchParameter,
)


def get_result_count(ct_file):
    count = 0
    with open(ct_file, "r", encoding="utf8") as f:
        rows = pandas.read_csv(f, delimiter=",")
        count = len(rows)
        logger.info("Results Count: " + str(count))
        return count

def process_file_row(row, search):
    # there are two types of fiels (old and new version)
    # is missing some headers and some of them are named differently
    search_config = SearchConfiguration.objects.get(
        database=search.db,
        literature_review=search.literature_review
    )
    study_results_param = SearchParameter.objects.get(
        search_config=search_config, name="Study Results"
    )
    results_condition = True 

    if row.get("Status"):    
        if study_results_param.value == "Studies With Results":
            results_condition = row["Study Results"] == "Has Results" 
        
        if row["Status"] == "Completed" and results_condition:
            abstract = """ 
               <strong> NCT Number:</strong> {0}   </br></br>   \n
               <strong> Title:</strong>  {1} </br></br> \n
                <strong>Conditions:</strong>  {2}</br></br> \n 
                <strong>Interventions:</strong>  {3} </br></br>  \n
                <strong>Outcome Measures:</strong> {4} </br></br> 
                <strong>Gender:</strong>  {5} </br></br> 
                <strong>Age:</strong>  {6} </br></br> 
                <strong>Phase:</strong>  {7} </br></br> 
                <strong>Enrollment:</strong> {8} </br></br> 
                <strong>Study Type:</strong>   {9} </br></br> 
                <strong>Study Designs:</strong>  {10} </br> </br>
                <strong>Locations:</strong>   {11} </br> </br>
                <strong>Link:</strong>    <a  target="_blank" href={12}>{12}</a> </br></br> 
            """.format(
                row["NCT Number"],
                row["Title"],
                row["Conditions"],
                row["Interventions"],
                row["Outcome Measures"],
                row["Gender"],
                row["Age"],
                row["Phases"],
                row["Enrollment"],
                row["Study Type"],
                row["Study Designs"],
                row["Locations"],
                row["URL"],
            )

            citation = " {0}, {1}, {2}".format(
                row["NCT Number"], row["Title"], row["URL"]
            )

            result = {
                "title": row["Title"],
                "abstract": abstract,
                "citation": citation,
                "pubmed_uid": row["NCT Number"],
                "publication_year": row.get("Start Date"),
                "url": row["URL"],
            }
            return result
            # insert_article(result, lit_search)
            # proccess += 1

    else:
        if study_results_param.value == "Studies With Results":
            results_condition = row["Study Results"] == "YES"

        if row["Study Status"] == "COMPLETED" and results_condition:
            abstract = """ 
                NCT Number: {0} </br>   \n
                Title:  {1}</br> \n
                Conditions:  {2}</br> \n 
                Interventions:  {3} </br>  \n
                Outcome Measures: {4} </br> 
                Gender:  {5} </br> 
                Age:  {6} </br> 
                Phase:  {7} </br> 
                Enrollment: {8} </br> 
                Study Type:   {9} </br> 
                Study Designs:  {10} </br> 
                Locations:   {11} </br> 
                Link:    <a  target="_blank" href={12}>{12}</a> </br> 
            """.format(
                row["NCT Number"],
                row["Study Title"],
                row["Conditions"],
                row["Interventions"],
                row["Primary Outcome Measures"],
                row["Sex"],
                row["Age"],
                row["Phases"],
                row["Enrollment"],
                row["Study Type"],
                row["Study Design"],
                row["Locations"],
                row["Study URL"],
            )

            citation = " {0}, {1}, {2}".format(
                row["NCT Number"], row["Study Title"], row["Study URL"]
            )

            result = {
                "title": row["Study Title"],
                "abstract": abstract,
                "citation": citation,
                "pubmed_uid": row["NCT Number"],
                "publication_year": row.get("Start Date"),
                "url": row["Study URL"],
            }
            return result
            # insert_article(result, lit_search)
            # proccess += 1


def parse_text(ct_gov_file, search_term, lit_review_id, expected_result_count=None, lit_search_id=None):
    # Get init search info
    proccess = 0 
    db = NCBIDatabase.objects.get(entrez_enum="ct_gov")
    lit_review = LiteratureReview.objects.get(id=lit_review_id)
    try:
        lit_search = LiteratureSearch.objects.get_or_create(
            literature_review=lit_review, db=db, term=search_term
        )[0]
    except:
        lit_search = LiteratureSearch.objects.get(id=lit_search_id)
    serch_protocol = SearchProtocol.objects.get(literature_review=lit_review)
    disable_exclusion = lit_search.disable_exclusion
    logger.info(f"Disable Exclusion Result is {str(disable_exclusion)}.")
    max_imported_search_results = serch_protocol.max_imported_search_results
    logger.info(f"Max Imported Search Result is {str(max_imported_search_results)}.")


    # set result count
    if (expected_result_count == None or expected_result_count <= max_imported_search_results) and ct_gov_file:
        count = get_result_count(ct_gov_file)
    else:
        count = expected_result_count
    logger.info(f"CT GOVE database import for search term {lit_search.term} Result count is {str(count)}.")
    set_result_count(lit_search, lit_review_id ,count)
    
    
    # run search if results are within the permitted range
    if count < 1 or (disable_exclusion and count > DEFAULT_EXCLUSION_MAX) or (not disable_exclusion and count > max_imported_search_results):
        logger.info(f"CT GOVE database import for search term {lit_search.term} Result count are out of Range {str(count)}.")
        ## TODO create a SearchProtocl object and store the results here.
    else:
        f = pandas.read_csv(ct_gov_file, delimiter=",")
        for index, row in f.iterrows():
            result = process_file_row(row, lit_search)
            if result:
                insert_article(result, lit_search)
                proccess += 1

    imported_articles = ArticleReview.objects.filter(search=lit_search).count()
    return {
        "processed_articles": proccess,
        "imported_articles": imported_articles,
        "import_status": "COMPLETE",
    }


def add_excluded_searches(filename, lit_review_id):

    print("adding excluded searches now")

    rows = pandas.read_csv(filename, delimiter=",")

    for index, row in rows.iterrows():

        db = NCBIDatabase.objects.get(entrez_enum="ct_gov")

        search = LiteratureSearch(
            term=row["Term"],
            result_count=int(float(str(row["Results"]).strip().replace(",", ""))),
            literature_review_id=lit_review_id,
            db=db,
        )
        search.save()
