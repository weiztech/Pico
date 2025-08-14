
import re
import time 
import datetime
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from django.core.files import File
from django.contrib.auth import get_user_model
from backend.logger import logger
from lit_reviews.models import (
    KeyWord,
    CustomKeyWord,
    ArticleReview,
    ClinicalLiteratureAppraisal,
    LiteratureReview,
    ArticleTag,
    Article,
)
from lit_reviews.helpers.ai import ai_suggest_first_pass_proccessing
from lit_reviews.helpers.articles import (
    get_clinical_appraisal_status_report, 
    form_review_search_kw,
    highlight_full_text_pdf,
)
from accounts.models import Subscription
from lit_reviews.helpers.generic import create_tmp_file

User = get_user_model()


def replace_kw_with_formated_kw(text, kw, color):
    # return text.lower().replace(
    #     " "+kw.lower().strip()+" ",
    #     " <span style='background-color:{0};'>{1}</span> ".format(color, kw),
    # )
    pattern = re.escape(kw.lower().strip())
    return re.sub(rf"\b{pattern}\b", f" <span style='background-color:{color};'>{kw}</span> ", text.lower())


def process_abstract_kw_task(abstract, title, literature_review_id, article_kws=None):
    kw = KeyWord.objects.get_or_create(literature_review__id=literature_review_id)[0]
    if kw.population:
        pop_list = kw.population.split(",")
    else:
        pop_list = []
    if kw.intervention:
        int_list = kw.intervention.split(",")
    else:
        int_list = []
    if kw.comparison:
        comp_list = kw.comparison.split(",")
    else:
        comp_list = []
    if kw.outcome:
        out_list = kw.outcome.split(",")
    else:
        out_list = []
    if kw.exclusion:
        exc_list = kw.exclusion.split(",")
    else:
        exc_list = []

    population_color = kw.population_color
    if not population_color:
        population_color = "#ebe4c2"

    intervention_color = kw.intervention_color
    if not intervention_color:
        intervention_color = "#d5cad0"

    comparison_color = kw.comparison_color
    if not comparison_color:
        comparison_color = "#c7d7cf"

    outcome_color = kw.outcome_color
    if not outcome_color:
        outcome_color = "#aec2d0"

    exclusion_color = kw.exclusion_color
    if not exclusion_color:
        exclusion_color = "#ff0000"

    default_article_kw_color = "#7FFFD4"
    for kw in pop_list:
        if kw != "" and kw != " ":
            logger.debug("replacing for kw : {0}".format(str(kw)))
            abstract = replace_kw_with_formated_kw(abstract, kw, population_color)
            title = replace_kw_with_formated_kw(title, kw, population_color)

    for kw in int_list:
        if kw != "" and kw != " ":
            logger.debug("replacing for kw : {0}".format(str(kw)))
            abstract = replace_kw_with_formated_kw(abstract, kw, intervention_color)
            title = replace_kw_with_formated_kw(title, kw, intervention_color)

    for kw in comp_list: 
        if kw != "" and kw != " ":
            logger.debug("replacing for kw : {0}".format(str(kw)))
            abstract = replace_kw_with_formated_kw(abstract, kw, comparison_color)
            title = replace_kw_with_formated_kw(title, kw, comparison_color)

    for kw in out_list:
        if kw != "" and kw != " ":
            logger.debug("replacing for kw : {0}".format(str(kw)))
            abstract = replace_kw_with_formated_kw(abstract, kw, outcome_color)
            title = replace_kw_with_formated_kw(title, kw, outcome_color)

    for kw in exc_list:
        if kw != "" and kw != " ":
            logger.debug("replacing for kw : {0}".format(str(kw)))
            abstract = replace_kw_with_formated_kw(abstract, kw, exclusion_color)
            title = replace_kw_with_formated_kw(title, kw, exclusion_color)

    if article_kws:
        article_keywords = article_kws.split(",")
        for kw in article_keywords:
            if kw != "" and kw != " ":
                logger.debug("replacing for article kw : {0}".format(str(kw)))
                abstract = replace_kw_with_formated_kw(abstract, kw, default_article_kw_color)
                title = replace_kw_with_formated_kw(title, kw, default_article_kw_color)

    # adding the custom keywords
    custom_keywords = CustomKeyWord.objects.filter(literature_review__id=literature_review_id)
    logger.debug("custom keywords : {0}".format(custom_keywords))
    for kw_item in custom_keywords:
        logger.debug("kw item : {0}".format(kw_item))
        kw_list = kw_item.custom_kw.split(",")
        for kw in kw_list:
            # special case keyword is background
            if kw == "background":
                # adding the background space 
                kw = "background "
                abstract = replace_kw_with_formated_kw(abstract, kw, kw_item.custom_kw_color)
                title = replace_kw_with_formated_kw(title, kw, kw_item.custom_kw_color)

                # adding the background dots
                kw = "background:"
                abstract = replace_kw_with_formated_kw(abstract, kw, kw_item.custom_kw_color)
                title = replace_kw_with_formated_kw(title, kw, kw_item.custom_kw_color)

            elif kw != "" and kw != " ":
                logger.debug("replacing for kw: {0}".format(str(kw)))
                abstract = replace_kw_with_formated_kw(abstract, kw, kw_item.custom_kw_color)
                title = replace_kw_with_formated_kw(title, kw, kw_item.custom_kw_color)

    logger.debug("abstract returned {0}".format(abstract))
    return abstract, title


def process_abstract_text_task(literature_review_id, review_id=None):
    reviews = ArticleReview.objects.filter(
        search__literature_review__id=literature_review_id, 
    ).prefetch_related("article").exclude(state__in=['D', 'E']).order_by("article__title")
    if review_id:
        reviews = reviews.filter(id=review_id)
        
    logger.debug("Processing abstracts for {0} reviews".format(len(reviews)))
    for rev in reviews:
        # calculate new score
        rev.score = rev.article_score
        rev.save()
        # print("adding review row to rows")
        processed_abstract, processed_title = process_abstract_kw_task(
            rev.article.abstract, 
            rev.article.title, 
            literature_review_id,
            article_kws=rev.article.keywords,
        )
        rev.processed_abstract = processed_abstract
        rev.processed_title = processed_title

        rev.save()
        # adding old article review scoring function
        # get old article review for the article and get last_old_article_review
        last_old_article_reviews = ArticleReview.objects.filter(article = rev.article).exclude(id = rev.id).order_by("-search__created_time")
        for article_rev in last_old_article_reviews:
            if article_rev.state == "I":
                rev.score = rev.score + 10
                rev.save()
                break
            elif article_rev.state == "E":
                rev.score = rev.score - 10
                rev.save()
                break
    
    logger.success(f"Keyword highlighting for review with id {literature_review_id} is completed successfully!")
    # notify active users
    channel_layer = get_channel_layer()
    room_name = f"review-room-{literature_review_id}"
    group_name = f"group_{room_name}"
    async_to_sync(channel_layer.group_send)(
        group_name,
        {
            "type": "review_kw_updated",
            "message": "kw were updated and articles were proccessed successfully",
        }
    )


def state_change_task(id, selected_state, user_id):
    from lit_reviews.tasks import check_full_article_link_async

    article_reviews = ArticleReview.objects.filter(
        search__literature_review__id=id, state=selected_state
    )
    for review in article_reviews:
        review.state = "I"
        review.save()
        check_full_article_link_async.delay(review.article.id, review.id, user_id)

    # recalculate scores based on this changment
    process_abstract_text_task(id)


def bulk_article_review_update_task(lit_review_id, review_ids, state, note, exclusion_reason, exclusion_comment, tag_ids, user_id=None):
    from lit_reviews.tasks import check_full_article_link_async

    reviews = ArticleReview.objects.filter(id__in=review_ids, search__literature_review__id=lit_review_id)
    for review in reviews:
        if state:
            review.state = state 
        if note:
            review.notes = note 
        if exclusion_reason:
            review.exclusion_reason = exclusion_reason 
        if exclusion_comment:
            review.exclusion_comment = exclusion_comment 
        if tag_ids:
            tags = ArticleTag.objects.filter(id__in=tag_ids)
            for tag in tags:
                tag.article_reviews.add(review)

        review.save()
        if review.state == "I":
            check_full_article_link_async.delay(review.article.id, review.id, user_id)

    return "success"


def recalculate_second_pass_appraisals_status_task(lit_review_id):
    appraisals = ClinicalLiteratureAppraisal.objects.filter(article_review__search__literature_review__id=lit_review_id)
    get_clinical_appraisal_status_report(appraisals, force_status_recalculation=True)


def deduct_remaining_license_credits(user_id, deducted_credits):
    user = User.objects.get(id=user_id)
    user_licence = Subscription.objects.filter(user=user).first()
    if user_licence.remaining_credits > 0:
        user_licence.remaining_credits = user_licence.remaining_credits - deducted_credits
        user_licence.save()


def generate_ai_suggestionss_first_pass_task(article_review_ids, sorting):
    article_reviews = ArticleReview.objects.filter(id__in=article_review_ids).order_by(sorting)
    for article_review in article_reviews:
        ai_suggest_first_pass_proccessing(article_review)

    lit_review = article_review.search.literature_review
    channel_layer = get_channel_layer()
    room_name = f"review-room-{lit_review.id}"
    group_name = f"group_{room_name}"
    async_to_sync(channel_layer.group_send)(
        group_name,
        {
            "type": "article_review_ai_suggestions_completed_all",
            "message": {
                "text": "AI Suggestion for All 1st pass abstracts is completed successfully!"
            },
        }
    )


def calculate_clinical_appraisal_status_task(appraisal_id):
    appraisal = ClinicalLiteratureAppraisal.objects.get(id=appraisal_id)
    
    # wait a few seconds for extraction fields updates if any!
    time.sleep(2)
    appraisal.app_status = appraisal.status
    appraisal.save()

    
def generate_highlighted_pdf_task(review_id, article_id):
    article = Article.objects.get(id=article_id) 
    review = LiteratureReview.objects.get(pk=review_id)
    tmp_file_name = str(review) + str(datetime.datetime.now()) + "-highlighted.pdf"
    tmp_file_name = tmp_file_name.replace("/", "")
    tmp_file_name_output = str(review) + str(datetime.datetime.now()) + "-highlighted-output.pdf"
    tmp_file_name_output = tmp_file_name_output.replace("/", "")

    ## AI Part is not ready yet, to be considered in the future
    #  ### TODO move the below into celery task for async processing
    # ai_search_texts = get_ai_search_texts("/tmp/" + tmp_file_name)

    search_texts = form_review_search_kw(review.id) # + ai_search_texts
    # search_texts = form_review_search_kw(review.id) + ai_search_texts
    pdf = article.full_text.file.open('r')
    file_content = pdf.read()        
    output_tmp_file_path = create_tmp_file(tmp_file_name_output, file_content)
    input_tmp_file_path = create_tmp_file(tmp_file_name, file_content)
    highlight_full_text_pdf(input_tmp_file_path, output_tmp_file_path, search_texts)

    with open(output_tmp_file_path, "rb") as output_path:
        # article.highlighted_full_text = File(output_path)
        article.highlighted_full_text.save(tmp_file_name, File(output_path))
        article.save()

    logger.success(f"PDF keyword highlighting for review with id {review_id} is completed successfully!")
    # notify active users
    channel_layer = get_channel_layer()
    room_name = f"review-room-{review_id}"
    group_name = f"group_{room_name}"
    async_to_sync(channel_layer.group_send)(
        group_name,
        {
            "type": "pdf_kw_highlighting_completed",
            "message": {
                "article_id": article_id,
                "test": "PDF keyword highlighting is completed successfully!",
            } 
        }
    )

