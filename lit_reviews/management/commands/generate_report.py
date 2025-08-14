import json
import xlrd
import requests
import os
from django.core.management.base import BaseCommand, CommandError
from datetime import datetime, timedelta

from lit_reviews.models import *

from lit_reviews.tasks import build_report


from lit_reviews.report_builder.utils import validate_report
from lit_reviews.report_builder.cite_word import CiteWordDocBuilder, CiteProtocolBuilder
from lit_reviews.report_builder.appendices import (
    appendix_a,
    appendix_b,
    appendix_c,
    appendix_d,
    appendix_e,
    micro_deliverables

)
from django.db.models import Q

import csv


output_path = ""


class Command(BaseCommand):
    help = "Generates Report Document"

    def add_arguments(self, parser):
        # parser.add_argument('--terms', nargs='+', type=str)
        parser.add_argument("--reviewId", nargs="+", type=str)

        # status = options['user_id'][0]

        pass

    def handle(self, *args, **options):

        review_id = options["reviewId"][0]
        output_path = "./review_output/{0}/".format(review_id)


        print("TESTING CELERY TASK")
        build_report(review_id)

        raise Exception('after celery task')


        #print("Micro deliverables: ")
        #micro_deliverables(output_path, review_id)

        # print("Testing Protocol Generator")
        # protocol = CiteProtocolBuilder(review_id, output_path)

        # protocol.a5_adverse_databases()

        # print("SKIPPING VALIDATION FOR TESTING")
        validate_report(review_id)
        print("Validating Report is complete..")

        # print("SKIPPING APPENDIX A FOR TESTING")
        print("running appendix a")
        appendix_a(output_path, review_id)

        # print("SKIPPING APPENDIX b FOR TESTING")

        print("running appendix b")
        appendix_b(output_path, review_id, retained_and_included=False)
        appendix_b(output_path, review_id, retained_and_included=True)

        print("running appendix c...")
        appendix_c(output_path, review_id)
        appendix_c(output_path, review_id, retained_and_included=True)

        # appendix_c_writeups(output_path, review_id ) ### TODO****

        # a = input('stop')

        print("appendix d")
        appendix_d(output_path, review_id)

        #print("appendix e")
        #appendix_e(output_path, review_id)
