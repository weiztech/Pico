from rest_framework import serializers
from lit_reviews.models import ScraperReport, LiteratureReview, NCBIDatabase
from client_portal.models import Project

class ScraperReportSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()
    user_email = serializers.SerializerMethodField()
    literature_review = serializers.SerializerMethodField()
    project = serializers.SerializerMethodField()
    start_date = serializers.DateField(format="%d-%m-%Y")
    end_date = serializers.DateField(format="%d-%m-%Y")
    script_timestamp = serializers.DateTimeField(format="%d-%m-%Y %H:%M")
    literature_review__id = serializers.IntegerField(source="literature_review.id", default=None)

    def get_literature_review(self, obj):
        return str(obj)

    def get_user(self, obj):
        if obj.user:
            return obj.user.username
        else:
            "Automated Search"
            
    def get_user_email(self, obj):
        if obj.user:
            return obj.user.email
        else:
            "Automated Search"

    def get_project(self, obj):
        return str(obj.literature_review) 

    class Meta:
        model = ScraperReport
        fields = "__all__"


class LiterateReviewSerializer(serializers.ModelSerializer):
    label = serializers.SerializerMethodField()

    def get_label(self, obj):
        return str(obj) 
        
    class Meta:
        model = LiteratureReview
        fields = ["id", "label"]  


class NCBIDatabaseSerializer(serializers.ModelSerializer):
        
    class Meta:
        model = NCBIDatabase
        fields = ["displayed_name", "name"]  

