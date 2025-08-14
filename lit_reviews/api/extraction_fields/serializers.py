import json
from numpy import source
from django.db import IntegrityError

from rest_framework import serializers 
from lit_reviews.models import (
    ExtractionField,
    LiteratureReview,
    ClinicalLiteratureAppraisal,   
)
from lit_reviews.helpers.articles import (
    get_or_create_appraisal_extraction_fields,
)
from lit_reviews.tasks import recalculate_second_pass_appraisals_status_task

class ExtractionFieldSerializer(serializers.ModelSerializer):
    drop_down_values = serializers.SerializerMethodField()
    type = serializers.CharField(source="get_type_display")
    category = serializers.CharField(source="get_category_display")
    field_section = serializers.CharField(source="get_field_section_display")
    
    def get_drop_down_values(self, obj):
        if obj.drop_down_values:
            try:
                return json.loads(obj.drop_down_values)
            except json.JSONDecodeError as e:
                # Log the problematic value for debugging
                print(f"Invalid JSON in drop_down_values for {obj.id}: {obj.drop_down_values[:100]}")
                # Return empty list instead of crashing
                return []
        else:
            return []

    class Meta:
        model = ExtractionField
        fields = [
            "id",
            "name",
            "name_in_report",
            "type",
            "category",
            "ai_prompte",
            "description",
            "field_section",
            "drop_down_values",
        ]


class CreatExtractionFieldSerializer(serializers.Serializer):
    name = serializers.CharField()
    type = serializers.CharField()
    category = serializers.CharField(required=False, allow_blank=True)
    field_section = serializers.CharField()
    drop_down_values = serializers.ListField()
    description = serializers.CharField(required=False, allow_blank=True)
    ai_prompte = serializers.CharField(required=False, allow_blank=True)
    name_in_report = serializers.CharField(required=False, allow_blank=True)

    def validate(self, data):
        field_section = data.get('field_section')
        category = data.get('category')

        if field_section == "EF":
            if not category:
                raise serializers.ValidationError({"category":"This field may not be blank."})

        return data

    def validate_name(self, value):
        if len(value) > 256:
            raise serializers.ValidationError("Field name should not contain more than 256 chars")

        return value 
        
    def create(self, validated_data):
        validated_data["is_template"] = True
        lit_review_id = self.context.get("lit_review_id")
        lit_review = LiteratureReview.objects.get(id=lit_review_id)

        if validated_data["type"] == "TEXT":
            validated_data.pop("drop_down_values")

        else:
            values = validated_data["drop_down_values"]
            validated_data["drop_down_values"] = json.dumps(values)

        obj = ExtractionField(**validated_data)
        obj.literature_review = lit_review
        
        try:
            obj.save()
            # if extraction field is created successfuly update current project appraisals status
            appraisals = ClinicalLiteratureAppraisal.objects.filter(article_review__search__literature_review=lit_review)
            for appraisal in appraisals:
                get_or_create_appraisal_extraction_fields(appraisal, obj)
            recalculate_second_pass_appraisals_status_task.delay(lit_review_id)

        except IntegrityError:
            raise serializers.ValidationError("An extraction field with this name already exists in this project!")
        return obj
    
    def update(self, instance, validated_data):
        lit_review_id = self.context.get("lit_review_id")
        lit_review = LiteratureReview.objects.get(id=lit_review_id)

        # Handle drop_down_values based on the type
        new_type = validated_data.get("type", instance.type)
        if new_type != "DROP_DOWN":
            validated_data["drop_down_values"] = None
        else:
            values = validated_data.get("drop_down_values", [])
            validated_data["drop_down_values"] = json.dumps(values)

        # Update instance attributes
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        try:
            # Save updated instance
            instance.save()

            # Update related appraisals
            appraisals = ClinicalLiteratureAppraisal.objects.filter(
                article_review__search__literature_review=lit_review
            )
            for appraisal in appraisals:
                appraisal_field = get_or_create_appraisal_extraction_fields(appraisal, instance)
                if appraisal_field:
                    appraisal_field.value = None  # Reset the value
                    appraisal_field.save()

            # Recalculate statuses asynchronously
            recalculate_second_pass_appraisals_status_task.delay(lit_review_id)

        except IntegrityError:
            raise serializers.ValidationError(
                "An extraction field with this name already exists in this project!"
            )

        return instance