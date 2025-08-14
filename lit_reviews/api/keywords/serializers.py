from rest_framework import serializers 

from lit_reviews.models import (
    KeyWord,
    CustomKeyWord,
)


class KeywordSerializer(serializers.ModelSerializer):

    class Meta:
        model = KeyWord 
        fields = ["population", "intervention", "comparison","outcome","exclusion",
        "population_color","intervention_color","comparison_color","outcome_color","exclusion_color"
        ]


class CustomKeyWordSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField()
    class Meta:
        model = CustomKeyWord 
        fields = ["id","custom_kw", "custom_kw_color"]


class SubmitKeywordSerializer(serializers.Serializer):
    keyword = KeywordSerializer()
    custom_keyword = CustomKeyWordSerializer(many=True)
    
    def update(self,instance, validated_data):

        keyword = validated_data.pop("keyword")
        lit_keyword = instance

        lit_keyword.population = keyword.pop("population")
        lit_keyword.intervention = keyword.pop("intervention")
        lit_keyword.comparison = keyword.pop("comparison")
        lit_keyword.outcome = keyword.pop("outcome")
        lit_keyword.exclusion = keyword.pop("exclusion")
        lit_keyword.population_color = keyword.pop("population_color")
        lit_keyword.intervention_color = keyword.pop("intervention_color")
        lit_keyword.comparison_color = keyword.pop("comparison_color")
        lit_keyword.outcome_color = keyword.pop("outcome_color")
        lit_keyword.exclusion_color = keyword.pop("exclusion_color")
        lit_keyword.save()

        custom_keyword = validated_data.pop("custom_keyword")
        for kw in custom_keyword:
            kw_id = kw.pop("id")
            if kw_id != 0:
                # updating an old custom keyword
                custom_keyword = CustomKeyWord.objects.filter(id=kw_id).first()
                custom_keyword.custom_kw = kw.pop("custom_kw")
                custom_keyword.custom_kw_color = kw.pop("custom_kw_color")
                custom_keyword.save()
            else:
                # creating new custom keyword
                custom_keyword = CustomKeyWord.objects.create(
                    literature_review = lit_keyword.literature_review,
                    custom_kw=kw.pop("custom_kw"),
                    custom_kw_color=kw.pop("custom_kw_color")
                )
                custom_keyword.save()
        
        return lit_keyword