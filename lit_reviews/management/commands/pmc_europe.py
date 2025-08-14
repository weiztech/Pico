import pandas
import requests

import json

import sys
from pathlib import Path

from copy import deepcopy
import rispy

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


from lit_reviews.database_imports.pmc_europe import *
## moved to database_imports package



# steps for new citemed v2
if __name__ == '__main__':
    pass
    
    print("run parse text")


class Command(BaseCommand):
    help = 'Executes hourly pull data'

    def add_arguments(self, parser):
        #parser.add_argument('--terms', nargs='+', type=str)
        parser.add_argument('--reviewId', nargs='+', type=str)
        parser.add_argument('--yearsBack', nargs='+', type=str)

        # status = options['user_id'][0]

        pass

    def handle(self, *args, **options):

        #print(options['terms'])
        #search_terms = options['terms'][0]
        #filename = options['filename'][0]
        lit_review_id = options['reviewId'][0]
        years_back = options['yearsBack'][0]

        #print(search_terms + " "  + filename)

        for filename in os.listdir('./manual_imports/{0}/pmc_europe'.format(lit_review_id)):

            print("fname: " + filename)

            if filename.find(".ris") != -1 and filename.lower().find('exclude') == -1:

            
                search_terms = filename.replace("_STAR", "*").replace(".ris","")

                print("search terms: " + str(search_terms))

        #return True
                parse_text('./manual_imports/{0}/pmc_europe/{1}'.format(lit_review_id, filename) , search_terms, lit_review_id, years_back)

            elif filename.lower().find('exclude') != -1 and filename.find(".csv") != -1:

                # exclude file.  parse this differently.
                add_excluded_searches('./manual_imports/{0}/pmc_europe/{1}'.format(lit_review_id, filename), lit_review_id, years_back)




# create LiteratureSearch object

# parse each returned article.  create Article  and passit's pubmed ID

# create Article (get or create )
 # Article.objects.get_or_create(**article_dict)
 
 # create ArticleReview obj 

