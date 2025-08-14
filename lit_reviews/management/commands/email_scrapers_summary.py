from django.core.management.base import BaseCommand
from lit_reviews.tasks import send_scrapers_report

class Command(BaseCommand):
    help = 'Create a dump file for the current database and store ti on aws s3 bucket'

    def handle(self, *args, **options):
        send_scrapers_report()