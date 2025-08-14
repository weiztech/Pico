from django.shortcuts import redirect, render, get_object_or_404
from django.db.models import Q
from backend.logger import logger 
from lit_reviews.models import (
    NCBIDatabase,
    LiteratureReview,
    AdverseEventReview,
    AdverseRecallReview,
    AdversDatabaseSummary,
    LiteratureSearch,
)
from lit_reviews.forms import (
    AdversDatabaseSummaryForm,
    AdverseEventForm,
    ManualAdverseEventReview,
    ManualAdverseRecallReview,
    AdverseRecallForm,
    AdverseEventReviewForm,
)
from django.http import HttpResponseRedirect, JsonResponse
from django.urls import reverse
from django.db.models import Q
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from lit_reviews.custom_permissions import protected_project

@protected_project
def adverse_database_summary(request, id):
    lit_review_id = id
    if request.method == "POST":
        database_name = request.POST['database']
        summary = request.POST['summary'].strip()
        database = get_object_or_404(NCBIDatabase, name=database_name)
        literature_review =  get_object_or_404(LiteratureReview, id=lit_review_id)

        try:
            ae_db_summary = AdversDatabaseSummary.objects.get(database=database, literature_review=literature_review)   
        except   AdversDatabaseSummary.DoesNotExist:
            ae_db_summary = AdversDatabaseSummary(database=database, literature_review=literature_review)  

        ae_db_summary.summary = summary
        ae_db_summary.save()
        return redirect('literature_reviews:adverse_database_summary', id=lit_review_id)

    adverse_event_reviews = AdverseEventReview.objects.filter(
        Q(search__literature_review_id=lit_review_id) &  Q( Q(state="IN") | Q(state="SM"))
    ).values_list("search__db__name", flat=True)
    adverse_recall_reviews = AdverseRecallReview.objects.filter(
        Q(search__literature_review_id=lit_review_id) &  Q( Q(state="IN") | Q(state="SM"))
    ).values_list("search__db__name", flat=True)

    ## use this list to get a list of databases. 
    dbs_set = set([*adverse_event_reviews, *adverse_recall_reviews])
    dbs_list = list(dbs_set)
    
    rows = []
    for db in dbs_list:
        ae_reviews =  AdverseEventReview.objects.filter(search__literature_review_id=lit_review_id,  search__db=db, state="IN")
        ae_recalls = AdverseRecallReview.objects.filter(search__literature_review__id=lit_review_id,  search__db=db, state="IN")
        ae_db_summary = AdversDatabaseSummary.objects.filter(database__name=db, literature_review__id=lit_review_id).first()
        summary_init_value = ae_db_summary.summary if ae_db_summary else ""
        form = AdversDatabaseSummaryForm(initial={'database': db, "summary": summary_init_value})
        events_exceeded_limits = False
        recalls_exceeded_limits = False
        if ae_reviews.count() > 100:
            events_exceeded_limits = True 
            ae_reviews = []
        if ae_recalls.count() > 100:
            recalls_exceeded_limits = True
            ae_recalls = [] 

        template_row =  {
            "ae_events": ae_reviews, 
            "ae_recalls": ae_recalls, 
            "database": db, 
            "form": form,
            "events_exceeded_limits": events_exceeded_limits,
            "recalls_exceeded_limits": recalls_exceeded_limits,
        } 
        rows.append(template_row)

    return render(request, "lit_reviews/adverse_database_summary.html", {"rows": rows})

@protected_project
def manual_ae_searches(request, id):
    return render(request, "lit_reviews/manual_ae_searches_vue.html", {"test":" test"})

@protected_project
def delete_adverse_event(request, id, ae_id):
    lit_review_id = id
    ae = get_object_or_404(AdverseEventReview, pk=ae_id)
    ae.delete()
    return redirect("lit_reviews:manual_ae_searches", id=lit_review_id)

@protected_project
def delete_adverse_recall(request, id, ar_id):
    lit_review_id = id = id
    ar = get_object_or_404(AdverseRecallReview, pk=ar_id)
    ar.delete()
    return redirect("lit_reviews:manual_ae_searches", id=lit_review_id)

@protected_project
def update_adverse_event(request, id, ae_id):
    lit_review_id = id = id
    ae_review = get_object_or_404(AdverseEventReview, pk=ae_id)
    ae = ae_review.ae

    if request.method == "POST":
        form_review = ManualAdverseEventReview(request.POST, instance=ae_review, prefix="ae_review")
        form = AdverseEventForm(request.POST, request.FILES, instance=ae, prefix="ae")
        if form.is_valid():
            form.save()
        else:
            return render(request, "lit_reviews/update_adverse_recall.html", {"form": form, "form_review": form_review, "errors": form.errors})

        if form_review.is_valid():
            form_review.save()
        else:
            return render(request, "lit_reviews/update_adverse_recall.html", {"form": form, "form_review": form_review, "errors": form_review.errors})

        return redirect("lit_reviews:manual_ae_searches", id=lit_review_id)
    
    form_review = ManualAdverseEventReview(instance=ae_review, prefix="ae_review")
    form_review.fields["search"].queryset = LiteratureSearch.objects.filter(db=ae_review.search.db,  literature_review_id=lit_review_id)
    form = AdverseEventForm(instance=ae, prefix="ae")
    return render(request, "lit_reviews/update_adverse_event.html", {"form": form, "form_review": form_review})

@protected_project
def update_adverse_recall(request, id, ar_id):
    lit_review_id = id
    ar_review = get_object_or_404(AdverseRecallReview, pk=ar_id)
    ar = ar_review.ae

    if request.method == "POST":
        form_review = ManualAdverseRecallReview(request.POST, instance=ar_review, prefix="ar_review")
        form = AdverseRecallForm(request.POST, request.FILES, instance=ar, prefix="ar")
        if form.is_valid():
            form.save()
        else:
            return render(request, "lit_reviews/update_adverse_recall.html", {"form": form, "form_review": form_review, "errors": form.errors})

        if form_review.is_valid():
            form_review.save()
        else:
            return render(request, "lit_reviews/update_adverse_recall.html", {"form": form, "form_review": form_review, "errors": form_review.errors})

        return redirect("lit_reviews:manual_ae_searches", id=lit_review_id)
    
    form_review = ManualAdverseRecallReview(instance=ar_review, prefix="ar_review")
    form_review.fields["search"].queryset = LiteratureSearch.objects.filter(db=ar_review.search.db,  literature_review_id=lit_review_id)
    form = AdverseRecallForm(instance=ar, prefix="ar")
    return render(request, "lit_reviews/update_adverse_recall.html", {"form": form, "form_review": form_review})

@protected_project
def adverse_event_review_detail(request, id, ae_id):
    instance = get_object_or_404(AdverseEventReview, id=ae_id)
    form = AdverseEventReviewForm(request.POST or None, instance=instance)

    sorting = request.GET.get("sorting", "ae__event_date")
    event_types_list = request.GET.getlist("event-type")
    search_term = request.GET.get("search_term", "")
    state_filter = request.GET.get("state", "")

    # build url filters
    query_params = "?"
    for key, value in request.GET.items():
        if key == "event-type":
            for event in event_types_list:
                query_params += f"&{key}={event}"
        else:
            query_params += f"&{key}={value}"

    if request.method == "POST":
        nex_ae_id = None
        lit_review_id = instance.literature_review_id

        if "next" in request.POST:
            nex_ae_id = next_adverse_actionable_id(lit_review_id, instance.id, sorting, event_types_list, search_term, state_filter)

        if form.is_valid():
            form.save()
            
            if nex_ae_id:
                url = reverse(
                        "lit_reviews:adverse_event_review_detail",
                        args=[
                            str(lit_review_id),
                            str(nex_ae_id),
                        ],
                    )

                return HttpResponseRedirect(url+query_params)

            if "back" in request.GET:
                return HttpResponseRedirect(request.GET["back"])
            
            return HttpResponseRedirect(
                reverse("lit_reviews:ae_list", args=[str(lit_review_id)]) + query_params
            )
    else:
        return render(
            request,
            "lit_reviews/ae_review_detail.html",
            {"object": AdverseEventReview.objects.get(id=ae_id), "form": form},
        )

@protected_project
@csrf_exempt
def include_single_ae_review(request):
	if request.method == 'POST':
		if request.POST['type'] == 'ae':
			ae = AdverseEventReview.objects.get(id=request.POST['ae_review_id'])
		elif request.POST['type'] == 'recall':
			ae = AdverseRecallReview.objects.get(id=request.POST['ae_review_id'])

		ae.state = request.POST['ae_review_state']
		ae.save()
		return JsonResponse({"success": True, "msg": "updated"})
    
@protected_project
def ae_list(request, id):
    eventsLitsSelected = []
    if request.method == "POST":
        state_event = request.POST.get('state')
        eventsLitsSelected = request.POST.get('eventsBulk[]')
        eventsLitsSelected = [int(x) for x in eventsLitsSelected.split(',') ] 
        for e_id in eventsLitsSelected:
            obj = AdverseEventReview.objects.get(id=e_id)
            obj.state = state_event
            obj.save()
        
        
    events_page = request.GET.get("events_page")
    recalls_page = request.GET.get("recalls_page")
    sorting = request.GET.get("sorting", "ae__event_date")

    page_switcher = request.GET.get("page_switcher", "events")

    # advanced filter
    search_term = request.GET.get("search_term", "")
    search_recall = request.GET.get("search_recall", "")
    manufacturer_filter =  request.GET.get("manufacturer", "").replace("+", " ")
    brand_name_filter =  request.GET.get("brand_name", "").replace("+", " ")
    state_filter = request.GET.get("state", "").replace("+", " ")
    event_types_list = request.GET.getlist("event-type")

    current_sorting = sorting
    current_manufacturer_filter = manufacturer_filter
    current_brand_name_filter = brand_name_filter
    current_state_filter = state_filter
    pagination_params = f"&sorting={sorting}&search_term={search_term}&manufacturer={current_manufacturer_filter}&brand_name={brand_name_filter}&page_switcher={page_switcher}&state={current_state_filter}"
    
    if search_recall:
        pagination_params += f"&search_recall={search_recall}"
    
    logger.debug("pagination_params: "+ pagination_params)
    for type in event_types_list:
        pagination_params += f"&event-type={type}"

    if events_page:
        events_page = int(events_page)
    else:
        events_page = 1

    if recalls_page:
        recalls_page = int(recalls_page)
    else:
        recalls_page = 1
        
    reviews = (
        AdverseEventReview.objects.filter(search__literature_review__id=id, search__db__entrez_enum="maude")
        .prefetch_related("ae")
        .order_by(sorting, "id")
    )

    if state_filter != "DU":
        reviews = reviews.exclude(state="DU")
    
    # get list of manufacturers
    manufacturer_list = reviews.values_list("ae__manufacturer", flat=True).order_by("ae__manufacturer").distinct("ae__manufacturer")
    brand_name_list = reviews.values_list("ae__brand_name", flat=True).order_by("ae__brand_name").distinct("ae__brand_name")

    # counts based on event type
    death_count = reviews.filter(ae__event_type="Death").count()
    injury_count = reviews.filter(ae__event_type="Injury").count()
    malfunction_count = reviews.filter(ae__event_type="Malfunction").count()
    other_count = reviews.filter(ae__event_type="Other").count()

    if event_types_list and len(event_types_list):
        reviews = reviews.filter(ae__event_type__in=event_types_list)

    if manufacturer_filter and manufacturer_filter != "None":
        reviews = reviews.filter(ae__manufacturer=manufacturer_filter)

    if brand_name_filter and brand_name_filter != "None":
        reviews = reviews.filter(ae__brand_name=brand_name_filter)

    if state_filter and state_filter != "None":
        reviews = reviews.filter(state=state_filter)
        
    if search_term:
        __filter = Q ( 
            Q(ae__description__icontains=search_term) 
            | Q(ae__event_type__icontains=search_term) 
            | Q(ae__manufacturer__icontains=search_term) 
            | Q(ae__brand_name__icontains=search_term) 
            | Q(ae__event_uid__icontains=search_term) 
            | Q(state__icontains=search_term) 
        )
        reviews = reviews.filter(__filter)

    recalls = []
    for search in LiteratureSearch.objects.filter(literature_review__id=id):
        recalls += search.ae_recalls.all()

    recalls = AdverseRecallReview.objects.filter(
        search__literature_review__id=id, search__db__entrez_enum="maude_recalls"
    ).prefetch_related("ae").order_by("ae__event_date","id")

    if search_recall:
        __filter_recall = Q ( 
            Q(ae__event_uid__icontains=search_recall) 
            | Q(ae__product_description__icontains=search_recall) 
            | Q(ae__trade_name__icontains=search_recall) 
            | Q(ae__firm_name__icontains=search_recall) 
            | Q(ae__recall_reason__icontains=search_recall) 
            | Q(state__icontains=search_recall) 
        )
        recalls = recalls.filter(__filter_recall)
    
    elif search_term:
        __filter = Q ( 
            Q(ae__trade_name__icontains=search_term) 
            | Q(ae__event_uid__icontains=search_term) 
            | Q(ae__product_description__icontains=search_term) 
            | Q(ae__firm_name__icontains=search_term) 
            | Q(ae__recall_reason__icontains=search_term) 
            | Q(state__icontains=search_term) 
        )
        recalls = recalls.filter(__filter)

    paginated_reviews = Paginator(reviews, 50) 
    paginated_reviews =  paginated_reviews.page(events_page)
    pageinated_recalls = Paginator(recalls, 50) 
    pageinated_recalls =  pageinated_recalls.page(recalls_page)

    pagination = paginated_reviews if page_switcher == "events" else pageinated_recalls
    page_starting_from = ((pagination.number-1) * 50 + 1)
    page_ends_at =  ((pagination.number-1) * 50 + len(pagination))
    total_count = reviews.count() if page_switcher == "events" else recalls.count()
    current_page_pagination_details = f"{page_starting_from}-{page_ends_at} of {total_count}"

    return render(
        request, 
        "lit_reviews/ae_list.html", 
        {   
            # "events_list_selected":  eventsLitsSelected if len(eventsLitsSelected) else [] , 
            "events": paginated_reviews.object_list, 
            "recalls": pageinated_recalls.object_list,
            "events_paginator": paginated_reviews, 
            "recalls_paginator": pageinated_recalls,
            "total_count": reviews.count() if page_switcher == "events" else recalls.count(),
            "current_sorting": current_sorting,
            "current_event_types": event_types_list,
            "current_manufacturer_filter": current_manufacturer_filter,
            "current_brand_name_filter": current_brand_name_filter,
            "current_state_filter": current_state_filter,
            "state_filter": state_filter,
            "death_count": death_count,
            "injury_count": injury_count,
            "malfunction_count": malfunction_count,
            "other_count": other_count,
            "search_term": search_term,
            "search_recall": search_recall,

            "events_page":events_page,
            "recalls_page":recalls_page,

            "page_switcher":page_switcher,

            "manufacturer_list": manufacturer_list,
            "brand_name_list": brand_name_list,
            "pagination_params": pagination_params,
            "current_page_pagination_details": current_page_pagination_details,
        }
    )

@csrf_exempt
def quick_include_ae(request):
    if request.method == "POST":
        try:
            ae_review = AdverseEventReview.objects.get(id=request.POST["ae_review_id"])
            ae_review.state = request.POST["state"]
            ae_review.save()
            return JsonResponse({"success": True, "ae_review_id": ae_review.id})

        except Exception as e:

            return JsonResponse({"success": False})


def next_adverse_actionable_id(literature_review_id, previous_ae_id, sorting, event_types_list, search_term, state_filter):
    reviews = (
        AdverseEventReview.objects.filter(search__literature_review__id=literature_review_id)
        .prefetch_related("ae")
        .order_by(sorting,"id")
        .exclude(state="DU")
    )

    if event_types_list and len(event_types_list):
        reviews = reviews.filter(ae__event_type__in=event_types_list)

    if search_term:
        __filter = Q ( 
            Q(ae__description__icontains=search_term) 
            | Q(ae__event_type__icontains=search_term) 
            | Q(ae__manufacturer__icontains=search_term) 
            | Q(ae__event_uid__icontains=search_term) 
            | Q(state__icontains=search_term) 
        )
        reviews = reviews.filter(__filter)

    if not reviews.count():
        # no reviews ? redirect back to ae list page
        return None
    try:
        for index, value in enumerate(reviews):
            if value.id == previous_ae_id:
                logger.debug("found previous, return next : " + str(reviews[index + 1].id))
                return reviews[index + 1].id

    except Exception as e:
        logger.warning("AE save and next Couldn't found next item : " + str(e))
        return False
