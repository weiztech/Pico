from rest_framework import status
from rest_framework.test import APITestCase
from django.urls import reverse
from accounts.models import User
from lit_reviews.models import Client
from lit_reviews.models import LiteratureReview, LiteratureSearch, NCBIDatabase

class SearchTermsAPITests(APITestCase):
    def setUp(self):
        self.client_model = Client.objects.create(name="Test Client")
        self.user = User.objects.create_user(username="testuser", email="test@example.com", password="password")
        self.user.client = self.client_model
        self.user.save()
        self.client.force_authenticate(user=self.user)
        self.lit_review = LiteratureReview.objects.create(client=self.client_model)
        self.db = NCBIDatabase.objects.create(name="pubmed", entrez_enum="pubmed")

    def test_create_search_term_with_pico_category(self):
        """
        Ensure we can create a new search term with a PICO category.
        """
        url = reverse("search_terms_api", args=[self.lit_review.id])
        data = {
            "term": "test search term",
            "db": self.db.name,
            "pico_category": LiteratureSearch.PicoCategory.POPULATION
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(LiteratureSearch.objects.count(), 1)
        self.assertEqual(LiteratureSearch.objects.get().pico_category, LiteratureSearch.PicoCategory.POPULATION)

    def test_update_single_search_term_pico_category(self):
        """
        Ensure we can update the pico_category of a single LiteratureSearch.
        """
        search = LiteratureSearch.objects.create(
            literature_review=self.lit_review,
            term="initial term",
            db=self.db,
            pico_category=LiteratureSearch.PicoCategory.POPULATION
        )
        url = reverse("search_terms_update_api", args=[self.lit_review.id])
        data = {
            "update_type": "single",
            "id": search.id,
            "pico_category": LiteratureSearch.PicoCategory.INTERVENTION
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        search.refresh_from_db()
        self.assertEqual(search.pico_category, LiteratureSearch.PicoCategory.INTERVENTION)

    def test_bulk_update_search_terms_pico_category(self):
        """
        Ensure we can bulk update the pico_category of multiple LiteratureSearch instances.
        """
        search1 = LiteratureSearch.objects.create(
            literature_review=self.lit_review, term="term 1", db=self.db
        )
        search2 = LiteratureSearch.objects.create(
            literature_review=self.lit_review, term="term 2", db=self.db
        )
        url = reverse("search_terms_update_api", args=[self.lit_review.id])
        data = {
            "update_type": "bulk",
            "pico_category": LiteratureSearch.PicoCategory.COMPARISON,
            "search_ids": [search1.id, search2.id]
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        search1.refresh_from_db()
        search2.refresh_from_db()
        self.assertEqual(search1.pico_category, LiteratureSearch.PicoCategory.COMPARISON)
        self.assertEqual(search2.pico_category, LiteratureSearch.PicoCategory.COMPARISON)

    def test_clear_search_term_pico_category(self):
        """
        Ensure we can clear the pico_category of a LiteratureSearch.
        """
        search = LiteratureSearch.objects.create(
            literature_review=self.lit_review,
            term="initial term",
            db=self.db,
            pico_category=LiteratureSearch.PicoCategory.POPULATION
        )
        url = reverse("search_terms_update_api", args=[self.lit_review.id])
        data = {
            "update_type": "single",
            "id": search.id,
            "pico_category": ""
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        search.refresh_from_db()
        self.assertIsNone(search.pico_category)