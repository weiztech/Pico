
from lit_reviews.models import (
    LiteratureSearch, 
    AdverseEventReview,
    AdverseRecallReview,
)

from .serializers import (
    ManualAdverseEventSerializer,
)

class ManualAdverEventSearchsMixin:

    def get_aes_values(self):
        """
        Extract ae's values from request data and construct a list of aes objects.
        """
        values = self.request.data
        aes = []
        forms_count = values.get("forms_count")
        forms_count = int(forms_count)
        db = values.get("db")

        for i in range(1, forms_count+1):
            ae_values = {}
            ae_values["type"] = values.get(f"type{i}")
            ae_values["severity"] = values.get(f"severity{i}")
            ae_values["link"] = values.get(f"link{i}")
            ae_values["pdf"] = values.get(f"pdf{i}")
            ae_values["ae_or_recall"] = values.get(f"ae_or_recall{i}")
            ae_values["event_date"] = values.get(f"event_date{i}") if values.get(f"event_date{i}") != "" else None
            ae_values["search"] = values.get(f"search{i}")
            ae_values["db"] = db
            aes.append(ae_values)

        return aes 

    def get_adverse_events(self, db, lit_review_id):
        __filter = {"db": db, "literature_review__id": lit_review_id}
        is_completed_review = LiteratureSearch.objects.filter(**__filter, result_count=0).count() == LiteratureSearch.objects.filter(**__filter).count()
        ae_events =  AdverseEventReview.objects.filter(search__literature_review__id=lit_review_id, search__db=db)
        ae_recalls = AdverseRecallReview.objects.filter(search__literature_review__id=lit_review_id, search__db=db)
        searches =  LiteratureSearch.objects.filter(db=db, literature_review__id=lit_review_id)
        values = {
            "database": db,
            "adverse_events": ae_events,
            "adverse_recalls": ae_recalls,
            "is_completed_review": is_completed_review,
            "search_id": db.literaturesearch_set.first().id,
            "forms_count": 0,
            "searches": searches,
        }
        manual_ae_search_serializer = ManualAdverseEventSerializer(values)

        return manual_ae_search_serializer.data