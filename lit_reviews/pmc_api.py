import random
import traceback

from time import sleep, time
from xml.etree import ElementTree
from urllib.parse import urlencode
from typing import List, Any, Dict, Iterable

from Bio import Medline
from django.db import IntegrityError
from django.db.models import Q
from backend import settings

from .models import (
    LiteratureReviewSearchProposal,
    Article,
    ArticleReview,
    LiteratureSearch, LiteratureReview, ClinicalLiteratureAppraisal,
)
from .constants import RANDOM_USER_AGENT_LIST, Databases, DateTypes, ABSTRACT_FIELD
from .biopython_wrapper import Entrez

from backend.logger import logger
import requests
import uuid
import os
# Maude
# https://open.fda.gov/apis/query-parameters/

class PubmedAPI:
    url_root = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"

    class Services:
        esearch = "esearch"
        einfo = "einfo"

    class Databases:
        pubmed_central = "pmc"
        pubmed = "pm"

    def __init__(self):
        pass

    @staticmethod
    def query_url(service: str, q: Dict) -> str:
        url = PubmedAPI.url_root + f"{service}.fcgi"
        if not q:
            return url
        return url + f"?{urlencode(q)}"

    @staticmethod
    def get(service: str, q: Dict, as_json: bool = False, **get_kwargs) -> str:
        if as_json:
            q.update(dict(retmode="json"))
        url = PubmedAPI.query_url(service, q)
        response = requests.get(url, **get_kwargs)
        if as_json:
            return response.json()[f"{service}result"]
        return response

    @staticmethod
    def get_db_info(dbs: Iterable[str] = None) -> Dict:
        if dbs is None:
            dbs = PubmedAPI.get(PubmedAPI.Services.einfo, dict(), as_json=True)
            dbs = dbs["dblist"]
        data = dict()
        for db in dbs:
            result = PubmedAPI.get(PubmedAPI.Services.einfo, dict(db=db), as_json=True)
            try:
                data[db] = result["dbinfo"]
            except KeyError:
                import pprint

                pprint.pprint(result)
                return
        return data

    @staticmethod
    def pmc_result_count(
        term: str,
        years_back: float,
        in_abstract: bool,
        full_text_available: bool,
        db: str,
        datetype: str,
        **get_kwargs,
    ) -> int:
        if in_abstract:
            abstract_field = ABSTRACT_FIELD[db]
            term = f"{term}[{abstract_field}]"
        if full_text_available:
            term = f"{term} AND free fulltext[filter]"
        q = dict(db=db, term=term, reldate=int(365 * years_back), datetype=datetype)
        print(q)
        return int(
            PubmedAPI.get(PubmedAPI.Services.esearch, q, as_json=True, **get_kwargs)[
                "count"
            ]
        )

    @staticmethod
    def pmc_ids_for_term(term: str) -> List[Any]:
        raise NotImplementedError

    @staticmethod
    def pm_metadata_from_pmc_metadata(pmc_metadata: Dict) -> Dict:
        pm_id = None
        for id_info in pmc_metadata["articleids"]:
            if id_info["idtype"] == "pmid":
                pm_id = id_info["value"]
                break
        if pm_id is None:
            return None
        #         raise KeyError("Didn't find Pubmed ID for PubmedCentral ID.")
        url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pubmed&id={pm_id}&tool=my_tool&email=my_email@example.com&rettype=abstract"
        try:
            response = requests.get(url)
        except Exception as e:
            logger.error(f"An unhandled error occured scraping {url}: {e}")
            return None
        #     return json.loads(response.content.decode()replace("Pubmed-entry ::= ", "").strip())
        return ElementTree.fromstring(response.content.decode())


def get_user_agent():
    return {"User-Agent": random.choice(RANDOM_USER_AGENT_LIST)}


def download_pmc_full_text(pmc_id: str):
    if not pmc_id.startswith("PMC"):
        try:
            int(pmc_id)
        except:
            raise Exception(
                f"{pmc_id} does not appear to be a Pubmed Central ID, nor does it start with PMC"
            )
        pmc_id = f"PMC{pmc_id}"
    url = f"https://www.ncbi.nlm.nih.gov/pmc/articles/{pmc_id}/pdf"
    with open(f"/Users/gdp/temp/{pmc_id}.pdf", "wb") as f:
        f.write(requests.get(url, headers=get_user_agent()).content)


def get_count(
    term: str,
    db: str,
    years_back: int,
    in_abstract: bool,
    full_text_available: bool,
    datetype: str = DateTypes.publication,
):
    # if in_abstract:
    #     abstract_field = ABSTRACT_FIELD[db]
    #     term = f"{term}[{abstract_field}]"
    # if full_text_available:
    #     term = f"{term} AND free fulltext[filter]"
    q = dict(db=db, term=term, reldate=int(365 * years_back), datetype=datetype)
    from .biopython_wrapper import Entrez

    print('sending')
    Entrez.email = "A.NOther@mail.com"
    handle = Entrez.esearch(**q)
    print('sent')
    record = Entrez.read(handle)
    print('read')
    handle.close()
    print(f'Result: {record}')
    return record["Count"]


def get_citation(db: str, id: str):
    # pmc articles have an extra PMC in thier ids
    if "PMC" in id:
        id = id.replace("PMC", "")

    NOW = time()
    THIRTY_SECONDS_FROM_NOW = NOW + 30
    while time() < THIRTY_SECONDS_FROM_NOW: 
        try:
            api_key = settings.PUBMED_API_KEY
            url = f"https://api.ncbi.nlm.nih.gov/lit/ctxp/v1/{db}/?format=citation&contenttype=json&id={id}"
            if api_key:
                url += "&api_key={}".format(api_key)

            res = requests.get(url, headers={"User-Agent": "Hydra/1.3.15"})
            logger.debug(f"Pubmed API Citation Res: {res}")
            return res.json()["ama"][
                "format"
            ]

        except Exception as error:
            error_msg = str(traceback.format_exc())
            logger.warning("Error trying to get article citation: " + error_msg)
            sleep(2)

    return ""

def create_related_article_items(
    search_proposal: LiteratureReviewSearchProposal, article_dict: Dict
):
    search, created = LiteratureSearch.objects.get_or_create(
        literature_review=search_proposal.literature_review,
        in_abstract=search_proposal.in_abstract,
        full_text_available=search_proposal.full_text_available,
        db=search_proposal.db,
        term=search_proposal.term,
        years_back=search_proposal.years_back,
    )
    search.result_count = search_proposal.result_count
    search.save()

    if article_dict:
        try:
            article, created = Article.objects.get_or_create(**article_dict)
        except IntegrityError as e:
            print(f'Could not create article: {article_dict["title"]}: {e}')
            # TODO match better
            article = Article.objects.filter(title=article_dict["title"]).first()
        try:
            ArticleReview.objects.create(article=article, search=search)
        except IntegrityError as e:
            print(f'Could not create article review: {article_dict["title"]}: {e}')


def clear_literature_review_data(lit_review: LiteratureReview):
    # article reviews and clinical literature appraisals delete from a cascade of the existing searches
    LiteratureSearch.objects.filter(literature_review=lit_review).delete()


## original tom code 
def materialize_search_proposal(
    search_proposal: LiteratureReviewSearchProposal, batch_size: int = 25
):
    # first, clear existing data
    print("Running Materialize Search Proposal now {0}".format(search_proposal.term))
    batch_size = 50
    
    search_results = Entrez.read(
        Entrez.esearch(usehistory="y", **search_proposal.as_entrez_dict())
    )

    search_url =   Entrez.esearch(usehistory="y", **search_proposal.as_entrez_dict()).url


    count = int(search_results["Count"])
    db = search_proposal.db.entrez_enum

    if count > 0 and count < 200: 
        articles = []
        for start in range(0, count, batch_size):
            end = min(count, start + batch_size)
            

            try:

                fetch_handle = Entrez.efetch(
                    db=db,
                    rettype="medline",
                    retmode="text",
                    retstart=start,
                    retmax=batch_size,
                    webenv=search_results["WebEnv"],
                    query_key=search_results["QueryKey"],
                )
            except Exception as e:
                print("exception entrez efetch " + str(e))
                sleep(10)

                fetch_handle = Entrez.efetch(
                    db=db,
                    rettype="medline",
                    retmode="text",
                    retstart=start,
                    retmax=batch_size,
                    webenv=search_results["WebEnv"],
                    query_key=search_results["QueryKey"],
                )
           

            print("Entrez object received {0}, parse articles now".format(fetch_handle))

            path = './manual_imports/{0}/pmc_pubmed/'.format(search_proposal.literature_review.id,
                    search_proposal.term, search_proposal.db)

            filename = '{0}-{1}.txt'.format( search_proposal.term, db)
            if not os.path.exists(path):
                os.makedirs(path)
   
            try:

                with open(path + filename ,'w') as handle:
                    handle.write("{0} \n \n ".format(search_url))
                    handle.write(fetch_handle.read())

                fetch_handle.close()


            except Exception as e:
                print("Exception reading from pubmed into file... retry")

                sleep(10)

                with open(path + filename ,'w') as handle:
                    handle.write("{0} \n \n ".format(search_url))
                    handle.write(fetch_handle.read())

                fetch_handle.close()

            print("written to output ")
            fetch_handle = open(path + filename, 'r')

            for article in Medline.parse(fetch_handle):
                #print("Processing article {0}".format(article))
                citemed = medline_json_to_citemed_article(article)
                articles.append(dict(raw=article, citemed=citemed))
                articles.append(citemed)
                create_related_article_items(search_proposal, citemed)
            #fetch_handle.close()
        print("completed processing articles!")
        return articles
    else:
        # outside threshold, so don't created any articles

        citemed = None
        create_related_article_items(search_proposal, citemed)
        print("completed materialize_search_proposal! results out of range 0 - 200 {0} {1} {2}".format(count, search_proposal.term, search_proposal.db.entrez_enum))
        print("search_results: " + str(search_results))




def medline_json_to_citemed_article(article: Dict) -> Dict:
    d = dict()
    d["pmc_uid"] = None 
    d["pubmed_uid"] = None

    id_source = None
    _id = None
    if "PMC" in article:
        d["pmc_uid"] = article["PMC"]  
        id_source = "pmc"
        _id = article["PMC"]
        d["url"] = f"https://www.ncbi.nlm.nih.gov/pmc/articles/{_id}/"
    if "PMID" in article:
        d["pubmed_uid"] = article["PMID"]
        id_source = "pubmed"
        _id = article["PMID"]
        d["url"] = f"https://pubmed.ncbi.nlm.nih.gov/{_id}/"  

    identifiers = article.get("AID", [])
    d["doi"] = None
    for identifier in identifiers:
        if "[doi]" in identifier:
            d["doi"] = identifier.replace("[doi]", "").strip()
            break 

    d["abstract"] = article.get("AB", "Abstract wasn't found or could not be processed. If you think this is a mistake please contact support.")
    d['title'] = article.get('TI', 'Title missing, please contact citemed support!')
    
    if d['title'] == 'Title missing, please contact citemed support!':
        d['title'] = article.get('BTI', 'Title missing, please contact citemed support!')
        if isinstance(d["title"], list):
            d['title'] = " ".join(d["title"])

    d['publication_year'] = article.get('DP', "")
    
    if id_source is None:
        logger.debug(f'No IDs found for {d["title"]}!')
    else:
        try:
            d["citation"] = get_citation(id_source, _id)
        except Exception as error:
            logger.warning(f'Unable to get citation for {d["title"]} for the following error: {error}' )
    return d


if __name__ == "__main__":
    get_citation(Databases.pubmed, "20069275")
