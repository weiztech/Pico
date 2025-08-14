import datetime, pytz
from django.urls import reverse
from django.shortcuts import get_object_or_404

from rest_framework.views import APIView
from rest_framework.generics import DestroyAPIView, UpdateAPIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.db.models import Q, Case, When, Value, F, fields
from django.db.models.functions import Concat

from lit_reviews.models import (
    FinalReportConfig, 
    FinallReportJob,
    LiteratureReview,
    SearchTermValidator,
    ClinicalLiteratureAppraisal,
)
from client_portal.models import Project

from lit_reviews.api.report_builder.serializers import (
    ProjectSerializer,
    FinallReportJobSerializer,
    ReportConfigSerializer,
    ReportCommentSerializer,
)
from lit_reviews.api.search_terms.serializers import (
    SearchTermValidatorSerializer,
)
from lit_reviews.tasks import (
    build_report,
    build_abbott_report,
    build_protocol,
    generate_ae_report,
    generate_appendix_e2_report,
    generate_fulltext_zip_async,
    export_2nd_pass_extraction_articles,
    export_2nd_pass_extraction_articles_ris,
    generate_search_terms_summary,
    generate_search_terms_summary_excel,
    generate_appendix_e2_report_excel,
    export_article_reviews,
    generate_condense_report,
    build_prisma,
    build_second_pass_word_report,
    export_article_reviews_ris_report,
    generate_search_zip,
    generate_duplicates_report,
    generate_audit_tracking_logs_report,
    generate_device_history_report,
    generate_cumulative_report,
)
from lit_reviews.helpers.articles import get_clinical_appraisal_status_report
from backend.logger import logger
from lit_reviews.api.cutom_permissions import (
    doesClientHaveAccess, 
    doesClientHaveAccessToReport,
    isProjectOwner,
    IsNotArchived
)
class ReportBuilderView(APIView):
    permission_classes = [permissions.IsAuthenticated, isProjectOwner, IsNotArchived]

    def get(self, request, *args, **kwargs):
        lit_review_id = kwargs.get("id") 
        lit_review = LiteratureReview.objects.get(id=lit_review_id)
        self.check_object_permissions(self.request, lit_review)
        project = Project.objects.filter(lit_review=lit_review).first()
        reports = FinallReportJob.objects.filter(literature_review=lit_review).order_by("-id")
        validator = SearchTermValidator.objects.filter(literature_review=lit_review).first()
        config = FinalReportConfig.objects.filter(literature_review=lit_review).first()
        if not config:
            config = FinalReportConfig.objects.create(literature_review=lit_review)

        # Report Filters 
        # Sorting
        sorting = self.request.query_params.get("sorting", None)
        if sorting:
            reports = reports.order_by(sorting)

        # text search filter
        text_filter = self.request.query_params.get("search", None)
        if text_filter:
            reports = reports.filter(Q(
                Q(comment__icontains=text_filter) 
                | Q(report_type__icontains=text_filter) 
                | Q(status__icontains=text_filter)    
            )) 

        # Report Type Filter
        type_filter = self.request.query_params.get("types", None)
        if type_filter:
            types = type_filter.split(",")
            reports = reports.annotate(
                exact_report_type=Case(
                    When(is_simple=True, then=Concat(Value('SIMPLE_'), F('report_type'))),  # If report is simple
                    default=F('report_type'),  # Otherwise, use `regular_value`
                    output_field=fields.CharField(max_length=128)
                )
            ).filter(exact_report_type__in=types) 
            # reports = reports.filter(report_type__in=types) 

        # Report Status Filter
        status_filter = self.request.query_params.get("status", None)
        if status_filter:
            status_list = status_filter.split(",")
            reports = reports.filter(status__in=status_list) 

        # Check if all Clinical Appraisals are completed 
        appraisals = ClinicalLiteratureAppraisal.objects.filter(
            article_review__search__literature_review__id=lit_review_id, article_review__state="I"
        )
        app_list, app_status, app_completed, app_incompleted = get_clinical_appraisal_status_report(appraisals)
        app_completed_count = len(app_completed)
        app_incompleted_count = len(app_incompleted)
        UncompleteExceptExtractions = app_status["UncompleteExceptExtractions"]
        logger.info(f"UncompleteExceptExtractions {UncompleteExceptExtractions}")
        if UncompleteExceptExtractions > 0:
            # Project contains some incomplete Clinical Appraisals 
            complete_articles_link = reverse("lit_reviews:clinical_literature_appraisal_list", kwargs={"id": lit_review_id})
            error_message = f"""
            Some Clinical Literature Appraisals are not completed yet! Ideally, 
            if you want a full report you must first complete all of the listed Clinical 
            Literature Appraisals under <a href="{complete_articles_link}"> 2nd Pass Extractions </a>, but if you wish to generate a 
            Report without completing this step please click 'Yes, Generate'
            """
            project_appraisals = {"is_completed" : False, "error_message": error_message, "complete_articles_link": complete_articles_link}
            logger.warning(f"Incompleted Appraisals {app_incompleted_count} / Completed Appraisals {app_completed_count}")

        else:
            project_appraisals = {"is_completed" : True}
            logger.info(f"Incompleted Appraisals {app_incompleted_count} / Completed Appraisals {app_completed_count}")

        # check client logo
        client_logo =  lit_review.client.logo
        if client_logo:
            logo_exsite = True
        else:
            logo_exsite = False

        context = {
            "reports": FinallReportJobSerializer(reports, many=True).data,
            "validator": SearchTermValidatorSerializer(validator).data,
            "project": ProjectSerializer(project).data,
            "configuration": ReportConfigSerializer(config).data,
            "project_appraisals": project_appraisals,
            "logo_exsite":logo_exsite,
        }

        return Response(context, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):

        report_type = request.data.get("report_type")
        literature_review_id = kwargs.get("id")
        lit_review = LiteratureReview.objects.get(id=literature_review_id)
        self.check_object_permissions(self.request, lit_review)
        logger.debug("report type: "+report_type)
        if report_type == "report": 
            build_report.delay(literature_review_id)
        elif report_type == "protocol": 
            build_protocol.delay(literature_review_id)
        if report_type == "simple_report":
            build_report.delay(literature_review_id, is_simple=True)
        elif report_type == "simple_protocol": 
            build_protocol.delay(literature_review_id, is_simple=True)
        elif report_type == "vigilance": 
            generate_ae_report.delay(literature_review_id)
        elif report_type == "appendix_e2": 
            generate_appendix_e2_report.delay(literature_review_id)
        elif report_type == "appendix_e2_excel":
            generate_appendix_e2_report_excel.delay(literature_review_id)
        elif report_type == "2nd_pass": 
            export_2nd_pass_extraction_articles.delay(literature_review_id)
        elif report_type == "2nd_pass_ris": 
            export_2nd_pass_extraction_articles_ris.delay(literature_review_id)
        elif report_type == "export_article_reviews":
            export_article_reviews.delay(literature_review_id)
        elif report_type == "terms_summary": 
            generate_search_terms_summary.delay(literature_review_id)
        elif report_type == "terms_summary_excel": 
            generate_search_terms_summary_excel.delay(literature_review_id)
        elif report_type == "condense_report": 
            generate_condense_report.delay(literature_review_id)
        elif report_type == "prisma": 
            build_prisma.delay(literature_review_id)
        elif report_type == "2nd_pass_word": 
            build_second_pass_word_report.delay(literature_review_id)
        elif report_type == "full_text_zip": 
            generate_fulltext_zip_async.delay(literature_review_id, request.user.id)
        elif report_type == "article_reviews_ris": 
            export_article_reviews_ris_report.delay(literature_review_id)
        elif report_type == "search_validation_zip": 
            generate_search_zip.delay(literature_review_id)
        elif report_type == "duplicates": 
            generate_duplicates_report.delay(literature_review_id)
        elif report_type == "audit_tracking_logs": 
            generate_audit_tracking_logs_report.delay(literature_review_id)
        elif report_type == "device_history": 
            generate_device_history_report.delay(literature_review_id, user_id=request.user.id)
        elif report_type == "cumulative_report": 
            generate_cumulative_report.delay(literature_review_id, user_id=request.user.id)
        if report_type == "abbott_report": 
            build_abbott_report.delay(literature_review_id)

        return Response("success", status=status.HTTP_200_OK)


class ReportStatusAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated, isProjectOwner, IsNotArchived]

    def get(self, request, *args, **kwargs):
        lit_review_id = kwargs.get("id")
        lit_review = LiteratureReview.objects.get(id=lit_review_id)
        reports = FinallReportJob.objects.filter(literature_review=lit_review).order_by("-id")
        context = {"reports": FinallReportJobSerializer(reports, many=True).data}
        return Response(context, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):

        lit_review_id = kwargs.get("id")
        lit_review = LiteratureReview.objects.get(id=lit_review_id)
        running_reports_ids = request.data.get("running_reports_ids")
        report_running = FinallReportJob.objects.filter(
            id__in=running_reports_ids, 
            status="RUNNING", 
            literature_review=lit_review,
        ).exclude(job_started_time=None)
        UTC = pytz.utc
        for running in report_running:
            current_time = datetime.datetime.now(UTC)
            scripts_time = running.job_started_time
            time = current_time - scripts_time
            ONE_HOUR = 60*60
            if time.seconds >= ONE_HOUR:
                running.status = "INCOMPLETE-ERROR"
                running.error_msg = "The report generation is taking longer than expected, exceeding one hour. Please contact support for assistance in resolving the issue."
                running.save()

        running_count = FinallReportJob.objects.filter(id__in=running_reports_ids, status="RUNNING").count()
        if running_count == 0:
            lit_review_id = kwargs.get("id")
            lit_review = LiteratureReview.objects.get(id=lit_review_id)
            reports = FinallReportJob.objects.filter(literature_review=lit_review, id__in=running_reports_ids).order_by("-id")
            context = {"is_completed": True, "reports": FinallReportJobSerializer(reports, many=True).data}
        else:
            context = {"is_completed": False}

        return Response(context, status=status.HTTP_200_OK)

class GenerateFullTextZipView(APIView):
    permission_classes = [permissions.IsAuthenticated, isProjectOwner, IsNotArchived]

    def post(self, request, *args, **kwargs):

        lit_review_id = kwargs.get("id")
        lit_review = LiteratureReview.objects.get(id=lit_review_id)
        self.check_object_permissions(self.request, lit_review)
        report_id = request.data.get("report_id")
        is_checking = request.data.get("is_checking")
        if is_checking:
            report = FinallReportJob.objects.filter(literature_review__id=lit_review_id, id=report_id).first()
            report_ser = FinallReportJobSerializer(report)
            is_complete = report.generte_zip_status != "RUNNING"
            context = {"is_completed": is_complete, "report": report_ser.data}
            return Response(context, status=status.HTTP_200_OK)

        else:
            lt_review = LiteratureReview(id=lit_review_id)
            finalereportjob = FinallReportJob.objects.filter(literature_review=lt_review, id=report_id).first()
            finalereportjob.generate_zip_error = None
            finalereportjob.generte_zip_status = "RUNNING"
            finalereportjob.save()
            generate_fulltext_zip_async.delay(lit_review_id, report_id)
            return Response("Ok", status=status.HTTP_200_OK)

class UpdateReportCommentView(UpdateAPIView):
    lookup_url_kwarg = "report_id"
    permission_classes = [permissions.IsAuthenticated, isProjectOwner, doesClientHaveAccessToReport, IsNotArchived]
    queryset = FinallReportJob.objects.all()
    serializer_class = ReportCommentSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        lit_review_id = self.kwargs.get("id")
        literature_review = get_object_or_404(LiteratureReview, pk=lit_review_id)
        return queryset.filter(literature_review=literature_review)
    
class UpdateFinalReportConfigView(UpdateAPIView):
    lookup_url_kwarg = "config_id"
    permission_classes = [permissions.IsAuthenticated, isProjectOwner, IsNotArchived]
    queryset = FinalReportConfig.objects.all()
    serializer_class = ReportConfigSerializer

class DestroyReportAPIView(DestroyAPIView):
    permission_classes = [permissions.IsAuthenticated, isProjectOwner, doesClientHaveAccessToReport, IsNotArchived]
    lookup_url_kwarg = "report_id"
    queryset = FinallReportJob.objects.all()

    def get_queryset(self):
        queryset = super().get_queryset()
        lit_review_id = self.kwargs.get("id")
        literature_review = get_object_or_404(LiteratureReview, pk=lit_review_id)
        return queryset.filter(literature_review=literature_review)