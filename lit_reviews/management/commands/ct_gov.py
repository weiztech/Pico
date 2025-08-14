
import requests
import json
import pandas
import urllib.parse


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

from datetime import datetime, timedelta

from lit_reviews.database_imports.ct_gov import *


### moved to lit_reviews.database_imports.ct_gov






# steps for new citemed v2
if __name__ == '__main__':
    pass
    
    print("run parse text")


class Command(BaseCommand):
    help = 'Executes hourly pull data'

    def add_arguments(self, parser):
        #parser.add_argument('--terms', nargs='+', type=str)
        #parser.add_argument('--filename', nargs='+', type=str)
        parser.add_argument('--reviewId', nargs='+', type=str)
        parser.add_argument('--yearsBack', nargs='+', type=str)

        # status = options['user_id'][0]

        pass

    def handle(self, *args, **options):

        lit_review_id = options['reviewId'][0]
        years_back = options['yearsBack'][0]


        for filename in os.listdir('./manual_imports/{0}/ct_gov'.format(lit_review_id)):

            
            if filename.find(".csv") != -1 and filename.lower().find('exclude') == -1:

                print("fname: " + filename)
                search_terms = filename.replace(".csv", "").replace("_", " ").replace("_STAR", "*")
                print("search terms: " + str(search_terms))

            #a = input('wait')

                #print(options['terms'])
                #search_terms = options['terms'][0]
                #filename = options['filename'][0]

                url_prefix = "https://clinicaltrials.gov/ct2/results?"

                to_date = datetime.today()

                from_date = (to_date - timedelta(days=int(years_back) * 365)) .strftime('%m/%d/%Y')
                from_date = urllib.parse.quote(from_date, safe='')

                to_date = urllib.parse.quote(to_date.strftime('%m/%d/%Y'), safe='')

                serach_terms = urllib.parse.quote(search_terms, safe='')



                search_url = "cond=&term={0}&type=&rslt=&age_v=&age=1&age=2&gndr=&intr=&titles=&outc=&spons=&lead=&id=&cntry=&state=&city=&dist=&locn=&rsub=&strd_s=&strd_e=&prcd_s=&prcd_e=&sfpd_s=&sfpd_e=&rfpd_s={1}&rfpd_e={2}&lupd_s=&lupd_e=&sort=".format(search_terms, from_date, to_date)

                

                search_url = url_prefix + urllib.parse.quote(search_url)


                with open('./manual_imports/{0}/ct_gov/{1}'.format(lit_review_id, 'search_urls.txt'), 'a') as f:


                    f.write("{0}, {1} \n".format(search_terms, search_url))



                print(search_terms + " "  + filename)
                #return True
                parse_text('./manual_imports/{0}/ct_gov/{1}'.format(lit_review_id,filename) , search_terms, lit_review_id, years_back)

            elif filename.lower().find('exclude') != -1 and filename.find(".csv") != -1:
                add_excluded_searches('./manual_imports/{0}/ct_gov/{1}'.format(lit_review_id, filename), lit_review_id, years_back)

            else:
                print("Skipped file: {0}".format(filename))

# create LiteratureSearch object

# parse each returned article.  create Article  and passit's pubmed ID

# create Article (get or create )
 # Article.objects.get_or_create(**article_dict)
 
 # create ArticleReview obj 

