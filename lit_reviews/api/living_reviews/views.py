from django.shortcuts import get_object_or_404
from django.db.models import Q
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.generics import UpdateAPIView, ListAPIView

from lit_reviews.api.cutom_permissions import IsLivingReviewOwner, isProjectOwner
from lit_reviews.models import (
    LivingReview,
    LiteratureReview,
    ArticleReview,
    ArticleReviewDeviceMention,
)
from .serializers import LivingReviewSerializer, ArticleReviewSerializer, UpdateLivingReviewSerializer


class LivingReviewListAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        user = request.user
        all_living_reviews = LivingReview.objects.filter(is_active=True)  # Fetch active reviews 
        user_living_reviews_ids = []
        for review in all_living_reviews:
            if review.does_user_have_access(user):
                user_living_reviews_ids.append(review.id)

        user_living_reviews = LivingReview.objects.filter(id__in=user_living_reviews_ids)      
        serializer = LivingReviewSerializer(user_living_reviews, many=True)
        return Response(serializer.data)


class LivingReviewDetailAPIView(APIView):
    permission_classes = [IsAuthenticated, IsLivingReviewOwner]

    def get(self, request, id, *args, **kwargs):
        living_review = get_object_or_404(LivingReview, pk=id)
        serializer = LivingReviewSerializer(living_review)
        return Response(serializer.data)
        

class ArticleReviewListAPIView(ListAPIView):
    permission_classes = [IsAuthenticated, isProjectOwner]
    serializer_class = ArticleReviewSerializer

    def get_queryset(self):
        request = self.request 
        id = self.kwargs.get("id")
        # Ensure the literature review exists
        literature_review = get_object_or_404(LiteratureReview, pk=id)

        # Fetch all article reviews linked to the given literature review

        # Filters
        search_term_filter = request.query_params.get("search")
        db_filter = request.query_params.get("db")
        device_mention = self.request.query_params.get("device_mention", None)
        start_date_filter = request.query_params.get("start_date")
        end_date_filter = request.query_params.get("end_date")

        article_reviews = ArticleReview.objects.filter(search__literature_review=literature_review)
        if search_term_filter:
            article_reviews = article_reviews.filter(
                Q(article__title__icontains=search_term_filter)
                |
                Q(article__abstract__icontains=search_term_filter)
            )

        # Data Base Filter
        db_filter = request.query_params.get("db", None)
        if db_filter:
            dbs = db_filter.split(",")
            article_reviews = article_reviews.filter(search__db__entrez_enum__in=dbs) 

        # Date Filter
        start_date = request.query_params.get("start_date", None)
        if start_date:
            article_reviews = article_reviews.filter(search__start_search_interval__gte=start_date) 
        
        end_date = request.query_params.get("end_date", None)
        if end_date:
            article_reviews = article_reviews.filter(search__end_search_interval__lte=end_date) 

        if device_mention:
            mentions_ids = ArticleReviewDeviceMention.objects.filter(
                article_review__search__literature_review=literature_review
            ).distinct("article_review").values_list("id", flat=True)
            mentions_ids = list(mentions_ids)
            article_reviews = article_reviews.filter(id__in=mentions_ids)

        return article_reviews
    

class UpdateLivingReviewAPIView(UpdateAPIView):
    permission_classes = [IsAuthenticated, IsLivingReviewOwner]
    serializer_class = UpdateLivingReviewSerializer
    queryset = LivingReview.objects.all()
    lookup_field = 'id'

    def update(self, request, *args, **kwargs):
        partial = True  # Always use partial update
        instance = self.get_object()
        
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        
        updated_obj = serializer.save()
        
        # Return the full serialized response using the read serializer
        response_serializer = LivingReviewSerializer(updated_obj)
        return Response(response_serializer.data, status=200)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update({"request": self.request})
        return context