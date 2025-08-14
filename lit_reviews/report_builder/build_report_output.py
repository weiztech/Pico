import traceback
from datetime import timedelta
from docxtpl import DocxTemplate
from django.core.files import File
from backend.logger import logger

from lit_reviews.report_builder.protocol_context_builder import *
from lit_reviews.report_builder.report_context_builder import (
    appendix_a1_context,
    appendix_a2_context,
    appendix_b_context,
    appendix_c_context,
    appendix_d_context,
    appendix_e_context,
    prisma_context,
)
from lit_reviews.models import (
    LiteratureReview,
    SearchProtocol
)
from lit_reviews.helpers.articles import create_missing_clinical_appraisals_file
from lit_reviews.helpers.generic import construct_report_error
from lit_reviews.helpers.reports import get_company_logo


def build_report_output(review_id, report_job, report_type, report_path, is_simple=False, appendix_path=None):
    RT = "LITR Report" if report_type == "REPORT" else "LITR Condensed Report" 

    version_number = report_job.version_number
    lit_review = LiteratureReview.objects.get(id=review_id)

    # add missing clinical appraisals file
    missing_clinical_appraisals_file = create_missing_clinical_appraisals_file(review_id,report_job)
    if missing_clinical_appraisals_file:
        f = open(missing_clinical_appraisals_file, "rb")
        report_job.missing_clinical_appraisals = File(f)
        report_job.save()
        logger.debug("Missing Appraisals File Created successfully")
    else:
        logger.warning(f"Missing Appraisals File Creation Failed")

    
    try:
        ## get our search dates from protocol
        search_protocol = SearchProtocol.objects.get(literature_review=lit_review)
        protocol_start_date = search_protocol.ae_start_date_of_search
        protocol_end_date = search_protocol.ae_date_of_search
        
        if not protocol_start_date:
            ae_years_back = search_protocol.ae_years_back
            days = 365 * ae_years_back
            protocol_start_date =  protocol_end_date - timedelta(days=days)

    except Exception as e:
        err_track = str(traceback.format_exc())
        error_msg = "Error while building report file please make sure to provide these fields : ae date of search and ae years back for the Search Protocol"
        return construct_report_error(error_msg, err_track, report_job, RT, lit_review, version_number)
    
    
    review = {}
    try:
        review['prisma'] = prisma_context(review_id)
        review['appendix_a1'] = appendix_a1_context(review_id)
        review['appendix_a2'] = appendix_a2_context(review_id)

        logger.debug("running appendix B contexts...")
        review['appendix_b_retinc'] = appendix_b_context(review_id, retained_and_included=True)
        review['appendix_b_all'] = appendix_b_context(review_id, retained_and_included=False)

        review['appendix_a1_table_count'] = review['appendix_a1'][-1]["table_index"]
        review['appendix_a2_table_count'] = review['appendix_a2'][-1]["table_index"]
        review['appendix_b_retinc_table_count'] = review['appendix_b_retinc'][-1]["table_index"]
        review['appendix_b_all_table_count'] = review['appendix_b_all'][-1]["table_index"]

        if report_type == "CONDENSED_REPORT":
            review['dynamique_tables_count'] = (
                review['appendix_a1'][-1]["table_index"] + review['appendix_a2'][-1]["table_index"]
            )
        else:
            review['dynamique_tables_count'] = (
                review['appendix_a1'][-1]["table_index"] + review['appendix_a2'][-1]["table_index"] + 
                review['appendix_b_retinc'][-1]["table_index"] + review['appendix_b_all'][-1]["table_index"]
            )

        retinc_rows = len(review['appendix_b_retinc'][0]['results_table']['rows'])
        all_rows = len(review['appendix_b_all'][0]['results_table']['rows'])
        logger.debug("Appendix B len of retinc rows {0} -  all {1}".format(retinc_rows, all_rows))

        logger.debug("running appendix C contexts..")
        review['appendix_c'] = appendix_c_context(review_id)

        review['dynamique_tables_count_two'] = (
            review['dynamique_tables_count'] + review['appendix_c']['excluded_table']["table_index"] + 5
        )
        
        review['appendix_d'] = appendix_d_context(review_id)

        if review['appendix_d']['all_retained_table']['rows']:
            review['dynamique_tables_count_three'] = (
                review['dynamique_tables_count_two'] + 1
            )
        else:
            review['dynamique_tables_count_three'] = review['dynamique_tables_count_two']


        review['appendix_e'] = appendix_e_context(lit_review_id=review_id, date_of_search=protocol_start_date, date_end=protocol_end_date) ## work in progress
        
        review['dynamique_tables_count_four'] = review['appendix_e']['maude_tables']['maude_recalls']['included']['table_index'] + 2 + review['dynamique_tables_count_three'] 
        
        if len(review['appendix_e']['ae_dbs']) > 0:
            review['dynamique_tables_count_five'] = review['appendix_e']['ae_dbs'][-1]['included']["table_index"] + review['dynamique_tables_count_four']
        else:
            review['dynamique_tables_count_five'] = review['dynamique_tables_count_four']

        if len(review['appendix_e']['recall_dbs']) > 0:
            review['dynamique_tables_count_six']  = review['appendix_e']['recall_dbs'][-1]['included']["table_index"] + review['dynamique_tables_count_five']
        else:
            review['dynamique_tables_count_six'] = review['dynamique_tables_count_five']

    except Exception as error:
        err_track = str(traceback.format_exc())
        return construct_report_error(error, err_track, report_job, RT, lit_review, version_number)
    
    context = {}
    try:
        context =  build_protocol_context(lit_review, report_job)

    except Exception as error:
        err_track = str(traceback.format_exc())
        error_msg = """
        Could you please make sure all neccessary inputs for Search Protocol are filled out? 
        it seems like some field on Search Protocol were not provided.
        """
        return construct_report_error(error_msg, err_track, report_job, RT, lit_review, version_number)

    context["review"] = review
    context["report_type"] = report_type

    ## this is for debugging purpuses
    # with open("tmp/LITR_json.json", "w") as litr_file:
    #     from django.core.serializers.json import DjangoJSONEncoder
    #     litr_file.write(json.dumps(context,sort_keys=True,indent=1,cls=DjangoJSONEncoder))

    if report_type == "CONDENSED_REPORT":
        # Condensed Report
        doc1 = DocxTemplate("report_templates/ReportTemplate.docx")

        # adding logo image
        image_link = context['company_logo_link']
        company_logo = get_company_logo(image_link, doc1)
        context['company_logo'] = company_logo

        doc1.render(context, autoescape=True)

        # Appendix B
        doc2 = DocxTemplate("report_templates/AppendixBTemplate.docx")

        # adding logo image
        image_link = context['company_logo_link']
        company_logo = get_company_logo(image_link, doc2)
        context['company_logo'] = company_logo
        
        doc2.render(context, autoescape=True)

        return doc1,doc2

    else:
        try:
            ## generate output document
            document_template = "SimpleReportTemplate.docx" if is_simple else "ReportTemplate.docx"
            doc = DocxTemplate("report_templates/"+document_template)

            # adding logo image
            image_link = context['company_logo_link']
            company_logo = get_company_logo(image_link, doc)
            context['company_logo'] = company_logo
            
            doc.render(context, autoescape=True)
            return doc
        
        except Exception as e:
            err_track = str(traceback.format_exc())
            error_msg = "Unkown Error when saving the report  \n " + str(e)
            return construct_report_error(error_msg, err_track, report_job, RT, lit_review, version_number)
        

def build_prisma_output(review_id, report_job, report_type):
    version_number = report_job.version_number
    lit_review = LiteratureReview.objects.get(id=review_id)
    review = {}

    try:
        review['prisma'] = prisma_context(review_id)

    except Exception as error:
        err_track = str(traceback.format_exc())
        return construct_report_error(error, err_track, report_job, report_type, lit_review, version_number)
    
    context = {}
    try:
        context =  build_protocol_context(lit_review, report_job)

    except Exception as error:
        err_track = str(traceback.format_exc())
        error_msg = """
        Could you please make sure all neccessary inputs for Search Protocol are filled out? 
        it seems like some field on Search Protocol were not provided.
        """
        return construct_report_error(error_msg, err_track, report_job, report_type, lit_review, version_number)

    context["review"] = review
    context["report_type"] = report_type

    try:
        ## generate output document
        doc = DocxTemplate("report_templates/PrismaTemplate.docx")

        # adding logo image
        image_link = context['company_logo_link']
        company_logo = get_company_logo(image_link, doc)
        context['company_logo'] = company_logo
        
        doc.render(context)
        return doc
    
    except Exception as e:
        err_track = str(traceback.format_exc())
        error_msg = "Unkown Error when saving the report  \n " + str(e)
        return construct_report_error(error_msg, err_track, report_job, report_type, lit_review, version_number)
    

def build_second_pass_word_output(review_id, report_job, report_type):
    version_number = report_job.version_number
    lit_review = LiteratureReview.objects.get(id=review_id)
    review = {}

    try:
        review['appendix_c'] = appendix_c_context(review_id)

    except Exception as error:
        err_track = str(traceback.format_exc())
        return construct_report_error(error, err_track, report_job, report_type, lit_review, version_number)
    
    context = {}
    try:
        context =  build_protocol_context(lit_review, report_job)

    except Exception as error:
        err_track = str(traceback.format_exc())
        error_msg = """
        Could you please make sure all neccessary inputs for Search Protocol are filled out? 
        it seems like some field on Search Protocol were not provided.
        """
        return construct_report_error(error_msg, err_track, report_job, report_type, lit_review, version_number)

    context["review"] = review
    context["report_type"] = report_type

    try:
        ## generate output document
        doc = DocxTemplate("report_templates/SecondPassTemplate.docx")

        # adding logo image
        image_link = context['company_logo_link']
        company_logo = get_company_logo(image_link, doc)
        context['company_logo'] = company_logo
        
        doc.render(context)
        return doc
    
    except Exception as e:
        err_track = str(traceback.format_exc())
        error_msg = "Unkown Error when saving the report  \n " + str(e)
        return construct_report_error(error_msg, err_track, report_job, report_type, lit_review, version_number)