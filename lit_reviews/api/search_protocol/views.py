
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status,permissions
from client_portal.models import Project
import datetime 
from lit_reviews.helpers.generic import calculte_years_back
from backend.logger import logger
from django.shortcuts import get_object_or_404
from django.db.models import Q
from django.core.exceptions import PermissionDenied
from lit_reviews.models import (
    LiteratureReview ,
    SearchProtocol,
    SearchConfiguration,
    NCBIDatabase,
    SearchParameter
)
from .serializers import (
    SearchProtocolSerailizer,
    UpdateSearchProtocolSerailizer,
    NCBIDatabaseSerializer,
    SearchConfigurationSerializer,
    UpdateSearchParameterSerializer
)
from lit_reviews.api.cutom_permissions import isProjectOwner,IsNotArchived

class SearchProtocolAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated, isProjectOwner, IsNotArchived]

    def get(self, request, *args, **kwargs):
        lit_review_id = kwargs.get("id")
        literature_review = LiteratureReview.objects.get(id=lit_review_id)
        project = Project.objects.filter(lit_review=literature_review).first()

        # get instance of searchProtocol
        instance = get_object_or_404(SearchProtocol, literature_review=literature_review)
        protocol_serializer = SearchProtocolSerailizer(instance)

        not_isrecall = Q( Q(is_recall=None) | Q(is_recall=False) )
        not_isae = Q( Q(is_ae=None) | Q(is_ae=False) )
        not_recall_and_not_ae = Q( not_isrecall & not_isae)
        isrecall_or_isae = Q( Q(is_ae=True) | Q(is_recall=True) )

        lit_searches_databases_to_search = NCBIDatabase.objects.filter(not_recall_and_not_ae, is_archived=False)
        lit_searches_databases_to_search_s = NCBIDatabaseSerializer(lit_searches_databases_to_search,
                                                                    many=True, context={'literature_review':literature_review})
        ae_databases_to_search= NCBIDatabase.objects.filter(isrecall_or_isae, is_archived=False)
        ae_databases_to_search_s= NCBIDatabaseSerializer(ae_databases_to_search,many=True,context={'literature_review':literature_review})

        return Response({
            'lit_search_protocol':protocol_serializer.data,
            'lit_searches_databases_to_search':lit_searches_databases_to_search_s.data,
            'ae_databases_to_search':ae_databases_to_search_s.data,
        },status=status.HTTP_200_OK )
    
    def put(self, request, *args, **kwargs):

        lit_review_id = kwargs.get("id")
        literature_review = LiteratureReview.objects.get(id=lit_review_id)
        # get instance of searchProtocol
        instance = get_object_or_404(SearchProtocol, literature_review=literature_review)
        serializer = UpdateSearchProtocolSerailizer(instance, data=request.data)

        if serializer.is_valid():
            validated_data = serializer.validated_data
            lit_start_date = None
            lit_end_date = None
            if validated_data['lit_start_date_of_search'] is not None:
                lit_start_date = datetime.datetime.strptime(str(validated_data['lit_start_date_of_search']), "%Y-%m-%d")
            if validated_data['lit_date_of_search'] is not None:
                lit_end_date = datetime.datetime.strptime(str(validated_data['lit_date_of_search']), "%Y-%m-%d")

            ae_start_date = None
            ae_end_date = None            
            if validated_data['ae_start_date_of_search'] is not None:
                ae_start_date = datetime.datetime.strptime(str(validated_data['ae_start_date_of_search']), "%Y-%m-%d")

            if validated_data['ae_date_of_search'] is not None:
                ae_end_date = datetime.datetime.strptime(str(validated_data['ae_date_of_search']), "%Y-%m-%d")
            
            years_back = calculte_years_back(lit_start_date, lit_end_date)
            ae_years_back = calculte_years_back(ae_start_date, ae_end_date)
            logger.debug("years back: " + str(years_back))
            logger.debug("Ae years back: " + str(ae_years_back))

            protocol = serializer.save()
            protocol.years_back = years_back
            if ae_years_back:
                protocol.ae_years_back = ae_years_back
            else:
                protocol.ae_years_back = 0  # Set a default value
            protocol.save()
            
            # Check if all db start/end date params have a default value if value is None
            search_protocol = get_object_or_404(SearchProtocol, literature_review=literature_review)
            default_end_date = search_protocol.lit_date_of_search
            default_start_date = search_protocol.lit_start_date_of_search
            configurations = SearchConfiguration.objects.filter(literature_review=literature_review)

            for config in configurations:
                for param in config.params.filter(name="Start Date"):
                    if not param.value:
                        param.value = default_start_date
                        param.save()

                for param in config.params.filter(name="End Date"):
                    if not param.value:
                        param.value = default_end_date
                        param.save()

            serializer = SearchProtocolSerailizer(protocol)
            return Response(serializer.data)
        
        return Response(serializer.errors, status=400)


class UpdateDBSearchConfigurationAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated, isProjectOwner, IsNotArchived]
    serializer_class = UpdateSearchParameterSerializer
    
    def put(self, request, *args, **kwargs):
        
        search_config_id = kwargs.get("search_config_id")
        params = request.data.get('params','None')
        config_type = request.data.get('config_type','None')

        if len(params):
            for param in params:
                param_instance = get_object_or_404(SearchParameter, id=param['id'])
                if param_instance.search_config.literature_review.id != kwargs.get("id"):
                    raise PermissionDenied()
                
                serializer = self.serializer_class(param_instance, data=param)
                serializer.is_valid(raise_exception=True)
                serializer.save()
        
        sc_instance = get_object_or_404(SearchConfiguration, id=search_config_id)  
        sc_instance.config_type = config_type  
        sc_instance.save()   

        serializer_data = SearchConfigurationSerializer(sc_instance)
        return Response(serializer_data.data, status=status.HTTP_200_OK)
    



