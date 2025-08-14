import os
from celery import Celery
#import django ## add this for testing independent celery run
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")
#django.setup()  # Add this line for testing in dependent celery run

app = Celery("backend")
#from lit_reviews.celery_tasks.scrapers import *
#from lit_reviews.tasks import *
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

