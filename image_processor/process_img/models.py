from django.db import models

class Task(models.Model):
    imgfolderid = models.AutoField(primary_key=True)
    pdfid = models.IntegerField()
    imgfolderpath = models.CharField(max_length=255)
    status = models.CharField(max_length=50)
    payload = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'task'  # Specify the existing table name

