from rest_framework import serializers
from django.db.models import Q

from accounts.models import User
from lit_reviews.models import (
    LiteratureReview,
    Device,
    Client,
    Manufacturer,
    ArticleTag,
    ArticleReview,
    NCBIDatabase,
    LiteratureSearch,
    Article,
    LivingReview,
)
from client_portal.models import Project
from lit_reviews.helpers.project import clone_project
from lit_reviews.tasks import clone_project_task


class ProjectSerializer(serializers.ModelSerializer):

    class Meta:
        model = Project
        fields = ["project_name", "type", "client"]

class CreateLiteratureReviewSerailizer(serializers.ModelSerializer):
    project = ProjectSerializer(write_only=True)
    is_copy_data = serializers.BooleanField(required=False, write_only=True)
    copy_from_lit_id = serializers.IntegerField(required=False, write_only=True)
    tag = serializers.PrimaryKeyRelatedField(required=False, queryset=ArticleTag.objects.all(), write_only=True)
    review_tag = serializers.PrimaryKeyRelatedField(required=False, queryset=ArticleTag.objects.all(), write_only=True)
    lit_review_id = serializers.IntegerField(required=False, write_only=True)

    class Meta:
        model = LiteratureReview
        fields = [
            "id", 
            "client", 
            "device", 
            "is_archived", 
            "review_type", 
            "project", 
            "is_copy_data", 
            "copy_from_lit_id",
            "tag",
            "review_tag",
            "lit_review_id",
        ]
        read_only_fields = ["id",]

    def validate_tag(self, data):
        request = self.context.get("request")
        if request.user.client:
            tag_owner = data.literature_review.client
            if tag_owner != request.user.client:
                return serializers.ValidationError("You don't own the tag you are trying to use")

        return data 
    
    def create(self, validated_data):
        project_data = validated_data.pop("project")
        is_copy_data = validated_data.pop("is_copy_data", None)
        tag = validated_data.pop("tag", None)
        review_tag = validated_data.pop("review_tag", None)
        lit_review_id = validated_data.pop("lit_review_id", None)

        if is_copy_data:
            copy_from_lit_id = validated_data.pop("copy_from_lit_id")

        # if request.user.client
        # must attach the client somehow
        literature_review = super().create(validated_data)

        # if the user selects a tag we take all the tagged articles and add it to the review
        if tag or review_tag:
            if tag:
                articles = tag.articles.all()
            else:
                reviews = review_tag.article_reviews.filter(search__literature_review__id=lit_review_id)
                articles = Article.objects.filter(id__in=reviews.values_list("article__id", flat=True))

            for article in articles:
                # check if there is an article review for this article
                review = ArticleReview.objects.filter(
                    Q(article__pubmed_uid=article.pubmed_uid)
                    |
                    Q(article__pmc_uid=article.pmc_uid)
                    |
                    Q(article__doi=article.doi)
                ).first()
                if review:
                    db = review.search.db 
                else:
                    db = NCBIDatabase.objects.filter(name="Unknown", is_external=True).first()
                    if not db:
                        db = NCBIDatabase.objects.create(
                            name="Unknown",
                            displayed_name="Unknown",
                            is_archived=True,
                            is_external=True,
                            entrez_enum="Unknown",
                        )

                search = LiteratureSearch.objects.get_or_create(
                    literature_review = literature_review,
                    term = "One-Off Manufacturer Search",
                    db=db,
                )[0]
                
                # create duplicate 
                article.pk = None 
                article.literature_review =  literature_review
                article.save()
                if tag:
                    tag.articles.add(article)

                article_review = ArticleReview.objects.create(search=search, article=article)
                if review_tag:
                    review_tag.article_reviews.add(article_review)

        # create project
        project = Project.objects.create(
            **project_data,
            lit_review = literature_review
        )
        project.save()

        if is_copy_data:
            copied_project_lit_review = LiteratureReview.objects.get(id=copy_from_lit_id) 
            literature_review.cloned_from = copied_project_lit_review
            literature_review.is_cloning_completed = False
            literature_review.save()
            clone_project_task.delay(copied_project_lit_review.id, literature_review.id)

        return literature_review
    
class DeviceSerializer(serializers.ModelSerializer):
    manufacturer = serializers.CharField(source="manufacturer.name")

    class Meta:
        model = Device
        fields = ["id", "name", "classification", "manufacturer", "markets"]
        read_only_fields = ["id"]

    def create(self, validated_data):
        manufacturer = validated_data.pop("manufacturer")
        manufacturer_name = manufacturer.get("name")
        manufacturer = Manufacturer.objects.filter(name=manufacturer_name).first()
        if not manufacturer:
            manufacturer = Manufacturer.objects.create(name=manufacturer_name)

        device = Device.objects.create(
            **validated_data,
            manufacturer=manufacturer,
        )
        return device
    
class CreateClientSerailizer(serializers.ModelSerializer):
    
    class Meta:
        model = Client
        fields = "__all__"

    def create(self, validated_data):
        user = self.context["request"].user
        if user.is_ops_member:
            validated_data["is_company"] = False
        new_company = super().create(validated_data=validated_data)
        if user.client:
            company_members = User.objects.filter(client=user.client)
            for member in company_members:
                member.companies.add(new_company)
        return new_company
    
class ManufacturerSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Manufacturer
        fields = "__all__"


class LiteratureReviewSerializer(serializers.ModelSerializer):
    label = serializers.SerializerMethodField()

    def get_label(self, obj):
        return str(obj)

    class Meta:
        model = LiteratureReview
        fields = "__all__"


class CreateLivingReviewSerializer(serializers.ModelSerializer):
    similar_devices = serializers.ListField(
        child=serializers.PrimaryKeyRelatedField(queryset=Device.objects.all()),
    ) 
    competitor_devices = serializers.ListField(
        child=serializers.PrimaryKeyRelatedField(queryset=Device.objects.all()),
    )
    class Meta:
        model = LivingReview
        fields = "__all__"

    def create(self, validated_data):
        start_date = validated_data['start_date']
        interval = validated_data['interval']

        # if interval monthly ensure start day is 01
        if interval == "monthly" or interval == "quarterly":
            new_start_date = start_date.replace(day=1)
            validated_data['start_date'] = new_start_date
        return super().create(validated_data)
    

class LivingReviewSerializer(serializers.ModelSerializer):
    similar_devices = DeviceSerializer(many=True)
    competitor_devices = DeviceSerializer(many=True)
    device = DeviceSerializer()
    project_protocol = LiteratureReviewSerializer()

    class Meta:
        model = LivingReview
        fields = "__all__"