from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Task
import json
from .utils.process_image import extract_voter_data
from .utils.formatJson import combine_json_files
import os
from dotenv import load_dotenv
load_dotenv()
@csrf_exempt
def process_batch(request):
    if request.method == 'POST':
        try:
            print(f"Raw request body: {request.body.decode('utf-8')}")
            data = json.loads(request.body)
            batch_id = data.get('batch_id')

            if not batch_id:
                return JsonResponse({'error': 'batch_id is required'}, status=400)

            try:
                image = Task.objects.get(pdfid=int(batch_id))
                print(f"Found image with batch_id {batch_id}")

            except Task.DoesNotExist:
                return JsonResponse({'error': 'No image found for the provided batch_id'}, status=404)

            imgfold = image.imgfolderpath

            image.status = "processing"
            image.save()
            print(f"Image {image.pdfid} is in processing state.")

            try:
                if image.status == "created":
                    is_extracted_data = extract_voter_data.delay(imgfold)
                    
                    if is_extracted_data:
                        image.status = "storing"
                    else:
                        image.status = "invalid"
            except Exception as e:
                print(f"Error during data extraction: {e}")
                image.status = "failed"
                image.save()
                return JsonResponse({'error': 'Data extraction failed', 'details': str(e)}, status=500)
            image.save()
            print(f"Image {image.pdfid} status updated to {image.status}.")

            image.payload = combine_json_files(
                os.getenv('VOTER_DATA_PATH'),
                os.getenv('MISSED_VOTER_PAGES_PATH'),
                os.getenv('COMBINED_DATA_PATH')
            )
            image.save()
            image.status = "completed"
            image.save()
            print(f"Image {image.pdfid} processed and payload saved.")

            return JsonResponse({'message': 'Batch processed successfully'}, status=200)

        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        except Exception as e:
            print(f"Error processing batch: {e}")
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Invalid request method'}, status=405)