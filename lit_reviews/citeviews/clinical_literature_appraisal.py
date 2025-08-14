from django.db.models import Q
from django.shortcuts import render, get_object_or_404

from backend.logger import logger
from lit_reviews.helpers.articles import get_clinical_appraisal_status_report
from lit_reviews.models import ClinicalLiteratureAppraisal
from lit_reviews.custom_permissions import protected_project


@protected_project
def clinical_literature_appraisal(request, id, appraisal_id):
    instance = get_object_or_404(ClinicalLiteratureAppraisal, id=appraisal_id)
    return render(
        request,
        "lit_reviews/clinical_literature_appraisal.html",
        {"appraisal_id": instance.id},
    )


@protected_project
def clinical_appraisals_list(request, id):
    return render(request, "lit_reviews/clinical_appraisals_list.html")

    
def next_actionable_appraisal_id(
        literature_review_id, 
        previous_appraisal_id,
        current_sorting,
        search_title,
        filter_status,
        status_count,
        filter_is_sota, 
        filter_is_ck3,
    ):
    
    app_list, app_status_counts = sorting_clinical_literature_appraisal_list(
        literature_review_id, 
        current_sorting,
        search_title,
        filter_status,
        status_count,
        filter_is_sota, 
        filter_is_ck3
    )

    try:
        for index, value in enumerate(app_list):
            if value["app"].id == previous_appraisal_id:
                print("found previous, return next")
                return app_list[index + 1]["app"].id

    except Exception as e:
        logger.error(str(e))
        try:
            for i in range(0, app_list.count()):
                if app_list[i].id == previous_appraisal_id:
                    print("found previous, return next")
                    return app_list[i+1].id
        except:
            return False

def sorting_clinical_literature_appraisal_list(
        literature_review_id, current_sorting, search_title, filter_status, 
        status_count=True, filter_is_sota=None,filter_is_ck3=None
    ):
    
    if search_title:
        appraisals = ClinicalLiteratureAppraisal.objects.filter(
            article_review__article__title__icontains=search_title,
            article_review__search__literature_review__id=literature_review_id,
            article_review__state="I"
        )
        # logger.info(f"appraisals: {appraisals}")
    else:
        q = Q(article_review__search__literature_review__id=literature_review_id)
        q &= Q(article_review__state="I")

        if filter_is_sota:
            if filter_is_sota == 'true':
                q &= Q(is_sota_article=True)
            elif filter_is_sota == 'false':
                q &= Q(is_sota_article=False)

        if filter_is_ck3:
            if filter_is_ck3 == 'true':
                q &= Q(fields__value='CK3 Determination and justification of criteria for the evaluation of the risk/benefit relationship')
            elif filter_is_ck3 == 'false':
                q &= ~Q(fields__value='CK3 Determination and justification of criteria for the evaluation of the risk/benefit relationship')

        appraisals = ClinicalLiteratureAppraisal.objects.filter(q).select_related("article_review__article", "article_review__search__db")
        logger.info('appraisals {}',appraisals.count())
        search_title = ''

    # Sorting the list based on the parameter passed
    if not status_count:
        return [{"app": app} for app in appraisals], None

    # if "status" not in current_sorting:
    #     if current_sorting == "is_ck3":
    #         appraisals = sorted(appraisals, key=lambda appraisal: appraisal.is_ck3, reverse=True)
    #     elif current_sorting == "-is_ck3":
    #         appraisals = sorted(appraisals, key=lambda appraisal: appraisal.is_ck3)
    #     else:
    #         appraisals = appraisals.order_by(current_sorting)

    app_list, app_status_counts, app_completed, app_incompleted = get_clinical_appraisal_status_report(appraisals)

    # logger.debug(f"app_list: {app_list}")
    logger.debug(f"current_sorting: {current_sorting}")
    logger.debug(f"filter_status: {filter_status}")

    if isinstance(filter_status, list) and len(filter_status) and filter_status != "Total":
        filtered_app_list = []
        for app in app_list:
            if "Complete SoTa Reviews" in filter_status and app["message"] == "Complete" and app["app"].is_sota_article:
                filtered_app_list.append(app)
            elif "Complete Device Reviews" in filter_status and app["message"] == "Complete" and not app["app"].is_sota_article:
                filtered_app_list.append(app)
            elif "Incomplete Device Review" in filter_status and "Incomplete Device Review" in app["message"]:
                filtered_app_list.append(app)
            elif app["message"] in filter_status:
                filtered_app_list.append(app)
        app_list = filtered_app_list

    # if current_sorting == "status":
    #     app_list = sorted(app_list, key=lambda item: item["message"])
    # elif current_sorting == "-status":
    #     app_list = sorted(app_list, key=lambda item: item["message"], reverse=True)

    return app_list, app_status_counts
