import json
from rest_framework.serializers import ModelSerializer, SerializerMethodField
from rest_framework import serializers
from lit_reviews.models import (
    LiteratureReview, 
    Client , 
    Device ,
    Manufacturer,
    SearchProtocol,
    ArticleReview,
    CustomerSettings,
    SearchLabelOption,
    SupportRequestTicket,
)
from accounts.models import User, Subscription
from client_portal.models import Project
from backend.logger import logger

class SearchProtocolSerializer(ModelSerializer):

    class Meta:
        model = SearchProtocol
        fields = ['lit_date_of_search']

class ProjectSerializer(ModelSerializer):
    type_display = serializers.CharField(source="get_type_display")

    class Meta:
        model = Project
        fields = '__all__'

class UserSerialzer(ModelSerializer):

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']


class ClientSerializer(ModelSerializer):

    class Meta:
        model = Client
        fields = '__all__'


class DeviceSerializer(ModelSerializer):

    class Meta:
        model = Device
        fields = '__all__'

class CustomerSettingsSerializer(ModelSerializer):
    ris_fields_list = serializers.SerializerMethodField()
    format_choices = serializers.SerializerMethodField()

    class Meta:
        model = CustomerSettings
        fields = '__all__'

    def get_ris_fields_list(self, obj):
        return json.loads(obj.ris_file_fields)

    def get_format_choices(self, obj):
        return CustomerSettings.FULL_TEXT_FORMAT_CHOICES
    
class LiteratureReviewSerializer(ModelSerializer):
    client = ClientSerializer(read_only=True)
    device = DeviceSerializer(read_only=True)
    authorized_users = UserSerialzer(read_only=True, many=True)
    project = SerializerMethodField()
    date_of_search = serializers.DateField(source='searchprotocol.lit_date_of_search')
    articles_analysis = serializers.SerializerMethodField()
    absolute_url = SerializerMethodField()
    created_at = serializers.DateTimeField(format="%m-%d-%Y %H:%M")
    manufacturer = SerializerMethodField()

    class Meta:
        model = LiteratureReview
        fields = [
            'id',
            'client',
            'device',
            'is_autosearch',
            'is_archived',
            'review_type',
            'authorized_users',
            'project',
            'date_of_search',
            'articles_analysis',
            "absolute_url",
            "created_at",
            "manufacturer"
        ]

    def get_absolute_url(self, obj):
        request = self.context.get('request')
        obj_url = obj.get_absolute_url()
        return request.build_absolute_uri(obj_url)
    
    def get_articles_analysis(self, obj):
        related_articles = ArticleReview.objects.filter(search__literature_review=obj)
        total = related_articles.count()
        reviewed = related_articles.exclude(state="U").count()
        pending = related_articles.filter(state="U").count()
        completed = related_articles.filter(state__in=["I", "E"]).count()

        return {
            "total": total,
            "reviewed": reviewed,
            "pending": pending,
            "completed": completed,
        }
    
    def get_project(self, obj):
        project = obj.project_set.all().first()
        return ProjectSerializer(project).data
    
    def get_manufacturer(self, obj):
        if obj.device and obj.device.manufacturer:
            manufacturer = obj.device.manufacturer.name
            return manufacturer

class SearchLabelOptionSerializer(ModelSerializer):

    class Meta:
        model = SearchLabelOption
        fields = ['id','label','customer_settings']    
    

class ManufacturerSerializer(serializers.ModelSerializer):

    class Meta:
        model = Manufacturer
        fields = ["id","name"]


class SubscriptionSerializer(ModelSerializer):

    class Meta:
        model = Subscription
        fields = ['id', 'licence_type', 'plan_credits', 'remaining_credits', 'licence_end_date']

class SupportRequestTicketSerializer(serializers.ModelSerializer):
    class Meta:
        model = SupportRequestTicket
        fields = ['description', 'demo_video', 'follow_up_option']
        
    def validate_description(self, value):
        """Validate that description is not empty"""
        if not value.strip():
            raise serializers.ValidationError("Description cannot be empty.")
        return value.strip()
    
    def validate_follow_up_option(self, value):
        """Validate follow-up option"""
        valid_options = ['phone', 'email', 'teams']
        if value not in valid_options:
            raise serializers.ValidationError(f"Invalid follow-up option. Must be one of: {', '.join(valid_options)}")
        return value
    
    def create(self, validated_data):
        """Create support ticket with the current user"""
        user = self.context['request'].user
        validated_data['user'] = user
        return super().create(validated_data)