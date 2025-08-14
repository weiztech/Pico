
import os
from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q
from backend.logger import logger
from lit_reviews.models import (
    LiteratureReviewSearchProposal,
    Article,
    ArticleReview,
    NCBIDatabase,
    ExclusionReason,
    LiteratureSearch, 
    LiteratureReview, 
    ClinicalLiteratureAppraisal,
    ArticleTag,
)
from lit_reviews.report_builder.cite_word import CiteWordDocBuilder, CiteProtocolBuilder

import os


def prisma(lit_review_id=None):
    ## records identified through device search
    project = LiteratureReview.objects.get(id=lit_review_id)
    project_name = "{0} - {1} - {2}".format(project.id, project.client, project.device) 
    all_reviews = ArticleReview.objects.filter(search__literature_review__id=lit_review_id).count()

    ## additioanl records identified throug SoTa search
    sota_extra_reviews = ArticleReview.objects.filter(search__literature_review__id=lit_review_id,
        search__db__entrez_enum='embase'
    ).count()


    ## records after duplicates removed.
    reviews_no_dupes = ArticleReview.objects.filter(Q( Q(search__literature_review__id=lit_review_id) & ~Q(state='D'))).count()

    ## records screened (total from above)
    total_screened = reviews_no_dupes

    ## records excluded
    reviews_excluded = ArticleReview.objects.filter(Q( Q(search__literature_review__id=lit_review_id) & Q(state='E'))).count()
    reviews_excluded_full = ArticleReview.objects.filter(Q( Q(search__literature_review__id=lit_review_id) & Q(state='E'))).order_by('exclusion_reason')
    with open('exclusion_reasons_all.csv', 'w') as f:
        for review in reviews_excluded_full:
            f.write("{0}, \n".format(review.exclusion_reason))

    ## articles marked as retained
    reviews_retained = ArticleReview.objects.filter(Q( Q(search__literature_review__id=lit_review_id) & Q(state='I'))).count()

    ## articles marked as retained and included. 
    reviews_retained_included = ClinicalLiteratureAppraisal.objects.filter(
        article_review__search__literature_review__id=lit_review_id,
        article_review__state='I',
        included=True,
    ).count()
    ft_reviews_excluded = ClinicalLiteratureAppraisal.objects.filter(
        article_review__search__literature_review__id=lit_review_id,
        article_review__state='I',
        included=False,
    ).count()

    context = {"exclusion_reason_counts": {}}
    context['all_reviews'] = str(all_reviews)
    context['sota_extra_reviews'] = sota_extra_reviews
    context['reviews_no_dupes'] = reviews_no_dupes
    context['total_screened'] = total_screened
    context['reviews_excluded'] = reviews_excluded
    context['reviews_retained'] = reviews_retained
    context['ft_reviews_excluded'] = ft_reviews_excluded
    context['ft_included_synth'] =  reviews_retained - ft_reviews_excluded
    context['duplicates_reviews'] =  all_reviews - reviews_no_dupes
    context['total_reviews'] = (all_reviews - reviews_no_dupes) +  reviews_excluded  + ft_reviews_excluded

    # reviews excluded per each exclusion reason.
    exclusion_reasons = ExclusionReason.objects.filter(literature_review__id=lit_review_id)

    # context['no_reson_articles'] = sum(1 for article in all_articles if not any(article.exclusion_reason == reason.reason for reason in exclusion_reasons))
    exclusion_count = 0
    exclusion_reasons_rows = []

    for reason in exclusion_reasons:
        excludeds = ArticleReview.objects.filter(Q( Q(search__literature_review__id=lit_review_id) & Q(state='E') & Q(exclusion_reason=reason.reason))).count()
        row = {"Reason": reason.reason, "Count": excludeds} 
        exclusion_reasons_rows.append(row)
        exclusion_count += excludeds
    
    # Count the  articles with  a reason not montiend in the exclusion_reasons
    all_articles = ArticleReview.objects.filter(Q( Q(search__literature_review__id=lit_review_id) & Q(state='E')))
    other_exclusion_reasons = []
    for article in all_articles: 
        if not any(article.exclusion_reason == reason.reason for reason in exclusion_reasons) and article.exclusion_reason not in other_exclusion_reasons  and article.exclusion_reason != "" and article.exclusion_reason != None:
            # add the new reason
            print("article id",article.id)
            other_exclusion_reasons.append(article.exclusion_reason)
            # count the articles with this reason
            excludeds = ArticleReview.objects.filter(Q( Q(search__literature_review__id=lit_review_id) & Q(state='E') & Q(exclusion_reason=article.exclusion_reason))).count()
            row = {"Reason": article.exclusion_reason, "Count": excludeds} 
            exclusion_reasons_rows.append(row)
            exclusion_count += excludeds

    context['exclusion_reason_counts']['rows'] = exclusion_reasons_rows 
    context['exclusion_reason_counts']['custom'] = str(reviews_excluded-exclusion_count)
    context['exclusion_reason_counts']['ft-excluded'] = str( int(reviews_retained) - int(reviews_retained_included))
    context['exclusion_reason_counts']['retinc'] = str(reviews_retained_included)

    return context


def prisma_summary_excel_context(lit_review_id):
    row_list = []
    header = ["Label", "Count"]
    row_list.append(header)

    prisma_context_output = prisma(lit_review_id)
    row_list.append(["Records Identified Through Database Searching", prisma_context_output["all_reviews"] ])
    row_list.append(["Additional Records Identified", prisma_context_output["sota_extra_reviews"] ])
    row_list.append(["Records After Duplicates Removed", prisma_context_output["reviews_no_dupes"] ])
    row_list.append(["Records Screened", prisma_context_output["total_screened"] ])
    row_list.append(["Records Excluded", prisma_context_output["reviews_excluded"] ])
    row_list.append(["Full-Text Articles Assessed for Eligibility", prisma_context_output["reviews_retained"] ])
    row_list.append(["Full-Text Articles Excluded", prisma_context_output["ft_reviews_excluded"] ])
    row_list.append(["Studies Included in Qualitative Synthesis (Meta-Analysis)", prisma_context_output["ft_included_synth"] ])
    
    return row_list


def prisma_excluded_articles_summary_context(lit_review_id):
    row_list = []
    header = ["Reason", "Count"]
    row_list.append(header)

    prisma_context_output = prisma(lit_review_id)
    row_list.append(["Duplicates", prisma_context_output["duplicates_reviews"] ])
    for exclusion_reason in prisma_context_output['exclusion_reason_counts']['rows']:
        row_list.append([exclusion_reason["Reason"], exclusion_reason["Count"] ])

    row_list.append(["Full-Text Articles Excluded", prisma_context_output["ft_reviews_excluded"] ])
    row_list.append(["Total", prisma_context_output["total_reviews"] ])

    return row_list

def prisma_article_tags_summary_context(lit_review_id):
    row_list = []
    header = ["Article Tag", "Included", "Excluded", "Duplicate", "Maybe", "Unclassified", "Total Tag Count"]
    row_list.append(header)

    article_tags = ArticleTag.objects.filter(literature_review=lit_review_id)
    for tag in article_tags:
        tag_article_reviews = ArticleReview.objects.filter(tags__in=[tag])
        total_count = tag_article_reviews.count()
        included_count = tag_article_reviews.filter(state="I").count()
        excluded_count = tag_article_reviews.filter(state="E").count()
        unclassified_count = tag_article_reviews.filter(state="U").count()
        maybe_count = tag_article_reviews.filter(state="M").count()
        duplicate_count = tag_article_reviews.filter(state="D").count()
        row_list.append([tag.name, included_count, excluded_count, duplicate_count, maybe_count, unclassified_count, total_count])

    return row_list