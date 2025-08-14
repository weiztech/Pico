
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
    ExclusionReason,
    LiteratureSearch, LiteratureReview, ClinicalLiteratureAppraisal,
)
import pandas

from lit_reviews.report_builder.prisma import prisma


import csv



from lit_reviews.models import Article, ArticleReview




# steps for new citemed v2
if __name__ == '__main__':
    pass
    
    print("run parse text")


class Command(BaseCommand):
    help = 'Impots Google Scholar and Checks for Duplicates'

    def add_arguments(self, parser):
        #parser.add_argument('--terms', nargs='+', type=str)
        parser.add_argument('--reviewId', nargs='+', type=str)
        #parser.add_argument('--yearsBack', nargs='+', type=str)

        # status = options['user_id'][0]

        pass

    def handle(self, *args, **options):

        lit_review_id = options['reviewId'][0]
        output_path = "./review_output/{0}/".format(lit_review_id)

        #years_back = options['yearsBack'][0]

        prisma(output_path, int(lit_review_id))


# create LiteratureSearch object

# parse each returned article.  create Article  and passit's pubmed ID

# create Article (get or create )
 # Article.objects.get_or_create(**article_dict)
 
 # create ArticleReview obj 

