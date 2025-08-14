from lit_reviews.models import ProjectConfig
from rest_framework import serializers

class ProjectConfigSerializer(serializers.ModelSerializer):
    count_client_projects = serializers.SerializerMethodField()
    is_new_project = serializers.SerializerMethodField()
    class Meta:
        model = ProjectConfig
        fields = "__all__"

    def get_count_client_projects(self, obj):
        return obj.count_client_projects
    
    def get_is_new_project(self, obj):
        return obj.is_new_project
    
class ProjectConfigUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectConfig
        fields = ("id","sidebar_mode")
        read_only_fields = ("id",)
