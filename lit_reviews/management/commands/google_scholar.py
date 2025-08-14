
import requests

import json
from fuzzywuzzy import fuzz


#global searchId
import os
from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q

from lit_reviews.models import (
    LiteratureReviewSearchProposal,
    Article,
    ArticleReview,
    NCBIDatabase,
    LiteratureSearch, LiteratureReview, ClinicalLiteratureAppraisal,
)
import pandas

from lit_reviews.models import Article, ArticleReview

from lit_reviews.database_imports.google_scholar import *


### moved to database_imports

# steps for new citemed v2
if __name__ == '__main__':
    pass
    
    print("run parse text")


class Command(BaseCommand):
    help = 'Impots Google Scholar and Checks for Duplicates'

    def add_arguments(self, parser):
        #parser.add_argument('--terms', nargs='+', type=str)
        parser.add_argument('--reviewId', nargs='+', type=str)
        parser.add_argument('--yearsBack', nargs='+', type=str)

        # status = options['user_id'][0]

        pass

    def handle(self, *args, **options):

        lit_review_id = options['reviewId'][0]
        years_back = options['yearsBack'][0]

        #print(search_terms + " "  + filename)

        for filename in os.listdir('./manual_imports/{0}/scholar'.format(lit_review_id)):

            print("fname: " + filename)
            if filename.find(".csv") != -1 and filename.lower().find('exclude') == -1:
            
                search_terms = filename.replace(".csv", "").replace(".txt", "").replace("_", " ").replace("_STAR", "*")
                print("search terms: " + str(search_terms))

                parse_scholar('./manual_imports/{0}/scholar/{1}'.format(lit_review_id, filename) , search_terms, lit_review_id, years_back)


            elif filename.lower().find('exclude') != -1 and filename.find(".csv") != -1:
                add_excluded_searches('./manual_imports/{0}/scholar/{1}'.format(lit_review_id, filename), lit_review_id, years_back)

            else:
                print("Skipped file: {0}".format(filename))

# create LiteratureSearch object

# parse each returned article.  create Article  and passit's pubmed ID

# create Article (get or create )
 # Article.objects.get_or_create(**article_dict)
 
 # create ArticleReview obj 

