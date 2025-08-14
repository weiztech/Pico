from django.urls import reverse
from django.conf import settings
from django.core.files import File

from rest_framework import serializers 

from lit_reviews.models import (
    KeyWord,
    CustomKeyWord,
    LiteratureSearch, 
    NCBIDatabase,
    AdverseEventReview,
    AdverseRecallReview,
    AdverseEvent,
    AdverseRecall,
    NCBIDatabase,
)


class NCBIDatabaseSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = NCBIDatabase 
        fields = '__all__'

class AdverseEventSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = AdverseEvent 
        fields = '__all__'

class AdverseRecallSerializer(serializers.ModelSerializer):

    class Meta:
        model = AdverseRecall 
        fields = '__all__'

class NCBIDataBaseSerializer(serializers.ModelSerializer):

    class Meta:
        model = NCBIDatabase 
        fields = '__all__'

class AdverseEventReviewSerializer(serializers.ModelSerializer):
    ae = AdverseEventSerializer()
    update_ae_url = serializers.SerializerMethodField()
    delete_ae_url = serializers.SerializerMethodField()

    class Meta:
        model = AdverseEventReview 
        fields = '__all__'

    def get_update_ae_url(self, obj):
        return reverse('literature_reviews:update_adverse_event', kwargs={'id': obj.search.literature_review.id ,'ae_id': obj.id})

    def get_delete_ae_url(self, obj):
        return reverse('literature_reviews:delete_adverse_event', kwargs={'id': obj.search.literature_review.id ,'ae_id': obj.id})

    def update(self, instance, validated_data):
        ae_data = validated_data.get("ae")
        manual_pdf = ae_data.get("manual_pdf")
        ae = instance.ae
        ae.manual_type = ae_data.get("manual_type")
        ae.manual_severity = ae_data.get("manual_severity")
        ae.manual_link = ae_data.get("manual_link")
        ae.event_date = ae_data.get("event_date")
        if manual_pdf:
            ae.manual_pdf = manual_pdf 

        ae.save()

        instance.search = validated_data.get("search")
        instance.save()

        return instance


class AdverseRecallReviewSerializer(serializers.ModelSerializer):
    ae = AdverseRecallSerializer()
    update_ae_url = serializers.SerializerMethodField()
    delete_ae_url = serializers.SerializerMethodField()

    class Meta:
        model = AdverseRecallReview 
        fields = '__all__'

    def get_update_ae_url(self, obj):
        return reverse('literature_reviews:update_adverse_event', kwargs={'id': obj.search.literature_review.id ,'ae_id': obj.id})

    def get_delete_ae_url(self, obj):
        return reverse('literature_reviews:delete_adverse_event', kwargs={'id': obj.search.literature_review.id ,'ae_id': obj.id})

    def update(self, instance, validated_data):
        ae_data = validated_data.get("ae")
        manual_pdf = ae_data.get("manual_pdf")
        ae = instance.ae
        ae.manual_type = ae_data.get("manual_type")
        ae.manual_severity = ae_data.get("manual_severity")
        ae.manual_link = ae_data.get("manual_link")
        ae.event_date = ae_data.get("event_date")
        if manual_pdf:
            ae.manual_pdf = manual_pdf 

        ae.save()

        instance.search = validated_data.get("search")
        instance.save()

        return instance
        
class LiteratureSearchSerializer(serializers.ModelSerializer):

    class Meta:
        model = LiteratureSearch 
        fields = ["id", "term", "literature_review"]

class ManualAdverseEventSerializer(serializers.Serializer):
    database = NCBIDataBaseSerializer()
    adverse_events = AdverseEventReviewSerializer(many=True)
    adverse_recalls = AdverseRecallReviewSerializer(many=True)
    is_completed_review = serializers.BooleanField()
    search_id = serializers.IntegerField()
    forms_count = serializers.IntegerField()
    searches = LiteratureSearchSerializer(many=True)

class CreateAdverseRecallEventSerializer(serializers.Serializer):
    type = serializers.CharField(allow_null=True)
    severity = serializers.CharField(allow_null=True)
    link = serializers.CharField(allow_null=True, allow_blank=True)
    pdf = serializers.FileField(allow_null=True)
    ae_or_recall = serializers.CharField()
    event_date = serializers.DateField(allow_null=True, format="%m-%d-%Y")
    search = serializers.IntegerField()
    db = serializers.CharField()

    def get_adverse_event_key_values(self, validated_data):
        values = {}
        for key in validated_data:
            if key != "event_date" and key != "db":
                values["manual_" + key] = validated_data[key] 
            else:
                values[key] = validated_data[key] 

        print("values: ", values)
        return values

    def create(self, validated_data):
        ae_or_recall = validated_data.pop("ae_or_recall")
        pdf = validated_data.pop("pdf")
        search_id = validated_data.pop("search")
        search = LiteratureSearch.objects.get(id=search_id)
        db_name = validated_data.get("db")
        db = NCBIDatabase.objects.get(name=db_name)
        validated_data["db"] = db 
        values = self.get_adverse_event_key_values(validated_data)
        
        if ae_or_recall == "AE":
            instance = AdverseEvent.objects.create(**values)
            search.ae_events.add(instance)
            AdverseEventReview.objects.create(ae=instance, search=search, state="IN")

        else:
            instance = AdverseRecall.objects.create(**values)
            search.ae_recalls.add(instance)
            AdverseRecallReview.objects.create(ae=instance, search=search, state="IN")

        if pdf:
            TMP_ROOT = settings.TMP_ROOT
            FILE_PATH = TMP_ROOT +  "/search" + str(pdf)
            with open(FILE_PATH, "wb") as f:
                for chunk in pdf.chunks():
                    f.write(chunk)

            f = open(FILE_PATH, "rb")
            instance.manual_pdf = File(f)
            instance.save()

        return instance 


class KeywordSerializer(serializers.ModelSerializer):

    class Meta:
        model = KeyWord 
        fields = ["population", "intervention", "comparison","outcome","exclusion",
        "population_color","intervention_color","comparison_color","outcome_color","exclusion_color"
        ]


class CustomKeyWordSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField()
    class Meta:
        model = CustomKeyWord 
        fields = ["id","custom_kw", "custom_kw_color"]


class SubmitKeywordSerializer(serializers.Serializer):
    keyword = KeywordSerializer()
    custom_keyword = CustomKeyWordSerializer(many=True)
    
    def update(self,instance, validated_data):

        keyword = validated_data.pop("keyword")
        lit_keyword = instance

        lit_keyword.population = keyword.pop("population")
        lit_keyword.intervention = keyword.pop("intervention")
        lit_keyword.comparison = keyword.pop("comparison")
        lit_keyword.outcome = keyword.pop("outcome")
        lit_keyword.exclusion = keyword.pop("exclusion")
        lit_keyword.population_color = keyword.pop("population_color")
        lit_keyword.intervention_color = keyword.pop("intervention_color")
        lit_keyword.comparison_color = keyword.pop("comparison_color")
        lit_keyword.outcome_color = keyword.pop("outcome_color")
        lit_keyword.exclusion_color = keyword.pop("exclusion_color")
        lit_keyword.save()

        custom_keyword = validated_data.pop("custom_keyword")
        for kw in custom_keyword:
            kw_id = kw.pop("id")
            if kw_id != 0:
                # updating an old custom keyword
                custom_keyword = CustomKeyWord.objects.filter(id=kw_id).first()
                custom_keyword.custom_kw = kw.pop("custom_kw")
                custom_keyword.custom_kw_color = kw.pop("custom_kw_color")
                custom_keyword.save()
            else:
                # creating new custom keyword
                custom_keyword = CustomKeyWord.objects.create(
                    literature_review = lit_keyword.literature_review,
                    custom_kw=kw.pop("custom_kw"),
                    custom_kw_color=kw.pop("custom_kw_color")
                )
                custom_keyword.save()
        
        return lit_keyword