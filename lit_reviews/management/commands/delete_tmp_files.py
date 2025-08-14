from lit_reviews.tasks import delete_temp_files_async
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Delete yesterday's temp files"

    def handle(self, *args, **options):
        # run function
        delete_temp_files_async.delay()