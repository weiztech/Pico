import os
import uuid
from fuzzywuzzy import fuzz

from backend.logger import logger
from django.test import TransactionTestCase
from lit_reviews.models import (
    ArticleReview, 
    LiteratureReview,
    Client,
    Device,
    Manufacturer,
    NCBIDatabase,
    LiteratureSearch,
)
from lit_reviews.database_imports import (
    pubmed_pmc,
    embase,
)
from lit_reviews.helpers.articles import remove_duplicate, get_unclassified_and_duplicate_for_article
from lit_reviews.helpers.reports import create_excel_file
from lit_reviews.report_builder.all_articles_reviews import generate_article_duplicates_content

# 1. Check all duplicates are spotted and marked as duplicate
# 2. Check for each duplicate article, there is only one similar article marked as Unclassified
# And All others are marked as duplicate 

class ArticlesTestCases(TransactionTestCase):

    def setUp(self):
        self.manufacturer = Manufacturer.objects.create(name="Manufacturer 01")
        self.device = Device.objects.create(
            name="Device 01",
            manufacturer=self.manufacturer,
            classification="III",
            markets="US",
        )
        self.client = Client.objects.create(
            name="Client 01",
            short_name="Client 01",
            long_name="Client 01",
            full_address_string="Fake Address",
        )
        self.lit_review = LiteratureReview.objects.create(
            device=self.device,
            client=self.client,
        )
        self.protocol = self.lit_review.searchprotocol

        self.pubmed = NCBIDatabase.objects.create(
            name="Pubmed",
            entrez_enum="pubmed",
        )
        self.embase = NCBIDatabase.objects.create(
            name="Embase",
            entrez_enum="embase",
        )
        self.cochrane = NCBIDatabase.objects.create(
            name="Cochrane",
            entrez_enum="cochrane",
        )
        self.pmc = NCBIDatabase.objects.create(
            name="PubMed Central",
            entrez_enum="pmc",
        )

        self.protocol.lit_searches_databases_to_search.add(self.pubmed)
        self.protocol.lit_searches_databases_to_search.add(self.embase)
        self.protocol.lit_searches_databases_to_search.add(self.cochrane)

        self.pubmed_term01 = LiteratureSearch.objects.create(
            literature_review=self.lit_review,
            db=self.pubmed,
            term="term 01",
            years_back=1,
        )

        self.embase_term01 = LiteratureSearch.objects.create(
            literature_review=self.lit_review,
            db=self.embase,
            term="term 01",
            years_back=1,
        )

        self.cochrane_term01 = LiteratureSearch.objects.create(
            literature_review=self.lit_review,
            db=self.cochrane,
            term="term 01",
            years_back=1,
        )

        file_path = os.path.dirname(__file__)
        # upload pubmed
        pubmed_pmc.parse_text(
            filepath=file_path+"/files/pubmed_test.txt",
            search_term="term 01",
            lit_review_id=self.lit_review.id,
            expected_result_count=1,
            entrez_enum="pubmed",
        )

        embase.parse_text(
            embase_file=file_path+"/files/embase_test.ris",
            search_term="term 01",
            lit_review_id=self.lit_review.id,
        )

    def __upload_searches(self, search_term):
        self.embase_scath = LiteratureSearch.objects.create(
            literature_review=self.lit_review,
            db=self.embase,
            term=search_term,
            years_back=1,
        )

        self.pmc_scath = LiteratureSearch.objects.create(
            literature_review=self.lit_review,
            db=self.pmc,
            term=search_term,
            years_back=1,
        )

        self.pubmed_scath = LiteratureSearch.objects.create(
            literature_review=self.lit_review,
            db=self.pubmed,
            term=search_term,
            years_back=1,
        )

        file_path = os.path.dirname(__file__)

        # upload pubmed
        pubmed_pmc.parse_text(
            filepath=file_path+"/files/pubmed_scath.txt",
            search_term=search_term,
            lit_review_id=self.lit_review.id,
            entrez_enum="pubmed",
        )

        pubmed_pmc.parse_text(
            filepath=file_path+"/files/pmc_scath.txt",
            search_term=search_term,
            lit_review_id=self.lit_review.id,
            entrez_enum="pmc",
        )

        embase.parse_text(
            embase_file=file_path+"/files/embase_scath.ris",
            search_term=search_term,
            lit_review_id=self.lit_review.id,
        )

    def test_deduplcation_script_working_properly(self):
        """
        Check: 
        1. All duplicates are spotted and marked as duplicate.
        2. In a set of similar articles there should be only one article marked Unclassified.
        3. In the same set of similar articles the rest should be marked as duplicate.
        """
        self.assertEquals(self.lit_review.id, 1)
        self.assertTrue(ArticleReview.objects.filter(search__literature_review=self.lit_review).count() > 0)
        self.assertEquals(ArticleReview.objects.filter(state="D").count(), 0)

        # Run deduplication Script 
        remove_duplicate(self.lit_review.id)
        logger.info("Number of duplicates: " + str(ArticleReview.objects.filter(state="D").count()))
        self.assertTrue(ArticleReview.objects.filter(state="D").count() > 0)

        # For each duplicate article there should be one unclasified article the rest should be marked as duplicate.
        # in the below for each article we get all the similar articles than we have to check that:
        # 1. There should be only 1 unclasified article in the similar articles Set.
        # 2. If the similar articles length is greater than 1 than the number of duplicates should be (length of set - 1). 
        # 01 unclasified the rest should be marked as duplicate.
        for review in ArticleReview.objects.all():
            # if you want to treat each section as a seperate test
            with self.subTest(msg='Check dups for specific article'):
                article_dups_plus_original, unclassified, duplicated = get_unclassified_and_duplicate_for_article(review, ArticleReview.objects.all())
                
                # Below logs are more for debuggging purposes
                logger.debug(f"Number of duplicates including original for {review.article.title} is {len(article_dups_plus_original)}")
                # logger.debug(f"Number of duplicates for {review.article.title} is {len(duplicated)}")
                # for r in article_dups_plus_original:
                #     logger.debug(f"State for article id {r.article.pubmed_uid} titled {r.article.title} is {r.state}")
                
                self.assertEqual(len(unclassified), 1)
                if len(duplicated):
                    self.assertEqual(len(duplicated), len(article_dups_plus_original) - 1)
                else:
                    self.assertEqual(len(article_dups_plus_original), 1)
        
        
        # Mimik user upload a new search terms results files
        self.__upload_searches("scath")

        # Run deduplication Script 
        remove_duplicate(self.lit_review.id)

        for review in ArticleReview.objects.all():
            with self.subTest(msg='Check dups for specific article'):
                article_dups_plus_original, unclassified, duplicated = get_unclassified_and_duplicate_for_article(review, ArticleReview.objects.all())
                logger.debug(f"Number of duplicates including original for {review.article.title} is {len(article_dups_plus_original)}")
                
                self.assertEqual(len(unclassified), 1)
                if len(duplicated):
                    self.assertEqual(len(duplicated), len(article_dups_plus_original) - 1)
                else:
                    self.assertEqual(len(article_dups_plus_original), 1)

        articles_excel_list = generate_article_duplicates_content()
        # generate excel report 
        document_name_csv = "duplicates.csv"
        document_name_excel = "duplicates.xlsx"
        create_excel_file(1, 1, document_name_csv, document_name_excel, articles_excel_list)