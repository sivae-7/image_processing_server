from celery import shared_task
import json
import logging
import os
from .utils.formatJson import combine_json_files
from .models import Task
from .utils.process_image import extract_voter_data
from dotenv import load_dotenv
import os

@shared_task
def extract_and_combine_voter_data(imgfold, task_id):
    load_dotenv()
    logger = logging.getLogger(__name__)
    try:
        task = Task.objects.get(id=task_id)
    except Task.DoesNotExist:
        logger.error(f"Task with ID {task_id} does not exist.")
        return
    is_extracted_data = extract_voter_data(imgfold)
    print(f"Starting task for folder: {imgfold} and task ID: {task_id}")
    if is_extracted_data:
        try:
            combined_data = combine_json_files(
                os.getenv('VOTER_DATA_PATH'),
                os.getenv('MISSED_VOTER_PAGES_PATH'),
                os.getenv('COMBINED_DATA_PATH')
            )
            if combined_data:
                task.payload = json.dumps(combined_data, indent=4)
                task.status = "completed"
            else:
                task.status = "failed"  
        
        except Exception as e:
            print(f"combined_data result : {e}")
            logger.error(f"Error while combining JSON files: {e}")
            task.status = "failed"
            task.payload = json.dumps({"error": str(e)}, indent=4)
    else:
        print(f"extracted data result : {is_extracted_data}")
        task.status = "failed"

    task.save()
