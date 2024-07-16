
import os
from openai import AzureOpenAI
import requests
import json

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
            aoai_endpoint = config['aoai_endpoint'], 
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