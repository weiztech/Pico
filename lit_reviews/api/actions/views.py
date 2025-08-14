from rest_framework.generics import ListAPIView, UpdateAPIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from actstream.models import Action
from .serializers import ActionSerializer
from backend.logger import logger
from lit_reviews.api.pagination import CustomPaginationActions
from rest_framework import permissions, response, status, filters
from django.contrib.auth import get_user_model
from rest_framework.views import APIView 
from django.shortcuts import get_object_or_404
from lit_reviews.models import LiteratureReview
from django.db.models import IntegerField
from django.db.models.functions import Cast
from datetime import datetime
from django.db.models import Q
from lit_reviews.api.cutom_permissions import isProjectOwner

User = get_user_model()

class ActionsView(ListAPIView):
    permission_classes = [IsAuthenticated, isProjectOwner]
    queryset = Action.objects.all()
    serializer_class = ActionSerializer
    pagination_class = CustomPaginationActions
    # Explicitly specify which fields the API may be ordered against
    ordering_fields = ('actor_object_id', 'verb', 'timestamp')
    # This will be used as the default ordering
    ordering = ('-timestamp',)
    filter_backends = (filters.OrderingFilter,)


    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update({"request": self.request})
        return context

    def get_queryset(self):
        lit_review_id = self.kwargs.get("id")
        logger.info(f"lit_review_id {lit_review_id}")
        queryset = Action.objects.filter(
                target_object_id=lit_review_id,
                public = True
            )

        # text search filter
        text_filter = self.request.query_params.get("search", None)
        if text_filter:
            queryset = queryset.filter(
                Q (
                    Q(description__icontains=text_filter) 
                    | Q(verb__icontains=text_filter)
                )
            )

        # selected_user filter
        selected_user = self.request.query_params.get("selected_user", None)
        if selected_user:
            user = get_object_or_404(User, username=selected_user)
            queryset = queryset.filter(actor_object_id=user.id)


        # selected_types filter
        selected_types_str = self.request.query_params.get("selected_types", None)
        if selected_types_str:
            selected_types = selected_types_str.split(",")
            queryset = queryset.filter(verb__in=selected_types)
        
        # selected_start_date filter
        selected_start_date = self.request.query_params.get("selected_start_date", None)
        if selected_start_date:
            try:
                start_date = datetime.strptime(selected_start_date, '%Y-%m-%d')
                queryset = queryset.filter(timestamp__gte=start_date)
            except ValueError:
                logger.error(f"Invalid date format for selected_start_date: {selected_start_date}")

        # selected_end_date filter
        selected_end_date = self.request.query_params.get("selected_end_date", None)
        if selected_end_date:
            try:
                end_date = datetime.strptime(selected_end_date, '%Y-%m-%d')
                queryset = queryset.filter(timestamp__lte=end_date)
            except ValueError:
                logger.error(f"Invalid date format for selected_end_date: {selected_end_date}")


        # Apply ordering
        ordering = self.request.query_params.get('ordering', '-timestamp')
        queryset = queryset.order_by(ordering)

        return queryset
        
    def get(self,request, *args, **kwargs):
        queryset = self.get_queryset()
        page = self.paginate_queryset(queryset)
        
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return response.Response(serializer.data)


class ActionsFiltersView(APIView):
    permission_classes = [permissions.IsAuthenticated, isProjectOwner]

    def get(self, request, *args, **kwargs):
        lit_review_id = kwargs.get("id")
        lit_review = get_object_or_404(LiteratureReview, id=lit_review_id)
        self.check_object_permissions(self.request, lit_review)

        actions = Action.objects.filter(
                target_object_id=lit_review_id,
                public = True
            ).order_by('-timestamp')
        
        user_ids = actions.annotate(actor_object_id_int=Cast('actor_object_id', IntegerField())).values_list('actor_object_id_int', flat=True).distinct()
        users = User.objects.filter(id__in=user_ids).values_list('username', flat=True)

        distinct_verbs = set(actions.values_list('verb', flat=True))

        response_data = {
            'users': list(users),
            'verbs': list(distinct_verbs)
        }

        return Response(response_data, status=status.HTTP_200_OK)