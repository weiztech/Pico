from django.core.management.base import BaseCommand
from lit_reviews.helpers.articles import remove_duplicate
from lit_reviews.models import *
from fuzzywuzzy import fuzz
import time
from django.db.models import Q

class Command(BaseCommand):
    help = 'Removes Duplicates for full project'

    def add_arguments(self, parser):
        parser.add_argument('--reviewId', nargs='*', type=int)

    def handle(self, *args, **options):

        if options['reviewId'][0] > 0:
            review_id = options['reviewId'][0]

            lit_review_id = review_id
            remove_duplicate(review_id)
            print("MANUAL CHECKING OF EMBASE AND INCLUDEDS")

            db = NCBIDatabase.objects.get(entrez_enum='embase')
            article_reviews = list(ArticleReview.objects.filter(search__literature_review_id=lit_review_id
                ).exclude(search__db=db).exclude(state='D').values_list('id', 'article__citation', 'article__title', 'article__abstract'))
    
            embase_article_reviews = list(ArticleReview.objects.filter(search__literature_review_id=lit_review_id, 
                        search__db__entrez_enum='embase' ).exclude( state='D').prefetch_related('article').values_list('id', 'article__citation', 'article__title', 'article__abstract'))
    

            #print(article_reviews)
            print("Article Reviews (Non Embase): {0} \n Embase Reviews: {1}".format(len(article_reviews), len(embase_article_reviews) ))
  
            dupes = []
            for embase_article_review in embase_article_reviews:
                for article_review in article_reviews:    
                    
                    #print("comparing {0} \n and {1}".format(embase_article_review, article_review))

                    #citation_fuzzy = fuzz.token_set_ratio(embase_article_review.article.citation, article_review.article.citation)
                    citation_fuzzy = fuzz.token_set_ratio(embase_article_review[1], article_review[1])

                   # abstract_fuzzy =  fuzz.token_set_ratio(embase_article_review.article.abstract, article_review.article.abstract)
                    
                    abstract_fuzzy = fuzz.token_set_ratio(embase_article_review[3], article_review[3])

                    title_fuzzy = fuzz.token_set_ratio(embase_article_review[2], article_review[2])
                    # ## to look for the default 'no citaiton found or abstract text' 
                    if article_review[3].strip().lower().find("citemed") != -1:
                        abstract_fuzzy = 0


                    #print("Processing Citation: {0} \n \n fuzzys: {1} {2}".format(citation, citation_fuzzy, abstract_fuzzy))

                    if citation_fuzzy > 85 and abstract_fuzzy > 85 and title_fuzzy >90:

                        print("""Embase: \n

                                AR ID: {4}
                               
                                Citation: {0} \n
                                Abstract: {1} \n
                                \n
                                ############################### \n \n
                                AR ID: {5}
                               
                                {2} \n
                                {3} \n \n \n


                            """.format(embase_article_review[1], 
                                embase_article_review[3],
                                 article_review[1], 
                                 article_review[3],
                                  embase_article_review[0], 
                                  article_review[0] ))
                        

                        embase_ar = ArticleReview.objects.get(id=embase_article_review[0])
                        ar = ArticleReview.objects.get(id=article_review[0])
                        print("Embase: State: {0}-{1}   Regular State: {2}-{3}".format(embase_ar.state, embase_ar.search.db, ar.state, ar.search.db))
                        #a = input('found dupe, process it? y/n')
                        #if a.lower() == 'y':

                        if embase_ar.state == 'I' and ar.state == 'I':

                            a = input('both articles are Included, what to do? {0} and {1}'.format(embase_ar.id, ar.id))

                        

                        elif embase_ar.state == 'U':
                            embase_ar.state = 'D'
                            embase_ar.save()
                            dupes.append(embase_ar.id)


                        elif ar.state == 'U':
                            ar.state = 'D'
                            ar.save()
                            dupes.append(ar.id)


                        elif embase_ar.state == 'E':

                            embase_ar.state = 'D'
                            embase_ar.save()
                            dupes.append(embase_ar.id)

                        elif ar.state == 'E':

                            ar.state = 'D'
                            ar.save()
                            dupes.append(ar.id)

                        # else:
                        #     print("Skipped")
                        #     time.sleep(1.5)



            raise Exception('stop!')









