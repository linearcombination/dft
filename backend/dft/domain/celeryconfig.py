import os

## Broker settings.
broker_url = os.environ.get("CELERY_BROKER_URL", "redis://")

## Using the database to store task state and results.
result_backend = os.environ.get("CELERY_RESULT_BACKEND", "redis://")

# List of modules to import when the Celery worker starts.
imports = ("dft.domain.dft_checker",)
