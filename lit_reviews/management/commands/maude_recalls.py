import json
import xlrd
import requests
import os
from django.core.management.base import BaseCommand, CommandError
from datetime import datetime
from lit_reviews.models import *


from lit_reviews.database_imports.maude_recalls import *



        # self.searchId = searchId
        # self.productCode = productCode

        # self.wb = xlrd.open_workbook(
        #     '/opt/api/' + str(filename))
        # self

        # self.parse_workbook()





class Command(BaseCommand):
    help = 'Executes hourly pull data'

    def add_arguments(self, parser):
        parser.add_argument('--reviewId', nargs='+', type=str)
        # parser.add_argument('--filename', nargs='+', type=str)

        # status = options['user_id'][0]

        pass

    def handle(self, *args, **options):

        review_id = options['reviewId'][0]

        for filename in os.listdir('./manual_imports/{0}/maude_recalls/'.format(review_id)):

            print("fname: " + filename)
            search_terms = filename.replace(".csv", "").replace("xls", "").replace("_", " ").replace("_STAR", "*")
            print("search terms: " + str(search_terms))
            #filename = filename.replace(".csv", ".xls")

        #a = input('wait')

            #print(options['terms'])
            #search_terms = options['terms'][0]
            #filename = options['filename'][0]
            print(search_terms + " "  + filename)
            #return True
            parse_workbook('./manual_imports/{0}/maude_recalls/{1}'.format(review_id, filename) , search_terms, review_id)
