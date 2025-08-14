import pandas
from Bio import Medline
from lit_reviews.database_scrapers.utils import DEFAULT_EXCLUSION_MAX
from backend.logger import logger
from lit_reviews.database_imports.utils import set_result_count, insert_article
from lit_reviews.pmc_api import medline_json_to_citemed_article

from lit_reviews.models import (
    ArticleReview,
    NCBIDatabase,
    LiteratureSearch,
    LiteratureReview,
    SearchProtocol,
)

def build_citation(authors, title, year):
    no_authors = len(authors) == 0
    no_title = title == "Title missing, please contact citemed support!" 
    if  no_authors and no_title and not year:
        return "" 

    citation = ""
    for author in authors:
        citation += author + " ,"

    citation += "  "
    citation += title + ". "
    citation += "PubMed "

    citation += "(" + str(year) + ")"
    print("citation built:  " + str(citation))

    return citation


import xml.etree.ElementTree as ET

def parse_xml(filepath, search_term, lit_review_id, entrez_enum, expected_result_count=None):
    # expected_result_count will come only from Run Auto Search (Scraper Result Count).
    db = NCBIDatabase.objects.get(entrez_enum=entrez_enum)
    lit_review = LiteratureReview.objects.get(id=lit_review_id)
    lit_search = LiteratureSearch.objects.get_or_create(
        literature_review=lit_review, db=db, term=search_term
    )[0]

    serch_protocol = SearchProtocol.objects.get(literature_review=lit_review)
    disable_exclusion = lit_search.disable_exclusion
    logger.info(f"Disable Exclusion Result is {str(disable_exclusion)}.")
    max_imported_search_results = serch_protocol.max_imported_search_results
    logger.info(f"Max Imported Search Result is {str(max_imported_search_results)}.")
    
    process = 0
    if (expected_result_count == None or expected_result_count <= max_imported_search_results) and filepath:
        tree = ET.parse(filepath)
        root = tree.getroot()
        articles_list = root.findall('article')
        articles_count = len(list(articles_list))

    else:
        articles_count = expected_result_count

    set_result_count(lit_search, lit_review_id ,articles_count)
    
    if articles_count < 1 or (disable_exclusion and articles_count > DEFAULT_EXCLUSION_MAX) or (not disable_exclusion and articles_count > max_imported_search_results):
        logger.info(f"Pubmed database import for search term {lit_search.term} Result count are out of Range {str(articles_count)}.")

    else:
        for article in articles_list:
            print(article)
            
            article_as_dict = {}
            pmc_id = None
            pubmed_id = None
            abstract_text = None
            title_text = None 
            citation = None 


            pm_id_types = article.findall('.front/article-meta/article-id')
            for pm_id in pm_id_types:
                print(pm_id.attrib)
                if pm_id.attrib['pub-id-type'] == 'pmid':
                    #print("pubmed id: " + pm_id.text)
                    pubmed_id = pm_id.text
                    
                if pm_id.attrib['pub-id-type'] == 'pmc':   
                    pmc_id = pm_id.text
        
            title = article.find('.front/article-meta/title-group/article-title')
            try:
                if  len(list(title)) > 0:
                    title_text = "".join(title.itertext())
                else:
                    title_text = title.text
            except Exception as e: 
                logger.error(str(e))
                title_text = "Title missing, please contact citemed support!" 

            logger.debug(f"Title: {title_text}")
                
            authors_elements =  article.find('.front/article-meta/contrib-group')
            authors_list = []
            if authors_elements:
                for author_el in authors_elements:
                    if 'contrib-type' in author_el.attrib.keys()  and author_el.attrib['contrib-type'] == 'author':
                        ## we have an author
                        ## parse xml and append LastName, FirstName,
                        first_name = author_el.find(".name/surname")
                        try:
                            first_name = first_name.text
                        except:
                            first_name = ""

                        last_name = author_el.find(".name/given-names")
                        try:
                            last_name  = last_name.text
                        except:
                            last_name = ""

                        authors_list.append(first_name + " " + last_name)

            year = article.find('.front/article-meta/pub-date/year')
            try:
                year = year.text
            except:
                year = ""

            citation = build_citation(authors_list, title_text, year)  

            abstract = article.find('.front/article-meta/abstract')
            abstract_text = "Abstract wasn't found or could not be processed. If you think this is a mistake please contact support."  
            if abstract:
                abstract_text = "".join(abstract.itertext())

            article_as_dict = {
                "pmc_uid": pmc_id,
                "pubmed_uid":pubmed_id,
                "abstract": abstract_text,
                "title": title_text,
                "citation": citation,
                "publication_year": year,
            }
            insert_article(article_as_dict, lit_search)
            process += 1

    imported_articles = ArticleReview.objects.filter(search=lit_search).count()
    # fetch_handle.close()
    print("completed processing articles!")
    return {
        "processed_articles": process,
        "imported_articles": imported_articles,
        "import_status": "COMPLETE",
    }

def parse_text(filepath, search_term, lit_review_id, entrez_enum, expected_result_count=None, lit_search_id=None):
    # Get init search info
    process = 0
    db = NCBIDatabase.objects.get(entrez_enum=entrez_enum)
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
    if (expected_result_count == None or expected_result_count <= max_imported_search_results) and filepath:
        fetch_handle = open(filepath, "r", encoding="utf8")
        articles = []
        file_articles = Medline.parse(fetch_handle)
        articles_count = len(list(file_articles))
    
    else:
        articles_count = expected_result_count
    set_result_count(lit_search, lit_review_id ,articles_count)

    # run search if results are within the permitted range
    if articles_count < 1 or (disable_exclusion and articles_count > DEFAULT_EXCLUSION_MAX) or (not disable_exclusion and articles_count > max_imported_search_results):
        logger.info(f"Pubmed database import for search term {lit_search.term} Result count are out of Range {str(articles_count)}.")
    else:
        fetch_handle = open(filepath, "r", encoding="utf8")
        file_articles = Medline.parse(fetch_handle)
        for article in file_articles:
            if len(article.keys()) < 2:
                # ignore file line if it's not an article
                continue

            # print("Processing article {0}".format(article))
            citemed = medline_json_to_citemed_article(article)
            articles.append(dict(raw=article, citemed=citemed))
            process += 1
            ## or do insert here.
            articles.append(citemed)
            insert_article(citemed, lit_search)

    imported_articles = ArticleReview.objects.filter(search=lit_search).count()
    # fetch_handle.close()
    print("completed processing articles!")
    return {
        "processed_articles": process,
        "imported_articles": imported_articles,
        "import_status": "COMPLETE",
    }


def add_excluded_searches(filename, lit_review_id, db):

    print("adding excluded searches now for database " + str(db))

    db = NCBIDatabase.objects.get(entrez_enum=db)

    rows = pandas.read_csv(filename, delimiter=",")

    for index, row in rows.iterrows():

        search = LiteratureSearch(
            term=row["Term"],
            result_count=int(float(str(row["Results"]).strip().replace(",", ""))),
            literature_review_id=lit_review_id,
            db=db,
        )
        search.save()
