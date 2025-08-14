import datetime, pytz
import traceback

from django.shortcuts import get_object_or_404
from rest_framework.views import APIView 
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.parsers import MultiPartParser, FormParser

from backend import settings
from lit_reviews.tasks import send_email
from lit_reviews.models import (
    LiteratureReview,
    LiteratureSearch,
    NCBIDatabase,
)
from lit_reviews.api.search_dash.serializers import  (
    NCBIDatabaseSerializer,
    LiteratureSearchSerializer,
    UpdateLiteratureSearchSerializer,
    GenerateSearchReportSerializer,
    RequestSupportHelpSerailizer,
    ValidateManualFileSearchSerializer,
    AWSDirectUploadSerializer,
    UploadOwnCitationsSerializer,
)
from lit_reviews.tasks import (
    run_single_search, 
    search_clear_results_async,
    run_auto_search,
)
from client_portal.models import AutomatedSearchProject
from client_portal.api.AutomatedSearch.serializers import AutomatedSearchProjectSerializer
from backend.logger import logger
from lit_reviews.api.cutom_permissions import (
    isProjectOwner,
    IsNotArchived,
    DoesUserHaveEnoughCreditsForImportingArticles,
)
from lit_reviews.tasks import async_log_action_literature_search_results


class SearechDashboardView(APIView):
    permission_classes = [
        permissions.IsAuthenticated, 
        isProjectOwner, 
        IsNotArchived, 
        DoesUserHaveEnoughCreditsForImportingArticles
    ]
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
        literature_searchs_query = LiteratureSearch.objects.filter(
            literature_review__id=lit_review_id
        ).exclude(term="tmp term").exclude(
            term="One-Off Manufacturer Search"
        ).order_by("id")
        literature_searchs_ser = LiteratureSearchSerializer(literature_searchs_query, many=True)
        literature_searchs = literature_searchs_ser.data
        db_names = literature_searchs_query.values_list("db__name")        
        dbs_query = NCBIDatabase.objects.filter(name__in=db_names).distinct()
        dbs_ser = NCBIDatabaseSerializer(dbs_query, many=True)
        dbs = dbs_ser.data 
        autosearch = None 
        if lit_review.is_autosearch:
            autosearch = AutomatedSearchProject.objects.filter(lit_review=lit_review).first()
            autosearch = AutomatedSearchProjectSerializer(autosearch).data

        response_data = {
            "literature_searchs": literature_searchs, 
            "dbs": dbs, 
            "autosearch": autosearch,
            "max_imported_search_results": lit_review.searchprotocol.max_imported_search_results,
        }

        return Response(response_data, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs): 

        lit_review_id = kwargs.get("id") 
        lit_review = LiteratureReview.objects.get(id=lit_review_id)
        self.check_object_permissions(self.request, lit_review)

        literature_search_id = request.POST.get("literature_search_id")
        awsUploadedFile = request.POST.get("file") # this is the aws uploaded file key (the file was uploaded from the frontend directly)
        # if disable_exclusion is True the search should already have the results file we just want to process it again and force the import
        disable_exclusion = request.POST.get("disableExclusion", False)
        # fileType = request.POST.get("file_type")

        lit_search = LiteratureSearch.objects.get(id=literature_search_id, literature_review=lit_review)
        lit_search.disable_exclusion = True if disable_exclusion == "true" else False
        if not disable_exclusion:
            lit_search.search_file = awsUploadedFile
        lit_search.import_status = "RUNNING"
        lit_search.error_msg = None
        lit_search.script_time = datetime.datetime.now(pytz.utc)
        lit_search.save()
        user_id = request.user.id
        logger.info("Running Search for : " + lit_search.term)
        run_single_search.delay(literature_search_id,None,user_id)
        literature_searchs_ser = LiteratureSearchSerializer(lit_search)

        return Response(literature_searchs_ser.data, status=status.HTTP_200_OK)


class CheckRunningStatusView(APIView):
    permission_classes = [
        permissions.IsAuthenticated, 
        isProjectOwner, 
        IsNotArchived,
    ]
    http_method_names = [
        'get',
        'post',
        'head',
        'options',
    ]

    def post(self, request, *args, **kwargs):

        lit_review_id = kwargs.get("id") 
        lit_review = LiteratureReview.objects.get(id=lit_review_id)
        search_id = request.data.get("search_id")
        status_count = (
            LiteratureSearch.objects.filter(id=search_id)
            .exclude(import_status="RUNNING")
            .count()
        )
        is_completed = False
        if status_count > 0:
            is_completed = True

        literature_running = LiteratureSearch.objects.filter(
            id=search_id, import_status="RUNNING", literature_review=lit_review
        ).exclude(script_time=None)
        UTC = pytz.utc
        for running in literature_running:
            current_time = datetime.datetime.now(UTC)
            scripts_time = running.script_time
            time = current_time - scripts_time
            ONE_HOUR = 60 * 60 # this is in seconds
            if time.seconds >= ONE_HOUR:
                running.import_status = "INCOMPLETE-ERROR"
                running.error_msg = "The search process has been running for over an hour without results. Please contact support for assistance in resolving this issue."
                running.save()

        data = {"is_completed": is_completed}
        if is_completed:
            lit_searches = LiteratureSearch.objects.get(id=search_id)
            literature_searchs_ser = LiteratureSearchSerializer(lit_searches)
            data["literature_search"] = literature_searchs_ser.data

        return Response(data, status=status.HTTP_200_OK)

class RunAutoSearchView(APIView):
    permission_classes = [
        permissions.IsAuthenticated, 
        isProjectOwner, 
        IsNotArchived,
        DoesUserHaveEnoughCreditsForImportingArticles
    ]
    parser_classes = (MultiPartParser, FormParser,)
    http_method_names = [
        'post',
        'head',
        'options',
    ]
 
    def post(self, request, *args, **kwargs):

        lit_review_id = kwargs.get("id")
        lit_review = LiteratureReview.objects.get(id=lit_review_id)
        self.check_object_permissions(self.request, lit_review)
    
        literature_search_id = request.data.get("literature_search_id")
        # disable_exclusion = request.POST.get("disableExclusion")
        lit_search = LiteratureSearch.objects.get(id=literature_search_id, literature_review=lit_review)
        # lit_search.disable_exclusion = True if disable_exclusion == "true" else False
        lit_search.disable_exclusion = False
        lit_search.import_status = "RUNNING"
        lit_search.error_msg = None
        lit_search.script_time = datetime.datetime.now(pytz.utc)
        lit_search.save()
        lit_review_id = lit_search.literature_review.id

        if lit_search.db.auto_search_available:
            run_auto_search.delay(lit_review_id, lit_search.id, request.user.id)
        else:
            lit_search.import_status = "INCOMPLETE-ERROR"
            lit_search.error_msg = f"Sorry we don't have auto search for {lit_search.db.name} yet, please use Upload Manual Search instead!"
            lit_search.save()

        literature_searchs_ser = LiteratureSearchSerializer(lit_search)
        return Response(literature_searchs_ser.data, status=status.HTTP_200_OK)


class ExcludeSearchView(APIView):
    permission_classes = [permissions.IsAuthenticated, isProjectOwner, IsNotArchived]
    parser_classes = (MultiPartParser, FormParser,)
    serializer_class = UpdateLiteratureSearchSerializer
    http_method_names = [
        'put',
        'head',
        'options',
    ]

    def put(self, request, *args, **kwargs):

        lit_review_id = kwargs.get("id")
        lit_review = LiteratureReview.objects.get(id=lit_review_id)
        self.check_object_permissions(self.request, lit_review)

        literature_search_id = request.data.get("literature_search_id")
        lit_search = LiteratureSearch.objects.get(id=literature_search_id, literature_review=lit_review)
        update_ser = UpdateLiteratureSearchSerializer(lit_search, request.data)
        update_ser.is_valid(raise_exception=True)
        update_ser.save()
        async_log_action_literature_search_results.delay(
            request.user.id,
            "Excluded Literature Search",
            f"The search term '{lit_search.term}' or database '{lit_search.db}' completed successfully, but all results were excluded.",
            lit_search.id,
            lit_search.literature_review.id,
        )
        literature_searchs_ser = LiteratureSearchSerializer(lit_search)
        return Response(literature_searchs_ser.data, status=status.HTTP_200_OK) 

class ClearDatabaseView(APIView):
    permission_classes = [permissions.IsAuthenticated, isProjectOwner, IsNotArchived]
    serializer_class = UpdateLiteratureSearchSerializer
    http_method_names = [
        'post',
        'head',
        'options',
    ]

    def post(self, request, *args, **kwargs):

        lit_id = kwargs.get("id")
        literature_review = self.get_object(lit_id)
        self.check_object_permissions(self.request, literature_review)

        searches_ids = request.data.get("searches")
        response_data = {"is_completed": False}
        if request.data.get("check_status"):
            pending_clear_count = LiteratureSearch.objects.filter(
                id__in=searches_ids, literature_review=literature_review
            ).exclude(import_status="NOT RUN").count()
            if not pending_clear_count:
                response_data["is_completed"] = True 
                literature_searchs_query = LiteratureSearch.objects.filter(id__in=searches_ids, literature_review=literature_review)
                literature_searchs_ser = LiteratureSearchSerializer(literature_searchs_query, many=True)
                response_data["literature_searchs"] =  literature_searchs_ser.data

            return Response(response_data, status=status.HTTP_200_OK) 

        else:
            search_clear_results_async.delay(literature_review.id, searches_ids)
            return Response("success", status=status.HTTP_200_OK) 

    def get_object(self, pk):   
        return get_object_or_404(LiteratureReview, pk=pk)


class RequestSupportHelp(APIView):
    permission_classes = [permissions.IsAuthenticated, isProjectOwner]
    serializer_class = RequestSupportHelpSerailizer

    def post(self, request, *args, **kwargs):
        lit_id = kwargs.get("id")        
        literature_review = get_object_or_404(LiteratureReview, pk=lit_id)
        serailizer = RequestSupportHelpSerailizer(data=request.data, context={"request": request, "literature_review": literature_review})
        serailizer.is_valid(raise_exception=True)
        mail_info = serailizer.save()
    
        try:
            send_email.delay(mail_info.get("subject"), mail_info.get("message"), to=settings.SUPPORT_EMAILS, from_email=request.user.email)
            logger.debug("Email Message Send: {0}".format(mail_info.get("message")))
            return Response({"success": True}, status=status.HTTP_200_OK)

        except Exception as e:
            error_track = str(traceback.format_exc())
            logger.error("Error requesting support help " + str(error_track))
            return Response({"success": False}, status=status.HTTP_200_OK)


class AnonymousRequestSupportHelp(APIView):
    serializer_class = RequestSupportHelpSerailizer

    def post(self, request, *args, **kwargs):
        serailizer = RequestSupportHelpSerailizer(data=request.data, context={"request": request})
        serailizer.is_valid(raise_exception=True)
        mail_info = serailizer.save()
    
        try:
            send_email.delay(mail_info.get("subject"), mail_info.get("message"), to=settings.SUPPORT_EMAILS)
            logger.debug("Email Message Send: {0}".format(mail_info.get("message")))
            return Response({"success": True}, status=status.HTTP_200_OK)

        except Exception as e:
            error_track = str(traceback.format_exc())
            logger.error("Error requesting support help " + str(error_track))
            return Response({"success": False}, status=status.HTTP_200_OK)


class GenerateSearchReportView(APIView):
    permission_classes = [permissions.IsAuthenticated, isProjectOwner, IsNotArchived]
    serializer_class = UpdateLiteratureSearchSerializer
    http_method_names = [
        'post',
        'head',
        'options',
    ]

    def post(self, request, *args, **kwargs):

        lit_review_id = kwargs.get("id")
        lit_review = LiteratureReview.objects.get(id=lit_review_id)
        self.check_object_permissions(self.request, lit_review)
        
        is_checking = request.data.get("is_checking")
        search_id = request.data.get("search_id")
        
        if is_checking:
            search = LiteratureSearch.objects.get(pk=search_id, literature_review=lit_review)
            ser_res = LiteratureSearchSerializer(search)
            return Response(ser_res.data, status=status.HTTP_200_OK) 

        search_ser = GenerateSearchReportSerializer(data={"search": search_id})  
        search_ser.is_valid(raise_exception=True)
        search_ser.save()

        return Response("Ok", status=status.HTTP_200_OK) 


class ValidateManualFileSearchView(APIView):
    permission_classes = [permissions.IsAuthenticated, isProjectOwner, IsNotArchived]
    http_method_names = [
        'post',
        'head',
        'options',
    ]

    def post(self, request, *args, **kwargs):

        # Extract manual_file and search_id from request.data
        manual_file = request.data.get("manual_file")
        search_id = request.data.get("search_id")

        # Create an instance of the serializer and call its is_valid method
        serializer = ValidateManualFileSearchSerializer(data={"manual_file": manual_file, "search_id": search_id})
        if serializer.is_valid():
            # The validation logic is performed within the serializer's validate method
            validated_data = serializer.validated_data
            return Response(validated_data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


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

class CreateAWSS3DirectUploadURL(APIView):
    permission_classes = [permissions.IsAuthenticated, isProjectOwner]
    http_method_names = [
        'post',
        'head',
        'options',
    ]

    def post(self, request, *args, **kwargs):
        serializer = AWSDirectUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        ser_data = serializer.save()
        return Response(ser_data, status=status.HTTP_200_OK)