import datetime, pytz
from django.shortcuts import get_object_or_404
from django.core.paginator import Paginator
from django.db.models import Case, When, Value, IntegerField

from rest_framework.views import APIView 
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.generics import UpdateAPIView, ListAPIView, CreateAPIView

from lit_reviews.api.pagination import CustomPagination
from lit_reviews.models import (
    LiteratureReview,
    LiteratureSearch,
    NCBIDatabase,
    ArticleReview,
    ClinicalLiteratureAppraisal,
    AppraisalExtractionField,
    ExtractionField,
    Article,
)
from lit_reviews.api.clinical_appraisals.serializers import  (
    NCBIDatabaseSerializer,
    LiteratureSearchSerializer,
    UploadOwnCitationsSerializer,
    ClinicalLiteratureAppraisalSerializer,
    AppraisalExtractionFieldSerializer,
    ClinicalAppraisalListSerializer,
    CreateManualAppraisalSerializer,
    PDFHighlightingSerializer,
)

from lit_reviews.helpers.articles import get_or_create_appraisal_extraction_fields
from lit_reviews.citeviews.clinical_literature_appraisal import sorting_clinical_literature_appraisal_list
from lit_reviews.api.articles.serializers import ArticleReviewSerializer
from backend.logger import logger
from lit_reviews.api.home.serializers import LiteratureReviewSerializer
from lit_reviews.api.cutom_permissions import isProjectOwner, IsNotArchived
from celery.result import AsyncResult
from lit_reviews.tasks import appraisal_ai_extraction_generation_all_async, appraisal_ai_extraction_generation_async


class ClinicalAppraisalsListAPIView(ListAPIView):
    permission_classes = [permissions.IsAuthenticated, isProjectOwner]
    queryset = ClinicalLiteratureAppraisal.objects.all()
    pagination_class = CustomPagination
    serializer_class = ClinicalAppraisalListSerializer

    def get_queryset(self):
        queryset = self.queryset
        request = self.request
        lit_review_id = self.kwargs.get("id")
        sorting = request.query_params.get("sorting", "article_review__article__title")
        search_title = request.query_params.get("search_title", "")
        filters_status_str = request.query_params.get("filter_status", "") 
        logger.info(f"filters_status0: {filters_status_str}")
        filter_status = []
        if filters_status_str:  
            filters_status_param = request.query_params.getlist("filter_status", "") 
            filter_status =   [i for i in filters_status_param if i]
    
        filter_is_sota = request.query_params.get("filter_is_sota", "")
        app_list, app_status_counts = sorting_clinical_literature_appraisal_list(
            lit_review_id, 
            sorting, 
            search_title, 
            filter_status,
            True,
            filter_is_sota, 
            None
        )
        self.app_status_counts = app_status_counts 
        appraisal_ids = [appraisal["app"].id for appraisal in app_list]
        if "is_sota_article" in sorting:
            sorting_term = "-is_sota_article_true" if "-" in sorting else "is_sota_article_true"
            queryset = queryset.filter(id__in=appraisal_ids).annotate(
                is_sota_article_true=Case(
                    When(is_sota_article=True, then=Value(1)),  # True goes on top
                    default=Value(0),                           # False and None go below
                    output_field=IntegerField()
                )
            ).order_by(sorting_term)     
        else:
            queryset = queryset.filter(id__in=appraisal_ids).order_by(sorting)
        return queryset


    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        response.data['insights'] =  self.app_status_counts 
        return response
    

class CreateManualAppraisalAPI(CreateAPIView):
    permission_classes = [permissions.IsAuthenticated, isProjectOwner]
    queryset = Article.objects.all()
    serializer_class = CreateManualAppraisalSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        lit_review_id = self.kwargs.get("id")
        lit_review = LiteratureReview.objects.get(id=lit_review_id)
        context["literature_review"] = lit_review
        return context
    
    def create(self, request, *args, **kwargs):
        lit_review_id = kwargs.get("id")
        lit_review = LiteratureReview.objects.get(id=lit_review_id)
        self.check_object_permissions(self.request, lit_review)       
        return super().create(request, *args, **kwargs)


class AppraisalsDataAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated, isProjectOwner, IsNotArchived]
    parser_classes = (MultiPartParser, FormParser,)
    http_method_names = [
        'get',
        'post',
        'head',
        'options',
    ]

    def get(self, request, *args, **kwargs):
        lit_review_id = kwargs.get("id")
        lit_review = LiteratureReview.objects.get(id=lit_review_id)
        self.check_object_permissions(self.request, lit_review)       
        dbs_query = lit_review.searchprotocol.lit_searches_databases_to_search
        dbs_ser = NCBIDatabaseSerializer(dbs_query, many=True)
        dbs = dbs_ser.data 
        lit_reviews = request.user.my_reviews()

        lit_reviews_ser = LiteratureReviewSerializer(lit_reviews, many=True, context={"request": request})
        lit_reviews = lit_reviews_ser.data 

        response_data = {
            "dbs": dbs, 
            "lit_reviews":lit_reviews,
        }

        return Response(response_data, status=status.HTTP_200_OK)
    
    def post(self, request, *args, **kwargs):

        selected_prev_project_id = request.data.get("selected_prev_project_id")
        lit_review_id = kwargs.get("id")
        lit_review = LiteratureReview.objects.get(id=lit_review_id)
        self.check_object_permissions(self.request, lit_review)

        # get all retained articles from the other projects
        
        current_article_reviews = ArticleReview.objects.filter(
            state = "I",
            search__literature_review__id = lit_review_id
        )
        
        previous_article_reviews = ArticleReview.objects.filter(
            state = "I",
            search__literature_review__id = selected_prev_project_id
        )

        # Get titles of current article reviews
        current_article_titles = current_article_reviews.values_list('article__title', flat=True)
        
        # Filter potential imported article reviews based on title comparisons
        potential_imported_article_reviews = previous_article_reviews.exclude(
            article__title__in=current_article_titles
        )
        

        article_reviews_ser = ArticleReviewSerializer(potential_imported_article_reviews, many=True, context={"request": request})
        article_reviews = article_reviews_ser.data 

        response_data = {
            "article_reviews": article_reviews
        }

        return Response(response_data, status=status.HTTP_200_OK)
     

class CheckRunningCitationView(APIView):
    permission_classes = [permissions.IsAuthenticated, isProjectOwner, IsNotArchived]
    http_method_names = [
        'get',
        'post',
        'head',
        'options',
    ]

    def post(self, request, *args, **kwargs):

        search_id = request.data.get("search_id")
        literature_running = LiteratureSearch.objects.filter(id=search_id).first()
        logger.info(f"literature_running: {literature_running}")   


        if literature_running.import_status == "RUNNING":
            is_completed = False
        else:
            is_completed = True

        UTC = pytz.utc
        current_time = datetime.datetime.now(UTC)
        scripts_time = literature_running.script_time
        time = current_time - scripts_time
        ONE_HOUR = 60 * 60 # this is in seconds
        if time.seconds >= ONE_HOUR:
            literature_running.import_status = "INCOMPLETE-ERROR"
            literature_running.error_msg = "The search process has been running for over an hour without results. Please contact support for assistance in resolving this issue."
            literature_running.save()

        data = {"is_completed": is_completed}
        if is_completed:
            literature_search_ser = LiteratureSearchSerializer(literature_running)
            data["literature_search"] = literature_search_ser.data

        return Response(data, status=status.HTTP_200_OK)



class UploadOwnCitationsAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated, isProjectOwner, IsNotArchived]
    http_method_names = [
        'post',
        'head',
        'options',
    ]

    def post(self, request, *args, **kwargs): 

        lit_id = kwargs.get("id")        
        literature_review = get_object_or_404(LiteratureReview, pk=lit_id)       
        serializer = UploadOwnCitationsSerializer(data=request.data, context={"request": request, "literature_review": literature_review})
        serializer.is_valid(raise_exception=True)
        results = serializer.save()
        return Response(results, status=status.HTTP_200_OK)



class ImportManualSearchView(APIView):
    permission_classes = [permissions.IsAuthenticated, isProjectOwner, IsNotArchived]
    
    def post(self, request, *args, **kwargs):
        
        lit_review_id = kwargs.get("id")
        lit_review = LiteratureReview.objects.get(id=lit_review_id)
        article_ids = request.data.get("article_ids", [])
        logger.info(f"article_ids: {article_ids}")
        count = 0
        for article_id in article_ids:
            logger.info(f"article_id: {article_id}")
            article_review = ArticleReview.objects.get(id=article_id)
            logger.info(f"article_review: {article_review}")


            # get or create LiteratureSearch and associate with the new LiteratureReview
            literature_search = LiteratureSearch.objects.get_or_create(
                literature_review = lit_review,
                term = "One-Off Manufacturer Search",
                db=article_review.search.db,
            )[0]


            logger.info(f"literature_search: {literature_search.id}")
            clinical_appraisal = ClinicalLiteratureAppraisal.objects.filter(article_review=article_review).first()
            logger.info(f"clinical_appraisals: {clinical_appraisal.id}")
            appraisal_extraction_fields = AppraisalExtractionField.objects.filter(clinical_appraisal=clinical_appraisal)

            # Duplicate ArticleReview and associate with the new LiteratureSearch
            article_review.pk = None
            article_review.search = literature_search
            article_review.save()

            # delete the defualt ClinicalLiteratureAppraisals associate with the new ArticleReview
            clinical_appraisal_new = ClinicalLiteratureAppraisal.objects.filter(article_review=article_review).first()
            clinical_appraisal_new.delete()

            # Duplicate ClinicalLiteratureAppraisals and associate with the new ArticleReview
            clinical_appraisal.pk = None
            clinical_appraisal.article_review = article_review
            clinical_appraisal.save()

            # Duplicate AppraisalExtractionField and ExtractionField
            for field in appraisal_extraction_fields:
                # not all extraction fields are available in the new project, there might be some newly added ones on the previous
                # project we're copying from. we just skip this field 
                extraction_field = ExtractionField.objects.filter(literature_review=lit_review, name=field.extraction_field.name).first()
                if extraction_field:
                    new_field = AppraisalExtractionField.objects.create(
                        extraction_field=extraction_field,
                        clinical_appraisal=clinical_appraisal,
                        value=field.value
                    )
                    new_field.save()

            count += 1

        return Response({"count": count}, status=status.HTTP_200_OK)
    
 
class AppraisalNavigationAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated, isProjectOwner]

    def post(self, request, *args, **kwargs):
        # Extract parameters from the request
        literature_review_id = kwargs.get("id")

        current_appraisal_id = int(request.data.get("current_appraisal_id", []))
        current_sorting = request.data.get("current_sorting", "article_review__article__title")
        search_title = request.data.get("search_title", [])
        filter_status = request.data.get("filter_status", [])
        filter_is_sota = request.data.get("filter_is_sota", [])
        filter_is_ck3 = request.data.get("filter_is_ck3", [])
        status_count = True

        # Get sorted appraisals based on the provided parameters
        app_list, _ = sorting_clinical_literature_appraisal_list(
            literature_review_id,
            current_sorting,
            search_title,
            filter_status,
            status_count,
            filter_is_sota,
            filter_is_ck3
        )


        # Ensure app_list is valid
        if not app_list:
            return Response(
                {"next": None, "previous": None},
                status=status.HTTP_200_OK
            )
        
        # Find current appraisal index
        current_index = next((index for index, item in enumerate(app_list) if item["app"].id == current_appraisal_id), None)

        # Determine next and previous IDs
        next_id = app_list[current_index + 1]["app"].id if current_index is not None and current_index + 1 < len(app_list) else None
        previous_id = app_list[current_index - 1]["app"].id if current_index is not None and current_index > 0 else None

        # Return response
        return Response(
            {"next": next_id, "previous": previous_id},
            status=status.HTTP_200_OK
        )
    

class AddSubExtractionField(APIView):
    """
    Add Additional Sub Extraction Fields.
    By default each appraisal has 1 extraction field Value, this view.
    allow users to add multiple values for each appraisal extraction field.
    All appraisal fields should have the same number of extraction values we can't have 
    multiple values only for a specific field.  
    """
    permission_classes = [permissions.IsAuthenticated, isProjectOwner]

    def get(self, request, *args, **kwargs):
        """
        Get is only for getting the numbder of sub extractions that exists for a given appraisal.
        """
        # Extract parameters from the request
        literature_review_id = kwargs.get("id")
        appraisal_id = kwargs.get("appraisal_id")

        literature_review = LiteratureReview.objects.get(id=literature_review_id)
        extraction_fields = literature_review.extraction_fields.filter(field_section="EF")
        appraisal = ClinicalLiteratureAppraisal.objects.get(
            id=appraisal_id,
            article_review__search__literature_review=literature_review,
        )

        sub_extractions = AppraisalExtractionField.objects.filter(
            extraction_field=extraction_fields.first(), 
            clinical_appraisal=appraisal,    
        ).distinct("extraction_field_number").values_list("extraction_field_number", flat=True)
        return Response(
            {"sub_extractions": sub_extractions},
            status=status.HTTP_200_OK
        )


    def post(self, request, *args, **kwargs):
        # Extract parameters from the request
        literature_review_id = kwargs.get("id")
        appraisal_id = kwargs.get("appraisal_id")

        literature_review = LiteratureReview.objects.get(id=literature_review_id)
        extraction_fields = literature_review.extraction_fields.filter(field_section="EF")
        appraisal = ClinicalLiteratureAppraisal.objects.get(
            id=appraisal_id,
            article_review__search__literature_review=literature_review,
        )
        for extraction_field in extraction_fields:
            app_fields = AppraisalExtractionField.objects.filter(
                extraction_field=extraction_field, 
                clinical_appraisal=appraisal,    
            ).order_by("extraction_field_number")
            highest_sub_extraction = app_fields.last().extraction_field_number
            AppraisalExtractionField.objects.create(
                extraction_field=extraction_field, 
                clinical_appraisal=appraisal,  
                extraction_field_number=highest_sub_extraction+1,  
            )

        sub_extractions = AppraisalExtractionField.objects.filter(
            extraction_field=extraction_field, 
            clinical_appraisal=appraisal,    
        ).distinct("extraction_field_number").values_list("extraction_field_number", flat=True)
        return Response(
            {"sub_extractions": sub_extractions},
            status=status.HTTP_200_OK
        )
    

class DeleteSubExtractionField(APIView):
    permission_classes = [permissions.IsAuthenticated, isProjectOwner]


    def post(self, request, *args, **kwargs):
        # Extract parameters from the request
        literature_review_id = kwargs.get("id")
        appraisal_id = kwargs.get("appraisal_id")
        sub_extraction = request.data.get("sub_extraction")

        literature_review = LiteratureReview.objects.get(id=literature_review_id)
        extraction_fields = literature_review.extraction_fields.filter(field_section="EF")
        appraisal = ClinicalLiteratureAppraisal.objects.get(
            id=appraisal_id,
            article_review__search__literature_review=literature_review,
        )
        for extraction_field in extraction_fields:
            AppraisalExtractionField.objects.filter(
                extraction_field=extraction_field, 
                clinical_appraisal=appraisal,    
                extraction_field_number=sub_extraction,
            ).delete()

        sub_extractions = AppraisalExtractionField.objects.filter(
            extraction_field=extraction_field, 
            clinical_appraisal=appraisal,    
        ).distinct("extraction_field_number").values_list("extraction_field_number", flat=True)
        return Response(
            {"sub_extractions": sub_extractions},
            status=status.HTTP_200_OK
        )
    

class AppraisalDetailAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated, isProjectOwner]

    def get(self, request, *args, **kwargs):
        literature_review_id = kwargs.get("id")
        lit_review = LiteratureReview.objects.filter(id=literature_review_id).first() 
        appraisal_id = kwargs.get("appraisal_id")
        
        appraisal = ClinicalLiteratureAppraisal.objects.get(
            id=appraisal_id,
            article_review__search__literature_review_id=literature_review_id
        )
        
        extraction_fields = lit_review.extraction_fields.all()

        for extraction_field in extraction_fields:
            # create extraction fields if any is missing 
            get_or_create_appraisal_extraction_fields(appraisal, extraction_field)

        serializer = ClinicalLiteratureAppraisalSerializer(appraisal)
        return Response(serializer.data)

    def post(self, request, *args, **kwargs):
        literature_review_id = kwargs.get("id")
        appraisal_id = kwargs.get("appraisal_id")
        
        appraisal = ClinicalLiteratureAppraisal.objects.get(
            id=appraisal_id,
            article_review__search__literature_review_id=literature_review_id
        )

        serializer = ClinicalLiteratureAppraisalSerializer(
            instance=appraisal,
            data=request.data,
            context={'request': request}
        )
        
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



class AppraisalAIUpdateAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated, isProjectOwner]

    def patch(self, request, *args, **kwargs):
        literature_review_id = kwargs.get("id")
        appraisal_id = kwargs.get("appraisal_id")
        
        appraisal = ClinicalLiteratureAppraisal.objects.get(
            id=appraisal_id,
            article_review__search__literature_review_id=literature_review_id
        )
        
        appraisal_ai_extraction_generation_async.delay(appraisal.id, request.user.id)
        return Response("", status=status.HTTP_200_OK)
        

class AppraisalExtractionFieldAPIView(UpdateAPIView):
    serializer_class = AppraisalExtractionFieldSerializer
    permission_classes = [permissions.IsAuthenticated, isProjectOwner]
    lookup_url_kwarg = 'field_id'
    
    def get_queryset(self):
        literature_review_id = self.kwargs.get("id")
        appraisal_id = self.kwargs.get("appraisal_id")
        
        return AppraisalExtractionField.objects.filter(
            clinical_appraisal_id=appraisal_id,
            clinical_appraisal__article_review__search__literature_review_id=literature_review_id
        )
    
    def get_object(self):
        queryset = self.get_queryset()
        field_id = self.kwargs.get(self.lookup_url_kwarg)
        
        # Get the literature review to verify permissions
        lit_review = get_object_or_404(
            LiteratureReview, 
            id=self.kwargs.get("id")
        )
        self.check_object_permissions(self.request, lit_review)
        
        # Only get existing AppraisalExtractionField objects
        obj = get_object_or_404(queryset, id=field_id)
        return obj
    
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        
        if 'status' in request.data:
            request.data['ai_value_status'] = request.data.pop('status')
        
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        
        return Response(serializer.data)
    
    def perform_update(self, serializer):
        logger.info(f"Updating AI status for field {serializer.instance.id}")
        serializer.save()


class ProcessClinicalAppraisalAPIView(APIView):
    """
    API endpoint that queues all clinical appraisals in a literature review 
    for asynchronous AI processing
    """
    permission_classes = [permissions.IsAuthenticated, isProjectOwner, IsNotArchived]

    def post(self, request, *args, **kwargs):
        literature_review_id = kwargs.get("id")
        
        # Verify the literature review exists
        lit_review = LiteratureReview.objects.get(id=literature_review_id)
        self.check_object_permissions(self.request, lit_review)
        
        # Queue the task for asynchronous processing
        appraisal_ai_extraction_generation_all_async.delay(literature_review_id, request.user.id)
        
        logger.info(f"Queued all appraisals for literature review {literature_review_id} for processing")
        return Response({
            "success": True,
            "message": "Processing started successfully"
        }, status=status.HTTP_202_ACCEPTED)


class PDFHighlightingAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated, isProjectOwner]
    serializer_class = PDFHighlightingSerializer

    def post(self, request, *args, **kwargs):
        litreview_id = kwargs.get("id")
        serializer = PDFHighlightingSerializer(data=request.data, context={"litreview_id": litreview_id})
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response({
            "success": True,
            "message": "PDF Highlighting is initiated, once completed you'll recieve a web socket message",
        }, status=status.HTTP_200_OK,)