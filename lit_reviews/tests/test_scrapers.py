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
    SearchConfiguration,
    SearchParameter,
    AdverseEvent,
    AdverseRecall,
    AdverseEventReview,
    AdverseRecallReview,
)
from lit_reviews.database_imports import (
    pubmed_pmc,
    embase,
    cochrane,
    ct_gov,
    pmc_europe,
    maude,
    maude_recalls,
)
from lit_reviews.helpers.database import create_init_search_params_templates
from lit_reviews.helpers.reports import create_excel_file
from lit_reviews.report_builder.all_articles_reviews import generate_article_duplicates_content
from lit_reviews.tests.utils import TransactionTestCaseLiteratureReview
from lit_reviews.celery_tasks.scrapers import run_auto_search_task


class ScrapersTestCases(TransactionTestCaseLiteratureReview):

    def setUp(self):
        self.create_databases()
        self.create_literature_review(1)
        self.create_literature_review(2)
        create_init_search_params_templates()

    def test_pubmed(self):
        file_path = os.path.dirname(__file__)

        terms = [
            {
             "term": "('laparoscopy'/exp OR 'laparoscopy' OR 'pelvic endoscopy' OR 'peritoneoscopy')", 
             "start_date": "2022-12-29", 
             "end_date": "2022-12-30",
             "manual_file_path": file_path+"/files/scraper_results/pubmed_short_term.txt",
            },
            {
             "term": "('robot assisted surgery'/exp OR 'robot aided surgery' OR 'robot assisted surgery' OR 'robot surgery' OR 'robotic aided surgery' OR 'robotic surgery' OR 'robotic surgical procedure' OR 'robotic surgical procedures' OR 'robotically assisted surgery' OR 'robotic assisted laparoscopy'/exp) AND ('laparoscopy'/exp OR 'laparoscopy' OR 'pelvic endoscopy' OR 'peritoneoscopy') AND ('gynecologic surgery'/exp OR 'gynaecologic surgery' OR 'gynaecological operation' OR 'gynaecological surgery' OR 'gynaecology surgery' OR 'gynaecologic operation' OR 'gynecologic operation' OR 'gynaecologic surgery' OR 'gynecologic surgery' OR 'gynaecologic surgical procedure' OR 'gynecologic surgical procedure' OR 'gynecological operation' OR 'gynecological surgery' OR 'gynecology surgery' OR 'operative gynaecology' OR 'operative gynecology' OR 'urologic surgery'/exp OR 'genitourinary surgery' OR 'urogenital surgery' OR 'urogenital surgical procedures' OR 'urogenital tract surgery' OR 'urologic operation' OR 'urologic surgery' OR 'urologic surgical procedures' OR 'urological operation' OR 'urological surgery' OR 'general surgery'/exp OR 'general surgery' OR 'surgery, general') AND ((classicalarticle[Filter] OR clinicalstudy[Filter] OR clinicaltrial[Filter] OR comparativestudy[Filter] OR controlledclinicaltrial[Filter] OR correctedandrepublishedarticle[Filter] OR meta-analysis[Filter] OR observationalstudy[Filter] OR overall[Filter] OR preprint[Filter] OR randomizedcontrolledtrial[Filter] OR review[Filter] OR systematicreview[Filter]) AND (humans[Filter]) AND (2000/1/1:3000/12/12[pdat]) AND (english[Filter]) AND (allchild[Filter] OR allinfant[Filter] OR infant[Filter] OR preschoolchild[Filter] OR child[Filter] OR adolescent[Filter] OR youngadult[Filter]))", 
             "start_date": "2022-12-01", 
             "end_date": "2022-12-30",
            "manual_file_path": file_path+"/files/scraper_results/pubmed_long_term.txt",
            }
        ]

        for term_obj in terms:
            term = term_obj["term"]
            start_date = term_obj["start_date"]
            end_date = term_obj["end_date"]
            manual_file_path = term_obj["manual_file_path"]

            # set search dates  
            search_config1 = SearchConfiguration.objects.get(
                database=self.pubmed,
                literature_review=self.lit_review1,
            )
            search_config2 = SearchConfiguration.objects.get(
                database=self.pubmed,
                literature_review=self.lit_review2,
            )

            start_date_for_lit1 = SearchParameter.objects.get(
                search_config=search_config1, name="Start Date"
            )
            end_date_for_lit1 = SearchParameter.objects.get(
                search_config=search_config1, name="End Date"
            )
            start_date_for_lit1.value = start_date
            start_date_for_lit1.save()
            end_date_for_lit1.value = end_date
            end_date_for_lit1.save()
            
            start_date_for_lit2 = SearchParameter.objects.get(
                search_config=search_config2, name="Start Date"
            )
            end_date_for_lit2 = SearchParameter.objects.get(
                search_config=search_config2, name="End Date"
            )
            start_date_for_lit2.value = start_date
            start_date_for_lit2.save()
            end_date_for_lit2.value = end_date
            end_date_for_lit2.save()
                    
            # create the terms
            self.manual_search = LiteratureSearch.objects.create(
                literature_review=self.lit_review1,
                db=self.pubmed,
                term=term,
                years_back=1,
            )

            self.auto_search = LiteratureSearch.objects.create(
                literature_review=self.lit_review2,
                db=self.pubmed,
                term=term,
                years_back=1,
            )

            # Run manual search
            pubmed_pmc.parse_text(
                filepath=manual_file_path,
                search_term=self.manual_search.term,
                lit_review_id=self.lit_review1.id,
                entrez_enum="pubmed",
            )

            # Run auto search
            run_auto_search_task(self.lit_review2.id, self.auto_search.id)

            manual_results = ArticleReview.objects.filter(search=self.manual_search)
            auto_results = ArticleReview.objects.filter(search=self.auto_search)

            # search is completed successfully and there are results ?
            self.assertNotEqual(manual_results.count(), 0)
            self.assertNotEqual(auto_results.count(), 0) 

            # manual and auto search results count matches ?  
            self.assertEquals(manual_results.count(), auto_results.count())

            # same results were imported both for manual and auto searches
            for manual_article in manual_results:
                is_found = auto_results.filter(article__title=manual_article.article.title).exists()
                self.assertTrue(is_found)


    def test_cochrane(self):
        file_path = os.path.dirname(__file__)

        terms = [
            {
             "term": "Clamp OR hemostat AND “gastrointestinal occlusion”", 
             "start_date": "2021-01-01", 
             "end_date": "2022-01-01",
             "manual_file_path": file_path+"/files/scraper_results/cochrane_term.txt",
            }
        ]

        for term_obj in terms:
            term = term_obj["term"]
            start_date = term_obj["start_date"]
            end_date = term_obj["end_date"]
            manual_file_path = term_obj["manual_file_path"]

            # set search dates  
            search_config1 = SearchConfiguration.objects.get(
                database=self.cochrane,
                literature_review=self.lit_review1,
            )
            search_config2 = SearchConfiguration.objects.get(
                database=self.cochrane,
                literature_review=self.lit_review2,
            )

            start_date_for_lit1 = SearchParameter.objects.get(
                search_config=search_config1, name="Start Date"
            )
            end_date_for_lit1 = SearchParameter.objects.get(
                search_config=search_config1, name="End Date"
            )
            start_date_for_lit1.value = start_date
            start_date_for_lit1.save()
            end_date_for_lit1.value = end_date
            end_date_for_lit1.save()
            
            start_date_for_lit2 = SearchParameter.objects.get(
                search_config=search_config2, name="Start Date"
            )
            end_date_for_lit2 = SearchParameter.objects.get(
                search_config=search_config2, name="End Date"
            )
            start_date_for_lit2.value = start_date
            start_date_for_lit2.save()
            end_date_for_lit2.value = end_date
            end_date_for_lit2.save()
                    
            # create the terms
            self.manual_search = LiteratureSearch.objects.create(
                literature_review=self.lit_review1,
                db=self.cochrane,
                term=term,
                years_back=1,
            )

            self.auto_search = LiteratureSearch.objects.create(
                literature_review=self.lit_review2,
                db=self.cochrane,
                term=term,
                years_back=1,
            )

            # Run manual search
            cochrane.parse_text(
                cochrane_file=manual_file_path,
                search_term=self.manual_search.term,
                lit_review_id=self.lit_review1.id,
            )

            # Run auto search
            run_auto_search_task(self.lit_review2.id, self.auto_search.id)

            manual_results = ArticleReview.objects.filter(search=self.manual_search)
            auto_results = ArticleReview.objects.filter(search=self.auto_search)

            # search is completed successfully and there are results ?
            self.assertNotEqual(manual_results.count(), 0)
            self.assertNotEqual(auto_results.count(), 0) 

            # manual and auto search results count matches ?  
            self.assertEquals(manual_results.count(), auto_results.count())

            # same results were imported both for manual and auto searches
            for manual_article in manual_results:
                is_found = auto_results.filter(article__title=manual_article.article.title).exists()
                self.assertTrue(is_found)


    def test_clinical_trials(self):
        file_path = os.path.dirname(__file__)

        terms = [
            {
             "term": "Clamp OR hemostat AND “gastrointestinal occlusion”", 
             "start_date": "2021-01-01", 
             "end_date": "2022-01-01",
             "manual_file_path": file_path+"/files/scraper_results/clinical_long_term.csv",
            },
            {
             "term": "“Home Healthcare” AND cellular", 
             "start_date": "2021-01-01", 
             "end_date": "2022-01-01",
             "manual_file_path": file_path+"/files/scraper_results/clinical_short_term.csv",
            },
        ]

        for term_obj in terms:
            term = term_obj["term"]
            start_date = term_obj["start_date"]
            end_date = term_obj["end_date"]
            manual_file_path = term_obj["manual_file_path"]

            # set search dates  
            search_config1 = SearchConfiguration.objects.get(
                database=self.clinical,
                literature_review=self.lit_review1,
            )
            search_config2 = SearchConfiguration.objects.get(
                database=self.clinical,
                literature_review=self.lit_review2,
            )

            start_date_for_lit1 = SearchParameter.objects.get(
                search_config=search_config1, name="Start Date"
            )
            end_date_for_lit1 = SearchParameter.objects.get(
                search_config=search_config1, name="End Date"
            )
            start_date_for_lit1.value = start_date
            start_date_for_lit1.save()
            end_date_for_lit1.value = end_date
            end_date_for_lit1.save()
            
            start_date_for_lit2 = SearchParameter.objects.get(
                search_config=search_config2, name="Start Date"
            )
            end_date_for_lit2 = SearchParameter.objects.get(
                search_config=search_config2, name="End Date"
            )
            start_date_for_lit2.value = start_date
            start_date_for_lit2.save()
            end_date_for_lit2.value = end_date
            end_date_for_lit2.save()
                    
            # create the terms
            self.manual_search = LiteratureSearch.objects.create(
                literature_review=self.lit_review1,
                db=self.clinical,
                term=term,
                years_back=1,
            )

            self.auto_search = LiteratureSearch.objects.create(
                literature_review=self.lit_review2,
                db=self.clinical,
                term=term,
                years_back=1,
            )

            # Run manual search
            ct_gov.parse_text(
                ct_gov_file=manual_file_path,
                search_term=self.manual_search.term,
                lit_review_id=self.lit_review1.id,
            )

            # Run auto search
            run_auto_search_task(self.lit_review2.id, self.auto_search.id)

            manual_results = ArticleReview.objects.filter(search=self.manual_search)
            auto_results = ArticleReview.objects.filter(search=self.auto_search)

            # search is completed successfully and there are results ?
            self.assertNotEqual(manual_results.count(), 0)
            self.assertNotEqual(auto_results.count(), 0) 

            # manual and auto search results count matches ?  
            self.assertEquals(manual_results.count(), auto_results.count())

            # same results were imported both for manual and auto searches
            for manual_article in manual_results:
                is_found = auto_results.filter(article__title=manual_article.article.title).exists()
                self.assertTrue(is_found)


    def test_pubmed_central(self):
        file_path = os.path.dirname(__file__)

        terms = [
            {
             "term": "“rotator cuff repair”/exp OR “rotator cuff reconstruction” OR “rotator cuff repair” OR “shoulder cuff repair” OR “bankart repair”/exp OR “slap lesion repair” OR “biceps tenodesis”/exp OR “acromio-clavicular separation” OR “deltoid repair” OR “capsular shift” OR “capsulolabral reconstruction” OR “lateral stabilization” OR “medial stabilization” OR “achilles tendon repair”/exp OR “hallux valgus reconstruction” OR “mid-foot reconstruction” OR “capsule repair” OR “acetabular labrum reattachment” OR “capsular stabilization” OR “anterior shoulder instability” OR “capsulolabral repair”/exp OR “acromioclavicular separation repair” OR “lateral instability repair” OR “lateral instability reconstruction” OR “medial instability repair” OR “medial instability reconstruction” OR “midfoot reconstruction” OR “metatarsal ligament repair” OR “metatarsal ligament reconstruction” OR “tendon reconstruction” OR “bunionectomy”/exp OR “bunion surgery” OR “bunionectomy” OR “biceps tendon reattachment” OR “medial collateral ligament repair” OR “lateral collateral ligament repair” OR “ligament repair” OR “ulnar collateral ligament reconstruction” OR “radial collateral ligament reconstruction” OR “lateral epicondylitis repair” OR “extra capsular repair” OR “posterior oblique ligament repair” OR “patellar realignment” OR “tendon repair” OR “vastus medialis obliquousadvancement” OR “iliotibial band tenodesis” OR “degenerative rotator cuff tear” OR “• acute rotator cuff tear” OR “acute labral tear” AND ((“square” OR “answer” OR “revolution”) AND iconn OR ((“corkscrew pk ft” OR “corkscrew” OR “short peek pushlock” OR “short peek” OR “peek pushlock” OR “short pushlock” OR “peek swivelock” OR “swivelock”) AND “arthrex”) OR ((“bioraptor pk” OR “bioraptor”) AND (“smith and nephew” OR “smith & nephew” OR “smith&nephew”))) AND (“humans”[MeSH Terms] OR “humans”[All Fields])", 
             "start_date": "2022-01-01", 
             "end_date": "2024-12-31",
             "manual_file_path": file_path+"/files/scraper_results/pmc_long_term.txt",
            },
            {
             "term": "('laparoscopy'/exp OR 'laparoscopy' OR 'pelvic endoscopy' OR 'peritoneoscopy')", 
             "start_date": "2024-03-01", 
             "end_date": "2024-03-02", 
             "manual_file_path": file_path+"/files/scraper_results/pmc_short_term.txt",
            },
        ]

        for term_obj in terms:
            term = term_obj["term"]
            start_date = term_obj["start_date"]
            end_date = term_obj["end_date"]
            manual_file_path = term_obj["manual_file_path"]

            # set search dates  
            search_config1 = SearchConfiguration.objects.get(
                database=self.pmc,
                literature_review=self.lit_review1,
            )
            search_config2 = SearchConfiguration.objects.get(
                database=self.pmc,
                literature_review=self.lit_review2,
            )

            start_date_for_lit1 = SearchParameter.objects.get(
                search_config=search_config1, name="Start Date"
            )
            end_date_for_lit1 = SearchParameter.objects.get(
                search_config=search_config1, name="End Date"
            )
            start_date_for_lit1.value = start_date
            start_date_for_lit1.save()
            end_date_for_lit1.value = end_date
            end_date_for_lit1.save()
            
            start_date_for_lit2 = SearchParameter.objects.get(
                search_config=search_config2, name="Start Date"
            )
            end_date_for_lit2 = SearchParameter.objects.get(
                search_config=search_config2, name="End Date"
            )
            start_date_for_lit2.value = start_date
            start_date_for_lit2.save()
            end_date_for_lit2.value = end_date
            end_date_for_lit2.save()
                    
            # create the terms
            self.manual_search = LiteratureSearch.objects.create(
                literature_review=self.lit_review1,
                db=self.pmc,
                term=term,
                years_back=1,
            )

            self.auto_search = LiteratureSearch.objects.create(
                literature_review=self.lit_review2,
                db=self.pmc,
                term=term,
                years_back=1,
            )

            # Run manual search
            pubmed_pmc.parse_text(
                manual_file_path,
                search_term=self.manual_search.term,
                lit_review_id=self.lit_review1.id,
                entrez_enum="pmc"
            )

            # Run auto search
            run_auto_search_task(self.lit_review2.id, self.auto_search.id)

            manual_results = ArticleReview.objects.filter(search=self.manual_search)
            auto_results = ArticleReview.objects.filter(search=self.auto_search)

            # search is completed successfully and there are results ?
            self.assertNotEqual(manual_results.count(), 0)
            self.assertNotEqual(auto_results.count(), 0) 

            # manual and auto search results count matches ?  
            self.assertEquals(manual_results.count(), auto_results.count())

            # same results were imported both for manual and auto searches
            for manual_article in manual_results:
                is_found = auto_results.filter(article__title=manual_article.article.title).exists()
                self.assertTrue(is_found)


    def test_pmc_europe(self):
        file_path = os.path.dirname(__file__)

        terms = [
            {
             "term": "(“Thulio” OR “Thulio Performance Fiber” OR “Thulio 10x Reusable Light Guide” OR “SingleFlex” OR “SmartFlex” OR “HeatFlex” OR “GentleFlex” OR “laser fibre*” OR “laser fiber*” OR “light guide*” OR “laser fiber cable*” OR “laser fibre cable*” OR “laser*”) AND “Dornier”", 
             "start_date": "2023-01-01", 
             "end_date": "2023-01-31",
             "manual_file_path": file_path+"/files/scraper_results/pmc_europe_long_term.ris",
            },
            {
             "term": "\"ICG Fluorescence imaging\"", 
             "start_date": "2023-01-01", 
             "end_date": "2023-01-31",
             "manual_file_path": file_path+"/files/scraper_results/pmc_europe_short_term.ris",
            },
        ]

        for term_obj in terms:
            term = term_obj["term"]
            start_date = term_obj["start_date"]
            end_date = term_obj["end_date"]
            manual_file_path = term_obj["manual_file_path"]

            # set search dates  
            self.lit_review1.searchprotocol.lit_start_date_of_search = start_date
            self.lit_review1.searchprotocol.lit_date_of_search = end_date
            self.lit_review1.searchprotocol.save()

            self.lit_review2.searchprotocol.lit_start_date_of_search = start_date
            self.lit_review2.searchprotocol.lit_date_of_search = end_date
            self.lit_review2.searchprotocol.save()
                    
            # create the terms
            self.manual_search = LiteratureSearch.objects.create(
                literature_review=self.lit_review1,
                db=self.pmc_europe,
                term=term,
                years_back=1,
            )

            self.auto_search = LiteratureSearch.objects.create(
                literature_review=self.lit_review2,
                db=self.pmc_europe,
                term=term,
                years_back=1,
            )

            # Run manual search
            pmc_europe.parse_text(
                manual_file_path,
                search_terms=self.manual_search.term,
                lit_review_id=self.lit_review1.id,
            )

            # Run auto search
            run_auto_search_task(self.lit_review2.id, self.auto_search.id)

            manual_results = ArticleReview.objects.filter(search=self.manual_search)
            auto_results = ArticleReview.objects.filter(search=self.auto_search)

            # search is completed successfully and there are results ?
            self.assertNotEqual(manual_results.count(), 0)
            self.assertNotEqual(auto_results.count(), 0) 

            # manual and auto search results count matches ?
            self.assertEquals(manual_results.count(), auto_results.count())

            # same results were imported both for manual and auto searches
            for manual_article in manual_results:
                is_found = auto_results.filter(article__title=manual_article.article.title).exists()
                self.assertTrue(is_found)


    def test_fda_maude(self):
        file_path = os.path.dirname(__file__)

        terms = [
            {
             "term": "OTE", 
             "start_date": "2024-01-01", 
             "end_date": "2024-12-31",
             "manual_file_path": file_path+"/files/scraper_results/maude_term_OTE.csv",
            },
            {
             "term": "DQA", 
             "start_date": "2023-01-01", 
             "end_date": "2024-08-31",
             "manual_file_path": file_path+"/files/scraper_results/maude_term_DQA.csv",
            },
        ]

        for term_obj in terms:
            term = term_obj["term"]
            start_date = term_obj["start_date"]
            end_date = term_obj["end_date"]
            manual_file_path = term_obj["manual_file_path"]

            # set search dates  
            self.lit_review1.searchprotocol.ae_start_date_of_search = start_date
            self.lit_review1.searchprotocol.ae_date_of_search = end_date
            self.lit_review1.searchprotocol.save()

            self.lit_review2.searchprotocol.ae_start_date_of_search = start_date
            self.lit_review2.searchprotocol.ae_date_of_search = end_date
            self.lit_review2.searchprotocol.save()
                    
            # create the terms
            self.manual_search = LiteratureSearch.objects.create(
                literature_review=self.lit_review1,
                db=self.maude,
                term=term,
                years_back=1,
            )

            self.auto_search = LiteratureSearch.objects.create(
                literature_review=self.lit_review2,
                db=self.maude,
                term=term,
                years_back=1,
            )

            # Run manual search
            maude.parse_workbook(
                manual_file_path,
                search_term=self.manual_search.term,
                lit_review_id=self.lit_review1.id,
            )

            # Run auto search
            run_auto_search_task(self.lit_review2.id, self.auto_search.id)

            manual_results = AdverseEventReview.objects.filter(search=self.manual_search)
            auto_results = AdverseEventReview.objects.filter(search=self.auto_search)

            # search is completed successfully and there are results ?
            self.assertNotEqual(manual_results.count(), 0)
            self.assertNotEqual(auto_results.count(), 0) 
            
            # manual and auto search results count matches ?
            self.assertEquals(manual_results.count(), auto_results.count())

            # same results were imported both for manual and auto searches
            for manual_article in manual_results:
                is_found = auto_results.filter(ae__description=manual_article.ae.description).exists()
                self.assertTrue(is_found)


    def test_maude_recalls(self):
        file_path = os.path.dirname(__file__)

        terms = [
            {
             "term": "FLL", 
             "start_date": "2020-01-01", 
             "end_date": "2024-12-31",
             "manual_file_path": file_path+"/files/scraper_results/maude_recalls_term_FLL.csv",
            },
            {
             "term": "DWF", 
             "start_date": "2006-01-01", 
             "end_date": "2024-12-31",
             "manual_file_path": file_path+"/files/scraper_results/maude_recalls_term_DWF.csv",
            },
        ]

        for term_obj in terms:
            term = term_obj["term"]
            start_date = term_obj["start_date"]
            end_date = term_obj["end_date"]
            manual_file_path = term_obj["manual_file_path"]

            # set search dates  
            self.lit_review1.searchprotocol.ae_start_date_of_search = start_date
            self.lit_review1.searchprotocol.ae_date_of_search = end_date
            self.lit_review1.searchprotocol.save()

            self.lit_review2.searchprotocol.ae_start_date_of_search = start_date
            self.lit_review2.searchprotocol.ae_date_of_search = end_date
            self.lit_review2.searchprotocol.save()
                    
            # create the terms
            self.manual_search = LiteratureSearch.objects.create(
                literature_review=self.lit_review1,
                db=self.maude_recalls,
                term=term,
                years_back=1,
            )

            self.auto_search = LiteratureSearch.objects.create(
                literature_review=self.lit_review2,
                db=self.maude_recalls,
                term=term,
                years_back=1,
            )

            # Run manual search
            maude_recalls.parse_workbook(
                manual_file_path,
                search_term=self.manual_search.term,
                lit_review_id=self.lit_review1.id,
            )

            # Run auto search
            run_auto_search_task(self.lit_review2.id, self.auto_search.id)

            manual_results = AdverseRecallReview.objects.filter(search=self.manual_search)
            auto_results = AdverseRecallReview.objects.filter(search=self.auto_search)

            # search is completed successfully and there are results ?
            self.assertNotEqual(manual_results.count(), 0)
            self.assertNotEqual(auto_results.count(), 0) 
            
            # manual and auto search results count matches ?
            self.assertEquals(manual_results.count(), auto_results.count())

            # same results were imported both for manual and auto searches
            for manual_article in manual_results:
                is_found = auto_results.filter(ae__event_uid=manual_article.ae.event_uid).exists()
                self.assertTrue(is_found)


    def test_scholar(self):
        terms = [
            {
             "term": '"Ncircle" AND adverse AND safety', 
             "start_date": "2021-01-01", 
             "end_date": "2024-12-30",
            },
        ]

        for term_obj in terms:
            term = term_obj["term"]
            start_date = term_obj["start_date"]
            end_date = term_obj["end_date"]

            # set search dates  
            search_config1 = SearchConfiguration.objects.get(
                database=self.scholar,
                literature_review=self.lit_review1,
            )

            start_date_for_lit1 = SearchParameter.objects.get(
                search_config=search_config1, name="Start Date"
            )
            end_date_for_lit1 = SearchParameter.objects.get(
                search_config=search_config1, name="End Date"
            )
            start_date_for_lit1.value = start_date
            start_date_for_lit1.save()
            end_date_for_lit1.value = end_date
            end_date_for_lit1.save()

            # create the terms
            self.auto_search = LiteratureSearch.objects.create(
                literature_review=self.lit_review1,
                db=self.scholar,
                term=term,
                years_back=1,
            )

            # Run auto search
            run_auto_search_task(self.lit_review1.id, self.auto_search.id)
            auto_results = ArticleReview.objects.filter(search=self.auto_search)

            logger.info(f"{auto_results.count()} results were found for google scholar search")
            self.assertTrue(auto_results.count() > 0)