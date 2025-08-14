import pandas
from pathlib import Path

from lit_reviews.helpers.articles import process_ris_file
from backend.logger import logger
from lit_reviews.database_imports.utils import set_result_count, insert_article
from lit_reviews.database_scrapers.utils import DEFAULT_EXCLUSION_MAX
from lit_reviews.models import (
    ArticleReview,
    NCBIDatabase,
    LiteratureSearch, 
    LiteratureReview,
    SearchProtocol,
)

# def build_citation(authors, title, year, database):
#     no_authors = len(authors) == 0
#     no_title = title == "Title missing, please contact citemed support!" 
#     if  no_authors and no_title and not year:
#         return "" 

#     citation = ""
#     for author in authors:
#         citation += author + ","

#     citation += "  "
#     citation += title + ". "
#     citation += " {0} ".format(database)

#     citation += "(" + str(year) + ")"
#     print("citation built:  " + str(citation))

#     return citation

# def process_file_entries(entries):
#     articles = []
#     for entry in entries:
#         obj = {}
#         logger.debug(entry.keys())
#         logger.debug(entry['accession_number'])
    
#         try:
#             authors = entry['authors']
#         except KeyError as e:
#             authors = []
            
#         try:
#             title = entry['title'] 
#         except KeyError as e:
#             title = "Title missing, please contact citemed support!" 
#             pass
        
#         try:
#             year = entry['year']
#         except KeyError as e:
#             pass
#             year = None
        
#         try:
#             obj['abstract'] = entry['abstract']

#         except KeyError as e:
#             logger.debug("no abstract found")
#             obj['abstract'] = "Abstract wasn't found or could not be processed. If you think this is a mistake please contact support." 

#         try:
#             obj['pubmed_uid'] = entry['accession_number']
#             obj['pmc_uid'] = entry['accession_number']
#         except KeyError as e:
#             logger.debug("error importing article {0}".format(obj))
#             obj['pubmed_uid'] = entry['accession_number']

#         try:
#             database = entry['name_of_database']
#         except Exception as e:
#             database = ""
            
#         obj['title'] = entry['title']
#         obj['publication_year'] = entry['year']
#         obj['citation'] = build_citation(authors, title, year, database)
#         logger.debug(str(obj))
#         articles.append(obj)

#     return articles 

def process_file_and_extract_results(ris_file):
    db = NCBIDatabase.objects.get(entrez_enum='pmc_europe')
    results = process_ris_file(ris_file, db)
    return results

def parse_text(ris_file, search_terms, lit_review_id, expected_result_count=None, lit_search_id=None):
    # Get init search info
    proccess = 0
    ris_file =  str(ris_file)
    db = NCBIDatabase.objects.get(entrez_enum='pmc_europe')
    lit_review = LiteratureReview.objects.get(id=lit_review_id)
    try:
        lit_search = LiteratureSearch.objects.get_or_create(
            literature_review=lit_review, db=db, term=search_terms
        )[0]
    except:
        lit_search = LiteratureSearch.objects.get(id=lit_search_id)

    serch_protocol = SearchProtocol.objects.get(literature_review=lit_review)
    disable_exclusion = lit_search.disable_exclusion
    logger.info(f"Disable Exclusion Result is {str(disable_exclusion)}.")
    max_imported_search_results = serch_protocol.max_imported_search_results
    logger.info(f"Max Imported Search Result is {str(max_imported_search_results)}.")

    # set result count
    if (expected_result_count == None or expected_result_count <= max_imported_search_results) and ris_file:
        results = process_file_and_extract_results(ris_file)
        count = results["count"]
    else:
        count = expected_result_count

    set_result_count(lit_search, lit_review_id ,count)

    if count < 1 or (disable_exclusion and count > DEFAULT_EXCLUSION_MAX) or (not disable_exclusion and count > max_imported_search_results):
        logger.info(f"PMC Europe database import for search term {lit_search.term} Result count is out of Range {str(count)}.")

    else:
        results = process_file_and_extract_results(ris_file)
        entries = results["entries"]
        logger.info(f"PMC Europe database import for search term {lit_search.term} Result count is {str(count)}.")
        proccess = 0

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

    print('adding excluded searches now')

    rows = pandas.read_csv(filename, delimiter=',')

    for index, row in rows.iterrows():

        db = NCBIDatabase.objects.get(entrez_enum='pmc_europe')

        search = LiteratureSearch(term=row['Term'], result_count=int(float(str(row['Results']).strip().replace(",", ""))),
                                 literature_review_id=lit_review_id, db=db)
        search.save()
