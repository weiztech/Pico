from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponse 
from django.db.models import Q

from lit_reviews.models import ArticleReview, Article
from django.http import HttpResponseRedirect, JsonResponse
from django.urls import reverse
from django.db.models import Q
from lit_reviews.tasks import state_change_task_async,process_abstract_text
from django.core.paginator import Paginator

from backend.logger import logger
from django.shortcuts import render, get_object_or_404
from django.core.exceptions import PermissionDenied

from lit_reviews.models import (
    Article,
    ArticleReview,
    LiteratureReview,
    DuplicationReport,
)

from lit_reviews.forms import ArticleReviewForm
from lit_reviews.custom_permissions import protected_project
from lit_reviews.helpers.articles import get_article_redirect_url, check_full_article_link


def article_tags(request, id):
    return render(request, "lit_reviews/article_tags.html")


@protected_project
def citation_updater(request, id):
    if request.method == "POST":
        article_id = request.POST.get("article_id")
        citation = request.POST.get("citation")
        article = get_object_or_404(Article, id=article_id)
        citation = citation.strip()
        if not citation:
            return HttpResponseBadRequest("Please make sure to provide a citation before you click submit")

        article.citation = citation
        article.save()

        return JsonResponse({"artical": f"Citation for article {article.id} updated successfully" })

    else:
        article_reviews = ArticleReview.objects.filter(
                Q(
                    Q(search__literature_review_id=id)
                    & Q(Q(article__citation=None) | Q(article__citation=""))
                )
            )

        articles = [ar.article for ar in article_reviews]
        
        return render(request, "lit_reviews/citation_updater.html", {"articles": articles})

@protected_project
def article_review_detail(request, id, article_id):
    instance = get_object_or_404(ArticleReview, id=article_id)
    # CHECKING THE FULL TEXT ARTICLE LINK
    if instance and not instance.article.full_text:
        check_full_article_link(instance.article.id, instance.id, request.user.id)
        instance = ArticleReview.objects.filter(id=article_id).first()

    instance_state = instance.state
    if instance.search.literature_review not in request.user.my_reviews():
            raise PermissionDenied

    redirect_url = get_article_redirect_url(instance_state, id)
    if instance.article.pmc_uid:
        previous_articles_reviews = ArticleReview.objects.filter(article__pmc_uid=instance.article.pmc_uid).exclude(id=instance.id).order_by("-search__created_time")
    elif instance.article.pubmed_uid:
        previous_articles_reviews = ArticleReview.objects.filter(article__pubmed_uid= instance.article.pubmed_uid).exclude(id=instance.id).order_by("-search__created_time")
    else:
        previous_articles_reviews = ArticleReview.objects.filter(article= instance.article).exclude(id=instance.id).order_by("-search__created_time")

    if request.user.client:
        previous_articles_reviews = previous_articles_reviews.filter(search__literature_review__client=request.user.client)

    clinical_app_link = ""
    clin_appr = instance.clin_lit_appr.first()
    if clin_appr:
        clinical_app_link = reverse(
            "lit_reviews:clinical_literature_appraisal", 
            kwargs={"id": id, "appraisal_id": clin_appr.id}
        )

    form = ArticleReviewForm(
        request.POST or None,
        instance=instance,
        literature_review_id=instance.literature_review_id,
    )

    if request.method == "POST":
        if form.is_valid():
            article = form.save()
            lit_review_id = article.literature_review_id
            process_abstract_text.delay(lit_review_id, article_id)

            if "next" in request.POST:
                try:
                    next_article_id = next_actionable_id(lit_review_id, instance.id, instance_state)
                    return HttpResponseRedirect(
                        reverse(
                            "lit_reviews:article_review_detail",
                            args=[
                                str(id),
                                str(next_article_id)
                            ],
                        )
                    )

                except Exception as e:
                    print(e)
                    return HttpResponseRedirect(redirect_url)

            if "back" in request.GET:
                return HttpResponseRedirect(request.GET["back"])
            
            return HttpResponseRedirect(redirect_url)
    
    return render(
        request,
        "lit_reviews/article_review_detail.html",
        {
            "object": instance,
            "form": form,
            "articles_reviews":previous_articles_reviews,
            "clinical_app_link": clinical_app_link,
        },
    )

@protected_project
def article_state_change(request, id):
    selected_state = request.POST.get("selected_state")
    # redirect_view_name = request.POST.get("redirect_view_name", "lit_reviews:article_review_list")
    state_change_task_async.delay(id, selected_state, request.user.id)
    return JsonResponse({"success": True}) 

from lit_reviews.tasks import remove_duplicate_async

@protected_project
def article_reviews_list(request, id):
    state = request.GET.get("state")
    duplication_report, created = DuplicationReport.objects.get_or_create(literature_review_id=id)
    if duplication_report.needs_update:
        remove_duplicate_async.delay(id) 
    return render(request, "lit_reviews/first_pass.html", context={"state": state})

def next_actionable_id(literature_review_id, previous_article_id=0, previous_article_state="U"):
    reviews = ArticleReview.objects.filter(
        Q(search__literature_review__id=literature_review_id) & (Q(state=previous_article_state))
    )

    try:

        for index, value in enumerate(reviews):
            if value.id == previous_article_id:
                print("found previous, return next obj")
                print(reviews[index + 1])

                return reviews[index + 1].id
        raise Exception(" could not find matching review ")

    except Exception as e:
        print("could not find next via index, return any")
        return (
            ArticleReview.objects.filter(
                Q(search__literature_review__id=literature_review_id)
                & (Q(state=previous_article_state))
                # & (Q(state="U") | Q(state="M"))
            )
            .first()
            .id
        )


@protected_project
def duplicates_articles(request, id):
    duplication_report, created = DuplicationReport.objects.get_or_create(literature_review_id=id)
    
    if duplication_report.needs_update:
        remove_duplicate_async.delay(id) 

    return render(request, "lit_reviews/duplicates_articles.html")


@protected_project
def review_article_full_text_pdf(request, id, review_id):
    """
    Download Full Text PDF for a specific article review
    """
    literature_review = get_object_or_404(LiteratureReview, pk=id)
    article_review = get_object_or_404(ArticleReview, pk=review_id, search__literature_review=literature_review)
    if article_review.article.full_text:
        return HttpResponseRedirect(article_review.article.full_text.url)
    else:
        return HttpResponse(f"The full text pdf is for article with title <strong> {article_review.article.title} </strong> is missing or were not uploaded.")
    
    
##########################################################
# Below code is no longer used we are
# using DRF now you can find related logic 
# for belows functionalities here lit_review.api.articles
##########################################################
