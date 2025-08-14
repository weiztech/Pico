from client_portal.tasks import create_terms_for_automated_searches_cronjob
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Create search terms for AutomatedSearches based on intervals'

    def handle(self, *args, **options):
        # run function
        create_terms_for_automated_searches_cronjob()
        self.stdout.write(self.style.SUCCESS('Missing Search Terms were created successfully for Automated Searches'))




