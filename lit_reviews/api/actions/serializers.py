from rest_framework import serializers
from actstream.models import Action

from lit_reviews.models import ArticleReview
from ..articles.serializers import ArticleReviewSerializer

class ActionSerializer(serializers.ModelSerializer):
    actor = serializers.CharField(source='actor.username')
    action_object_url = serializers.SerializerMethodField()

    class Meta:
        model = Action
        fields = ['actor', 'verb', 'description', 'timestamp', 'action_object_url']


    def get_action_object_url(self, obj):
        if hasattr(obj.action_object, 'get_absolute_url'):
            return obj.action_object.get_absolute_url()
        return None
