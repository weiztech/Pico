from django.apps import AppConfig


class LitReviewsConfig(AppConfig):
    name = 'lit_reviews'

    def ready(self):
        import lit_reviews.signals
        import actstream.registry
        from lit_reviews.models import (
            ArticleReview,
            ClinicalLiteratureAppraisal,
            LiteratureReview,
            LiteratureSearch,
            SearchProtocol
        )

        actstream.registry.register(ArticleReview)
        actstream.registry.register(ClinicalLiteratureAppraisal)
        actstream.registry.register(LiteratureReview)
        actstream.registry.register(LiteratureSearch)
        actstream.registry.register(SearchProtocol)
