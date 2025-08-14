from django.http import HttpResponseRedirect
from django.urls import reverse
from django.shortcuts import render, get_object_or_404

from lit_reviews.models import LiteratureReview, ExclusionReason, ArticleReview
from lit_reviews.forms import ExclusionReasonForm
from lit_reviews.custom_permissions import protected_project

@protected_project
def exclusion_reason_list_create(request, id):
    literature_review = get_object_or_404(LiteratureReview, id=id)
    if request.method == "POST":
        form = ExclusionReasonForm(request.POST)
        if form.is_valid():
            exclustion_reason = form.save(commit=False)
            exclustion_reason.literature_review = literature_review
            exclustion_reason.save()

            return HttpResponseRedirect(
                reverse("lit_reviews:exclusion_reason", args=[str(id)])
            )
    else:
        form = ExclusionReasonForm()
    exclustion_reasons = literature_review.exclustion_reasons.all()
    return render(
        request,
        "lit_reviews/exclusion_reason.html",
        {"form": form, "exclustion_reasons": exclustion_reasons},
    )

@protected_project
def exclusion_reason_update(request, id, instance_id):
    literature_review_id = id
    instance = get_object_or_404(ExclusionReason, id=instance_id)
    old_reason_name = instance.reason
    form = ExclusionReasonForm(request.POST or None, instance=instance)
    if request.method == "POST":
        update_method = request.POST.get('UpdateMethod')
        if form.is_valid():
            form.save()
            if update_method == 'true':
                # update all article review old resons 
                article_reviews = ArticleReview.objects.filter(exclusion_reason = old_reason_name, search__literature_review__id = literature_review_id)
                for article_review in article_reviews:
                    article_review.exclusion_reason = instance.reason
                    article_review.save()
            return HttpResponseRedirect(
                reverse("lit_reviews:exclusion_reason", args=[str(literature_review_id)])
            )
    return render(
            request,
            "lit_reviews/exclusion_reason_update.html",
            {"form": form,},
    )

@protected_project
def exclusion_reason_delete(request, id, instance_id):
    literature_review_id = id
    instance = get_object_or_404(ExclusionReason, id=instance_id)
    instance.delete()
    return HttpResponseRedirect(
        reverse("lit_reviews:exclusion_reason", args=[str(literature_review_id)])
    )