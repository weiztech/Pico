from rest_framework.serializers import ModelSerializer, SerializerMethodField
from lit_reviews.models import (
    SearchProtocol,
    LiteratureReview,
    SearchConfiguration,
    NCBIDatabase,
    SearchParameter
)
import datetime 
from lit_reviews.helpers.generic import calculte_years_back
from backend.logger import logger
from rest_framework import serializers
from backend.logger import logger


class SearchParameterSerializer(ModelSerializer):

    class Meta:
        model = SearchParameter
        fields = '__all__'


class UpdateSearchParameterSerializer(ModelSerializer):

    class Meta:
        model = SearchParameter
        fields = ["id", "value"]
        read_only_fields = ("id",)

    def validate(self, data):
        data_value = data.get('value')

        if (self.instance.type == 'CK') and data_value:
            list_options = self.instance.options.split(',')
            list_value = data_value.split(',')            
            if not all(item in list_options for item in list_value):
                raise serializers.ValidationError({'params':"Some of the selected options you've provided are not valid"})
            
        return data       
    
   
class LiteratureReviewSerializer(ModelSerializer):

    class Meta:
        model = LiteratureReview
        fields = ['id','is_archived','is_autosearch']


class SearchConfigurationSerializer(ModelSerializer):
    params = SearchParameterSerializer(many=True)

    class Meta:
        model = SearchConfiguration
        fields = '__all__'


class NCBIDatabaseSerializer(ModelSerializer):
    search_configuration = SerializerMethodField()

    class Meta:
        model = NCBIDatabase
        fields = '__all__'

    def get_search_configuration(self,obj):
        literature_review = self.context.get('literature_review')        
        results = SearchConfiguration.objects.filter(database=obj.name,literature_review=literature_review)
        return SearchConfigurationSerializer(results, many=True).data


class UpdateSearchProtocolSerailizer(ModelSerializer):

    class Meta:
        model = SearchProtocol
        fields = '__all__'
    
    def validate(self,data):
        lit_start_date_of_search = data.get('lit_start_date_of_search')
        lit_date_of_search = data.get('lit_date_of_search')
        ae_start_date_of_search = data.get('ae_start_date_of_search')
        ae_date_of_search = data.get('ae_start_date_of_search')

        if lit_start_date_of_search is None:
            raise serializers.ValidationError({'lit_start_date_of_search':"Literature Search Start Date is required."})
        
        if lit_date_of_search is None:
            raise serializers.ValidationError({'lit_date_of_search':"Literature Search End Date is required."})
        
        if ae_start_date_of_search is None:
            raise serializers.ValidationError({'ae_start_date_of_search':"Adverse Event Search Start Date is required."})
        
        if ae_date_of_search is None:
            raise serializers.ValidationError({'ae_date_of_search':"Adverse Event Search End Date is required."})

        return data   
         

class SearchProtocolSerailizer(ModelSerializer):
    literature_review = LiteratureReviewSerializer()
    lit_searches_databases_to_search = SerializerMethodField() 
    ae_databases_to_search = SerializerMethodField() 
    
    class Meta:
        model = SearchProtocol
        fields = '__all__'

    def get_lit_searches_databases_to_search(self, obj):
        results = obj.lit_searches_databases_to_search.all()
        serializer = NCBIDatabaseSerializer(results, many=True , context={'literature_review':obj.literature_review})
        return serializer.data
    
    def get_ae_databases_to_search(self, obj):
        results = obj.ae_databases_to_search.all()
        serializer = NCBIDatabaseSerializer(results, many=True , context={'literature_review':obj.literature_review})
        return serializer.data
    