from django.utils import timezone
from django.urls import reverse
import matplotlib.pyplot as plt
from tempfile import NamedTemporaryFile

from lit_reviews.models import NCBIDatabase, LiteratureSearch, LiteratureReviewSearchProposal
import pytz

from backend.logger import logger
from backend.settings import SITE_URL 
from lit_reviews.tasks import run_auto_search


def construct_chart_image(categories, values, title, x_lable, y_label, file_temp, type="bar"):
    # Sample data
    # categories = ['Category A', 'Category B', 'Category C', 'Category D', 'Category E']
    # values = [10, 15, 13, 18, 16]

    # Create a figure and axis
    fig, ax = plt.subplots()

    if type == "bar":
        # Create a vertical bar chart
        ax.bar(categories, values)
        
    # Customize the chart
    ax.set_title(title)
    ax.set_xlabel(x_lable)
    ax.set_ylabel(y_label)
    
    # Save the chart as an image
    plt.savefig(file_temp)
    
    
def create_terms_for_autosearch(databases, terms, review, start_date, interval, client):
    if interval == "weekly":
        interval_days = 7
    elif interval == "monthly":
        interval_days = 30
    elif interval == "weekly":
        interval_days = 90
    elif interval == "weekly":
        interval_days = 360

    today = timezone.now()
    start_date = timezone.datetime.strptime(start_date, "%Y-%m-%d")
    start_date = start_date.replace(tzinfo=pytz.UTC) 

    range_start_date = start_date
    created_searches = []

    while today >= ( range_start_date + timezone.timedelta(days=interval_days-1) ):
        range_end_date = range_start_date + timezone.timedelta(days=interval_days-1)
        for term in terms:
            for db in databases:
                db_item = NCBIDatabase.objects.filter(displayed_name = db).first()
                term_values = {
                    "literature_review": review,
                    "db": db_item,
                    "term": term,
                    "start_search_interval": range_start_date,
                    "end_search_interval": range_end_date,
                }
                if not LiteratureSearch.objects.filter(**term_values).exists():
                    lit_search = LiteratureSearch.objects.create(**term_values)
                    created_searches.append(lit_search)
                    # term_values.pop("start_search_interval")
                    # term_values.pop("end_search_interval")
                    # LiteratureReviewSearchProposal.objects.create(**term_values,literature_search=lit_search)

                else:
                    logger.debug("Already exists")

        range_start_date = range_end_date + timezone.timedelta(days=1)
    
    ##### RUN SCRAPERS FOR NEWLY ADDED SEARCHES #########
    for search in created_searches:
        search.import_status = "RUNNING"
        search.save()
        run_auto_search(review.id, search.id)

    ##### SEND EMAIL NOTIFICATION TO SUPPORT TEAM #######
    formatted_searches = []
    for search in created_searches:
        start_date_str = search.start_search_interval.strftime("%d-%m-%Y")
        end_date_str = search.end_search_interval.strftime("%d-%m-%Y")
        formatted_searches.append(f"{search.db.name}-{search.term} : {start_date_str} to {end_date_str}")

    formatted_searches_str = ""
    for s in formatted_searches:
        formatted_searches_str += f"<li> {s} </li>"

    not_message = f"""
    New Automated Search that requires updates were created in this project: <bold> {str(review)} </bold> <br />
    Client: {client} <br />
    Searches: <br />
    <ul>
    {formatted_searches_str}
    </ul>

    Note some of these searches will be completed automatically using our scrapers, Please for those you found them
    already completed make sure to Re-run manually to confirm the results are correct.
    You can access the searches & upload results from Below Link. 
    """
    project_link = SITE_URL + reverse('literature_reviews:search_dashboard', args=[review.id])

    from client_portal.tasks import automated_search_notify_support_team
    automated_search_notify_support_team.delay(not_message, project_link)

    return created_searches