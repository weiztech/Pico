import os
import shutil
from datetime import datetime, timedelta

from lit_reviews.models import (
    ArticleReview, 
    LivingReview, 
    ArticleReviewDeviceMention,
    LiteratureReview,
    LiteratureSearch,
)
from backend.logger import logger 
from lit_reviews.helpers.generic import count_word_occurrences

def delete_temp_files_task():
    # Get the system temporary directory
    temp_dir = "tmp/"
    # Get today's and yesterday's date
    today = datetime.now().date()
    yesterday = today - timedelta(days=1)
    deleted = []

    for item in os.listdir(temp_dir):
        item_path = os.path.join(temp_dir, item)

        try:
            # Get the last modified date
            modify_time = datetime.fromtimestamp(os.path.getmtime(item_path)).date()

            # If it was modified yesterday, delete it
            if modify_time <= yesterday:
                item_path_str = str(item_path)
                if os.path.isfile(item_path) or os.path.islink(item_path):
                    os.remove(item_path)
                elif os.path.isdir(item_path):
                    shutil.rmtree(item_path)

                deleted.append(item_path_str)

        except Exception as e:
            logger.warning(f"Error processing {item_path}: {e}")

    # Report
    if deleted:
        logger.info("Deleted the following items modified yesterday:")
        for path in deleted:
            logger.info("* " + path)
    else:
        logger.info("No items modified yesterday were found.")


def process_article_review_device_mentions_task(review_id):
    literature_review = LiteratureReview.objects.filter(id=review_id).first()
    living_review = literature_review.parent_living_review
    searches = LiteratureSearch.objects.filter(literature_review=literature_review)
    for search in searches:
        article_reviews = ArticleReview.objects.filter(search=search).all()

        for article_review in article_reviews:
            logger.info(f"process article review id {article_review.id} for device mentions")

            # under evaluation
            under_evaluation_device = living_review.project_protocol.device
            under_evaluation_mentions = count_word_occurrences(article_review.article.title ,under_evaluation_device.name)
            under_evaluation_mentions += count_word_occurrences(article_review.article.abstract ,under_evaluation_device.name)
            if under_evaluation_mentions:
                ArticleReviewDeviceMention.objects.create(
                    device=under_evaluation_device,
                    article_review=article_review,
                    mentions_count=under_evaluation_mentions,
                    device_type="under_evaluation"
                )

            # similar devices
            for device in living_review.similar_devices.all():
                similar_mentions = count_word_occurrences(article_review.article.title ,device.name)
                similar_mentions += count_word_occurrences(article_review.article.abstract ,device.name)
                if similar_mentions:
                    ArticleReviewDeviceMention.objects.create(
                        device=device,
                        article_review=article_review,
                        mentions_count=similar_mentions,
                        device_type="similar"
                    )

            # competitor devices
            for device in living_review.competitor_devices.all():
                competitor_mentions = count_word_occurrences(article_review.article.title ,device.name)
                competitor_mentions += count_word_occurrences(article_review.article.abstract ,device.name)
                if competitor_mentions:
                    ArticleReviewDeviceMention.objects.create(
                        device=device,
                        article_review=article_review,
                        mentions_count=competitor_mentions,
                        device_type="competitor"
                    )