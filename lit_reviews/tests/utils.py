from django.test import TransactionTestCase
from lit_reviews.models import (
    ArticleReview, 
    LiteratureReview,
    Client,
    Device,
    Manufacturer,
    NCBIDatabase,
    LiteratureSearch,
)

class TransactionTestCaseLiteratureReview(TransactionTestCase):

    def create_literature_review(self, number):
        # Project Set Up
        manufacturer = Manufacturer.objects.create(name=f"Manufacturer {number}")
        setattr(self, f"manufacturer{number}", manufacturer)

        device = Device.objects.create(
            name=f"Device {number}",
            manufacturer=manufacturer,
            classification="III",
            markets="US",
        )
        setattr(self, f"device{number}", device)

        client = Client.objects.create(
            name=f"Client {number}",
            short_name=f"Client {number}",
            long_name=f"Client {number}",
            full_address_string="Fake Address",
        )
        setattr(self, f"client{number}", client)

        lit_review = LiteratureReview.objects.create(
            device=device,
            client=client,
        )
        setattr(self, f"lit_review{number}", lit_review)

        protocol = lit_review.searchprotocol
        setattr(self, f"protocol{number}", protocol)

        protocol.lit_searches_databases_to_search.add(self.pubmed)
        protocol.lit_searches_databases_to_search.add(self.embase)
        protocol.lit_searches_databases_to_search.add(self.scholar)
        protocol.lit_searches_databases_to_search.add(self.clinical)
        protocol.lit_searches_databases_to_search.add(self.pmc_europe)
        protocol.lit_searches_databases_to_search.add(self.maude)
        protocol.lit_searches_databases_to_search.add(self.maude_recalls)

    def create_databases(self):
        self.pubmed = NCBIDatabase.objects.create(
            name="Pubmed",
            entrez_enum="pubmed",
        )
        self.embase = NCBIDatabase.objects.create(
            name="Embase",
            entrez_enum="embase",
        )
        self.cochrane = NCBIDatabase.objects.create(
            name="Cochrane",
            entrez_enum="cochrane",
        )
        self.pmc = NCBIDatabase.objects.create(
            name="PubMed Central",
            entrez_enum="pmc",
        )
        self.scholar = NCBIDatabase.objects.create(
            name="Google Scholar",
            entrez_enum="scholar",
        )
        self.pmc_europe = NCBIDatabase.objects.create(
            name="PMC Europe",
            entrez_enum="pmc_europe",
        )
        self.clinical = NCBIDatabase.objects.create(
            name="Clinical Trials.gov",
            entrez_enum="ct_gov",
        )

        self.maude = NCBIDatabase.objects.create(
            name="FDA Maude",
            entrez_enum="maude",
            is_ae=True,
        )
        self.maude_recalls = NCBIDatabase.objects.create(
            name="Maude Recalls",
            entrez_enum="maude_recalls",
            is_recall=True,
        )
