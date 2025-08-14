
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


import csv

from lit_reviews.tasks import build_protocol, build_report

from lit_reviews.models import Article, ArticleReview


def check_duplicates(citation, lit_review_id):
    
    ## get all article reviews for the project
    
    
   # article_reviews = ArticleReview.objects.filter().prefetch_related('article')
    citation = str(citation)
    
    
    article_reviews = ArticleReview.objects.filter(search__literature_review__id=lit_review_id) \
                                                            .prefetch_related('article')

    print("article reviews found: {0}".format(len(article_reviews)))    
    dupes = []
    for article_review in article_reviews:

                
        citation_fuzzy = fuzz.token_set_ratio(article_review.article.citation, citation)
        #abstract_fuzzy =  fuzz.token_set_ratio(article_review.article.abstract, abstract)
        
        # if abstract.strip().lower() == 'no link':
        #     abstract_fuzzy = 0


        #print("Processing Citation: {0} \n \n fuzzys: {1} ".format(citation, citation_fuzzy))

        if citation_fuzzy > 65:
            dupes.append(
                {
                    'imported_citation': citation,
                   
                    'cite_citation': article_review.article.citation,
                    'citation_fuzzy': citation_fuzzy,
                    
                    'cite_status': article_review.state
                }
            )

    return dupes




def crosscheck(filename=None, lit_review_id=None):
    
    crosscheck_csv = pandas.read_csv(filename, delimiter=',')
    
    
    output_rows = []
    
   
    for index, row in crosscheck_csv.iterrows():
        dupes = []
        duplicate_selected = False
        #print("processing row " + str(row['Citation']))
        print("parsing row# " + str(index))

        potential_dupes = check_duplicates(row['Citation'], lit_review_id)
        
        if len(potential_dupes) > 0:
            
            for dupe in potential_dupes:
                
                # print("""Potentical Duplicate Found! \n
                #         Crosscheck Citation: \n
                #         {0} \n \n
                        
                #         CiteMed System Citation: \n
                #         {1}  \n \n
                        
                #         {2} - 
                #         Is Valid Duplicate? \n
                        
                #         y for yes \n
                #         n for no \n
                #         \n \n 
                
                #     """.format(dupe['scholar_citation'], dupe['cite_citation'], dupe['citation_fuzzy'] ))
                
               
                    #response = input('Enter:  ')
                    #is_dupe = True if response.lower() == 'y' else False

                is_dupe = True

                if is_dupe:
                    print("Duplicate selected! Create it now")

                    with open('./review_output/{0}/matches.txt'.format(lit_review_id), 'a') as csvfile:

                        writer = csv.DictWriter(csvfile, delimiter=',', fieldnames=list(dupe.keys()))

                        writer.writerow(dupe)

                       

                    duplicate_selected = True

                    break

                else:
                    continue

            if duplicate_selected:
                pass
                #a = input('duplicate was chosen, so conitnue on')
            else:
                pass
                #a = input('no dupes chosen, so create the final Article Review ' )

                # article =  Article(title=row['Title'], abstract=row['Abstract'],
                #                    citation=row['Citation_MLA'] )
                # article.save()
                # article_review = ArticleReview(search=search, article=article, state='U')
                # article_review.save()
                
        else:

        # no dupes to review, add it!

            pass
        
            #a = input('added article (no dupes found)' + str(article_review.id))  



## hans migration.
## algo
def hans():

    vigilance_report = LiteratureReview.objects.get(id=21)
    litr = LiteratureReview.objects.get(id=19)


    # 1 query all included articles in vigilance report search  

    vig_included = ClinicalLiteratureAppraisal.objects.filter(article_review__state='I', article_review__search__literature_review=vigilance_report)

    searches = vig_included.values_list('article_review__search').distinct()

    print("searches for vig_included {0}".format(searches))
    print("Vigilance appraisal objs {0}".format(vig_included))
    # a = input('wait')

    # for each of those, build a list of search terms + database 
    # make sure the dates are valid (article wasn't outside of the LitR search period)

    # for each LiteratureSearch in the list

    cas_added = 0

    for search in searches:

        search = LiteratureSearch.objects.get(id=search[0])
        article_reviews = ArticleReview.objects.filter(search=search)
        ## check doesn't already exist in litr 
        existing_search = LiteratureSearch.objects.filter(literature_review=litr, db=search.db, term = search.term)
        if len(existing_search) > 0:
            print("Need to skip, search exists {0} - {1}".format(search, existing_search))

        else:
            print("copying over search {0} for term: {1} db: {2}".format(search, search.term, search.db))
        ## then copy over LiteratureSearch object to LITR proejct

            new_search_litr = search
            new_search_litr.id = None 
           
            new_search_litr.literature_review = litr 
            new_search_litr.save()


            with open('hans_searches_created_19.txt', 'a') as w:

                w.write("{0} \n".format(new_search_litr.id))



            for ar in article_reviews:
                print("ar id: {0}".format(ar.id))
                ar_id = ar.id 


                new_ar = ar  
                new_ar.id = None 
                
                new_ar.search = new_search_litr
                new_ar.save() 

                if ar.state == 'I':
                    print("Gettign appraisal for ar id: {1} article {0}".format(ar.article.title, ar.id))
                    try:

                        clin_appr = ClinicalLiteratureAppraisal.objects.get(article_review__id=ar_id )
                        print("found I state so get the ClinAppr to copy over as well...")
                        new_clin_appr = clin_appr 
                        new_clin_appr.id = None 
                        
                        new_clin_appr.article_review = new_ar
                        new_clin_appr.save() 

                        cas_added +=1 
                    except Exception as e:
                        pass

    print("cas added " + str(cas_added))

        ## copy over every ArticleReview and Article(happens by default?)  to LITR proje
        ## and ClinicalLiteratureAppraisal 




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
        #years_back = options['yearsBack'][0]

        hans()

        # build_report.delay(lit_review_id)
        #build_protocol.delay(lit_review_id)





        # print("lit review id : " + str(lit_review_id))

        # #print(search_terms + " "  + filename)

        # for filename in os.listdir('./manual_imports/{0}/'.format(lit_review_id)):

        #     print("fname: " + filename)
        #     if filename.find("crosscheck") != -1 and filename.lower().find('exclude') == -1:
            
        #         #search_terms = filename.replace(".csv", "").replace(".txt", "").replace("_", " ").replace("_STAR", "*")
        #         #print("search terms: " + str(search_terms))
        #         print("running cross check for " + str(filename))

        #         crosscheck('./manual_imports/{0}/{1}'.format(lit_review_id, filename), lit_review_id)

        #         #parse_scholar('./manual_imports/{0}/scholar/{1}'.format(lit_review_id, filename) , search_terms, lit_review_id, years_back)


        #     else:
        #         print("Skipped file: {0}".format(filename))

# create LiteratureSearch object

# parse each returned article.  create Article  and passit's pubmed ID

# create Article (get or create )
 # Article.objects.get_or_create(**article_dict)
 
 # create ArticleReview obj 

