import rispy
import re
from lit_reviews.models import (
    ClinicalLiteratureAppraisal,
    LiteratureReview,
    ArticleReview,
    AppraisalExtractionField,
)
from lit_reviews.helpers.articles import ( 
    get_or_create_appraisal_extraction_fields,
)
from lit_reviews.helpers.generic import create_tmp_file
from lit_reviews.helpers.reports import form_ris_entry

def second_pass_articles_context(lit_review_id, add_project_name=False):
    appraisals = ClinicalLiteratureAppraisal.objects.filter(
        article_review__search__literature_review__id=lit_review_id, article_review__state="I"
    )
    row_list = []
    header = [
        "ID", #1
        "Title", #2
        "Abstract", #3
        "Citation", #4
        "Search Term", #9
        "Search Performed Date", #10
        "Status", #5
        "Score", #6
        "Included Appraisal?", #7
        "Justification", #8
    ]
    if add_project_name:
        header.insert(1, "#Project Number and Name")

    # Add Extraction fields #9
    lit_review = LiteratureReview.objects.get(pk=lit_review_id)
    extra_extractions = lit_review.extraction_fields.order_by("-field_section")
    for extra_extraction in extra_extractions:
        if extra_extraction.description:
            header.append(extra_extraction.description)
        else:
            header.append(extra_extraction.name.replace("_", " ").title())

    row_list.append(header)
    for app in appraisals:
        sub_extractions = list(
            AppraisalExtractionField.objects.filter(
                extraction_field=extra_extractions.first(), 
                clinical_appraisal=app,    
            ).distinct("extraction_field_number").values_list("extraction_field_number", flat=True)
        )
        for sub_extraction in sub_extractions:
            row=[]
            article_review = app.article_review

            # appraisal id #1
            row.append(str(app.id)) 
            # project name
            if add_project_name:
                row.append(f"#{str(lit_review.id)} {str(lit_review)}")
            # appraisal article title #2
            row.append(article_review.article.title)
            # appraisal article abstract #3
            row.append(article_review.article.abstract)
            # appraisal article citation #4
            row.append(article_review.article.citation)
            # article review search term #9
            row.append(get_appraisal_field_value(article_review.search.term))
            # article review performed date #10
            script_time = get_appraisal_field_value(article_review.search.script_time) 
            script_time =  script_time.strftime("%m/%d/%Y %H:%M") if script_time else ""
            row.append(script_time)
            # appraisal status #5
            row.append(get_appraisal_field_value(app.status))

            # appraisal article score #6
            row.append(article_review.score)

            # appraisal article score #7
            row.append(app.included)

            # appraisal article score #8
            row.append(app.justification)
            
            # Add Extraction fields #9
            for extra_extraction in extra_extractions:
                appraisal_extraction_field = get_or_create_appraisal_extraction_fields(app, extra_extraction, False, sub_extraction)
                if not appraisal_extraction_field:
                    row.append("")
                else:
                    row.append(get_appraisal_field_value(appraisal_extraction_field.value))

            # add new appraisal row
            row_list.append(row)
    
    return row_list



def get_appraisal_field_value(value):
    if value != None:
        return value
    else:
        return ""
    

def second_pass_articles_ris(lit_review_id, document_name):
    filepath = create_tmp_file(document_name, "")
    appraisals = ClinicalLiteratureAppraisal.objects.filter(
        article_review__search__literature_review__id=lit_review_id, article_review__state="I"
    )
    article_reviews = ArticleReview.objects.filter(search__literature_review__id=lit_review_id, state="I")
    entries = []

    for app in appraisals:
        article_review = app.article_review
        entry = form_ris_entry(article_review, article_reviews)
        entries.append(entry)

    with open(filepath, 'w') as bibliography_file:
        rispy.dump(entries, bibliography_file)

    return filepath