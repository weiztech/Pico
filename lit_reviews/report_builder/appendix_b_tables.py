
from lit_reviews.models import (
    LiteratureSearch, 
    LiteratureReviewSearchProposal, 
    ArticleReview,
    ClinicalLiteratureAppraisal,
    NCBIDatabase,
    FinalReportConfig
)
from django.db.models import Q
from lit_reviews.report_builder.utils import clear_special_characters
import collections


def appendix_b_get_dbs(lit_review_id):
    literature_searches = LiteratureSearch.objects.filter(
        literature_review__id=lit_review_id
    )

    dbs = list(
        set(
            LiteratureSearch.objects.filter(
                literature_review__id=lit_review_id
            ).exclude(db__is_recall=True).exclude(db__is_ae=True).values_list("db")
        )
    )
    dbs_list = []
    for tup in dbs:
        dbs_list.append(tup[0])

    return dbs_list


def appendix_b_process_db( db, literature_searches, retained_and_included):

    # cite_word.add_hx(
    #         "Database {0}".format(
    #             db,
    #         ),
    #         "CiteH1",
    #     )


    # table = cite_word.init_table(
    #     ["Search Term", "Citation", "State", "Included", "Justification"]
    # )
    # table.style = "Table Grid"

    print("Appendix B Processing DB: {0} - retinc_bool {1}".format(db, retained_and_included))    
    search_col = "Term" + " (" + db + ")"

    # total_included_and_retained = 0


    rows = [] 
    last_id = 0
    for lit_search in literature_searches:
        # get all articel reviews + articles.

        if retained_and_included:
            article_reviews = []

            article_reviews = ArticleReview.objects.filter(
                Q(search__id=lit_search.id),
                state="I",
                clin_lit_appr__included=True,
            ).prefetch_related("article")

#            total_included_and_retained += len(article_reviews)

        else:
            article_reviews = []
            article_reviews = ArticleReview.objects.filter(
                Q(
                    search__id=lit_search.id,
                )
            ).prefetch_related("article")

        #print("article reviews found for search: " + str(len(article_reviews)))


        #cite_word = appendix_b_results_table(cite_word, article_reviews, search_col, lit_search, table)
        rows_output, latest_id= appendix_b_results_table(article_reviews, search_col, lit_search, last_id)

        last_id = latest_id
        rows += rows_output
    #return cite_word
    return rows


def appendix_b_results_table( article_reviews, search_col, lit_search, last_id):
    pass

    rows_to_write = []
    rows_output = []

#### if there are no rows for the database, print no data.
    latest_id = last_id
 
    for review in article_reviews:
        state = "R" if review.state == "I" else review.state

        included = "N"
        if state == "R":
            for clin_lit_appr in review.clin_lit_appr.all():
                included = clin_lit_appr.included
            included = "Y" if included is True else "N"

        citation = (
            clear_special_characters(review.article.citation)
            if len(review.article.citation) > 2
            else "To Be Added: " + str(review.article.id)
        )

        exclusion_comment = f" - {review.exclusion_comment}" if review.exclusion_comment else ""
        justification = review.exclusion_reason + exclusion_comment if review.exclusion_reason else "NA"

        row = {
            "Term": lit_search.term,
            "Citation": citation,
            "S": state,
            "I": included,
            "Justification": justification,
        }
        if state == "R":  ## retained for evaluation.

            # row['Justification'] = 'Retained for Evaluation.'
            # print("article review id {0}".format(review.id))
            lit_appraisal = ClinicalLiteratureAppraisal.objects.filter(
                article_review=review
            ).first()
            if lit_appraisal.included:
                row["Justification"] = "Included"
            else:

                row["Justification"] = lit_appraisal.justification

            rows_to_write.insert(0, row)
        else:
            rows_to_write.append(row)

    # second pass processing
    final_rows_to_write = []
    for row in rows_to_write:
        if row["S"] == "R" and row["I"] == "Y":
            final_rows_to_write.insert(0, row)
        else:
            final_rows_to_write.append(row)

    for row in final_rows_to_write:

        rows_output.append(row)
    
    for row in rows_output:
        latest_id = latest_id + 1
        row['Id'] = latest_id
        #cite_word.add_table_row(table, row.values())
    return rows_output,latest_id 
    #return cite_word