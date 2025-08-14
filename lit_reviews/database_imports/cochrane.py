##cochrane.py
import pandas
from lit_reviews.database_scrapers.utils import DEFAULT_EXCLUSION_MAX

# global searchId
from backend.logger import logger

from lit_reviews.database_imports.utils import form_citation
from lit_reviews.database_imports.utils import set_result_count, insert_article
from lit_reviews.models import (
    Article,
    ArticleReview,
    NCBIDatabase,
    LiteratureSearch,
    LiteratureReview,
    SearchProtocol,
)

# not necessary
# def check_duplicate(searchId, title):
#     search = Search.objects.get(id=searchId)
#     projectId = search.projectId_id

#     print("project id is " + str(projectId))
#     print("checking duplicate for title " + title )
#     res = Article.objects.filter(
#         searchId__projectId=projectId, articleTitle=title.strip())
#     #res = Article.objects.filter(Search__projectId=projectId, articleTitle=title)
#     print(str(res) )
#     if len(res) > 0:
#         return True
#     print("no duplicate found" )

#     return False


def get_result():

    result = {
        "title": "Title missing, please contact citemed support!",
        "abstract": "Abstract wasn't found or could not be processed. If you think this is a mistake please contact support.",
        "citation": None,
        "pubmed_uid": None,
        #'pmc_uid': None
    }
    return result


def build_citation(authors, title, volume, number, range, doi, year, journal_name):
    # citation format: A1, A2, A3, A4. T1. PY; JO. VL(IS): SP-EP. doi: DO
    authors = ",".join(authors)
    return form_citation(authors, title, journal_name, year, volume, number, doi, range)


def get_result_count(cochrane_file):
    count = 0
    with open(cochrane_file, "r", encoding="utf8") as f:
        lines = f.readlines()

    for line in lines:
        if line.find(":") != -1:
            row = line.split(":")
            if row[0] == "US":
                count += 1

    return count

def process_file_lines(cochrane_file):
    articles = []
    lines = []
    with open(cochrane_file, "r", encoding="utf8") as f:
        lines = f.readlines()
    result = get_result()
    authors = []
    year = None

    for line in lines:
        if line.find(":") != -1:
            row = line.split(":")
            if row[0] == "US":
                title = result.get("title", "Title missing, please contact citemed support!")
                volume = result.get("volume", "")
                number = result.get("number", "")
                doi = result.get("doi", "")
                page_range = result.get("page_range", "")
                journal_name = result.get("journal_name", "")
                result["citation"] = build_citation(authors, title, volume, number, page_range, doi, year, journal_name)
                result["citation"] = result["citation"].replace("\n", "")
                result["meta_data"] = {
                    "volume": volume,
                    "volume_number": number,
                    "authors": authors,
                }
                url = row[1:]
                if url and len(url):
                    result["url"] = ":".join(url).strip() # US ROW Content
                articles.append(result)
                # empty results for next line
                result = get_result()
                authors = []

            else:
                if row[0] == "AU":
                    authors.append(row[1])
                if row[0] == "DOI":
                    result["doi"] = row[1]
                if row[0] == "PG":
                    result["page_range"] = row[1]
                if row[0] == "VL":
                    result["volume"] = row[1]
                if row[0] == "NO":
                    result["number"] = row[1]
                if row[0] == "SO":
                    result["journal_name"] = row[1]
                    if len(row) > 2:
                        result["journal_name"] += row[2]
                if row[0] == "AB":
                    if len(row) >= 3:
                        result["abstract"] = row[1] + row[2]
                    else:
                        result["abstract"] = row[1]
                if row[0] == "TI":
                    result["title"] = row[1].strip()
                if row[0] == "YR":
                    year = row[1]
                    result["publication_year"] = year
                if row[0] == "ID":
                    result["pubmed_uid"] = row[1].strip()

    return articles

def parse_text(cochrane_file, search_term, lit_review_id, expected_result_count=None, lit_search_id=None):
    print(str(cochrane_file))
    cochrane_file = str(cochrane_file)
    process = 0

    # Get init search info
    db = NCBIDatabase.objects.get(entrez_enum="cochrane")
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
    if (expected_result_count == None or expected_result_count <= max_imported_search_results) and cochrane_file:
        count = get_result_count(cochrane_file)
    else:
        count = expected_result_count
    logger.info(f"Cochrane database import for search term {lit_search.term} Result count is {str(count)}.")
    set_result_count(lit_search, lit_review_id ,count)

    # run search if results are within the permitted range
    if count < 1 or (disable_exclusion and count > DEFAULT_EXCLUSION_MAX) or (not disable_exclusion and count > max_imported_search_results):
        logger.info(f"Cochrane database import for search term {lit_search.term} Result count is out of Range {str(count)}.")
        ## we need to create a SearchProtocol Object here and store the result count
    else:
        articles = process_file_lines(cochrane_file)
        for article in articles:
            insert_article(article, lit_search)
            process += 1            

    imported_articles = ArticleReview.objects.filter(search=lit_search).count()
    return {
        "processed_articles": process,
        "imported_articles": imported_articles,
        "import_status": "COMPLETE",
    }


def add_excluded_searches(filename, lit_review_id):

    print("adding excluded searches now")

    rows = pandas.read_csv(filename, delimiter=",")

    for index, row in rows.iterrows():

        db = NCBIDatabase.objects.get(entrez_enum="cochrane")

        search = LiteratureSearch(
            term=row["Term"],
            result_count=int(float(str(row["Results"]).strip().replace(",", ""))),
            literature_review_id=lit_review_id,
            db=db,
        )
        search.save()