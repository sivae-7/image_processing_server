import json

def combine_json_files(success_file_path, failed_file_path, output_file_path=None):
    try:
        with open(success_file_path, 'r') as success_file:
            success_data = json.load(success_file)

        with open(failed_file_path, 'r') as failed_file:
            failed_data = json.load(failed_file)

        combined_data = {
            "success": success_data,
            "failed": failed_data
        }

        if output_file_path:
            with open(output_file_path, 'w') as output_file:
                json.dump(combined_data, output_file, indent=4)
            print(f"Data combined and saved to '{output_file_path}'")

        return combined_data

    except FileNotFoundError as e:
        print(f"Error: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")
        return None