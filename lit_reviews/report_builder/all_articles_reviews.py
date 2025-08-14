import uuid
import rispy 
from backend.logger import logger
from django.urls import reverse

from backend.settings import SITE_URL 
from lit_reviews.models import (
    ArticleReview,
    LiteratureReview,
    DuplicatesGroup,
    AppraisalExtractionField,
)
from lit_reviews.helpers.articles import ( 
    get_or_create_appraisal_extraction_fields,
)
from lit_reviews.helpers.generic import create_tmp_file
from lit_reviews.helpers.articles import get_unclassified_and_duplicate_for_article, generate_url_article_reviews
from lit_reviews.helpers.reports import form_ris_entry

def all_articles_reviews_context(lit_review_id, add_project_name=False):
    reviews = ArticleReview.objects.filter(
        search__literature_review__id=lit_review_id
    ) 
    return generate_excel_context(reviews, lit_review_id, add_project_name)


def generate_excel_context(reviews, lit_review_id=None, add_project_name=False):
    row_list = []
    header = [
        "ID", 
        "Search Term", 
        "Search Performed Date",
        "Database Name",
        "Title",
        "Abstract",
        "Citation",
        "Status",
        "Article Tags",
        "Exclusion Reason",
        "Score",  
        "Article Link",
        "Full Text Link"
    ]
    if add_project_name:
        header.insert(1, "Project Number and Name")

    # Add Extraction fields
    if lit_review_id: # Include Extraction Fields only if review_id is provided otherwise generate excel without extractions columns
        lit_review = LiteratureReview.objects.get(pk=lit_review_id)
        extra_extractions = lit_review.extraction_fields.order_by("-field_section")
        for extra_extraction in extra_extractions:
            if extra_extraction.description:
                header.append(extra_extraction.description)
            else:
                header.append(extra_extraction.name.replace("_", " ").title())

    
    row_list.append(header)

    for review in reviews:
        app = None
        sub_extractions = [1] # by default one sub extraction if retained, if not retained we only need to include the appraisal once same as default
        if review.get_state_display() == "Retained":
            app =  review.clin_lit_appr.first()
            sub_extractions = list(
                AppraisalExtractionField.objects.filter(
                    extraction_field=extra_extractions.first(), 
                    clinical_appraisal=app,    
                ).distinct("extraction_field_number").values_list("extraction_field_number", flat=True)
            )

        for sub_extraction in sub_extractions:
            row=[]
            # article review id
            row.append(str(review.id))
            # project name
            if add_project_name:
                row.append(f"#{str(lit_review.id)} {str(lit_review)}")
            # article review search term
            row.append(get_appraisal_field_value(review.search.term))
            # article review performed date
            script_time = get_appraisal_field_value(review.search.script_time) 
            script_time =  script_time.strftime("%m/%d/%Y %H:%M") if script_time else ""
            row.append(script_time)
            # article review search db
            row.append(get_appraisal_field_value(review.search.db))
            # article review title
            row.append(get_appraisal_field_value(review.article.title))
            # article review abstract
            row.append(get_appraisal_field_value(review.article.abstract))
            # article review citation
            row.append(get_appraisal_field_value(review.article.citation))
            # appraisal status
            row.append(review.get_state_display())
            
            # article tags 
            tags = [tag.name for tag in review.tags.all()] 
            row.append(", ".join(tags))

            # article review exclusion_reason
            if review.get_state_display() == "Excluded":
                exclusion_comment = f" - {review.exclusion_comment}" if review.exclusion_comment else ""
                row.append(
                    get_appraisal_field_value(review.exclusion_reason) + exclusion_comment
                )
            else:
                row.append("Not applicable")

            # article review  score
            row.append(get_appraisal_field_value(review.score))

            # article link
            if review.article.url:
                article_link =  review.article.url
            else:     
                article_link = generate_url_article_reviews(review.article, review.search.db.entrez_enum)
            
            row.append(article_link)

            # Full Text Link
            if review.article.full_text:
                # we can't feed it review.article.full_text.url directly since this link is private and can be accessed only temporary 
                full_text_link = SITE_URL + reverse(
                    "literature_reviews:review_article_full_text_pdf", 
                    kwargs={"id": review.search.literature_review.id, "review_id": review.id}
                )
                row.append(full_text_link)
            else:
                row.append("Not Uploaded")

            # clinical apparsial fileds
            if app:
                # Add Extraction Fields
                for extra_extraction in extra_extractions:
                    appraisal_extraction_field = get_or_create_appraisal_extraction_fields(app, extra_extraction, False, sub_extraction)
                    if not appraisal_extraction_field:
                        row.append("")
                    else:
                        row.append(get_appraisal_field_value(appraisal_extraction_field.value))

            row_list.append(row)
    
    return row_list


def get_appraisal_field_value(value):
    if value != None:
        return value
    else:
        return ""
    

def generate_article_duplicates_content(review_id=None, include_all_if_no_dups=True):
    headers = ["Article ID", "Duplicate ID", "Title", "State", "Database", "Citation"]
    articles_excel_list = []
    articles_excel_list.append(headers)
    duplicate_groups = None
    if review_id:
        duplicate_groups = DuplicatesGroup.objects.filter(original_article_review__search__literature_review__id=review_id).all()
        lit_review = LiteratureReview.objects.get(id=review_id)
        reviews = ArticleReview.objects.filter(search__literature_review=lit_review)
    else:
        reviews = ArticleReview.objects.all()

    if duplicate_groups:
        for dup_group in duplicate_groups:
            DUP_ID = uuid.uuid4().hex
            articles_excel_list.append(
                [
                    dup_group.original_article_review.id, 
                    DUP_ID, 
                    dup_group.original_article_review.article.title, 
                    dup_group.original_article_review.get_state_display(), 
                    dup_group.original_article_review.search.db.name,
                    dup_group.original_article_review.article.citation, 
                ]
            )
            for dup in dup_group.duplicates.all():
                articles_excel_list.append(
                    [
                        dup.id, 
                        DUP_ID, 
                        dup.article.title, 
                        dup.get_state_display(), 
                        dup.search.db.name,
                        dup.article.citation, 
                    ]
                )
            articles_excel_list.append([None, None, None, None, None])

    elif include_all_if_no_dups:   
        for review in reviews:
                review_was_processed = any([row[0] == review.id for row in articles_excel_list])
                if not review_was_processed:
                    article_dups_plus_original, unclassified, duplicated = get_unclassified_and_duplicate_for_article(review, reviews)
                    logger.debug(f"Number of duplicates including original for {review.article.title} is {len(article_dups_plus_original)}")

                    # this is for the excel report:
                    DUP_ID = uuid.uuid4().hex
                    for review_dup in article_dups_plus_original:
                        excel_list_article = None
                        excel_list_article_index = None
                        for i in range(0, len(articles_excel_list)):
                            item = articles_excel_list[i]
                            if item[0] == review_dup.id:
                                excel_list_article = item 
                                excel_list_article_index = i
                                break

                        if not excel_list_article:
                            articles_excel_list.append(
                                [
                                    review_dup.id, 
                                    DUP_ID, 
                                    review_dup.article.title, 
                                    review_dup.get_state_display(), 
                                    review_dup.search.db.name,
                                    review_dup.article.citation, 
                                ]
                            )

                        elif len(article_dups_plus_original) > 1:
                            excel_list_article[1] = DUP_ID
                            articles_excel_list[excel_list_article_index] = excel_list_article

                # add empty row between list of duplicates
                articles_excel_list.append([None, None, None, None, None])

    logger.info("Number of duplicates: " + str(reviews.filter(state="D").count()))
    return articles_excel_list


def get_article_reviews_ris(lit_review_id, document_name):
    filepath = create_tmp_file(document_name, "")
    article_reviews = ArticleReview.objects.filter(search__literature_review__id=lit_review_id)
    entries = []

    for article_review in article_reviews:
        entry = form_ris_entry(article_review, article_reviews)
        entries.append(entry)

    with open(filepath, 'w') as bibliography_file:
        rispy.dump(entries, bibliography_file)

    return filepath