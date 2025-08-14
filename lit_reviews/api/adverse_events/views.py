from django.db.models import Q

from rest_framework.views import APIView 
from rest_framework.generics import DestroyAPIView, UpdateAPIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser
from lit_reviews.citeviews.keywords import keyword
from lit_reviews.tasks import process_abstract_text

from lit_reviews.models import (
    CustomKeyWord,
    KeyWord,
    LiteratureSearch, 
    NCBIDatabase,
    AdverseEventReview,
    AdverseRecallReview,
    LiteratureReview
)

from lit_reviews.api.adverse_events.serializers import (
    AdverseEventReviewSerializer,
    CreateAdverseRecallEventSerializer,
    AdverseRecallReviewSerializer,
    KeywordSerializer,
    CustomKeyWordSerializer,
    SubmitKeywordSerializer
)
from lit_reviews.api.cutom_permissions import IsNotArchived

from django.shortcuts import render, get_object_or_404
from .mixins import ManualAdverEventSearchsMixin
from lit_reviews.api.adverse_events.mixins import ManualAdverEventSearchsMixin

class ManualAdverEventSearchsView(ManualAdverEventSearchsMixin, APIView):
    parser_classes = (MultiPartParser, FormParser,)
    http_method_names = [
        'get',
        'post',
        'delete',
        'head',
        'options',
    ]
    permission_classes = [IsNotArchived]

    def get(self, request, *args, **kwargs):
        lit_review_id = kwargs.get("id")
        is_ae_or_is_recall = Q( Q(db__is_recall=True) | Q(db__is_ae=True) ) 
        __filters = Q(is_ae_or_is_recall & Q(literature_review__id=lit_review_id) )
        lt_searchs = LiteratureSearch.objects.filter(__filters).prefetch_related('db').values('db').distinct()
        dbs_name_list = []
        for item in lt_searchs:
            dbs_name_list.append(item['db'])
            
        dbs = NCBIDatabase.objects.filter(name__in=dbs_name_list)
        response_data = []

        for db in dbs:
            if db.entrez_enum not in ['maude', 'maude_recalls']:
                adverse_events = self.get_adverse_events(db, lit_review_id)
                response_data.append(adverse_events)

            else:
                print("skipping maude db in render")

        return Response(response_data, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):

        lit_review_id = kwargs.get("id")
        is_review_completed = request.data.get("is_completed") == "true"
        db_name = request.data.get("db")
        db = NCBIDatabase.objects.get(name=db_name)
        aes_data = self.get_aes_values()
        
        if is_review_completed:
            LiteratureSearch.objects.filter(db__name=db_name, literature_review_id=lit_review_id).update(result_count=0)

        serializer = CreateAdverseRecallEventSerializer(data=aes_data, many=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        # return back this db ae events and recalls
        adverse_events = self.get_adverse_events(db, lit_review_id) 

        return Response(adverse_events, status=status.HTTP_200_OK)

class DestroyAdverseEventReviewView(DestroyAPIView):
    queryset = AdverseEventReview.objects.all()
    lookup_url_kwarg = "ae_id"
    permission_classes = [IsNotArchived]

    def destroy(self, request, *args, **kwargs):

        pk =  kwargs.get("ae_id")
        review_obj = self.get_object()
        adverse_id = review_obj.ae.id
        super().destroy(request, *args, **kwargs)

        return Response({"id": pk, "object_id": adverse_id} , status=status.HTTP_200_OK)

class DestroyAdverseRecallReviewView(DestroyAPIView):
    queryset = AdverseRecallReview.objects.all()
    lookup_url_kwarg = "ae_id"
    permission_classes = [IsNotArchived]

    def destroy(self, request, *args, **kwargs):

        pk =  kwargs.get("ae_id")
        review_obj = self.get_object()
        recall_id = review_obj.ae.id
        super().destroy(request, *args, **kwargs)

        return Response({"id": pk, "object_id": recall_id} , status=status.HTTP_200_OK)


class UpdateAdverseEventReviewView(UpdateAPIView):
    queryset = AdverseEventReview.objects.all()
    lookup_url_kwarg = "ae_id"
    serializer_class = AdverseEventReviewSerializer
    permission_classes = [IsNotArchived]

    def partial_update(self, request, *args, **kwargs):

        pk =  kwargs.get("ae_id")
        review_obj = self.get_object()
        adverse_id = review_obj.ae.id
        response = super().partial_update(request, *args, **kwargs)
        context = {"id": pk, "object_id": adverse_id, "updated_instance": response.data}

        return Response(context , status=status.HTTP_200_OK)

class UpdateAdverseRecallReviewView(UpdateAPIView):
    queryset = AdverseRecallReview.objects.all()
    lookup_url_kwarg = "ae_id"
    serializer_class = AdverseRecallReviewSerializer
    permission_classes = [IsNotArchived]

    def partial_update(self, request, *args, **kwargs):
        
        pk =  kwargs.get("ae_id")
        review_obj = self.get_object()
        adverse_id = review_obj.ae.id
        response = super().partial_update(request, *args, **kwargs)
        context = {"id": pk, "object_id": adverse_id, "updated_instance": response.data}

        return Response(context , status=status.HTTP_200_OK)

