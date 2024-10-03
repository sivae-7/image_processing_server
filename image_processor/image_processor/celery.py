from __future__ import absolute_import, unicode_literals
import os
from celery import Celery

# Set the default Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'image_processor.settings')

# Create the Celery app instance
app = Celery('image_processor')

# Load the Django settings into Celery
app.config_from_object('django.conf:settings', namespace='CELERY')

# Discover tasks from all registered apps
app.autodiscover_tasks()

app.conf.worker_concurrency = 3

