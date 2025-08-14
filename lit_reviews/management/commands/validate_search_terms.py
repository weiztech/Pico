
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

        terms_from_app = []
        terms_from_app_pmc = []
        terms_from_app_pubmed = []

        terms_from_input = []


        for item in proposals:
            #print(item.db.entrez_enum)
            terms_from_app.append(item.term.strip().lower())

            if item.db.entrez_enum == 'pmc':
                terms_from_app_pmc.append(item.term.strip().lower())

            elif item.db.entrez_enum == 'pubmed':
                terms_from_app_pubmed.append(item.term.strip().lower())

        # check all import terms have match.
        input_with_match = []
        input_no_match = []

        app_with_match = []
        app_no_match = []

        try:
            with open('./manual_imports/{0}/terms_input.txt'.format(review_id), 'r') as f:
                input_terms = f.readlines()
                for term in input_terms:
                    term = term.strip().lower()
                    terms_from_input.append(term)

            # now check inputs.
            for term in terms_from_input:
                if term in terms_from_app:
                    input_with_match.append(term)
                else:
                    input_no_match.append(term)


            for term in terms_from_app:
                if term in terms_from_input:
                    app_with_match.append(term)
                else:
                    app_no_match.append(term)


        except Exception as e:
            print("exception processing term input. Skipping..." + str(e))

        print("writing search APP search terms to output file...")

        with open('./review_output/{0}/terms_output_{0}.txt'.format(review_id), 'w') as out:
            out.write("Terms FROM App Search Protocol: \n")

            uniques = []
            for item in proposals:
                out.write(item.term + "\n")
                if item.term not in uniques:
                    uniques.append(item.term)
            out.write("UNIQUE TERMS BELOW: \n")

            for item in uniques:
                out.write(item + "\n")


            ## maybe could write out the other protocol fields here too? 


        print("Checking pubmed + pmc term counts are equal...")
        counter = Counter(terms_from_app)
        for item in counter.keys():
            if counter[item] != 2:
                print("Missing pair found for term: " + item)

        print("checking for no duplicates on PMC and Pubmed")
        print("PMC Duplicates...")
        pmc_counter = Counter(terms_from_app_pmc)
        for item in pmc_counter.keys():
            if pmc_counter[item] != 1:
                print("duplicate found for pmc term: " + item)
        print("...Complete!")

        print("Pubmed Duplicates...")

        pubmed_counter = Counter(terms_from_app_pubmed)
        for item in pubmed_counter.keys():
            if pubmed_counter[item] != 1:
                print("duplicate found for pubmed term: " + item)
        print("...Complete!")



        print("VALIDATION RESULTS:" )
        print("Terms in APP: " + str(len(terms_from_app)))
        print("Pubmed Terms: {0}".format(len(terms_from_app_pubmed)))
        print("PMC Terms: {0}".format(len(terms_from_app_pmc)))
        print("Terms in Manual Import: " + str(len(terms_from_input)))
        print("Input Terms with NO MATCH (in input, not in APP): " + str(len(input_no_match)))
        print(str(input_no_match))
        print("APP Terms with no MATCH (in APP, not in input file:{0} ".format(len(app_no_match)) )
        print(str(app_no_match))



# create LiteratureSearch object

# parse each returned article.  create Article  and passit's pubmed ID

# create Article (get or create )
 # Article.objects.get_or_create(**article_dict)
 
 # create ArticleReview obj 

