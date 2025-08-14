import pandas
from backend.logger import logger
from lit_reviews.database_imports.utils import form_citation
from lit_reviews.database_imports.utils import set_result_count, insert_article
from lit_reviews.database_scrapers.utils import DEFAULT_EXCLUSION_MAX
from lit_reviews.helpers.articles import process_ris_file
from lit_reviews.models import (
    ArticleReview,
    NCBIDatabase,
    LiteratureSearch,
    LiteratureReview,
    SearchProtocol,
)

# def build_citation(ris_entry, mapping):
#     # citation format: A1, A2, A3, A4. T1. PY; JO. VL(IS): SP-EP. doi: DO
#     # citation Format "{authors} {title}. {journal_name}. {year}; {volume}({number}): {range}. doi:{doi}   
#     a1_authors = ris_entry.get(mapping["A1"], [])
#     a2_authors = ris_entry.get(mapping["A2"], [])
#     a3_authors = ris_entry.get(mapping["A3"], [])
#     a4_authors = ris_entry.get(mapping["A4"], [])
#     authors = [*a1_authors, *a2_authors, *a3_authors, *a4_authors]
#     authors = ",".join(authors)

#     title = ris_entry.get(mapping["T1"], "Title missing, please contact citemed support!" )
#     year = ris_entry.get(mapping["PY"], "")
#     journal_name = ris_entry.get(mapping["JO"], "")
#     volume = ris_entry.get(mapping["VL"], "")
#     number = ris_entry.get(mapping["IS"], "")
#     start_page = ris_entry.get(mapping["SP"], "")
#     end_page = ris_entry.get(mapping["EP"], "")
#     doi = ris_entry.get(mapping["DO"], "")
#     year = ris_entry.get(mapping["Y1"], "")
#     if start_page and end_page:
#         range = f"{start_page}-{end_page}"
#     else:
#         range = ""

#     # if JO is not available try JF
#     if not journal_name:
#         journal_name = ris_entry.get(mapping["JF"], "")

#     return form_citation(authors, title, journal_name, year, volume, number, doi, range)


def parse_text(embase_file, search_term, lit_review_id, lit_search_id=None):
    embase_file = str(embase_file)

    # get database obj and create search object"
    db = NCBIDatabase.objects.get(entrez_enum="embase")
    lit_review = LiteratureReview.objects.get(id=lit_review_id)
    try:
        lit_search = LiteratureSearch.objects.get_or_create(
            literature_review=lit_review, db=db, term=search_term
        )[0]
    except:
        lit_search = LiteratureSearch.objects.get(id=lit_search_id)

    logger.info("counting articles for search: " + str(search_term))

    results = process_ris_file(embase_file, db)
    ## this will be len of events
    count = results["count"]
    entries = results["entries"]
    set_result_count(lit_search, lit_review_id ,count)
    logger.info(f"Embase database import for search term {lit_search.term} Result count is {str(count)}.")
    proccess = 0

    serch_protocol = SearchProtocol.objects.get(literature_review=lit_review)
    disable_exclusion = lit_search.disable_exclusion
    logger.info(f"Disable Exclusion Result is {str(disable_exclusion)}.")
    max_imported_search_results = serch_protocol.max_imported_search_results
    logger.info(f"Max Imported Search Result is {str(max_imported_search_results)}.")
    
    if count < 1 or (disable_exclusion and count > DEFAULT_EXCLUSION_MAX) or (not disable_exclusion and count > max_imported_search_results):
        logger.info(f"Embase database import for search term {lit_search.term} Result count is out of Range {str(count)}.")

    else:
        for entry in entries:
            proccess += 1
            insert_article(entry, lit_search)
            
    imported_articles = ArticleReview.objects.filter(search=lit_search).count()
    return {
        "processed_articles": proccess,
        "imported_articles": imported_articles,
        "import_status": "COMPLETE",
    }


def add_excluded_searches(filename, lit_review_id):
    logger.debug("Adding excluded searches now")
    rows = pandas.read_csv(filename, delimiter=",")

    for index, row in rows.iterrows():
        db = NCBIDatabase.objects.get(entrez_enum="embase")
        search = LiteratureSearch(
            term=row["Term"],
            result_count=int(float(str(row["Results"]).strip().replace(",", ""))),
            literature_review_id=lit_review_id,
            db=db,
        )
        search.save()
