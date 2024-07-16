
from openai import AzureOpenAI
import requests
import time
import datetime

class AOAIHandler:
    def __init__(self, config):
        self.config_data = config
        self.model = config["aoai_deployment_name"]
        self.batch_endpoint = config["batch_job_endpoint"]
        self.completion_window = config["completion_window"]
        self.aoai_client = self.init_client(config)
        self.batch_status = {}
    def init_client(self,config):
        client = AzureOpenAI(
            azure_endpoint = config['aoai_endpoint'], 
            api_key=config['aoai_key'],  
            api_version=config['aoai_api_version']
        )
        return client
    def upload_batch_input_file(self,input_file_name, input_file_path):
        url = f"{self.azure_endpoint}openai/files/import?api-version={self.api_version}"
        headers = {
        "Content-Type": "application/json",
        "api-key": self.api_key  # Replace with your actual API key
        }   
        # Define the payload
        payload = {
            "purpose": "batch",
            "filename": input_file_name,
            "content_url": input_file_path
        }
    
        return requests.request("POST", url, headers=headers, json=payload)
    def delete_single(self, file_id):
        deletion_status = False
        try:
            # Attempt to delete the file
            response = self.aoai_client.files.delete(file_id)
            print(f"File {file_id} deleted successfully.")
            deletion_status = True
        except Exception as e:
            # Handle any exceptions that occur
            print(f"An error occurred while deleting file {file_id}: {e}")
        return deletion_status
    def delete_all_files(self):
        deletion_status = {}
        file_objects = self.aoai_client.files.list().data
        # Extracting the ids using a list comprehension
        file_ids = [file_object.id for file_object in file_objects] 
        for file_id in file_ids:
            try:
                # Attempt to delete the file
                response = self.aoai_client.files.delete(file_id)
                print(f"File {file_id} deleted successfully.")
                deletion_status[file_id] = True
            except Exception as e:
                # Handle any exceptions that occur
                print(f"An error occurred while deleting file {file_id}: {e}")
                deletion_status[file_id] = False
    
        return deletion_status
    def create_batch_job(self,file_id):
        # Submit a batch job with the file
        batch_response = self.aoai_client.batches.create(
            input_file_id=file_id,
            endpoint=self.batch_endpoint,
            completion_window=self.completion_window,
        )
        # Save batch ID for later use
        batch_id = batch_response.id
        self.batch_status[batch_id] = "Submitted"
        return batch_id
    def wait_for_file_upload(self, file_id):
        status = "pending"
        while status != "processed" or status != "error":
            time.sleep(15)
            file_response = self.aoai_client.files.retrieve(file_id)
            status = file_response.status
            print(f"{datetime.now()} File Id: {file_id}, Status: {status}")
        if status == "error":
            print(f"Error occurred while processing file {file_id}")
        else:
            print(f"File {file_id} processed successfully.")
        return status
    def wait_for_batch_job(self, batch_id):
        # Wait until the uploaded file is in processed state
        status = "Validating"
        while status not in ("Completed", "Failed", "Canceled"):
            time.sleep(60)
            batch_response = self.aoai_client.batches.retrieve(batch_id)
            status = batch_response.status
            print(f"{datetime.now()} Batch Id: {batch_id},  Status: {status}")
        if status == "Failed":
            print(f"Batch job {batch_id} failed.")
        elif status == "Canceled":
            print(f"Batch job {batch_id} was canceled.")
        else:
            print(f"Batch job {batch_id} completed successfully.")
        return status