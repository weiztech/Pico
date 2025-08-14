from rest_framework import serializers 
from client_portal.models import Project , Action
from lit_reviews.models import LiteratureReview, Device
from django.urls import reverse

class DeviceSerializer(serializers.ModelSerializer):
    device_name = serializers.SerializerMethodField()

    class Meta:
        model = Device
        fields = ["id", "device_name"]

    def get_device_name(self, obj):
        return obj.__str__()


class ProjectSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()
    type = serializers.CharField(source="get_type_display")
    lit_review_hyperlink = serializers.HyperlinkedRelatedField(
        view_name='lit_reviews:literature_review_detail', 
        source="lit_review", 
        queryset=LiteratureReview.objects.all(),
        lookup_field="id",
    )
    detail_view_hyperlink = serializers.SerializerMethodField()
    
    def get_detail_view_hyperlink(self, obj):
        url = reverse('client_portal:project_details', args=[obj.id])
        return url

    def get_name(self, obj):
        return obj.__str__()

    class Meta:
        model = Project
        fields = [
            "id",
            "name",
            "type",
            "initial_complated_date",
            "lit_review_hyperlink",
            "detail_view_hyperlink",
        ]


class ActionSerializer(serializers.ModelSerializer):
    detail_view_hyperlink = serializers.SerializerMethodField()

    def get_detail_view_hyperlink(self, obj):
        url = reverse('client_portal:action_details', args=[obj.id])
        return url
    
    class Meta:
        model = Action
        fields = ["project", "date_sent","message","type","resolved_status","detail_view_hyperlink"]