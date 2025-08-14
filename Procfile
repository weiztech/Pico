
worker1: celery -A backend worker -P threads --concurrency=2 --loglevel=INFO ## for celery search handling
worker2: celery -A backend worker -Q $CELERY_DEDUPLICATION_QUEUE -P threads --concurrency=2 --loglevel=INFO ## for celery search handling
web: daphne -b 0.0.0.0 -p $PORT backend.asgi:application
