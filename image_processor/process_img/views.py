from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Task
from .models import Batch
import json
from .task import extract_and_combine_voter_data
import os
import uuid
from dotenv import load_dotenv
load_dotenv()
@csrf_exempt
def process_batch(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            batch_id = data.get('batch_id')
            if not batch_id:
                return JsonResponse({'error': 'batch_id is required'}, status=400)

            try:
                batch_uuid = uuid.UUID(batch_id) 
                batch = Batch.objects.get(id=batch_uuid)  
                image = Task.objects.get(batch=batch)  
                print(batch.filepath,"  ------------>pdf path")
                print(f"Found image folder with batch_id {batch_id}")

            except Task.DoesNotExist:
                return JsonResponse({'error': 'No image found for the provided batch_id'}, status=404)

            imgfold = image.images_path

            if image.status == "started":
                extract_and_combine_voter_data.delay(imgfold, image.id)
                return JsonResponse({'message': 'Batch processing started'}, status=202)

            return JsonResponse({'error': 'Image processing already in progress or completed.'}, status=400)

        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        except Exception as e:
            print(f"Error processing batch: {e}")
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Invalid request method'}, status=405)