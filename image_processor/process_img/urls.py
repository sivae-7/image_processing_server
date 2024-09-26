from django.urls import path
from .views import process_batch 
urlpatterns = [
    path('process-batch/', process_batch, name='process_batch'), 
]