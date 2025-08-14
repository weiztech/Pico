
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

import csv

class Command(BaseCommand):
    help = 'Rollback Manual'

    def add_arguments(self, parser):
        #parser.add_argument('--terms', nargs='+', type=str)
        parser.add_argument('--reviewId', nargs='+', type=str)
        #parser.add_argument('--db', nargs='+', type=str)

        # status = options['user_id'][0]

        pass

    def handle(self, *args, **options):

        #print(options['terms'])
        #search_terms = options['terms'][0]
        #filename = options['filename'][0]
        

        lit_review_id = options['reviewId'][0]
        #db_enum = options['reviewId'][0]


        #a = input('enter any key to continue, ctcl c to cancel')


        ars = ArticleReview.objects.filter(search__literature_review__id=lit_review_id,  state='I')

        field_names = ['Title', 'Citation', 'Retained and Included', 'Type (SP or SoTA']

        csvwriter = csv.writer(open('./review_output/{0}/included_titles_all.csv'.format(lit_review_id), 'w'))
        csvwriter.writerow(field_names)


        

        for item in ars:

            lit_app = ClinicalLiteratureAppraisal.objects.get(article_review=item)

            ## cleanup search terms that have stupid .txt in them.
            item.search.term = item.search.term.replace(".txt", "")
            item.search.save()

            try:

                search_proposal = LiteratureReviewSearchProposal.objects.filter(literature_review=lit_review_id, term=item.search.term,)[0]
    
            except Exception as e:
                print("could not find LitRevSearchProp for term {0}".format(item.search.term))

                #raise Exception('error')
            search_type = 'SoTA' if search_proposal.is_sota_term else 'Safety'

            csvwriter.writerow([str(item.article.title), str(item.article.citation), str(lit_app.included), search_type ] )

  