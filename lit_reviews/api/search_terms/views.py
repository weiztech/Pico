from datetime import datetime, timedelta

from django.shortcuts import get_object_or_404
from django.utils import timezone

from rest_framework.views import APIView
from rest_framework.generics import DestroyAPIView
from rest_framework.response import Response
from rest_framework import status, permissions

from backend.logger import logger
from rest_framework.parsers import MultiPartParser, FormParser
from lit_reviews.models import (
    LiteratureReview,
    LiteratureSearch,
    LiteratureReviewSearchProposal,
    NCBIDatabase,
    SearchTermsPropsSummaryReport,
    SearchTermValidator,
    SearchProtocol,
    SearchTermPreview,
    CustomerSettings,
    SearchLabelOption
)
from lit_reviews.api.search_terms.serializers import (
    NCBIDatabaseSerializer,
    SearchTermsPropsSummaryReportSerializer,
    SearchTermValidatorSerializer,
    SearchProtocolSerializer,
    CreateNewSearchTermSerializer,
    UpdateSearchTermSerializer,
    SplitTermSerializer,
    LiteratureReviewSearchProposalReport,
    ResultSummarySerializer,
    SearchTermPreviewSerializer,
)
from lit_reviews.helpers.generic import get_customer_settings
from lit_reviews.api.home.serializers import SearchLabelOptionSerializer
from lit_reviews.tasks import (
    validate_search_terms_async,
    generate_search_terms_summary,
    run_auto_search,
)
from lit_reviews.helpers.search_terms import construct_search_terms_list
from lit_reviews.api.cutom_permissions import (
    doesClientHaveAccess, 
    doesClientHaveAccessToProposal,
    isProjectOwner,
    IsNotArchived
)
from lit_reviews.utils.consts import (
    OTHER_TERMS,
    CONDITION_AND_DISEASE,
    INTERVENTIOO_TREAMENT,
    LOCATION,
    PRODUCT_CODE,
    MANUFACTURER,
    MODEL_NUMBER,
    REPORT_NUMBER,
    BRAND_NAME, 
)
CLINICAL_TRIALS_SEARCH_FIELD_OPTIONS = [OTHER_TERMS, CONDITION_AND_DISEASE, INTERVENTIOO_TREAMENT, LOCATION]
FDA_MAUDE_SEARCH_FIELD_OPTIONS = [PRODUCT_CODE, MANUFACTURER, MODEL_NUMBER, REPORT_NUMBER, BRAND_NAME]


class SearchTermsView(APIView):
    permission_classes = [permissions.IsAuthenticated, isProjectOwner, IsNotArchived]
    http_method_names = [
        'get',
        'post',
        'head',
        'options',
    ]

    def get(self, request, *args, **kwargs):
        """
        Retrieve list of terms.
        """
        lit_review_id = kwargs.get("id")
        lit_review = LiteratureReview.objects.get(id=lit_review_id)
        self.check_object_permissions(self.request, lit_review)
        props = LiteratureReviewSearchProposal.objects.filter(
            literature_review=lit_review
        ).prefetch_related("literature_search", "report").order_by("id")

        terms_list, total_terms = construct_search_terms_list(props)

        ncbi_database = NCBIDatabase.objects.filter(is_archived=False).order_by("name")
        db_ser = NCBIDatabaseSerializer(ncbi_database, many=True) 

        search_protocol  = SearchProtocol.objects.filter(literature_review__id=lit_review_id).first()

        lit_dbs = search_protocol.lit_searches_databases_to_search
        lit_dbs_ser = NCBIDatabaseSerializer(lit_dbs, many=True, context={'literature_review':lit_review})

        ae_dbs = search_protocol.ae_databases_to_search
        ae_dbs_ser = NCBIDatabaseSerializer(ae_dbs, many=True, context={'literature_review':lit_review})

        summary_doc = SearchTermsPropsSummaryReport.objects.filter(literature_review__id=lit_review_id).order_by("-start_date").first()
        summary_doc_ser = SearchTermsPropsSummaryReportSerializer(summary_doc)
        validator = SearchTermValidator.objects.filter(literature_review__id=lit_review_id).first()
        validator_ser = SearchTermValidatorSerializer(validator)
        search_protocol = SearchProtocol.objects.filter(literature_review__id=lit_review_id).first()
        search_protocol_ser = SearchProtocolSerializer(search_protocol)

        customer_settings = get_customer_settings(request.user)
        search_labels = SearchLabelOption.objects.filter(customer_settings=customer_settings)
        search_labels_serializer = SearchLabelOptionSerializer(search_labels, many=True)

        pico_categories = [{"value": choice[0], "label": choice[1]} for choice in LiteratureSearch.PicoCategory.choices]
        json_res =  {
            "validator": validator_ser.data,
            "lit_review_id": lit_review_id,
            "search_protocol":search_protocol_ser.data,
            "terms": terms_list,
            "summary_doc": summary_doc_ser.data,
            "total_terms": total_terms,
            "dbs": db_ser.data,
            "lit_dbs": lit_dbs_ser.data,
            "ae_dbs": ae_dbs_ser.data,
            "CLINICAL_TRIALS_SEARCH_FIELD_OPTIONS": CLINICAL_TRIALS_SEARCH_FIELD_OPTIONS,
            "FDA_MAUDE_SEARCH_FIELD_OPTIONS": FDA_MAUDE_SEARCH_FIELD_OPTIONS,
            "search_labels":search_labels_serializer.data,
            "pico_categories": pico_categories
        }

        return Response(json_res, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        """
        Add a new literature Search Term.
        """
        
        lit_review_id = kwargs.get("id")
        lit_review = LiteratureReview.objects.get(id=lit_review_id)
        self.check_object_permissions(self.request, lit_review)        
        # is_tem_term_exists = LiteratureReviewSearchProposal.objects.filter(term="temp term", literature_review__id=lit_review_id).exists()
        # if not is_tem_term_exists:
        #     ser = CreateNewSearchTermSerializer(data={"term_type": term_type, "lit_review_id": lit_review_id})
        #     ser.is_valid(raise_exception=True)
        #     new_row = ser.save()
            
        #     res_data = {
        #         "value": new_row,
        #         "term": "temp term",
        #         "id": new_row[0].get('proposal').get("id"),
        #         "index": last_id_count + 1,
        #     }
        #     return Response(res_data, status=status.HTTP_201_CREATED)
        current_terms_count = request.data.get("total_count")
        ser = CreateNewSearchTermSerializer(data=request.data, context={"user_id": request.user.id, "lit_review_id": lit_review_id})
        ser.is_valid(raise_exception=True)
        updated_term = ser.save()
        props = LiteratureReviewSearchProposal.objects.filter(
            term=updated_term, 
            literature_review=lit_review
        )
        terms_list, total_terms = construct_search_terms_list(props, current_terms_count)
        return Response({"added_terms": terms_list}, status=status.HTTP_200_OK)
    


class UpdateSearchTermsView(APIView):
    permission_classes = [permissions.IsAuthenticated, isProjectOwner, IsNotArchived]

    def post(self, request, *args, **kwargs):

        lit_review_id = kwargs.get("id")
        lit_review = LiteratureReview.objects.get(id=lit_review_id)
        self.check_object_permissions(self.request, lit_review)
        
        if request.data.get("is_checking", False):
            order_by = request.data.get("order_by", "id")
            inprogress_reports = LiteratureReviewSearchProposalReport.objects.filter(
                status__in=["PROCESSING", "FETCHING_PREVIEW"],
                literature_review=lit_review,
            )
            
            # if fetching preview takes more than five min mark it as failed.
            for in_progress_report in inprogress_reports:
                updated_at_plus_five = in_progress_report.updated_at + timedelta(minutes=5)
                now_ware = timezone.make_aware(datetime.now(), timezone.get_current_timezone())
                if  now_ware > updated_at_plus_five:
                    in_progress_report.status = "FAILED"
                    in_progress_report.errors = "Failed to fetch preview data. The process was running endlessly. Please contact support for further assistance!"
                    in_progress_report.save()

            props = LiteratureReviewSearchProposal.objects.filter(
                literature_review=lit_review
            ).prefetch_related("literature_search", "report").order_by(order_by)
            terms_list, total_terms = construct_search_terms_list(props)

            if not inprogress_reports.count():
                return Response({"is_completed": True, "terms": terms_list}, status=status.HTTP_200_OK)

            else:
                return Response({"is_completed": False, "terms": terms_list}, status=status.HTTP_200_OK)

        if request.data.get("update_type") == "single":
            current_terms_count = request.data.get("total_count")
            ser = UpdateSearchTermSerializer(data=request.data, context={"user_id": request.user.id})
            ser.is_valid(raise_exception=True)
            updated_term = ser.save()
            props = LiteratureReviewSearchProposal.objects.filter(
                term=updated_term, 
                literature_review=lit_review
            )
            terms_list, total_terms = construct_search_terms_list(props, current_terms_count)
            return Response({"new_terms": terms_list}, status=status.HTTP_200_OK)

        elif request.data.get("update_type") == "bulk":
            ser = UpdateSearchTermSerializer(data=request.data.get("rows"), many=True, context={"user_id": request.user.id})
            ser.is_valid(raise_exception=True)
            ser.save()
            return Response("success", status=status.HTTP_200_OK)

        elif request.data.get("update_type") == "split":
            ser = SplitTermSerializer(data=request.data, context={"user_id": request.user.id, "lit_review": lit_review})
            ser.is_valid(raise_exception=True)
            ser.save()

            props = LiteratureReviewSearchProposal.objects.filter(
                literature_review=lit_review
            ).prefetch_related("literature_search", "report").order_by("id")

            terms_list, total_terms = construct_search_terms_list(props)
            return Response({"terms": terms_list, "total_terms": total_terms}, status=status.HTTP_200_OK)            

class DeleteSearchTermsView(DestroyAPIView):
    permission_classes = [permissions.IsAuthenticated, isProjectOwner, doesClientHaveAccessToProposal, IsNotArchived]
    queryset = LiteratureReviewSearchProposal.objects.all()
    lookup_url_kwarg = "prop_id"

    def destroy(self, request, *args, **kwargs):

        prop = self.get_object()
        term = prop.term
        lit_review_id = kwargs.get("id")
        props = LiteratureReviewSearchProposal.objects.filter(term=term, literature_review__id=lit_review_id)
        for prop in props:
            lit_search = LiteratureSearch.objects.filter(
                db=prop.db,
                term=prop.term,
                literature_review=prop.literature_review
            ).first()
            if lit_search:
                lit_search.delete()
            prop.delete()

        return Response({"term": term}, status=status.HTTP_200_OK)

class BulkSearchTermDelteView(APIView):
    permission_classes = [permissions.IsAuthenticated, isProjectOwner, IsNotArchived]

    def post(self, request, *args, **kwargs):

        lit_review_id = kwargs.get("id")
        lit_review = LiteratureReview.objects.get(id=lit_review_id)
        self.check_object_permissions(self.request, lit_review)
        props_ids = request.data.get("props_ids") 
        for id in props_ids:
            prop = LiteratureReviewSearchProposal.objects.filter(id=id).first()
            if prop:
                term = prop.term
                props = LiteratureReviewSearchProposal.objects.filter(term=term, literature_review__id=lit_review_id)
                for prop in props:
                    lit_search = LiteratureSearch.objects.filter(
                        db=prop.db,
                        term=prop.term,
                        literature_review=prop.literature_review
                    ).first()
                    if lit_search:
                        lit_search.delete()
                    prop.delete()

        return Response({"term": term}, status=status.HTTP_200_OK)
    


class SearchTermValidatorView(APIView):
    permission_classes = [permissions.IsAuthenticated, isProjectOwner]

    def post(self, request, *args, **kwargs):

        json_res = {}
        literature_review_id = kwargs.get("id")
        if request.data.get("is_checking"):
            validator = SearchTermValidator.objects.filter(literature_review__id=literature_review_id).first()
            validator_ser = SearchTermValidatorSerializer(validator)
            json_res["validator"] = validator_ser.data

        else:
            print("literature_review_id: ", literature_review_id)
            validate_search_terms_async.delay(literature_review_id)
            json_res["success"] = True

        return Response(json_res, status=status.HTTP_200_OK)


class ResultSummaryView(APIView):
    permission_classes = [permissions.IsAuthenticated, isProjectOwner, IsNotArchived]
    
    def get(self, request, *args, **kwargs):
        lit_review_id = kwargs.get("id")
        lit_review = LiteratureReview.objects.get(id=lit_review_id)
        self.check_object_permissions(self.request, lit_review)

        summary_doc = SearchTermsPropsSummaryReport.objects.filter(literature_review__id=lit_review_id).order_by("-start_date").first()
        serializer = ResultSummarySerializer(summary_doc)
        return Response(serializer.data, status=status.HTTP_200_OK)
            
    def post(self, request, *args, **kwargs):

        lit_review_id = kwargs.get("id")
        lit_review = LiteratureReview.objects.get(id=lit_review_id)
        self.check_object_permissions(self.request, lit_review)

        generate_search_terms_summary.delay(lit_review_id)

        return Response({"success": True}, status=status.HTTP_200_OK)
    

class RunPreviewAutoSearchView(APIView):
    permission_classes = [permissions.IsAuthenticated, isProjectOwner, IsNotArchived]
    # parser_classes = (MultiPartParser, FormParser,)
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
        lit_search = LiteratureSearch.objects.get(id=literature_search_id)
        lit_review_id = lit_search.literature_review.id
        
        AVAILABLE_SCRAPERS = ["pubmed", "cochrane", "pmc", "ct_gov", "maude", "pmc_europe","maude_recalls"]
        if lit_search.db.entrez_enum in AVAILABLE_SCRAPERS:
            preview = SearchTermPreview.objects.create(status="RUNNING", literature_search=lit_search, user=request.user)
            result_url = None
            if lit_search.db.entrez_enum in ["pubmed", "pmc"]:
                result_url = run_auto_search(lit_review_id, lit_search.id, request.user.id, preview=preview.id)
            else:
                run_auto_search.delay(lit_review_id, lit_search.id, request.user.id, preview=preview.id)
        else:
            return Response({"error": "Auto Search not available for this database yet!"}, status=status.HTTP_400_BAD_REQUEST)

        return Response({"preview_id": preview.id, "result_url": result_url}, status=status.HTTP_200_OK)
    
class CheckPreviewStatusAPI(APIView):
    permission_classes = [permissions.IsAuthenticated, isProjectOwner, IsNotArchived]
    # parser_classes = (MultiPartParser, FormParser,)
    http_method_names = [
        'post',
        'head',
        'options',
    ]

    def post(self, request, *args, **kwargs):
        
        preview_id = request.data.get("preview_id")
        preview = get_object_or_404(SearchTermPreview, id=preview_id)
        lit_search = preview.literature_search
        lit_review_id = lit_search.literature_review.id
        lit_review = LiteratureReview.objects.get(id=lit_review_id)
        self.check_object_permissions(self.request, lit_review)
        ser = SearchTermPreviewSerializer(preview)

        return Response(ser.data, status=status.HTTP_200_OK)