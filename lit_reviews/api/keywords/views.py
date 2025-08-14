from rest_framework.views import APIView 
from rest_framework.response import Response
from rest_framework import status, permissions
from lit_reviews.tasks import process_abstract_text
from django.shortcuts import get_object_or_404

from lit_reviews.models import (
    CustomKeyWord,
    KeyWord,
    LiteratureReview
)

from lit_reviews.api.adverse_events.serializers import (
    KeywordSerializer,
    CustomKeyWordSerializer,
    SubmitKeywordSerializer
)
from lit_reviews.api.cutom_permissions import doesClientHaveAccess
from lit_reviews.api.cutom_permissions import isProjectOwner, IsNotArchived

# keyWord API 
class KeywordView(APIView):
    permission_classes = [permissions.IsAuthenticated, isProjectOwner, IsNotArchived]

    def get(self, request, *args, **kwargs):
        lit_review_id = kwargs.get("id")
        lit_review = get_object_or_404(LiteratureReview, id=lit_review_id)
        self.check_object_permissions(self.request, lit_review)

        keyword = KeyWord.objects.get_or_create(literature_review=lit_review)[0]
        keyword_serializer = KeywordSerializer(keyword)
        custom_keyword = CustomKeyWord.objects.filter(literature_review=lit_review)
        custom_keyword_serializer = CustomKeyWordSerializer(custom_keyword, many=True)
                    
        response_data = {
            "keyword":keyword_serializer.data,
            "custom_keywords":custom_keyword_serializer.data
        }

        return Response(response_data, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):

        lit_review_id = kwargs.get("id")
        lit_review = get_object_or_404(LiteratureReview, id=lit_review_id)
        self.check_object_permissions(self.request, lit_review)
        instance = KeyWord.objects.get_or_create(literature_review=lit_review)[0]
        serializer = SubmitKeywordSerializer(instance,data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        process_abstract_text.delay(lit_review_id)

        keyword_serializer = KeywordSerializer(instance)
        custom_keyword = CustomKeyWord.objects.filter(literature_review=lit_review)
        custom_keyword_serializer = CustomKeyWordSerializer(custom_keyword, many=True)
                    
        response_data = {
            "keyword":keyword_serializer.data,
            "custom_keywords":custom_keyword_serializer.data
        }

        return Response(response_data, status=status.HTTP_200_OK)

class CustomKeyword(APIView):
    permission_classes = [permissions.IsAuthenticated, isProjectOwner, IsNotArchived]
    
    def get_object(self, pk):
        custom_keyword = get_object_or_404(CustomKeyWord, pk=pk)
        return custom_keyword

    def post(self, request, *args, **kwargs):
        
        lit_review_id = kwargs.get("id")
        lit_review = get_object_or_404(LiteratureReview, id=lit_review_id)
        self.check_object_permissions(self.request, lit_review)
        custom_kw_id = kwargs.get("custom_kw_id")

        custom_kw = self.get_object(custom_kw_id)
        custom_kw.delete()

        process_abstract_text.delay(lit_review_id)

        return Response(status=status.HTTP_200_OK)
