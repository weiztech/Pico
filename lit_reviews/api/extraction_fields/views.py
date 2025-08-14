from rest_framework.views import APIView 
from django.shortcuts import get_object_or_404 
from rest_framework import status, response, permissions
from lit_reviews.models import (
    LiteratureReview, 
    ExtractionField,
    AppraisalExtractionField,
)
from .serializers import (
    ExtractionFieldSerializer,
    CreatExtractionFieldSerializer,
)
from lit_reviews.api.cutom_permissions import isProjectOwner, IsNotArchived
from rest_framework.exceptions import ValidationError
from django.db.models import F

class ExtractionFieldsView(APIView):
    permission_classes = [permissions.IsAuthenticated, isProjectOwner, IsNotArchived]

    def get(self, request, *args, **kwargs):
        lit_review_id = kwargs.get("id")
        lit_review = LiteratureReview.objects.get(id=lit_review_id)
        self.check_object_permissions(self.request, lit_review)

        # Get sorting parameter
        ordering = request.query_params.get("ordering", "id")

        # Validate ordering field
        valid_fields = ["id", "name", "type"]
        descending = ordering.startswith("-")
        field_name = ordering.lstrip("-")

        if field_name not in valid_fields:
            raise ValidationError(f"Invalid sorting field: {field_name}")

        # Apply ordering
        if descending:
            extraction_fields = lit_review.extraction_fields.order_by(F(field_name).desc())
        else:
            extraction_fields = lit_review.extraction_fields.order_by(F(field_name))

        # Serialize data
        ExtractionSer = ExtractionFieldSerializer(extraction_fields, many=True)
        return response.Response(
            ExtractionSer.data,
            status=status.HTTP_200_OK
        )

    def post(self, request, *args, **kwargs):

        lit_review_id = kwargs.get("id")    
        lit_review = LiteratureReview.objects.get(id=lit_review_id)
        self.check_object_permissions(self.request, lit_review)
        serializer = CreatExtractionFieldSerializer(data=request.data, context={"lit_review_id": lit_review_id})
        serializer.is_valid(raise_exception=True)
        obj = serializer.save()
        res_serializer = ExtractionFieldSerializer(obj)

        return response.Response(
            res_serializer.data,
            status=status.HTTP_200_OK
        ) 
    
    def put(self, request, *args, **kwargs):
        field_id = request.data.get("id")
        if not field_id:
            return response.Response({"detail": "Field ID is required."}, status=status.HTTP_400_BAD_REQUEST)

        lit_review_id = kwargs.get("id")
        lit_review = LiteratureReview.objects.get(id=lit_review_id)
        self.check_object_permissions(self.request, lit_review)

        try:
            extraction_field = ExtractionField.objects.get(id=field_id, literature_review=lit_review)
        except ExtractionField.DoesNotExist:
            return response.Response({"detail": "Extraction field not found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = CreatExtractionFieldSerializer(
            extraction_field,
            data=request.data,
            context={"lit_review_id": lit_review_id},
            partial=True 
        )
        serializer.is_valid(raise_exception=True)
        obj = serializer.save()

        res_serializer = ExtractionFieldSerializer(obj)
        return response.Response(res_serializer.data, status=status.HTTP_200_OK)


from django.http import JsonResponse
from rest_framework.parsers import JSONParser

class ExtractionFieldsBulkDeleteView(APIView):
    permission_classes = [permissions.IsAuthenticated, isProjectOwner, IsNotArchived]
    parser_classes = [JSONParser]  

    def delete(self, request, id):
        # Get the associated LiteratureReview
        literature_review = get_object_or_404(LiteratureReview, pk=id)

        # Extract selected IDs from the request data
        selected_ids = request.data.get("selectedExtractionFields", [])

        # Validate the input
        if not selected_ids:
            return JsonResponse(
                {"detail": "No fields were selected for deletion."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Filter and delete the selected extraction fields
        extraction_fields = ExtractionField.objects.filter(
            id__in=selected_ids, literature_review=literature_review
        )
        count = extraction_fields.count()

        if count == 0:
            return JsonResponse(
                {"detail": "No matching fields found for the given IDs."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Perform deletion
        AppraisalExtractionField.objects.filter(extraction_field__in=extraction_fields).delete()
        extraction_fields.delete()

        return JsonResponse(
            {"detail": f"{count} extraction field(s) deleted successfully."},
            status=status.HTTP_200_OK,
        )