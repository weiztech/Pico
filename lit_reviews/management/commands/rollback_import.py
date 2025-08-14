
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



if __name__ == '__main__':
    pass
    
    print("run parse text")


class Command(BaseCommand):
    help = 'Rollback Manual'

    def add_arguments(self, parser):
        #parser.add_argument('--terms', nargs='+', type=str)
        parser.add_argument('--reviewId', nargs='+', type=str)
        parser.add_argument('--db', nargs='+', type=str)

        # status = options['user_id'][0]

        pass

    def handle(self, *args, **options):

        #print(options['terms'])
        #search_terms = options['terms'][0]
        #filename = options['filename'][0]
        

        lit_review_id = options['reviewId'][0]
        db = options['db'][0]

        print("Rolling back (deleting) all terms for review id: {0},  database: {1}".format(lit_review_id, db))

        a = input('enter any key to continue, ctcl c to cancel')


        ars = ArticleReview.objects.filter(search__literature_review__id=lit_review_id, search__db__entrez_enum=db)

        print("{0} Article Reviews ".format(len(ars)))

        for a in ars:
            a.delete()

        searches = LiteratureSearch.objects.filter(literature_review__id=lit_review_id, db__entrez_enum=db)

        print("{0} Searches found: ".format(len(searches)))

        for s in searches:
            s.delete()
        print("completed!")
        