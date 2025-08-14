from fuzzywuzzy import fuzz
import pandas

from django.db.models import Q
from backend.logger import logger
from lit_reviews.database_imports.utils import set_result_count, insert_article, form_citation
from lit_reviews.database_scrapers.utils import DEFAULT_EXCLUSION_MAX
from lit_reviews.helpers.articles import process_ris_file
from lit_reviews.models import (
    ArticleReview,
    NCBIDatabase,
    LiteratureSearch,
    SearchProtocol,
    LiteratureReview,
)

def check_duplicates(citation, abstract, lit_review_id):
    logger.info("Checking Duplicates for google scholar")
    ## get all article reviews for the project
    # article_reviews = ArticleReview.objects.filter().prefetch_related('article')
    citation = str(citation)
    abstract = str(abstract)
    
    article_reviews = ArticleReview.objects.filter(Q(search__literature_review_id=lit_review_id) & ~Q(search__db__entrez_enum='scholar', state='D')) \
                                                            .prefetch_related('article')
    
    dupes = []
    for article_review in article_reviews:
        citation_fuzzy = fuzz.token_set_ratio(article_review.article.citation, citation)
        abstract_fuzzy =  fuzz.token_set_ratio(article_review.article.abstract, abstract)

        if abstract.strip().lower() == 'no link':
            abstract_fuzzy = 0

        if citation_fuzzy > 85 and abstract_fuzzy > 85:
            dupes.append(
                {
                    'scholar_citation': citation,
                    'scholar_abstract': abstract,
                    'cite_citation': article_review.article.citation,
                    'citation_fuzzy': citation_fuzzy,
                    'abstract_fuzzy': abstract_fuzzy,
                    'cite_article': article_review.article
                }
            )

    return dupes


def parse_scholar(filename=None, search_terms=None, lit_review_id=None):
    scholar_csv = pandas.read_csv(filename, delimiter=',', encoding='unicode_escape')
    output_rows = []
    
    try:
        db = NCBIDatabase.objects.get(entrez_enum='scholar')
        search = LiteratureSearch.objects.get(
            term=search_terms, db=db,
            literature_review_id=lit_review_id
        )

    except Exception as e:
        logger.info("no search obj found, create new one")
        db = NCBIDatabase.objects.get(entrez_enum='scholar')
        search = LiteratureSearch(term=search_terms, literature_review_id=lit_review_id, db=db)
        search.save()

    # check if this results needs to be excluded
    serch_protocol = SearchProtocol.objects.get(literature_review__id=lit_review_id)
    disable_exclusion = search.disable_exclusion
    logger.info(f"Disable Exclusion Result is {str(disable_exclusion)}.")
    max_imported_search_results = serch_protocol.max_imported_search_results
    logger.info(f"Max Imported Search Result is {str(max_imported_search_results)}.")
    articles_count = len(scholar_csv)
    # set result count in case of exluded on the app will show up number of exclded results
    set_result_count(search, lit_review_id ,articles_count)

    proccess = 0
    total_duplicates = 0
    if articles_count < 1 or (disable_exclusion and articles_count > DEFAULT_EXCLUSION_MAX) or (not disable_exclusion and articles_count > max_imported_search_results):
        logger.info(f"Pubmed database import for search term {search.term} Result count are out of Range {str(articles_count)}.")

    else:
        for index, row in scholar_csv.iterrows():
            dupes = []
            duplicate_selected = False
            potential_dupes = check_duplicates(row['Citation MLA'], row['Abstract'], lit_review_id)
            
            if not isinstance(row['Title'], str):
                # if not title is provided skip this row
                continue 

            if len(potential_dupes) > 0:
                for dupe in potential_dupes:
                    logger.warning("""Potentical Duplicate Found! \n
                            Scholar Citation: \n
                            {0} \n \n
                            
                            CiteMed System Citation: \n
                            {1}  \n \n
                            
                            {2} - {3}
                            Is Valid Duplicate? \n
                            
                            y for yes \n
                            n for no \n
                            \n \n 
                    
                        """.format(dupe['scholar_citation'], dupe['cite_citation'], dupe['citation_fuzzy'],
                        dupe['abstract_fuzzy']) )
                    
                    if dupe['abstract_fuzzy'] > 80 and dupe['citation_fuzzy'] > 80:
                        pass
                        is_dupe = True 
                    else:
                        is_dupe = True
                        #response = input('Enter:  ')
                        #is_dupe = True if response.lower() == 'y' else False


                    if is_dupe:
                        total_duplicates += 1
                        article_review = ArticleReview(search=search, article=dupe['cite_article'], state='D')
                        article_review.save()
                        #a = input('added articlereview and marked duplicate! {0}'.format(article_review.id))
                        duplicate_selected = True
                        break

                    else:
                        continue

                if duplicate_selected:
                    pass

                else:
                    article_obj = {
                        "title": row['Title'],
                        "abstract": row['Abstract'],
                        "citation": row['Citation MLA'],
                        "publication_year": None,
                    }
                    insert_article(article_obj, search)
                    proccess += 1
                    
            else:
                # no dupes to review, add it!
                article_obj = {
                    "title": row['Title'],
                    "abstract": row['Abstract'],
                    "citation": row['Citation MLA'],
                    "publication_year": None,
                }
                insert_article(article_obj, search)
                proccess += 1

    imported_articles = ArticleReview.objects.filter(search=search).count()
    return {
        "processed_articles": proccess,
        "imported_articles": imported_articles,
        "import_status": "COMPLETE",
        "duplicates": total_duplicates,
    }


def parse_ris(ris_file, search_term, lit_review_id, lit_search_id=None):
    ris_file = str(ris_file)

    # get database obj and create search object"
    db = NCBIDatabase.objects.get(entrez_enum="scholar")
    lit_review = LiteratureReview.objects.get(id=lit_review_id)
    try:
        lit_search = LiteratureSearch.objects.get_or_create(
            literature_review=lit_review, db=db, term=search_term
        )[0]
    except:
        lit_search = LiteratureSearch.objects.get(id=lit_search_id)

    results = process_ris_file(ris_file, db)
    count = results["count"]
    entries = results["entries"]
    proccess = 0
    set_result_count(lit_search, lit_review_id ,count)
    logger.info(f"Google Scholar Database import for search term {lit_search.term} Result count is {str(count)}.")
    serch_protocol = SearchProtocol.objects.get(literature_review=lit_review)
    disable_exclusion = lit_search.disable_exclusion
    logger.info(f"Disable Exclusion Result is {str(disable_exclusion)}.")
    max_imported_search_results = serch_protocol.max_imported_search_results
    logger.info(f"Max Imported Search Result is {str(max_imported_search_results)}.")
    
    if count < 1 or (disable_exclusion and count > DEFAULT_EXCLUSION_MAX) or (not disable_exclusion and count > max_imported_search_results):
        logger.info(f"Google Scholar database import for search term {lit_search.term} Result count is out of Range {str(count)}.")

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

    print('adding excluded searches now')

    rows = pandas.read_csv(filename, delimiter=',')

    for index, row in rows.iterrows():

        db = NCBIDatabase.objects.get(entrez_enum='scholar')

        search = LiteratureSearch(term=row['Term'], result_count=int(float(row['Results'].strip().replace(",", ""))),
                                 literature_review_id=lit_review_id, db=db)
        search.save()
