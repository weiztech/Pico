from rest_framework.views import APIView 
from rest_framework.generics import ListAPIView, CreateAPIView, DestroyAPIView, UpdateAPIView
from rest_framework import permissions, response, status, filters
from django.shortcuts import get_object_or_404 

from lit_reviews.api.pagination import CustomPagination
from lit_reviews.models import (
    ArticleTag, 
    LiteratureReview
)
from .serializers import (
    ArticleTagSerializer, 
    AttachTagToArticlesSerializer,
)
from lit_reviews.api.cutom_permissions import isProjectOwner, IsNotArchived

class ArticleTagListAPIView(ListAPIView):
    permission_classes = [permissions.IsAuthenticated, isProjectOwner]
    serializer_class = ArticleTagSerializer
    # pagination_class = CustomPagination
    queryset = ArticleTag.objects.all()
    # Explicitly specify which fields the API may be ordered against
    # ordering_fields = ('article__title', '-article__title', 'score', "-score")
    # This will be used as the default ordering
    # ordering = ('-article__title')
    # filter_backends = (filters.OrderingFilter,)

    def get_queryset(self):
        queryset = super().get_queryset()
        lit_review_id = self.kwargs.get("id")
        literature_review = get_object_or_404(LiteratureReview, pk=lit_review_id)
        return queryset.filter(literature_review=literature_review)
    


class ArticleTagCreateAPIView(CreateAPIView):
    permission_classes = [permissions.IsAuthenticated, isProjectOwner, IsNotArchived]
    serializer_class = ArticleTagSerializer
    queryset = ArticleTag.objects.all()

    def perform_create(self, serializer):
        return  serializer.save(creator=self.request.user)


class ArticleTagUpdateAPIView(UpdateAPIView):
    permission_classes = [permissions.IsAuthenticated, isProjectOwner, IsNotArchived]
    serializer_class = ArticleTagSerializer
    queryset = ArticleTag.objects.all()
    lookup_url_kwarg = "tag_id"

    def get_queryset(self):
        queryset = super().get_queryset()
        lit_review_id = self.kwargs.get("id")
        literature_review = get_object_or_404(LiteratureReview, pk=lit_review_id)
        return queryset.filter(literature_review=literature_review)
    
class ArticleTagDeleteAPIView(DestroyAPIView):
    permission_classes = [permissions.IsAuthenticated, isProjectOwner, IsNotArchived]
    serializer_class = ArticleTagSerializer
    queryset = ArticleTag.objects.all()
    lookup_url_kwarg = "tag_id"

    def get_queryset(self):
        queryset = super().get_queryset()
        lit_review_id = self.kwargs.get("id")
        literature_review = get_object_or_404(LiteratureReview, pk=lit_review_id)
        return queryset.filter(literature_review=literature_review)
    
    
class AttachTagToArticlesView(APIView):
    serializer_class = AttachTagToArticlesSerializer
    permission_classes = [permissions.IsAuthenticated, isProjectOwner]

    def post(self, request):
        serializer = AttachTagToArticlesSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return response.Response({"success": True}, status=status.HTTP_200_OK)  