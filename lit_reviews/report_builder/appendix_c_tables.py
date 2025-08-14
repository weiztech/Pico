

import traceback
from lit_reviews.models import (
    ClinicalLiteratureAppraisal,
    ExtractionField,
)
from django.db.models import Q
import collections

from lit_reviews.report_builder.utils import (
    get_grade_score, 
    clear_special_characters,
    construct_appraisal_data_contribution, 
    construct_appraisal_data_suitability,
    SUITABILITY_VALUES_SYMBOLES,
)
from lit_reviews.helpers.articles import get_or_create_appraisal_extraction_fields
from backend.logger import logger

def sota_table(retained_reviews, lit_review_id):

    try:
        for review in retained_reviews:
            lit_appraisal = ClinicalLiteratureAppraisal.objects.get(
                article_review=review
            )

            if lit_appraisal.is_sota_article is None:
                raise Exception("retained review without device/sota declaration")

        if len(retained_reviews) == 0:
            return []
    
        output = {}
        headers = []
        sota_fields = ExtractionField.objects.filter(field_section="ST", literature_review__id=lit_review_id)
        for extraction in sota_fields:
            header_value = extraction.name_in_report if extraction.name_in_report else extraction.name.title()
            headers.append(header_value)
        
        output["headers"] = headers
        rows = []
        index = 0
        for review in retained_reviews:
            lit_appraisal = ClinicalLiteratureAppraisal.objects.get(
                article_review=review
            )
            index += 1
            row = {
                "id": index,
                "citation": clear_special_characters(review.article.citation),
                "cols":  [] # Extra dynamic cols
            }
            lit_appraisal = ClinicalLiteratureAppraisal.objects.get(article_review=review)
            for extraction in sota_fields: 
                app_extraction_field = get_or_create_appraisal_extraction_fields(lit_appraisal, extraction)
                if app_extraction_field.value != None and app_extraction_field.value != "":
                    row["cols"].append(app_extraction_field.value)
                else:
                    row["cols"].append("NA")
            rows.append(row)

        output["content"] = rows 
        return output
    

    except Exception as e:
        import traceback
        print(traceback.format_exc())
        raise Exception("Appendix C exception in sota_table: {0} ".format(e))



##3 t1 
def device_suitability_appraisal(retained_reviews, lit_review_id):

    try:
        if len(retained_reviews) == 0:
            return []

        output = {}
        suitability_extraction_fields = ExtractionField.objects.filter(field_section="SO", literature_review__id=lit_review_id)
        t1_cols = []
        for extraction in suitability_extraction_fields:
            t1_cols.append(extraction.name_in_report)
        output["headers"] = t1_cols
        rows = []
        index = 0 
        for review in retained_reviews:
            index = index + 1
            t1_row = {
                "id": str(index),
                "citation": clear_special_characters(review.article.citation),
                "cols":  [] # Extra dynamic cols
            } 
            lit_appraisal = ClinicalLiteratureAppraisal.objects.get(article_review=review)
            for extraction in suitability_extraction_fields: 
                app_extraction_field = get_or_create_appraisal_extraction_fields(lit_appraisal, extraction)
                if app_extraction_field.value and extraction.name in SUITABILITY_VALUES_SYMBOLES.keys():
                    value = SUITABILITY_VALUES_SYMBOLES[extraction.name][app_extraction_field.value]
                    t1_row["cols"].append(value)
                else:
                    t1_row["cols"].append(app_extraction_field.value)
                    
            rows.append(t1_row)
        
        output["content"] = rows
        return output
    
    except Exception as e:

        raise Exception("Appendix C Exception in device_suitability_appraisal: {0}".format(e))



def summary_data_contribution_outcomes_appraisal(retained_reviews, lit_review_id):
    try:
        if len(retained_reviews) == 0:
            return []

        output = {}
        headers = []
        quality_and_cont_fields = ExtractionField.objects.filter(field_section="QC", literature_review__id=lit_review_id)
        for extraction in quality_and_cont_fields:
            header_value = extraction.description if extraction.description else extraction.name.title()
            headers.append(header_value)
        
        output["headers"] = headers
        rows = []
        index = 0
        for review in retained_reviews:
            lit_appraisal = ClinicalLiteratureAppraisal.objects.get(
                article_review=review
            )
            index += 1
            row = {
                "id": index,
                "citation": clear_special_characters(review.article.citation),
                "cols":  [] # Extra dynamic cols
            }
            lit_appraisal = ClinicalLiteratureAppraisal.objects.get(article_review=review)
            for extraction in quality_and_cont_fields: 
                app_extraction_field = get_or_create_appraisal_extraction_fields(lit_appraisal, extraction)
                symbole = "T" if extraction.name == "design_yn" else extraction.name[0].upper()
                value = symbole+"1" if app_extraction_field.value.lower() == "yes" else symbole+"2"
                row["cols"].append(value)
            rows.append(row)

        output["content"] = rows 
        return output

    except Exception as e:
        logger.error('Appendix C exception in summary_data_contribution_outcomes_appraisal: {}'.format(e))
        raise Exception("""
            Appendix C Error Please make sure all your Extraction fields are filled out inside the 2nd pass extractions
            Seems like some fields related to Quality and Contribution Questions are empty make sure to fill them out!
        """)



def data_extraction_summary_table(retained_reviews, extr_config ):

    try:
        if len(retained_reviews) == 0:
            return []

        #print("building T4 - appendix C")
        ## need to do something with the headers
        t4_cols = [
            "ID",
            "Safety" if extr_config.safety else "",
            "Performance" if extr_config.performance else "",
            "Adverse Events" if extr_config.adverse_events else "",
            "SoTA" if extr_config.sota else "",
            "Guidance" if extr_config.guidance else "",
            "Other" if extr_config.other else "",
            "Study Design" if extr_config.study_design else "",
            "Total Sample Size?" if extr_config.total_sample_size else "",
            "Objective" if extr_config.objective else "",
            "Treatment Modality" if extr_config.treatment_modality else "",
            "Study Conclusions" if extr_config.study_conclusions else "",
            "GRADE Evidence" if extr_config.grade else "",
            #"MDCG-2020-6 Data Evidence Rank" if extr_config. else "",
        ]
        t4_cols = [item for item in t4_cols if item ]  

        rows = []
        index = 0
        for review in retained_reviews:

            lit_appraisal = ClinicalLiteratureAppraisal.objects.get(article_review=review)

            if lit_appraisal.is_sota_article is False and lit_appraisal.included is True:       
                index = index + 1

                if extr_config.grade:

                    grade_score = get_grade_score(lit_appraisal)
                ## this is the 'short summary' table
                t4_row = {
                    # review.article.citation,

                    "id": index,
                    "Safety": lit_appraisal.safety_short if extr_config.safety else "",
                    "Performance": lit_appraisal.performance_short if extr_config.performance else "",
                    "Adverse Events": lit_appraisal.adverse_events_short if extr_config.adverse_events else "",
                    "SoTA": lit_appraisal.sota_short if extr_config.sota else "",
                    "Guidance": lit_appraisal.guidance_short if extr_config.guidance else "",
                    "Other": lit_appraisal.other_short if extr_config.other else "",
                    "Study Design": lit_appraisal.study_design_short if extr_config.study_design else "",
                    "Total Sample Size": lit_appraisal.total_sample_size_short if extr_config.total_sample_size else "",
                    "Objective": lit_appraisal.objective_short if extr_config.objective else "",
                    "Treatment Modality": lit_appraisal.treatment_modality_short if extr_config.treatment_modality else "",
                    "Study Conclusions": lit_appraisal.study_conclusions_short if extr_config.study_conclusions else "",
                    "GRADE Numerical Score": grade_score if extr_config.grade else "",
                    # data_evidence_rank?
                }
                #t4_row = [item for item in t4_row if item] Dont need.
                rows.append(t4_row)
        return rows
        
    except Exception as e:
        raise Exception('Appendix C excpetion in data_extraction_summary_table: {0} '.format(e))


## for retained and included articles.
def data_extraction_detailed_paragraphs(retained_reviews, lit_review_id):

    try:
        if len(retained_reviews) == 0:
            return []

        rows = []
        index_2 = 0
        for review in retained_reviews:

            row = {}
            lit_appraisal = ClinicalLiteratureAppraisal.objects.get(
                article_review=review
            )

            if (
                lit_appraisal.included
                and lit_appraisal.is_sota_article is False
            ):
                index_2 = index_2 + 1

                row['id'] = index_2
                row['Citation'] = clear_special_characters(review.article.citation) #review.article.citation
                
            #     if extr_config.safety:
            #         row['Safety'] = lit_appraisal.safety
            #     else:
            #         row['Safety'] = None

            #     # cite_word.add_hx('Performance', 'CiteH3')
            #     # cite_word.add_p(lit_appraisal.performance.replace('||', ' - '))
                
            #     if extr_config.performance:
            #         row['Performance'] = lit_appraisal.performance.replace("||", " - ")
            #     else:
            #         row['Performance'] = None
            #   #  print("after performance")

            #     if extr_config.adverse_events: 
            #         row['Adverse Events'] = lit_appraisal.adverse_events.replace("||", " - ")
            #     else:
            #         row['Adverse Events'] = None
            #    # print("after adverse events")

            #     # if extr_config.sota:
            #     #     row['SoTA'] = lit_appraisal.sota.replace("||", " - ")

            #     # else:
            #     #     row['SoTA'] = None

            #     if extr_config.guidance:
            #         row['Guidance'] = lit_appraisal.guidance.replace("||", " - ")
            #     else:
            #         row['Guidance'] = None

            #     if extr_config.other:
            #         row['Other'] = lit_appraisal.other.replace("||", " - ")
            #     else:
            #         row['Other'] = None

            #     if extr_config.study_design:
            #         row['Study Design'] = lit_appraisal.study_design.replace("||", " - ")
            #     else:
            #         row['Study Design'] = None 

            #     if extr_config.total_sample_size:
            #         row['Total Sample Size'] =  lit_appraisal.total_sample_size.replace("||", " - ")
            #     else:
            #         row['Total Sample Size'] = None 

            #     if extr_config.objective:
            #         row['Objective'] = lit_appraisal.objective.replace("||", " - ")
            #     else:
            #         row['Objective'] = None 
                
            #     if extr_config.treatment_modality:
            #         row['Treatment Modality'] = lit_appraisal.treatment_modality.replace("||", " - ")
            #     else:
            #         row['Treatment Modality'] = None 

            #     if extr_config.adverse_events:
            #         row['Adverse Events'] = lit_appraisal.adverse_events.replace("||", " - ")
            #     else:
            #         row['Adverse Events'] = None 

            #     if extr_config.study_conclusions:
            #         row['Study Conclusions'] = lit_appraisal.study_conclusions.replace("||", " - ")
            #     else:
            #         row['Study Conclusions'] = None 

            #     if lit_appraisal.indication:
            #         row['Indication'] = lit_appraisal.indication.replace("||", " - ")
            #     else:
            #         row['Indication'] = None 

            #     if lit_appraisal.device_name:
            #         row['Device'] = lit_appraisal.device_name.replace("||", " - ")
            #     else:
            #         row['Device'] = None 


                # Extraction fields
                row["extra_fields"] = []
                for extra_field in lit_appraisal.fields.filter(extraction_field__field_section="EF").order_by("extraction_field__field_order"):
                    # Check if the extra_field value is valid before replacing
                    if extra_field.value:
                        value = extra_field.value.replace("||", " - ")
                    else:
                        value = "NA"
                        
                    row["extra_fields"].append({
                        "name": extra_field.extraction_field.name.replace("_", " ").title(),
                        "value": value,
                        "category": extra_field.extraction_field.category,
                    })

                if (
                    lit_appraisal.justification is not None
                    and len(lit_appraisal.justification) > 1
                ):
                    row['Additional Comments'] = lit_appraisal.justification
                else:
                    row['Additional Comments'] = None 

                # MDCG Ranking
                extraction_field = ExtractionField.objects.filter(name="mdcg_ranking", literature_review__id=lit_review_id).first()
                if extraction_field:
                    app_extraction_field = get_or_create_appraisal_extraction_fields(lit_appraisal, extraction_field)
                    row["Rank"] = app_extraction_field.value

                row['Grade 02'] = construct_appraisal_data_contribution(lit_appraisal, lit_review_id)
                row['Grade 01'] = construct_appraisal_data_suitability(lit_appraisal, lit_review_id)

                rows.append(row)
                
        return rows

    except Exception as e:
        raise Exception('Appendix C exception in data_extraction_detailed_paragraphs: {0}'.format(e))


def retained_citations_not_appraised(excluded_reviews ):


    try:
        if len(excluded_reviews) == 0:
            return []
        # t_excluded_cols = ["Citation", "Justification"]
        # t_excluded = cite_word.init_table(t_excluded_cols)
        # t_excluded.style = "Table Grid"
        rows = []
        for review in excluded_reviews:
            lit_appraisal = ClinicalLiteratureAppraisal.objects.get(article_review=review)
            # cite_word.add_table_row(
            #     t_excluded, [review.article.citation, lit_appraisal.justification]
            # )
            row = {}
            row['Citation'] = clear_special_characters(review.article.citation)
            row['Justification']  = clear_special_characters(lit_appraisal.justification)
            rows.append(row)
            # rows.append({"Citation":review.article.citation, "Justification": lit_appraisal.justification})
        return rows

    except Exception as e:

        raise Exception('Appendix C exception in retained_citations_not_appraised: {0}'.format(e))

