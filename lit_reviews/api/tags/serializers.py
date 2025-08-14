from rest_framework import serializers
from lit_reviews.models import ArticleTag, Article

class ArticleTagSerializer(serializers.ModelSerializer):
    rbga_color = serializers.CharField(source="hex_to_rgba", read_only=True)
    usage = serializers.SerializerMethodField(read_only=True)

    def get_usage(self, obj):
        return obj.article_reviews.count()

    class Meta:
        model = ArticleTag
        fields = "__all__"
        extra_kwargs = {
            'id': {'read_only': True},
            'article_reviews': {'read_only': True},
            'articles': {'required': False},
        }

class AttachTagToArticlesSerializer(serializers.Serializer):
    articles = serializers.PrimaryKeyRelatedField(queryset=Article.objects.all() ,required=True, many=True)
    tag = serializers.PrimaryKeyRelatedField(queryset=ArticleTag.objects.all() ,required=True)

    def validate_articles(self, data):
        # check the user have access to all the articles he selected
        user = self.context.get("request").user
        
        if user.client:
            for article in data:
                article_owner = None 

                if article.literature_review:
                    article_owner = article.literature_review.client
                else:
                    article_review = article.reviews.first()
                    if article_review:
                        article_owner = article_review.search.literature_review.client 

                if article_owner and article_owner != user.client:
                    return serializers.ValidationError("You don't have access to these articles")
                
        return data

    def create(self, validated_data):
        tag = validated_data.get("tag")
        articles = validated_data.get("articles")
        for article in articles:
            tag.articles.add(article)

        return tag