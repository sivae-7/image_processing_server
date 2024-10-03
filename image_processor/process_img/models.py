# models.py
from django.utils import timezone
from django.db import models
import uuid

class Batch(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    triggered_at = models.DateTimeField(blank=True, null=True)
    completed_at = models.DateTimeField(blank=True, null=True)
    status = models.CharField(max_length=255, null=False)
    status_path = models.CharField(max_length=255, blank=True, null=True)
    filepath = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now, editable=False)
    updated_at = models.DateTimeField(default=timezone.now, editable=False)

    class Meta:
        db_table = 'batch'

    def __str__(self):
        return f"Batch {self.id} - Status: {self.status}"


class Task(models.Model):
    class Status(models.TextChoices):
        STARTED = 'started', 'Started'
        COMPLETED = 'completed', 'Completed'
        FAILED = 'failed', 'Failed'
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    batch = models.ForeignKey(Batch, on_delete=models.CASCADE)  
    images_path = models.CharField(max_length=255)
    status = models.CharField(max_length=50, choices=Status.choices, default=Status.STARTED)  
    payload = models.JSONField(blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now, editable=False)  
    updated_at = models.DateTimeField(default=timezone.now, editable=False) 

    class Meta:
        db_table = 'task'

    def __str__(self):
        return f"Task {self.id} - Batch {self.batch_id}"
    @property
    def batch_uuid(self):
        """Return the UUID of the related Batch."""
        return self.batch_id.id  # Access the UUID of the Batch instance