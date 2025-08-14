from django.core.management.base import BaseCommand
from lit_reviews.tasks import import_project_backup_task

class Command(BaseCommand):
    help = 'Import a project providing a project dump file'

    def add_arguments(self, parser):
        # Add positional arguments
        parser.add_argument('dump_file_aws_key', type=str, help="dump file name")
        parser.add_argument('client_name', type=str, help="client name")


    def handle(self, *args, **options):
        # Retrieve arguments
        dump_file_aws_key = options['dump_file_aws_key']
        client_name = options['client_name']

        import_project_backup_task.delay(dump_file_aws_key, client_name)