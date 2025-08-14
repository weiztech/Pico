from rest_framework import serializers
from lit_reviews.models import (
    LivingReview, 
    LiteratureReview, 
    ArticleReview, 
    Device, 
    SearchProtocol,
    Article,
    ArticleReviewDeviceMention,
)
from datetime import timedelta, datetime
from lit_reviews.api.articles.serializers import NCBIDatabaseSerializer
from lit_reviews.helpers.project import get_end_date_for_living_review_project

class DeviceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Device
        fields = ['id', 'name', 'manufacturer', 'classification', 'markets']

class SearchProtocolSerializer(serializers.ModelSerializer):
    class Meta:
        model = SearchProtocol
        fields = ['lit_date_of_search', 'ae_date_of_search', 'lit_start_date_of_search', 'ae_start_date_of_search']

class LiteratureReviewSerializer(serializers.ModelSerializer):
    search = SearchProtocolSerializer(source='searchprotocol', read_only=True)
    abstracts = serializers.SerializerMethodField()
    included = serializers.SerializerMethodField()
    incomplete = serializers.SerializerMethodField()
    similar_device_mentions_counts = serializers.SerializerMethodField() 
    under_evaluation_device_mentions_counts = serializers.SerializerMethodField() 
    competitor_device_mentions_counts = serializers.SerializerMethodField() 


    class Meta:
        model = LiteratureReview
        fields = [
            'id', 
            'client', 
            'device', 
            'is_archived', 
            'created_at', 
            'search',
            'abstracts', 
            'included', 
            'incomplete',
            'similar_device_mentions_counts', 
            'under_evaluation_device_mentions_counts', 
            'competitor_device_mentions_counts'
        ]

    def get_abstracts(self, obj):
        # Total count of all article reviews linked to the literature review
        return ArticleReview.objects.filter(search__literature_review=obj).count()

    def get_included(self, obj):
        # Total count of article reviews where state is 'INCLUDED'
        return ArticleReview.objects.filter(search__literature_review=obj, state='I').count()

    def get_incomplete(self, obj):
        # Total count of article reviews where state is 'UNCLASSIFIED'
        return ArticleReview.objects.filter(search__literature_review=obj, state='U').count()

    def get_similar_device_mentions_counts(self, obj):
        return ArticleReviewDeviceMention.objects.filter(
            article_review__search__literature_review=obj,
            device_type="similar"
        ).distinct("article_review").count()

    def get_competitor_device_mentions_counts(self, obj):
        return ArticleReviewDeviceMention.objects.filter(
            article_review__search__literature_review=obj,
            device_type="competitor"
        ).distinct("article_review").count()
    
    def get_under_evaluation_device_mentions_counts(self, obj):
        return ArticleReviewDeviceMention.objects.filter(
            article_review__search__literature_review=obj,
            device_type="under_evaluation"
        ).distinct("article_review").count()
    

class LivingReviewSerializer(serializers.ModelSerializer):
    device = DeviceSerializer()  # Use the nested DeviceSerializer
    similar_devices = DeviceSerializer(many=True, read_only=True)
    competitor_devices = DeviceSerializer(many=True, read_only=True) 
    client = serializers.CharField(source='project_protocol.client.name', read_only=True)  # Get client name directly
    last_run_date = serializers.SerializerMethodField()
    next_run_date = serializers.SerializerMethodField()
    latest_literature_reviews = serializers.SerializerMethodField() 

    under_review_analysis = serializers.SerializerMethodField()
    similar_analysis = serializers.SerializerMethodField()
    competitor_analysis = serializers.SerializerMethodField()

    class Meta:
        model = LivingReview
        fields = [
            'id', 
            'device', 
            'similar_devices', 
            'competitor_devices', 
            'client', 
            'interval', 
            'start_date', 
            'alert_type', 
            'is_active',
            'last_run_date', 
            'next_run_date',  
            'latest_literature_reviews',
            'under_review_analysis',
            'similar_analysis',
            'competitor_analysis',
        ]
        depth = 1  # To include related fields like `device` details

    def _get_device_analysis(self, reviews, extra_filters={}):
        # Count the number of articles with state = 'INCLUDED' in the latest LiteratureReview
        relevant_articles = 0
        reviewed_articles = 0
        relevant_articles_before = 0
        reviewed_articles_before = 0 

        latest_review = reviews.first()
        if latest_review:
            relevant_articles = ArticleReview.objects.filter(search__literature_review=latest_review, state='I', **extra_filters).count()
            reviewed_articles = ArticleReview.objects.filter(search__literature_review=latest_review, **extra_filters).count()

            if reviews.count() > 1:
                second_last_review = reviews[1]
                relevant_articles_before = ArticleReview.objects.filter(search__literature_review=second_last_review, state='I', **extra_filters).count()
                reviewed_articles_before = ArticleReview.objects.filter(search__literature_review=second_last_review, **extra_filters).count()

        return {
            "relevant_articles": relevant_articles,
            "reviewed_articles": reviewed_articles,
            "relevant_articles_before": relevant_articles_before,
            "reviewed_articles_before": reviewed_articles_before,
        }
    
    def get_last_run_date(self, obj):
        # Get the latest LiteratureReview linked to this LivingReview
        latest_review = LiteratureReview.objects.filter(parent_living_review=obj).order_by('-created_at').first()
        if latest_review and latest_review.searchprotocol:
            return latest_review.searchprotocol.lit_date_of_search
        return None

    def get_next_run_date(self, obj):
        # Calculate the next run date based on the interval + one day
        last_run_date = self.get_last_run_date(obj)
        if last_run_date:
            interval_mapping = {
                "weekly": timedelta(weeks=1),
                "monthly": timedelta(days=30),  # Approximation for a month
                "quarterly": timedelta(days=90),
                "annually": timedelta(days=365),
            }
            return last_run_date + interval_mapping.get(obj.interval, timedelta(weeks=1)) + timedelta(days=1)
        return None

    def get_under_review_analysis(self, obj):
        reviews = LiteratureReview.objects.filter(parent_living_review=obj).order_by('-created_at')
        return self._get_device_analysis(reviews)

    def get_similar_analysis(self, obj):
        article_review_ids = ArticleReviewDeviceMention.objects.filter(
            article_review__search__literature_review__parent_living_review=obj,
            device_type="similar"
        ).distinct("article_review").values_list("article_review__id", flat=True)
        article_review_ids = list(article_review_ids)
        extra_filters = {"id__in": article_review_ids}
        reviews = LiteratureReview.objects.filter(parent_living_review=obj).order_by('-created_at')
        return self._get_device_analysis(reviews, extra_filters)
    
    def get_competitor_analysis(self, obj):
        # Get the latest literature reviews linked to this LivingReview
        article_review_ids = ArticleReviewDeviceMention.objects.filter(
            article_review__search__literature_review__parent_living_review=obj,
            device_type="competitor"
        ).distinct("article_review").values_list("article_review__id", flat=True)
        article_review_ids = list(article_review_ids)
        extra_filters = {"id__in": article_review_ids}
        reviews = LiteratureReview.objects.filter(parent_living_review=obj).order_by('-created_at')
        return self._get_device_analysis(reviews, extra_filters)
    
    def get_latest_literature_reviews(self, obj):
        # Get the latest literature reviews linked to this LivingReview
        reviews = LiteratureReview.objects.filter(parent_living_review=obj).order_by('-created_at')
        data = LiteratureReviewSerializer(reviews, many=True).data

        # get projects dates for this living review
        date_ranges = []
        today = datetime.now()
        start_date = obj.start_date 

        while start_date < today.date():
            end_date = get_end_date_for_living_review_project(obj, start_date)   
            if end_date < today.date():        
                date_ranges.append((start_date, end_date))
            
            start_date = end_date + timedelta(days=1)

        date_ranges.reverse()
        missing_dates = []
        existing_review_dates = [review["search"]["lit_start_date_of_search"] for review in data]
        for index in range(0, len(date_ranges)):
            start_date_range = date_ranges[index][0]
            if start_date_range.strftime("%Y-%m-%d") not in existing_review_dates:
                missing_dates.append(date_ranges[index])


        for index in range(0, len(missing_dates)):
            missing_start_date = missing_dates[index][0]
            for j in range(0, len(data)):
                if data[j].get("search"):
                    review_start_date = data[j]["search"]["lit_start_date_of_search"]
                else:
                    review_start_date = data[j]["start_date"]

                if datetime.strptime(review_start_date, "%Y-%m-%d").date() < missing_start_date:
                    data.insert(j, {
                        "id": index,
                        "search": {
                            "lit_start_date_of_search": missing_dates[index][0].strftime("%Y-%m-%d"),
                            "lit_date_of_search": missing_dates[index][1].strftime("%Y-%m-%d")
                        },
                        "is_missing": True,
                    })
                    break

        return data


class UpdateLivingReviewSerializer(serializers.ModelSerializer):
    """Serializer for updating LivingReview instances"""
    
    # Define the fields explicitly to handle many-to-many relationships
    device = serializers.IntegerField(required=False, allow_null=True)  # Accept ID, not object
    similar_devices = serializers.ListField(
        child=serializers.IntegerField(), 
        required=False, 
        allow_empty=True
    )
    competitor_devices = serializers.ListField(
        child=serializers.IntegerField(), 
        required=False, 
        allow_empty=True
    )
    alert_type = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    
    class Meta:
        model = LivingReview
        fields = ['device', 'similar_devices', 'competitor_devices', 'interval', 'alert_type']
        
    def update(self, instance, validated_data):
        # Handle device update
        if 'device' in validated_data:
            device_id = validated_data.pop('device')
            if device_id:
                try:
                    device = Device.objects.get(id=device_id)
                    instance.device = device
                except Device.DoesNotExist:
                    raise serializers.ValidationError({'device': 'Device not found'})
            else:
                instance.device = None
        
        # Handle similar_devices update
        if 'similar_devices' in validated_data:
            similar_device_ids = validated_data.pop('similar_devices')
            instance.similar_devices.clear()
            for device_id in similar_device_ids:
                try:
                    device = Device.objects.get(id=device_id)
                    instance.similar_devices.add(device)
                except Device.DoesNotExist:
                    raise serializers.ValidationError({'similar_devices': f'Device with id {device_id} not found'})
        
        # Handle competitor_devices update
        if 'competitor_devices' in validated_data:
            competitor_device_ids = validated_data.pop('competitor_devices')
            instance.competitor_devices.clear()
            for device_id in competitor_device_ids:
                try:
                    device = Device.objects.get(id=device_id)
                    instance.competitor_devices.add(device)
                except Device.DoesNotExist:
                    raise serializers.ValidationError({'competitor_devices': f'Device with id {device_id} not found'})
        
        # Handle alert_type - convert None to empty string if needed
        if 'alert_type' in validated_data:
            alert_type = validated_data.pop('alert_type')
            instance.alert_type = alert_type if alert_type is not None else ''
        
        # Update other fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        instance.save()
        return instance

class ArticleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Article
        fields = "__all__"

class ArticleReviewSerializer(serializers.ModelSerializer):
    article = ArticleSerializer()
    database = NCBIDatabaseSerializer(source="search.db")
    term = serializers.SerializerMethodField()
    absolute_url = serializers.SerializerMethodField()

    class Meta:
        model = ArticleReview
        fields = "__all__"

    def get_term(self, obj):
        return obj.search.term
    
    def get_absolute_url(self, obj):
        return obj.get_absolute_url()
