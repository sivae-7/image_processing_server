from __future__ import absolute_import, unicode_literals
import os
from celery import Celery

# Set the default Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')

# Create the Celery app instance
app = Celery('myproject')

# Load the Django settings into Celery
app.config_from_object('django.conf:settings', namespace='CELERY')

# Discover tasks from all registered apps
app.autodiscover_tasks()
