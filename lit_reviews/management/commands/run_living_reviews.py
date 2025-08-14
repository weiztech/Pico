from lit_reviews.tasks import create_living_reviews_projects_async
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Create projects for living reviews'

    def handle(self, *args, **options):
        # run function
        create_living_reviews_projects_async.delay()
        self.stdout.write(self.style.SUCCESS('Periodic runs for living reviews are successfull'))