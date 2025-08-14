from rest_framework import serializers
from lit_reviews.models import FinallReportJob, FinalReportConfig 
from client_portal.models import Project 

class FinallReportJobSerializer(serializers.ModelSerializer):

    class Meta:
        model = FinallReportJob
        fields = "__all__"


class ProjectSerializer(serializers.ModelSerializer):
    type = serializers.CharField(source="get_type_display")

    class Meta:
        model = Project
        fields = "__all__"

class ReportConfigSerializer(serializers.ModelSerializer):
    extra_kwargs = {
        "literature_review": {'read_only': True},
    }

    class Meta:
        model = FinalReportConfig
        fields = "__all__"


class ReportCommentSerializer(serializers.ModelSerializer):
    extra_kwargs = {
        "id": {'read_only': True},
    }

    class Meta:
        model = FinallReportJob
        fields = ["id", "comment"]
