import json
from django.core.management.base import BaseCommand, CommandError
from lit_reviews.models import (
    NCBIDatabase,
)
from lit_reviews.helpers.database import create_init_search_params_templates


class Command(BaseCommand):
    help = 'Imports data from a JSON file into Databases.'

    def handle(self, *args, **options):
        with open('lit_reviews/defualt_database_data/database_data.json') as f:
            initial_databases = json.load(f)

        for db in initial_databases:
            if not NCBIDatabase.objects.filter(name=db["name"]).exists():
                NCBIDatabase.objects.create(
                    name = db["name"],
                    entrez_enum = db["entrez_enum"],
                    url = db["url"],
                    is_ae = db["is_ae"],
                    is_recall = db["is_recall"],
                    description = db["description"],
                    search_strategy = db["search_strategy"],
                    displayed_name=db["name"],
                    instructions_for_search=db["instructions_for_search"],
                    export_file_format=db["export_file_format"],
                )
            else:
                print("Database named {} already exists".format(db["name"]))

        # run function
        create_init_search_params_templates()

        self.stdout.write(self.style.SUCCESS('Data imported successfully.'))






