from django.core.management.base import BaseCommand
from lit_reviews.helpers.database import backup_database

class Command(BaseCommand):
    help = 'Create a dump file for the current database and store ti on aws s3 bucket'

    def handle(self, *args, **options):
        backup_database()