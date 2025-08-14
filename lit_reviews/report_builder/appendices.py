import json
import xlrd
import requests
import os
from django.core.management.base import BaseCommand, CommandError
from datetime import datetime, timedelta, date

from lit_reviews.models import *
from lit_reviews.helpers.articles import remove_ae_duplicates

from lit_reviews.report_builder.utils import validate_report, set_unknowns, get_grade_score, get_db_list, clear_special_characters
from lit_reviews.report_builder.cite_word import CiteWordDocBuilder, CiteProtocolBuilder
from lit_reviews.report_builder.appendix_c_tables import *
from lit_reviews.report_builder.appendix_b_tables import *
from lit_reviews.report_builder.appendix_e_tables import *
from lit_reviews.report_builder.protocol_context_builder import get_db_info
from lit_reviews.report_builder.vigilance_tables import (
        vig_annual_maude_counts_by_term,
        vig_db_monthly_summary_table,
        ae_counts_by_search_and_year,
        get_ae_years,
    )
from django.db.models import Q
from lit_reviews.helpers.articles import get_clinical_appraisal_status_report
from backend.logger import logger

import csv


output_path = ""

def appendix_a(lit_review_id=1, sota=False):
    pass
    """
    Search Table and Summaries of Each Term and Database

    First show search information
    Database

    List of terms searched + their IDs

    Table Following Columns:
    Search ID,  Publications Yielded,  
    Duplicate Results, Retained for Eval,
    Excluded, Included  

    """
    # if not os.path.exists(output_path + "appendix_a"):
    #     os.makedirs(output_path + "appendix_a")

    table_col_names = [
        "Search Term",
        "Search Performed Date",
        "Publications Yielded",
        "Duplicate Results",
        "Included",
        "Excluded",
    ]

    literature_searches_all = LiteratureSearch.objects.filter(
        literature_review__id=lit_review_id
    ).exclude(db__is_ae=True).exclude(db__is_recall=True)

    dbs = list(
        set(
            LiteratureSearch.objects.filter(
                literature_review__id=lit_review_id
            ).exclude(db__is_ae=True).exclude(db__is_recall=True).order_by('db__name').values_list("db")
        )
    )
    dbs_list = []
    for tup in dbs:
        dbs_list.append(tup[0])

    appendix_a_context = []

    table_index = 0
    for db in dbs_list:
        
        lit_review = LiteratureReview.objects.get(id=lit_review_id)
        db = NCBIDatabase.objects.get(name=db)

        db_protocol_context = get_db_info(lit_review, db)
        db_context = {
            "table_index": table_index,
            "protocol": db_protocol_context,
            "results_summary_table":{
            "headers": ["Search Term", "Publications Yielded","Duplicate Results", "Included", "Excluded"],
            "rows": []
            }
        }

        literature_searches = LiteratureSearch.objects.filter(literature_review__id=lit_review_id, db__name=db.name).order_by("term")
        
        if sota:
            literature_searches = literature_searches.filter(
                Q(Q(is_sota_term=True) | Q(literaturereviewsearchproposal__is_sota_term=True))
            )
        else:
            literature_searches = literature_searches.exclude(
                Q(Q(is_sota_term=True) | Q(literaturereviewsearchproposal__is_sota_term=True))
            )

        for row_id, lit_search in enumerate(literature_searches):
            # calculate, PUbs Yielded, duplicates,  retained, included excluded

            pubs_yielded = len(
                ArticleReview.objects.filter(search__id=lit_search.id)
            )

            if pubs_yielded == 0:
                # then either a real 0 or too many  so get the search protocol
                try:

                    search_prop = LiteratureReviewSearchProposal.objects.get(
                        literature_review__id=lit_review_id,
                        term=lit_search.term,
                        db=lit_search.db,
                    )
                    #pubs_yielded = search_prop.result_count  ETHAN TEST 5.20.22
                    pubs_yielded = lit_search.result_count

                except Exception as e:
                    logger.debug("couldn't find Proposal, check search count itself")
                    if lit_search.result_count is not None:
                        pubs_yielded = lit_search.result_count
                    else:
                        error_msg = """The following search term '{0}' for '{1}' database \
                            is missing results please make sure all your searches are run and completed.
                        """.format(lit_search.term, lit_search.db.entrez_enum )
                        logger.error(str(error_msg))
                        raise Exception(error_msg)

            elif pubs_yielded == -1:
                pubs_yielded == "None"

            duplicates = len(
                ArticleReview.objects.filter(
                    search__id=lit_search.id, state="D"
                )
            )
            included = len(
                ArticleReview.objects.filter(
                    search__id=lit_search.id, state="I"
                )
            )
            excluded = len(
                ArticleReview.objects.filter(
                    search__id=lit_search.id, state="E"
                )
            )
            unclassified = len(
                ArticleReview.objects.filter(
                    search__id=lit_search.id, state="U"
                )
            )

            articles_reviews_search = len(
                ArticleReview.objects.filter(search__id=lit_search.id)
            )
            if  lit_search.result_count is not None and articles_reviews_search == 0 and lit_search.result_count > 0:
                not_imported = pubs_yielded - (duplicates + included + excluded)
            else:
                not_imported = 0

            script_time = lit_search.script_time.strftime("%m/%d/%Y") if lit_search.script_time else "NA"
            row = {
                "id": row_id +1,
                "Search Term": lit_search.term,
                "Search Performed Date": str(script_time),
                "Publications Yielded": str(pubs_yielded),
                "Duplicate Results": str(duplicates),
                "Included": str(included),
                "Excluded": str(excluded),
                "Unclassified": str(unclassified),
                "Not Imported":str(not_imported),
            }

            db_context['results_summary_table']['rows'].append(row)
            row_id += 1
        #print("db context to append {0}".format(db_context))
        if len(db_context['results_summary_table']['rows']) > 0:
            table_index += 1
            db_context['table_index'] = table_index

        appendix_a_context.append(db_context)

    
    return appendix_a_context 
    #return cite_word.save_file("appendix_a.docx")





def appendix_b(lit_review_id=1, retained_and_included=None):
    pass
    """ 
    Table of searchesults for all searches + dbs
    - organize by term + db

    Before Table:  Show Database + Terms

    Table Columns
    Search ID,  Citation,  Retained, Included,  Justification 

    If justification is > 200 chars, we can move it to the end.

    After Table: Show any of the long form justifications

    """
    #if not os.path.exists(output_path + "appendix_b"):
    #    os.makedirs(output_path + "appendix_b")

    #section_name = "Retained and Included Citations" 

    #cite_word = CiteWordDocBuilder(output_path + "appendix_b/")
    #cite_word.add_hx("Appendix B - {0}".format(section_name), "CiteH1")


    dbs_list = appendix_b_get_dbs(lit_review_id)

    appendix_b_context  = []

    table_index = 0
    for db in dbs_list:

        database_context = {
            "table_index": table_index,
            "protocol": {}, ## need to get this.
            "results_table": {
                "headers":[],
                # "rows": None
                "rows": []

            }, ## about to generat

        }


        db_obj = NCBIDatabase.objects.get(name=db)
        lit_review = LiteratureReview.objects.get(id=lit_review_id)

        db_protocol_context = get_db_info(lit_review, db_obj)
        database_context['protocol'] = db_protocol_context 
        

        search_col = "Term" + " (" + db + ")"
        #table_col_names = [search_col, "Citation", "S", "I", "Justification"]
        database_context['results_table']['headers'] =  {"Term": search_col, "Citation": "Citation", "S":"S", "I":"I", "Justification":"Justification"} 


        logger.debug("building appendix b table for database: " + str(db))
        table_rows = []

        literature_searches = LiteratureSearch.objects.filter(
            literature_review__id=lit_review_id, db__name=db
        ).exclude(db__is_ae=True).exclude(db__is_recall=True)

        if retained_and_included:

            article_reviews_total = ArticleReview.objects.filter(search__literature_review__id=lit_review_id,
                                search__db__name=db, state='I', clin_lit_appr__included=True).count()

        else:
            article_reviews_total = ArticleReview.objects.filter(search__literature_review__id=lit_review_id,
                                search__db__name=db).count()



        if article_reviews_total == 0:
            pass
            # no reviews, don't print the tables
            # cite_word.add_hx("Database {0}".format(db,),"CiteH1")
            # cite_word.add_p("No results for database to display.") 

        else:
            logger.debug("lit search objects found for database: " + str(len(literature_searches)))            
            #cite_word = appendix_b_process_db(cite_word, db, literature_searches, retained_and_included=True)    
            rows_output = appendix_b_process_db(db, literature_searches, retained_and_included)    
            
            database_context['results_table']['rows'] = rows_output


        if len(database_context['results_table']['rows']) > 0:
            table_index += 1
            database_context['table_index'] = table_index
        appendix_b_context.append(database_context)

    return appendix_b_context
    # section_name = "All Citations"

    # #cite_word = CiteWordDocBuilder(output_path + "appendix_b/")
    # cite_word.add_hx("Appendix B - {0}".format(section_name), "CiteH1")

    # #dbs_list = appendix_b_get_dbs(lit_review_id)

    # for db in dbs_list:

    #     # table_col_names = [search_col, "Citation", "S", "I", "Justification"]

    #     print("building appendexi b table for database: " + str(db))

    #     literature_searches = LiteratureSearch.objects.filter(
    #         literature_review__id=lit_review_id, db__name=db
    #     ).exclude(db__is_ae=True).exclude(db__is_recall=True)

    #     print("lit search objects found for database: " + str(len(literature_searches)))

        
    #     article_reviews_total = ArticleReview.objects.filter(search__literature_review__id=lit_review_id,
    #                             search__db__name=db).count()

    #     if article_reviews_total == 0:
    #         # no reviews, don't print the tables
    #         cite_word.add_hx("Database {0}".format(db,),"CiteH1")
    #         cite_word.add_p("No results for database to display.")

    #     else:

    #         cite_word = appendix_b_process_db(cite_word, db, literature_searches, retained_and_included=False)    

    return cite_word.save_file("appendix_b.docx")



def appendix_c(
    lit_review_id=1,
    table="",
    
):
    """
    Clinical Lit Appraisal
    Table 34, criteria for state of the art
    Table 35 - Criteria for suitability - Retained and included 
    Table 36 - Data Acceptability Level - All Retained Citations  (device application, population, report)
    Table 38 - Criteria for Data Contribution - Retained and Included Citations design, outcome measures stat sig, clin_sig  Y/Ns
    Tble 39 Criteria for Data Contribution - All Retained Citations  Data Out Fol Stat Clin
    **NOTE** table 38 and 39 are exactly the same but shown differently, this is confusing.
    Table 40 Data Excraction Summary Table
    Table 41 Data Exctraction Detailed (Writeups)
    """

    try:
        extr_config = FinalReportConfig.objects.get(literature_review_id=lit_review_id)

    except Exception as e:

        raise Exception('No Extraction Fields Configure, Please Submit a Configuration ')

    appraisals = ClinicalLiteratureAppraisal.objects.filter(
        article_review__search__literature_review__id=lit_review_id, article_review__state="I"
    )
    app_list, app_status, app_completed, app_incompleted = get_clinical_appraisal_status_report(appraisals)
    app_incompleted_count = len(app_incompleted)
    if  app_incompleted_count > 0:
        logger.warning(f"Project contains {app_incompleted_count} Incompleted Appraisals")
        retained_reviews = ArticleReview.objects.filter(
            search__literature_review_id=lit_review_id, state="I", clin_lit_appr__in=app_completed,
        ).order_by('article__citation')

    else:
        retained_reviews = ArticleReview.objects.filter(
            search__literature_review_id=lit_review_id, state="I"
        ).order_by('article__citation')
        # remove incompleted reviews

    if table == 'sota':
        #   Table 34, criteria for state of the art
        retained_reviews_sota = retained_reviews.filter(clin_lit_appr__is_sota_article=True)
        rows = sota_table(retained_reviews_sota, lit_review_id)

    elif table =='suitability_retinc':
        #Table 35 - Criteria for suitability - Retained and included   (device application, population, report)
        header = "Device Suitability Appraisal - Retained and Included Citations"
        retained_reviews_suitability = retained_reviews.filter(clin_lit_appr__included=True)
        rows = device_suitability_appraisal(retained_reviews_suitability, lit_review_id)

    elif table == 'suitability_all':
        # Table 36 - Data Suitability Level - All Retained Citations  (device application, population, report)
        header = "Device Suitability Appraisal - All Retained Citations"
        retained_reviews_suitability = retained_reviews
        rows = device_suitability_appraisal(retained_reviews_suitability, lit_review_id)

    elif table == 'datacontribution_retinc':
        # Table 38 - Criteria for Data Contribution - Retained and Included Citations design, outcome measures stat sig, clin_sig  Y/Ns
        header = "Criteria for Data Contribution - Retained and Included Citations "
        retained_reviews_contribution =  retained_reviews.filter(clin_lit_appr__included=True).exclude(clin_lit_appr__is_sota_article=True)
        #retained_reviews_contribution =  retained_reviews.filter(clin_lit_appr__included=True) ## we want the sotas now 6.24.22
        rows = summary_data_contribution_outcomes_appraisal(retained_reviews_contribution, lit_review_id)


    ## **TODO***  We don't fill these ?s out for excluded articles... so can't show this table. 
    #   Tble 39 Criteria for Data Contribution - All Retained Citations  Data Out Fol Stat Clin
        # header = "Criteria for Data Contribution - All Citations" 
        # retained_reviews_contribution =  retained_reviews.exclude(clin_lit_appr__is_sota_article=True)
        # cite_word = summary_data_contribution_outcomes_appraisal(cite_word, retained_reviews_contribution, header, extr_config )

    
    elif table == 'extraction_summary':
        #  Table 40 Data Excraction Summary Table
        retained_reviews_extraction_summary = retained_reviews.filter(clin_lit_appr__included=True).exclude(clin_lit_appr__is_sota_article=True)
        rows = data_extraction_summary_table(retained_reviews_extraction_summary, extr_config)

    elif table == 'extraction_detail':
        # Table 41 Data Exctraction Detailed (Writeups)
        retained_reviews_extraction_detailed = retained_reviews.filter(clin_lit_appr__included=True).exclude(clin_lit_appr__is_sota_article=True)
        rows = data_extraction_detailed_paragraphs(retained_reviews_extraction_detailed, lit_review_id)

    elif table == 'excluded':
        ## extra table (42?)
        ## table for citations taht were retained but not included
        excluded_reviews = ArticleReview.objects.filter(
            search__literature_review_id=lit_review_id,
            state="I",
            clin_lit_appr__included=False,
            clin_lit_appr__is_sota_article=False,
        )
        rows = retained_citations_not_appraised(excluded_reviews)
        ### TODO decide what to do with this table,  it's been removed here but not in citemed template
        # Table 3 - SP Quality and Contributions Table (original table no lonfwe needed)
        # t3_row = {
        #             "Citation": str(review.article.citation).replace(";", ""),
        #             "Data": lit_appraisal.get_data_contribution_display(),
        #             "Out.": lit_appraisal.outcome_measures,
        #             "Fol.": lit_appraisal.appropriate_followup,
        #             "Stat.": lit_appraisal.statistical_significance,
        #             "Clin.": lit_appraisal.clinical_significance
        # }
        #     Table 3b - SP Quality and Contributions Yes/No table

    rows_results = rows.get("content", None) if type(rows) == dict else rows
    logger.info(f"Total Count of rows for {table} is {len(rows_results)}")
    return rows

def appendix_d(lit_review_id=1):


    

    article_reviews = ArticleReview.objects.filter(
        search__literature_review_id=lit_review_id, state="I")\
        .order_by('article__citation').prefetch_related("clin_lit_appr")

    rows = [] 
    
    index = 0 
    for rev in article_reviews:
        for clin_lit_appr in rev.clin_lit_appr.all():


            if clin_lit_appr.included is True:
                index += 1
                row = {"Index": index, "Citation": clear_special_characters(rev.article.citation)}
                
                rows.append(row)

    return rows


def appendix_e_maude(lit_review_id=0, date_of_search=None, date_end=None):


    context = {}
    literature_review = LiteratureReview.objects.get(id=lit_review_id)
    maude_db_obj = NCBIDatabase.objects.get(entrez_enum='maude')
    maude_recall_db = NCBIDatabase.objects.get(entrez_enum='maude_recalls')
    db_summary = AdversDatabaseSummary.objects.filter(literature_review__id=lit_review_id, database=maude_db_obj).first()
    recalls_db_summary = AdversDatabaseSummary.objects.filter(literature_review__id=lit_review_id, database=maude_recall_db).first()
    
    db_summary = db_summary.summary if db_summary else "No written summary for this database was deemed necessary for the reviewer"
    recalls_db_summary = recalls_db_summary.summary if recalls_db_summary else "No written summary for this database was deemed necessary for the reviewer"

    maude_ae_context = { "protocol": {},
                "summary": db_summary,
                "recalls_summary": recalls_db_summary,
                "single_row_summary": {},
                "maude_by_year": {},
                "maude_included_events": {},
                "E2_maude_aes": {},

    }

    maude_recall_context = {
        "protocol": {},
        "by_year": {},
        "included": {},

    }
#def maude_ae_summary_table(lit_review_id, db_obj, date_of_search, date_end):
    
    maude_ae_context['protocol'] = get_db_info(literature_review, maude_db_obj)
    maude_ae_context['single_row_summary'] =  maude_ae_summary_table(lit_review_id, maude_db_obj, date_of_search=date_of_search, date_end=date_end)
    maude_ae_context['maude_by_year']['rows'] = maude_aes_by_year(lit_review_id, maude_db_obj, date_of_search, date_end)
    maude_ae_context['maude_included_events']['rows'] = included_aes(lit_review_id, maude_db_obj, date_of_search, date_end) 
    index_tables_e = 0
    if len(maude_ae_context['maude_included_events']['rows']):
        index_tables_e  = index_tables_e + 1
        maude_ae_context['maude_included_events']['table_index'] = index_tables_e
    else:
        maude_ae_context['maude_included_events']['table_index'] = index_tables_e

    # we moved this to a seperate report builder generator (Appendix E2 Document).
    #maude_ae_context['E2_maude_aes']['rows'] = all_maude_aes(lit_review_id, date_end, date_of_search)
    maude_ae_context['E2_maude_aes']['rows'] = []


    context['maude_aes'] = maude_ae_context

    maude_recall_context['by_year']['rows'] =  maude_recalls_by_year_db_summary(lit_review_id, maude_recall_db) 
    maude_recall_context['protocol'] = get_db_info(literature_review, maude_recall_db)

    if len(maude_recall_context['by_year']['rows']):
        index_tables_e  = index_tables_e + 1
        maude_recall_context['by_year']['table_index'] = index_tables_e
    else:
        maude_recall_context['by_year']['table_index'] = index_tables_e

    maude_recall_context['included']['rows'] =  maude_included_recalls(lit_review_id, date_of_search, date_end) 
    if len(maude_recall_context['included']['rows']):
        index_tables_e  = index_tables_e + 1
        maude_recall_context['included']['table_index'] = index_tables_e
    else:
        maude_recall_context['included']['table_index'] = index_tables_e

#maude_included_recalls(lit_review_id, date_of_search, date_end)
    context['maude_recalls'] = maude_recall_context


    return context

def appendix_e_aes(lit_review_id=1, is_vigilance=False, date_of_search=None, date_end=None):

    
    literature_review = LiteratureReview.objects.get(id=lit_review_id)  
    dbs_list = get_db_list(lit_review_id, db_type='ae')
    
    #dbs_list.remove('FDA MAUDE') ## remove maude, we build these separately. 

    aes_context = []
    index_tables_e_2 = 0
    for db in dbs_list:

        db_obj = NCBIDatabase.objects.get(name=db)
        db = db_obj.name

        ## building AE summary table.
        db_context = {
            "protocol": {},
            "included": {},
            "summary": "",
        }

        db_context['protocol'] = get_db_info(literature_review, db_obj)
        ###AE summary table (per datbase)
        db_context['included']['rows'] = included_aes_by_database(lit_review_id, db_obj,date_of_search, date_end)
        if len(db_context['included']['rows']) > 0:
            index_tables_e_2 += 1

        db_context['included']['table_index']  = index_tables_e_2


        try:
            ars = AdverseEventReview.objects.filter(search__db=db_obj, search__literature_review=literature_review)
            if len(ars) > 0:
                summary = AdversDatabaseSummary.objects.filter(database=db_obj, literature_review=literature_review).first()
                db_context['summary'] = summary.summary if summary else "No written summary for this database was deemed necessary for the reviewer"


            # ars = AdverseEventReview.objects.filter(search__db=db_obj, search__literature_review=literature_review)
            # if len(ars) > 0:

            #     summary = AdversDatabaseSummary.objects.get(database=db_obj, literature_review=literature_review)
            #     db_context['summary'] = summary.summary

        except Exception as e:
            pass
            #raise Exception('No Adverse DB Summary for {0}'.format(db))
  
        aes_context.append(db_context)

#    recall_reviews = AdverseRecallReview.objects.filter(search__literature_review_id=lit_review_id).prefetch_related('search')

    return aes_context


def appendix_e_recalls(lit_review_id=1, is_vigilance=False, date_of_search=None, date_end=None):

    
    literature_review = LiteratureReview.objects.get(id=lit_review_id)  
    dbs_list = get_db_list(lit_review_id, db_type='recall')
   # dbs_list.remove('FDA MAUDE') ## remove maude, we build these separately. 
   # dbs_list.remove('Maude Recalls')
    recalls_context = []
    index_tables_e_3 = 0
    for db in dbs_list:

        db_obj = NCBIDatabase.objects.get(name=db)
        db = db_obj.name

        ## building AE summary table.
        db_context = {
            "protocol": {},
            "included": {},
            "summary": "",
        }



        db_context['protocol'] = get_db_info(literature_review, db_obj)
        db_context['included']['rows'] = included_recalls_by_database(lit_review_id, db_obj, date_of_search, date_end)
        if len(db_context['included']['rows']) > 0:
            index_tables_e_3 += 1
            
        db_context['included']['table_index']  = index_tables_e_3

        try:
            ars = AdverseEventReview.objects.filter(search__db=db_obj, search__literature_review=literature_review)
            if len(ars) > 0:
                summary = AdversDatabaseSummary.objects.filter(database=db_obj, literature_review=literature_review).first()
                db_context['summary'] = summary.summary if summary else "No written summary for this database was deemed necessary for the reviewer"

        except Exception as e:

            raise Exception('No Adverse DB Summary for {0}'.format(db))
  


        recalls_context.append(db_context)

    return recalls_context


def archive_appendix_e_recalls(lit_review_id=1, is_vigilance=False, date_of_search=None, date_end=None):

    recall_dbs_list = get_db_list(lit_review_id, db_type='recall')
    recall_dbs_list.remove('FDA MAUDE RECALLS')


    recalls_context = []
    for db in recall_dbs_list:
        db_obj = NCBIDatabase.objects.get(pk=db)
        db = db_obj.name
        ## same thing year by years for recalls though.
        db_context = {

            "protocol": {},
            "recalls_by_year_table": {}
        }


        db_context['protocol'] = get_db_info(literature_review, db_obj)
        db_context['recalls_by_year']['rows'] = recalls_by_year_db_summary(lit_review_id, db_obj)

        recalls_context.append(db_context)


    return recalls_context
    

def vigilance_report(output_path, lit_review_id=None, date_of_search=None, date_end=None):
    

    """
    This is an invidiaul vigilance report

    Tables Needed
    -------------

    AE Tbles 
    ---------------

    Table 2 Overview Breakdown by Year (fiscal or calendar?)
    Columns = [Year, Search Terms, Death, Injury, Malfunction, Other/NA ]
    for maude and other AEs. 


    Table 3 Monthly Overview of AE Safety Data 
    Cols = [ Year, Month(Jan-December), All Terms, Death, Injury Malfunction Other/NA ]

    for every year found:

        for every month in [ Jan, Feb, March ....]:

            row[ ]


    
    Table 4 Assessments of Relevant Safety Events AE Data 
    cols = [ Date, Search Term, Adverse Event, Incident Type, Relevant AE ]



    Recall Tables
    -----------------

    Table 6 Recall Non-Maude Summary -- 
    cols = [ Date, Search Term, Recall Type, Event Description  ] 



    """



    #print("REMOVING AE DUPLICATES")
    #remove_ae_duplicates(lit_review_id)



   # Table 2 Overview Breakdown by Year (fiscal or calendar?)

   #  Columns = [Year, Search Terms, Death, Injury, Malfunction, Other/NA ]
   #  for maude and other AEs. 

   ## get all years for AE reviews. 

    ## for every term
          ## for every year with that term


          ## build row

    #maude first.


    ## TODO get date of search from Protocol model 

   # search_protocol = SearchProtocol.objects.get(literature_review__id=lit_review_id)
   # date_of_search = search_protocol.date_of_search
   # years_back = search_protocol.years_back




    if not os.path.exists(output_path + "vigilance_report"):
        os.makedirs(output_path + "vigilance_report")


    cite_word = CiteWordDocBuilder(output_path + "vigilance_report/")
    cite_word.add_hx("Vigilance Report - Adverse Events", "CiteH1")

    cite_word.add_hx("Maude Adverse Events Summary for Dates {0} - {1}".format(date_of_search, date_end), "CiteH2")


    maude_db = NCBIDatabase.objects.get(entrez_enum='maude')

    
    lit_review = LiteratureReview.objects.get(id=lit_review_id)
    ## get literature searches
    literature_searches = LiteratureSearch.objects.filter(db__entrez_enum=maude_db, literature_review__id=lit_review_id)
    ## for each literature search term. 

        ## init table

    t2_cols = ["Year", "Search Terms", "Death", "Injury", "Malfunction", "Other/NA"]
    t2 = cite_word.init_table(t2_cols)


    for lit_search in literature_searches:


        ## get all ae_reviews associated with that search.  
        adverse_reviews = AdverseEventReview.objects.filter(search=lit_search,
         ae__event_date__gte=date_end,
          ae__event_date__lte=date_of_search).exclude(state='DU')

        ## todo get years by passiing lit_search.
        years = get_ae_years(lit_search.literature_review, lit_search.db, date_of_search, date_end, lit_search=lit_search)
        for year in years:
            counts = ae_counts_by_search_and_year(lit_search, year, lit_review_id)
            row = {

                "Year": year,
                "Search Terms": lit_search.term,
                "Death": counts['death'] ,
                "Injury": counts['injury'],
                "Malfunction": counts['malfunction'] ,
                "Other/NA": counts['na_other']
            }

            ## write row to table. 
            cite_word.add_table_row(t2, row.values())


    # Table 3 Monthly Overview of AE Safety Data   per year. 
    # Cols = [ Year, Month(Jan-December), All Terms, Death, Injury Malfunction Other/NA ]

    # for every year found:

    #     for every month in [ Jan, Feb, March ....]:

    #         row[ ]


    ## get years by passing database, project_ID


    logger.debug("TERUMO SPECIFIC TABLES")


    cite_word = vig_annual_maude_counts_by_term(lit_review, maude_db, 2021, cite_word, True)
    cite_word = vig_annual_maude_counts_by_term(lit_review, maude_db, 2021, cite_word, False)

    ####  Include duplicates 
   #good  cite_word = vig_db_monthly_summary_table(lit_review, maude_db, date_of_search, date_end, cite_word, specific_term="DYB", all_records=False)
    # good cite_word = vig_db_monthly_summary_table(lit_review, maude_db, date_of_search, date_end, cite_word, specific_term="DYB", all_records=True)

    cite_word = vig_db_monthly_summary_table(lit_review, maude_db, date_of_search, date_end, cite_word, specific_term="MGB", all_records=True)
    cite_word = vig_db_monthly_summary_table(lit_review, maude_db, date_of_search, date_end, cite_word, specific_term="MGB", all_records=False)

    cite_word = vig_db_monthly_summary_table(lit_review, maude_db, date_of_search, date_end, cite_word, specific_term="DQX", all_records=True)
    cite_word = vig_db_monthly_summary_table(lit_review, maude_db, date_of_search, date_end, cite_word, specific_term="DQX", all_records=False)

    cite_word = vig_db_monthly_summary_table(lit_review, maude_db, date_of_search, date_end, cite_word, specific_term="DYB", all_records=True)
    cite_word = vig_db_monthly_summary_table(lit_review, maude_db, date_of_search, date_end, cite_word, specific_term="DYB", all_records=False)


    cite_word = vig_db_monthly_summary_table(lit_review, maude_db, date_of_search, date_end, cite_word, specific_term=None, all_records=False)
    cite_word = vig_db_monthly_summary_table(lit_review, maude_db, date_of_search, date_end, cite_word, specific_term=None, all_records=True)


    logger.debug("IGNORING vig all included per db run ")
    #cite_word = vig_all_included_per_db(lit_review_id, date_end, date_of_search, cite_word)
  


######
  
  #### ########

    # Table 4 Assessments of Relevant Safety Events AE Data 
    # cols = [ Date, Search Term, Adverse Event, Incident Type, Relevant AE ]

    ## FDA Maude -- and all AEs

    ## get reviews that are include for the db.

    ## get list of ae_dbs where we have reviews....



# Table 5 Overall US Recall Summary 

# Date  Search Term  Recall Type  Event Description 

    # print("starting table 5 in vig report")

    # dbs = NCBIDatabase.objects.filter(is_recall=True)

    # for db in dbs:

    #     recall_reviews = AdverseRecallReview.objects.filter(search__db=db, state="IN", search__literature_review_id=lit_review_id)
    #     cite_word.add_hx('Table 5 OverallRecall Summary - {0} All Years'.format(db), "CiteH2")

    #     t5_cols = ["Date", "Search Term", "Recall Type", "Event Description"]
    #     t5 = cite_word.init_table(t5_cols)

    #     for rr in recall_reviews:

    #         row = {
    #             "Date": str(rr.ae.event_date),
    #             "Search Term":  rr.search.term,
    #             "Recall Type": rr.ae.recall_class if (db.entrez_enum == 'maude' or db.entrez_enum == 'fda_tplc') else rr.ae.manual_type,
    #             "Event Description": rr.ae.product_description + "VERIFY" if (db.entrez_enum == 'maude' or db.entrez_enum == 'fda_tplc') else rr.ae.manual_severity,
    #         }
    #         print("row for table 5 {0}".format(row.values()))
    #         cite_word.add_table_row(t5, row.values())


########







##########

    return cite_word.save_file("vigilance_report.docx")


def dedupe_individual_search(ar_list):
    deduped = []
    deduped_ids = []
    for ar in ar_list.order_by('ae__event_type'):

        
            ## we can skip this, since we already have it.     
        if ar.ae.event_number_full is not None and ar.ae.event_number_full not in deduped_ids:

            deduped.append(ar)
            deduped_ids.append(ar.ae.event_number_full)
           
    logger.debug("Returned Deduped Search Objs " + str(deduped))
    return deduped



def ae_counts_by_db_and_month(lit_review_id, db_obj, month, year, all_records=False, specific_term=False):


    # death = AdverseEvent.objects.filter(
    #     ae_events__literature_review__id=lit_review_id,
    #     event_type="Death",
    #     db=db_obj,
    #     event_date__year=year,
    #     event_date__month=month,

    # ).count()

    # injury = AdverseEvent.objects.filter(Q(
    #     Q(ae_events__literature_review__id=lit_review_id) &
    #     Q(db=db_obj) &
    #     Q( Q(event_type="Injury") | Q(manual_severity="Injury")) &
    #     Q(event_date__year=year) &
    #     Q(event_date__month=month)
    # )
    # ).count()

    # malfunction = AdverseEvent.objects.filter(
    #     ae_events__literature_review__id=lit_review_id,
    #     db=db_obj,
    #     event_type="Malfunction",
    #     event_date__year=year,
    #     event_date__month=month,

    # ).count()
    # na_other = AdverseEvent.objects.filter(
    #     Q(ae_events__literature_review__id=lit_review_id),
    #     Q(db=db_obj),
    #     Q(event_date__year=year),
    #     Q(event_date__month=month),
    #     Q(Q(event_type="NA") | Q(event_type="Other")),
    # ).count()
#############################

    descr_or_filter, manuf_or_filter = get_ae_filters(lit_review_id)
 

    if specific_term and all_records:  ## Specific Term and All Records

        try:

            search =  LiteratureSearch.objects.get(literature_review__id=lit_review_id, db=db_obj, term=specific_term)
        
            death = AdverseEventReview.objects.filter(
                search__literature_review__id=lit_review_id,
                ae__event_type="Death",
                search__db=db_obj,
                search=search,
                ae__event_date__year=year,
                ae__event_date__month=month,
               # state="IN"
            ).prefetch_related('ae')

            injury = AdverseEventReview.objects.filter(Q(
                Q(search__literature_review__id=lit_review_id) &
                Q(search__db=db_obj) &
                Q(search=search) &
                Q( Q(ae__event_type="Injury") | Q(ae__manual_severity="Injury")) &
                Q(ae__event_date__year=year) &
                Q(ae__event_date__month=month) 
                #Q(state="IN")
            )
            ).prefetch_related('ae')

            malfunction = AdverseEventReview.objects.filter(
                search__literature_review__id=lit_review_id,
                search__db=db_obj,
                search=search,
                ae__event_type="Malfunction",
                ae__event_date__year=year,
                ae__event_date__month=month,
              #  state="IN"

            ).prefetch_related('ae')
            na_other = AdverseEventReview.objects.filter(
                Q(search__literature_review__id=lit_review_id),
                Q(search__db=db_obj),
                Q(search=search),
                Q(ae__event_date__year=year),
                Q(ae__event_date__month=month),
                Q(Q(ae__event_type="NA") | Q(ae__event_type="Other")),
                #Q(state='IN')
            ).prefetch_related('ae')


        except Exception as e:

            death = "NO SEARCH FOUND FOR TERM: {0}".format(specific_term)
            injury = "NO SEARCH FOUND FOR TERM: {0}".format(specific_term)
            malfunction = "NO SEARCH FOUND FOR TERM: {0}".format(specific_term)
            na_other = "NO SEARCH FOUND FOR TERM: {0}".format(specific_term)



    elif all_records and not specific_term:

        death = AdverseEventReview.objects.filter(
        search__literature_review__id=lit_review_id,
        ae__event_type="Death",
        search__db=db_obj,
        ae__event_date__year=year,
        ae__event_date__month=month,
        # state="IN"

        ).prefetch_related('ae')

#        ).exclude(is_duplicate=True).prefetch_related('ae')


        injury = AdverseEventReview.objects.filter(Q(
        Q(search__literature_review__id=lit_review_id) &
        Q(search__db=db_obj) &
        Q( Q(ae__event_type="Injury") | Q(ae__manual_severity="Injury")) &
        Q(ae__event_date__year=year) &
        Q(ae__event_date__month=month) 
      #  Q(state="IN")
        )
        ).prefetch_related('ae')

        malfunction = AdverseEventReview.objects.filter(
        search__literature_review__id=lit_review_id,
        search__db=db_obj,
        ae__event_type="Malfunction",
        ae__event_date__year=year,
        ae__event_date__month=month,
       # state="IN"

        ).prefetch_related('ae')

        na_other = AdverseEventReview.objects.filter(
            Q(search__literature_review__id=lit_review_id),
            Q(search__db=db_obj),
            Q(ae__event_date__year=year),
            Q(ae__event_date__month=month),
            Q(Q(ae__event_type="NA") | Q(ae__event_type="Other")),
           # Q(state='IN')
        ).prefetch_related('ae')

    

    elif specific_term and not all_records:  ## specific term and Included Records Only

        try:

            search =  LiteratureSearch.objects.get(literature_review__id=lit_review_id, db=db_obj, term=specific_term)
        

            #  tags = ['tag1', 'tag2', 'tag3']
            # q_objects = Q() # Create an empty Q object to start with
            # for t in tags:
            #     q_objects |= Q(tags__tag__contains=t) # 'or' the Q objects together

            # designs = Design.objects.filter(q_objects)

            ## modifying this for test for multiple manufacturers AND keywords in description.

            


            death = AdverseEventReview.objects.filter(
                search__literature_review__id=lit_review_id,
                ae__event_type="Death",
                search__db=db_obj,
                search=search,
                ae__event_date__year=year,
                ae__event_date__month=month,
                # ae__manufacturer__icontains='TERUMO',
            ).prefetch_related('ae')

            death = death.filter( manuf_or_filter).filter(descr_or_filter)



            injury = AdverseEventReview.objects.filter(Q(
                Q(search__literature_review__id=lit_review_id) &
                Q(search__db=db_obj) &
                Q(search=search) &
                Q( Q(ae__event_type="Injury") | Q(ae__manual_severity="Injury")) &
                Q(ae__event_date__year=year) &
                Q(ae__event_date__month=month) 
                #Q(state="IN")
               # Q(ae__manufacturer__icontains='TERUMO')

            )
            ).prefetch_related('ae')

            injury = injury.filter( manuf_or_filter).filter(descr_or_filter)

            malfunction = AdverseEventReview.objects.filter(
                search__literature_review__id=lit_review_id,
                search__db=db_obj,
                search=search,
                ae__event_type="Malfunction",
                ae__event_date__year=year,
                ae__event_date__month=month,
               # ae__manufacturer__icontains='TERUMO',

            ).prefetch_related('ae')


            malfunction = malfunction.filter( manuf_or_filter).filter(descr_or_filter)

            na_other = AdverseEventReview.objects.filter(
                Q(search__literature_review__id=lit_review_id),
                Q(search__db=db_obj),
                Q(search=search),
                Q(ae__event_date__year=year),
                Q(ae__event_date__month=month),
                Q(Q(ae__event_type="NA") | Q(ae__event_type="Other")),
                #Q(ae__manufacturer__icontains='TERUMO')
            ).prefetch_related('ae')

            na_other = na_other.filter( manuf_or_filter).filter(descr_or_filter)

        except Exception as e:

            death = "NO SEARCH FOUND FOR TERM: {0}".format(specific_term)
            injury = "NO SEARCH FOUND FOR TERM: {0}".format(specific_term)
            malfunction = "NO SEARCH FOUND FOR TERM: {0}".format(specific_term)
            na_other = "NO SEARCH FOUND FOR TERM: {0}".format(specific_term)


    else:  ## All Devices,  Included Records
        logger.debug("inside terumo only, all terms so deduple")
        death = AdverseEventReview.objects.filter(
            search__literature_review__id=lit_review_id,
            ae__event_type="Death",
            search__db=db_obj,
            ae__event_date__year=year,
            ae__event_date__month=month,
           # ae__manufacturer__icontains='TERUMO'


        ).prefetch_related('ae')

        death = death.filter( manuf_or_filter).filter(descr_or_filter)


        injury = AdverseEventReview.objects.filter(Q(
            Q(search__literature_review__id=lit_review_id) &
            Q(search__db=db_obj) &
            Q( Q(ae__event_type="Injury") | Q(ae__manual_severity="Injury")) &
            Q(ae__event_date__year=year) &
            Q(ae__event_date__month=month)
            # Q(state="IN")
          #  Q(ae__manufacturer__icontains='TERUMO')

        )
        ).prefetch_related('ae')

        injury = injury.filter( manuf_or_filter).filter(descr_or_filter)

       # ).exclude(is_duplicate=True).prefetch_related('ae')

        malfunction = AdverseEventReview.objects.filter(
            search__literature_review__id=lit_review_id,
            search__db=db_obj,
            ae__event_type="Malfunction",
            ae__event_date__year=year,
            ae__event_date__month=month,
          #  ae__manufacturer__icontains='TERUMO'

            #state="IN"

        ).prefetch_related('ae')
#                ).exclude(is_duplicate=True).prefetch_related('ae')

        manlfunction = malfunction.filter( manuf_or_filter).filter(descr_or_filter)

        na_other = AdverseEventReview.objects.filter(
            Q(search__literature_review__id=lit_review_id),
            Q(search__db=db_obj),
            Q(ae__event_date__year=year),
            Q(ae__event_date__month=month),
            Q(Q(ae__event_type="NA") | Q(ae__event_type="Other")),
       #     Q(ae__manufacturer__icontains='TERUMO')

            #Q(state='IN')
        ).prefetch_related('ae')
#        ).exclude(is_duplicate=True).prefetch_related('ae')
        na_other = na_other.filter( manuf_or_filter).filter(descr_or_filter)


    ## dedupe  everything this way, why not?
    if True:
        logger.debug("deduping individual search")
        death = dedupe_individual_search(death)
        malfunction = dedupe_individual_search(malfunction)
        injury = dedupe_individual_search(injury)
        na_other = dedupe_individual_search(na_other)

        summary_row = {

        "death": len(death),
        "injury": len(injury),
        "malfunction": len(malfunction),
        "na_other": len(na_other),

        }

    # else:
    #     summary_row = {

    #     "death": death.count(),
    #     "injury": injury.count(),
    #     "malfunction": malfunction.count(),
    #     "na_other": na_other.count(),

    # }



    specific_term_txt = "Specific Term: {0}".format(search.term) if specific_term else "All Terms"
    all_records_txt = "All Records" if all_records else "Terumo Related Results Only - "
    dupes = "Duplicates Removed" if all_records and not specific_term else ""
    all_records_txt += dupes


    #with open("/home/ethand320/Dropbox/code/wy-citemed/citemedical/backend/review_output/{0}/".format(lit_review_id) + "vigilance_dumps/" + "{0}-{1}-{2}-{3}.csv".format(month, year, specific_term_txt, all_records_txt, lit_review_id ) , "w") as csvfile:
      #  print("Writing CSV Output FOr Month Now")
     #   table_col_names = ["Event Date", "Event ID Short", "Event ID Full", "Is Duplicate", "Manufacturer", "Event Type", "Event Description"]

       # writer = csv.DictWriter(csvfile, fieldnames=table_col_names)
        #writer.writeheader()

        # for item in [death, injury, malfunction, na_other]:
        #     print("Writing item {0} ".format(item))
        #     for ar in item:
        #         row = {
        #             "Event Date": ar.ae.event_date ,
        #             "Event ID Short": ar.ae.event_number_short,
        #             "Event ID Full": ar.ae.event_number_full,
        #             "Is Duplicate": ar.is_duplicate, 
        #             "Manufacturer": ar.ae.manufacturer,
        #             "Event Type": ar.ae.event_type,
        #             "Event Description": ar.ae.description
        #         }
        #         print("Writing row to csv : {0}".format(row))
        #         writer.writerow(row)


    return summary_row 

         


def micro_deliverables(output_path="", lit_review_id=1):

    ##1.  search results general (total articles, duplicates, initially excluded)

    excluded_articles = ArticleReview.objects.filter(
        search__literature_review_id=lit_review_id, state="E"
    )

    included_articles = ArticleReview.objects.filter(
        search__literature_review_id=lit_review_id, state="I"
    )

    duplicate_articles = ArticleReview.objects.filter(
        search__literature_review_id=lit_review_id, state="D"
    )

    total_articles = ArticleReview.objects.filter(
        search__literature_review_id=lit_review_id
    )

    logger.debug(
        """
        Total Articles: {0} \n
        Dupllicates Removed: {1} \n
        Excluded: {2} \n 

        """.format(
            len(total_articles), len(duplicate_articles), len(excluded_articles)
        )
    )

    ##2. sample of 100 abstracts + exclusion reasons. ,  X abstracts with inclusion + reason (if specfic)

    if not os.path.exists(output_path + "micro_deliverables"):
        os.makedirs(output_path + "micro_deliverables")

    with open(output_path + "micro_deliverables/" + "excluded.csv", "w") as csvfile:

        table_col_names = ["Citation", "Abstract", "Justification"]

        writer = csv.DictWriter(csvfile, fieldnames=table_col_names)
        writer.writeheader()

        for review in excluded_articles[0:100]:

            row = {
                "Citation": review.article.citation,
                "Abstract": review.article.abstract,
                "Justification": review.exclusion_reason,
            }
            writer.writerow(row)

    with open(output_path + "micro_deliverables/" + "included.csv", "w") as csvfile:

        table_col_names = ["Citation", "Abstract", "Justification"]

        writer = csv.DictWriter(csvfile, fieldnames=table_col_names)
        writer.writeheader()

        for review in included_articles[0:50]:

            row = {
                "Citation": review.article.citation,
                "Abstract": review.article.abstract,
            }
            writer.writerow(row)

    ##3. data extraction tables

    extraction_rows = [
        "study name",
        "study design",
        "years of data collection",
        "geographic location",
        "procedure",
        "intervention",
        "sample size for laparoscopic and robotic procedure",
        "indication for surgery",
        "age",
        "gender",
        "BMI",
        "ASA Score",
        "case difficulty",
        "inclusion and exclusion",
        "length of follow-up",
        "Number of Surgeons",
        "seniority",
        "surgeon experience",
        "Relevant Outcomes Tbl 4",
        "Adverse Events",
        "Conclusions",
    ]

    table_col_names = ["extraction"]

    for review in included_articles:
        table_col_names.append(review.article.citation)

    with open(output_path + "micro_deliverables/" + "extraction.csv", "w") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=table_col_names)
        writer.writeheader()

        for extraction_row in extraction_rows:
            row = {"extraction": extraction_row}
            for abstract in table_col_names[1:]:
                row.update({abstract: " "})

            writer.writerow(row)

    a = input("stop")



