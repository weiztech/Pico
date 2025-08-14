import pandas
import requests

import json

import sys
from pathlib import Path


from Bio import Medline

#global searchId
import os
from django.core.management.base import BaseCommand, CommandError

from lit_reviews.pmc_api import medline_json_to_citemed_article

from lit_reviews.models import (
    LiteratureReviewSearchProposal,
    Article,
    ArticleReview,
    NCBIDatabase,
    LiteratureSearch, LiteratureReview, ClinicalLiteratureAppraisal,
)

from lit_reviews.database_imports.pubmed_pmc import *



### pubmed pmc moved to database imports


# steps for new citemed v2
if __name__ == '__main__':
    pass
    
    

class Command(BaseCommand):
    help = 'Import Pubmed or PMC files directly:  pubmed or pmc '

    def add_arguments(self, parser):
        #parser.add_argument('--terms', nargs='+', type=str)
        parser.add_argument('--reviewId', nargs='+', type=str)
        parser.add_argument('--yearsBack', nargs='+', type=str)
        parser.add_argument('--db', nargs='+', type=str)

        # status = options['user_id'][0]

        pass

    def handle(self, *args, **options):

        #print(options['terms'])
        #search_terms = options['terms'][0]
        #filename = options['filename'][0]
        lit_review_id = options['reviewId'][0]
        years_back = options['yearsBack'][0]

        db = options['db'][0]

        #print(search_terms + " "  + filename)

        for filename in os.listdir('./manual_imports/{0}/{1}'.format(lit_review_id, db)):

            print("fname: " + filename)

            if filename.find(".txt") != -1 and filename.lower().find('exclude') == -1:

            
                search_terms = filename.replace("_STAR", "*").replace(".txt","")

                print("search terms: " + str(search_terms))

        #return True
                parse_text('./manual_imports/{0}/{2}/{1}'.format(lit_review_id, filename, db) , search_terms, lit_review_id, years_back, db)

            elif filename.lower().find('exclude') != -1 and filename.find(".csv") != -1:

                # exclude file.  parse this differently.
                add_excluded_searches('./manual_imports/{0}/{2}/{1}'.format(lit_review_id, filename, db), lit_review_id, years_back, db)




# create LiteratureSearch object

# parse each returned article.  create Article  and passit's pubmed ID

# create Article (get or create )
 # Article.objects.get_or_create(**article_dict)
 
 # create ArticleReview obj 

