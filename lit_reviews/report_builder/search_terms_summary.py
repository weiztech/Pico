import datetime

from lit_reviews.models import (
    LiteratureReviewSearchProposal,
    LiteratureReview,
)
from lit_reviews.helpers.search_terms import get_search_date_ranges

def search_terms_summary_context(lit_review_id, add_project_name=False):
    row_list = []
    header = ["Search Term", "Database", "Search Date Range",]
    if add_project_name:
        header.insert(1, "Project Number and Name")

    row_list.append(header)
    
    search_terms = {}
    lit_review = LiteratureReview.objects.get(pk=lit_review_id)
    props = LiteratureReviewSearchProposal.objects.filter(
        literature_review__id=lit_review_id
    ).order_by("id")
    for prop in props:
        if prop.literature_search:
            if prop.term in search_terms:
                search_terms[prop.term]["dbs"] = [*search_terms[prop.term]["dbs"], prop.db.name]
                start_date, end_date = get_search_date_ranges(prop.literature_search)
                start_date = start_date.date() if isinstance(start_date, datetime.datetime) else start_date
                end_date = end_date.date() if isinstance(end_date, datetime.datetime) else end_date 
                search_terms[prop.term]["date_ranges"] = [*search_terms[prop.term]["date_ranges"], f"{start_date} to {end_date}"]
            else:
                start_date, end_date = get_search_date_ranges(prop.literature_search)
                start_date = start_date.date() if isinstance(start_date, datetime.datetime) else start_date
                end_date = end_date.date() if isinstance(end_date, datetime.datetime) else end_date 
                search_terms[prop.term] = {
                    "dbs": [prop.db.name],
                    "date_ranges": [f"{start_date} to {end_date}"]
                }
    
    for key, value in search_terms.items():
        row=[]
        search_term = key
        row.append(str(search_term))

        # project name
        if add_project_name:
            row.append(f"#{str(lit_review.id)} {str(lit_review)}")

        database = ", ".join(value["dbs"])
        row.append(str(database))

        date_range = ", ".join(value["date_ranges"])
        row.append(str(date_range))

        row_list.append(row)

    return row_list



def get_appraisal_field_value(value):
    if value:
        return value
    else:
        return ""



        
