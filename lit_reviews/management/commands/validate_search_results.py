
import requests

import json


#global searchId
import os
from django.core.management.base import BaseCommand, CommandError

from lit_reviews.models import (
    LiteratureReviewSearchProposal,
    Article,
    ArticleReview,
    NCBIDatabase,
    LiteratureSearch, LiteratureReview, ClinicalLiteratureAppraisal,
)

from collections import Counter


def parse_text(cochrane_file, search_terms, lit_review_id):
    print(str(cochrane_file))
    cochrane_file =  str(cochrane_file)

    # create search object here
    print("get database obj and create search object")
    db = NCBIDatabase.objects.get(entrez_enum='cochrane')
    lit_review = LiteratureReview.objects.get(id=lit_review_id)
    lit_search = LiteratureSearch.objects.get_or_create(literature_review=lit_review, db=db, term=search_terms, years_back=10)[0]

    print("Lit search created: " + str(lit_search))
    print("Lit review found: " + str(lit_review))

    #result object to be inserted.
    #search id will be passed eventually.
    lines = []

    with open(cochrane_file, 'r', encoding="utf8") as f:
        lines = f.readlines()

    result = get_result()
    authors = []
    year = None

    for line in lines:
        #try:

        if line.find(":") != -1:
            row = line.split(":")

            if row[0] == "US":

                #if check_duplicate(searchId, result['articleTitle']):
                #    result["isDuplicate"] = True
                   
                result["citation"] = build_citation(authors, result["title"],
                                                year)
                print("citation built! Posting.. ")
                print(str(result))
                result['citation'] = result['citation'].replace("\n", "")
                
                insert_cochrane(result, lit_search)
                result = get_result()

                authors = []
            else:

                if row[0] == "AU":
                    authors.append(row[1])
                if row[0] == "AB":
                    if len(row) >= 3:
                       
                        result["abstract"] = row[1] + row[2]
                    else:
                        result["abstract"] = row[1]

                if row[0] == "TI":
                    result["title"] = row[1].strip()
                if row[0] == "YR":
                    year = row[1]
                if row[0] == "ID":
                    result["pubmed_uid"] = row[1].strip()


# steps for new citemed v2
if __name__ == '__main__':
    pass
    
    print("run parse text")


class Command(BaseCommand):
    help = 'Executes hourly pull data'

    def add_arguments(self, parser):
        parser.add_argument('--reviewId', nargs='+', type=str)

        # status = options['user_id'][0]

        pass

    def handle(self, *args, **options):

        print("Validating Search Protocoll ")
        review_id = options['reviewId'][0]
        proposals = LiteratureReviewSearchProposal.objects.filter(literature_review__id=review_id).order_by('term')

        #pubmed_proposals =  LiteratureReviewSearchProposal.objects.filter(literature_review__id=review_id, db__entrez_enum='pubmed').order_by('term')
        #pmc_proposals =     LiteratureReviewSearchProposal.objects.filter(literature_review__id=review_id, db__entrez_enum='pmc').order_by('term')


        searches = LiteratureSearch.objects.filter(literature_review__id=review_id)

        for search in searches:

            article_reviews = ArticleReview.objects.filter(search=search)

            proposal = LiteratureReviewSearchProposal.objects.get(term=search.term, literature_review__id=review_id)
           

                ##  we need to check a few things
                ##  1.  all terms on all databases

                ## 2.  result counts for all searches.


# create LiteratureSearch object

# parse each returned article.  create Article  and passit's pubmed ID

# create Article (get or create )
 # Article.objects.get_or_create(**article_dict)
 
 # create ArticleReview obj 

