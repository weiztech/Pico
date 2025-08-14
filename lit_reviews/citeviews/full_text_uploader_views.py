import zipfile
import requests
from django.urls import reverse
from lit_reviews.tasks import send_email
from lit_reviews.models import *
from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.csrf import csrf_exempt
from django.core.files import File
from django.http import HttpResponse, JsonResponse
from ..forms import uploadFullText
from django.conf import settings
from lit_reviews.custom_permissions import protected_project
from lit_reviews.helpers.articles import (
    highlight_full_text_pdf, 
    form_review_search_kw, 
    name_article_full_text_pdf,
    get_ai_search_texts,
    generate_url_article_reviews
)
import datetime
from lit_reviews.helpers.aws_s3 import generate_upload_presigned_url
from django.utils import timezone
from lit_reviews.tasks import appraisal_ai_extraction_generation_async
from lit_reviews.helpers.generic import create_tmp_file


# @protected_project
# @csrf_exempt
# def upload_ft(request):
#     if request.method == "POST":
#         try:
#             ## or this should be Article object
#             article = Article.objects.get(id=request.POST["article-id"])
#             file_key = request.POST.get("aws-key")
#             # article.full_text = File(f)
#             article.full_text.name = file_key
#             article.save()

#             ## recalculate appraisal status
#             article_review_id = request.POST.get("article-review-id", "") 
#             if article_review_id:
#                 article_review = ArticleReview.objects.filter(id=article_review_id).first()
#                 appraisal = ClinicalLiteratureAppraisal.objects.filter(article_review=article_review).first()
#                 appraisal.app_status = appraisal.status
#                 logger.info("Full text file uploaded successfully")
#                 logger.info("clinical_literature_appraisal_id: {0}".format(appraisal.id))
#                 # Queue the task for asynchronous processing
#                 logger.info("Processing appraisal asynchronously")
#                 appraisal_ai_extraction_generation_async.delay(appraisal.id, request.user.id)

#             return JsonResponse({"success": True})

#         except Exception as e:
#             print("error processing file upload " + str(e))
#             return JsonResponse({"success": False})


@protected_project
def ft_uploader(request, id):
    return render(request, "lit_reviews/full_text_uploader.html")


@protected_project
def ft_download_all_files(request, id):
    article_reviews = (
        ArticleReview.objects.filter(search__literature_review_id=id)
        .exclude(article__full_text="")
        .prefetch_related("article")
    )
    response = HttpResponse(content_type="application/zip")
    zf = zipfile.ZipFile(response, "w")

    for review in article_reviews:
        article = review.article
        filenames = article.full_text
        r = requests.get(article.full_text.url)
        zf.writestr(article.full_text.name, r.content)

    response["Content-Disposition"] = f"attachment; filename=All_download.zip"
    return response

@csrf_exempt
def fulltext_upload_help(request):
    if request.method == "POST":
        try:
            user = request.user
            email = user.email
            
            subject = "Request For Help With Full Text Upload"
            message = f"The user with this {email} is experiencing difficulties with the full texts and is seeking assistance."
            send_email(subject, message, to=settings.SUPPORT_EMAILS)
            logger.debug("Email Message Send: {0}".format(message))
            return JsonResponse({"success": True})

        except Exception as e:
            print("error sending help message " + str(e))
            return JsonResponse({"success": False})
        

# def pdf_highlighter(request, id):
#     if request.method == "POST":
#         article_id = request.POST["article-id"]
#         appraisal_id = request.POST["appraisal-id"]
#         article = get_object_or_404(Article, pk=article_id)
#         review = get_object_or_404(LiteratureReview, pk=id)
#         tmp_file_name = str(review) + str(datetime.datetime.now()) + "-highlighted.pdf"
#         tmp_file_name = tmp_file_name.replace("/", "")
#         tmp_file_name_output = str(review) + str(datetime.datetime.now()) + "-highlighted-output.pdf"
#         tmp_file_name_output = tmp_file_name_output.replace("/", "")

#         ## AI Part is not ready yet, to be considered in the future
#         #  ### TODO move the below into celery task for async processing
#         # ai_search_texts = get_ai_search_texts("/tmp/" + tmp_file_name)

#         search_texts = form_review_search_kw(review.id) # + ai_search_texts
#         # search_texts = form_review_search_kw(review.id) + ai_search_texts
#         pdf = article.full_text.file.open('r')
#         file_content = pdf.read()        
#         output_tmp_file_path = create_tmp_file(tmp_file_name_output, file_content)
#         input_tmp_file_path = create_tmp_file(tmp_file_name, file_content)
#         highlight_full_text_pdf(input_tmp_file_path, output_tmp_file_path, search_texts)

#         with open(output_tmp_file_path, "rb") as output_path:
#             # article.highlighted_full_text = File(output_path)
#             article.highlighted_full_text.save(tmp_file_name, File(output_path))
#             article.save()

#     # return redirect(reverse("literature_reviews:full_text_upload", args=[review.id]))
#     return redirect(reverse("literature_reviews:clinical_literature_appraisal", args=[review.id, appraisal_id]))

 
# @protected_project
# def ft_clear(request, id, article_review_id):   
#     literature_review = get_object_or_404(LiteratureReview, pk=id) 
#     article_review = ArticleReview.objects.get(search__literature_review=literature_review, id=article_review_id)
#     article_review.article.full_text = ""
#     article_review.article.save()
#     return redirect(reverse("literature_reviews:full_text_upload", args=[literature_review.id])) 