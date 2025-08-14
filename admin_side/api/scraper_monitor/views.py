from rest_framework.generics import ListAPIView
from rest_framework import permissions, response, filters

from lit_reviews.models import ScraperReport, LiteratureReview, NCBIDatabase
from lit_reviews.api.cutom_permissions import isStaffUser
from lit_reviews.api.pagination import CustomPagination
from .serializers import (
    ScraperReportSerializer, 
    NCBIDatabaseSerializer,
    LiterateReviewSerializer,
)


class ScraperReportsListAPIView(ListAPIView):
    permission_classes = [
        permissions.IsAuthenticated,
        isStaffUser,
    ]
    serializer_class = ScraperReportSerializer
    pagination_class = CustomPagination
    queryset = ScraperReport.objects.all()
    # Explicitly specify which fields the API may be ordered against
    # ordering_fields = ('article__title', '-article__title', 'score', "-score")
    # This will be used as the default ordering
    ordering = ('id')
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['user__username', 'search_term']

    def apply_custom_filters(self, queryset):
        db_filter = self.request.query_params.get("database_name")
        review_filter = self.request.query_params.get("literature_review")
        status_filter = self.request.query_params.get("status")

        if db_filter:
            db_filter = db_filter.split(",")
            queryset = queryset.filter(database_name__in=db_filter)

        if review_filter:
            review_filter = review_filter.split(",")
            queryset = queryset.filter(literature_review__id__in=review_filter)

        if status_filter:
            status_filter = status_filter.split(",")
            queryset = queryset.filter(status__in=status_filter)

        return queryset 
    
    def get(self, request, *args, **kwargs):
        queryset = self.apply_custom_filters(self.get_queryset())
        queryset = self.filter_queryset(queryset)
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            res = self.get_paginated_response(serializer.data)
            reports = res.data
        else:
            serializer = self.get_serializer(queryset, many=True)
            reports = serializer.data 

        # Get list of reviews
        lit_reviews = LiteratureReview.objects.all()
        reviews_ser = LiterateReviewSerializer(lit_reviews, many=True)

        # Get list of databases
        dbs = NCBIDatabase.objects.all()
        dbs_ser = NCBIDatabaseSerializer(dbs, many=True)  

        return response.Response({
            "reports": reports,
            "dbs": dbs_ser.data,
            "lit_reviews": reviews_ser.data,
        })

    
