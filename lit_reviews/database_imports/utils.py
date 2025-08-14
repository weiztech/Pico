from backend.logger import logger
from django.db.models import Q 

from lit_reviews.models import (
    Article,
    ArticleReview,
    LiteratureReviewSearchProposal,
    NCBIDatabase,
    LiteratureReview,
    LiteratureSearch,
    SearchProtocol,
)
from lit_reviews.helpers.articles import process_ris_file, retained_articles
from lit_reviews.database_scrapers.utils import DEFAULT_EXCLUSION_MAX

def set_result_count(lit_search, lit_review_id ,articles_count):
    """
    This helper function set the result count for lit searches 
    this value will be displayed when the search is excluded 
    """
    lit_search.result_count = articles_count
    lit_search.save()
    # update LiteratureReviewSearchProposal result count
    try:
        lit_search_proposal = LiteratureReviewSearchProposal.objects.get(
            literature_review__id=lit_review_id,
            db=lit_search.db,
            term=lit_search.term,
        )
        lit_search_proposal.result_count = articles_count
        lit_search_proposal.save()
    except Exception as e:
        logger.error(f"Lit Search Proposal Not Found")


def form_citation(authors, title, journal_name, year, volume, number, doi, range):
    # citation Format "{authors} {title}. {journal_name}. {year}; {volume}({number}): {range}. doi:{doi} 
    citation = authors
    if title:
        citation += f" {title}."

    if journal_name:
        if journal_name[-1] == ".":
            citation += f" {journal_name}"
        else:
            citation += f" {journal_name}."

    if year:
        citation += f" {year};"

    if volume:
        citation += f" {volume}"

    if number:
        citation += f"({number}):"
    
    if range:
        citation += f" {range}."

    if doi:
        citation += f" doi:{doi}"

    if citation[-1] == ";":
        citation = citation[:-1]
        
    return citation


def insert_article(result, search):
    if 'citation' not in result.keys():
        logger.warning("no citation found for insert, set to None")
        result['citation'] = ""

    if result.get("meta_data"):
        result["meta_data"]["db"] = search.db.name
    else:
        result["meta_data"] = {"db": search.db.name}

    article = None
    article_exists = False
    pubmed_uid = result.get("pubmed_uid", None)
    pmc_uid = result.get("pmc_uid", None)
    doi = result.get("doi", None)
    query = Q()
    
    if pubmed_uid:
        query |= Q(pubmed_uid=pubmed_uid)
    if pmc_uid:
        query |= Q(pmc_uid=pmc_uid)
    if doi:
        query |= Q(doi=doi)
    
    query = Q(Q(literature_review=search.literature_review) & Q(query))
    similar_articles = Article.objects.filter(query)    
    for potential_match in similar_articles:
        if potential_match.title.lower() == result['title'].lower():
            article_exists = True 
            article = potential_match

    if article_exists:
        article.pubmed_uid = result.get("pubmed_uid", None)
        article.pmc_uid = result.get("pmc_uid", None)
        article.title = result['title']
        article.abstract = result['abstract']
        article.citation = result['citation']
        article.publication_year = result['publication_year']
        article.journal = result.get("journal")
        article.doi = result.get("doi")
        article.url = result.get("url")
        article.keywords = result.get("keywords")
        article.literature_review=search.literature_review
        if result.get("meta_data"):
            article.meta_data = result.get("meta_data")

        article.save()
        logger.info("Article titled {} was created.".format(result['title']))

    else:
        logger.info("couldn't find article titled {} based on (pmc_uid or pubmed_uid + literature review), creating it.".format(result['title']))
        article = Article.objects.create(
            pmc_uid = result.get("pmc_uid"), 
            pubmed_uid = result.get("pubmed_uid"), 
            literature_review = search.literature_review,
            title = result['title'],
            abstract = result['abstract'],
            citation = result['citation'],
            journal = result.get("journal"),
            doi = result.get("doi"),
            url = result.get("url"),
            publication_year = result['publication_year'],
        )
        if result.get("meta_data"):
            article.meta_data = result.get("meta_data")
            article.save()

    ArticleReview.objects.create(article=article, search=search)


def parse_one_off_ris(file_path, lit_review_id, search_id, is_retained=False): 
    """
    Process and import articles for One-Off Search.
    File is directly uploaded from Run Searches without creating a search term for.
    """
    logger.info(f"Ratained value: {is_retained}.")
    from lit_reviews.tasks import remove_duplicate_async

    lit_review = LiteratureReview.objects.get(id=lit_review_id)
    lit_search = LiteratureSearch.objects.get(id=search_id)
    initial_search_articles = ArticleReview.objects.filter(search=lit_search).count()

    results = process_ris_file(file_path, lit_search.db)
    count = results["count"]
    entries = results["entries"]
    set_result_count(lit_search, lit_review_id ,count)
    logger.info(f"Embase database import for search term {lit_search.term} Result count is {str(count)}.")

    serch_protocol = SearchProtocol.objects.get(literature_review=lit_review)
    max_imported_search_results = serch_protocol.max_imported_search_results
    logger.info(f"Max Imported Search Result is {str(max_imported_search_results)}.")
    
    if count > max_imported_search_results or count > DEFAULT_EXCLUSION_MAX:
        logger.info(f"One off search import Results are out of Range {str(count)}.")
        return {
            "count": count,
            "status": "Failed",
        }

    else:
        for entry in entries:
            insert_article(entry, lit_search)

        finale_search_articles = ArticleReview.objects.filter(search=lit_search).count()
        if not is_retained:
            remove_duplicate_async.delay(lit_review.id) 

        return {
            "processed_articles": count,
            "imported_articles": finale_search_articles-initial_search_articles,
            "status": "COMPLETE",
        }
