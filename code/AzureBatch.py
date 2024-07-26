import os
import json
from Utilities import Utils
import asyncio
import time
class AzureBatch:
    def __init__(self, aoai_client, input_storage_handler, 
                 error_storage_handler, processed_storage_handler, batch_path,
                input_directory_client, local_download_path):
        self.aoai_client = aoai_client
        self.input_storage_handler = input_storage_handler
        self.error_storage_handler = error_storage_handler
        self.processed_storage_handler = processed_storage_handler
        self.batch_path = batch_path
        self.input_directory_client = input_directory_client
        self.local_download_path = local_download_path

    async def process_all_files(self,files,micro_batch_size):
        tasks = []
        current_tasks = 0
        for file in files:
            tasks.append(self.process_file(file))
            current_tasks += 1
            if current_tasks == micro_batch_size:
                await asyncio.gather(*tasks)
                tasks = []
                current_tasks = 0
        #Process any remaining tasks
        if len(tasks) > 0:
            await asyncio.gather(*tasks)
        
    async def process_file(self,file):
        print(f"Processing file {file}")
        filename_only = Utils.get_file_name_only(file)
        #Mark start time
        processing_result = {}
        batch_storage_path = self.batch_path + file
        if self.local_download_path is not None:
            output_path = os.path.join(self.local_download_path, file)
            batch_file_data = self.input_storage_handler.save_file_to_local(file, 
                                        self.input_directory_client, output_path)
            token_size = Utils.get_tokens_in_file(output_path,"gpt-4")
        else:
            batch_file_data = self.input_storage_handler.get_file_data(file,self.input_directory_client)
            batch_file_string = str(batch_file_data)
            token_size = Utils.num_tokens_from_string(batch_file_string,"gpt-4")
        print(f"File {file} has {token_size} tokens")
        # Process the file
        file_status = self.aoai_client.upload_batch_input_file(file,batch_storage_path)
        file_content_json = file_status.json()
        file_id = file_content_json['id']
        print(f"file_id: {file_content_json['id']}")
        #TODO: Check if the file was uploaded successfully, if not, move to error folder and cleanup
        await self.aoai_client.wait_for_file_upload(file_id)
        initial_batch_response = self.aoai_client.create_batch_job(file_id)
        #This takes start time as a param
        (finished_batch_response) = await self.aoai_client.wait_for_batch_job(initial_batch_response.id)
        print(f"Batch job {initial_batch_response.id} completed.")
        batch_metadata = {
            "file_name": file,
            "input_file_id": finished_batch_response.input_file_id,
            "batch_job_id": initial_batch_response.id,
            "error_file_id": finished_batch_response.error_file_id,
            "output_file_id": finished_batch_response.output_file_id,
            "token_size": token_size
        }
        metadata_filename = f"{filename_only}_metadata.json"  
        error_file_content = self.aoai_client.aoai_client.files.content(finished_batch_response.error_file_id)
        error_file_content_string = str(error_file_content.text)
        output_file_content = self.aoai_client.aoai_client.files.content(finished_batch_response.output_file_id)  
        output_file_content_string = str(output_file_content.text)
        test = Utils.clean_binary_string(output_file_content_string)
        output_directory_name = Utils.append_postfix(file)
        if not error_file_content_string == "":
        #if True:
            error_filename = f"{filename_only}_error.json"
            batch_metadata["error_file_name"] = error_filename
            error_file_content_json = json.dumps(error_file_content_string)
            error_file_metadata = json.dumps(batch_metadata)
            error_content_write_result = self.error_storage_handler.write_content_to_directory(error_file_content_json,output_directory_name,error_filename)
            error_metadata_write_result = self.error_storage_handler.write_content_to_directory(error_file_metadata,output_directory_name,metadata_filename)
            file_write_result = self.error_storage_handler.write_content_to_directory(batch_file_data,output_directory_name,file)
            #TODO: Write original file to error directory
            if error_content_write_result and error_metadata_write_result:
                print(f"An error file with details written to the 'error' directory.")
                processing_result["error"] = True
                processing_result["status"] = False
                processing_result["details"] = True
            else:
                print(f"There was a problem processing file: {file} and details could not be written to storage. Please check {initial_batch_response.id} for more details.")
                processing_result["error"] = True
                processing_result["status"] = False
                processing_result["details"] = False
        #Same as above, will work with 7-1-2024-preview API when released on the 29th of July.
        if not output_file_content_string == "":
            output_filename = f"{filename_only}_output.json"
            batch_metadata["output_file_name"] = output_filename
            output_file_content = self.aoai_client.aoai_client.files.content(finished_batch_response.output_file_id)   
            output_file_content_json = json.dumps(output_file_content_string)
            output_file_metadata = json.dumps(batch_metadata)
            output_content_write_result = self.processed_storage_handler.write_content_to_directory(output_file_content_json,output_directory_name,output_filename)
            output_metadata_write_result = self.processed_storage_handler.write_content_to_directory(output_file_metadata,output_directory_name,metadata_filename)
            file_write_result = self.processed_storage_handler.write_content_to_directory(batch_file_data,output_directory_name,file)
            if output_content_write_result and output_metadata_write_result:
                print(f"File: {file} has been processed successfully. Results are available in the 'processed' directory.")
                processing_result["error"] = False
                processing_result["status"] = True
                processing_result["details"] = True
            else:
                print(f"File: {file} has been processed successfully but could not be written to storage. Please check {initial_batch_response.id} for more details.")   
                processing_result["error"] = False
                processing_result["status"] = True
                processing_result["details"] = True
        cleanup_status = self.cleanup_batch(file,file_id)
        processing_result["cleanup_status"] = cleanup_status
        return processing_result
    def cleanup_batch(self,filename,file_id):
        cleanup_result = {}
        deletion_status = self.aoai_client.delete_single(file_id)
        
        if deletion_status:
            print(f"File {filename} deleted successfully.")
            cleanup_result["file_deletion"] = True
        else:
            print(f"An error occurred while deleting file {filename}.")
            cleanup_result["file_deletion"] = False
        if self.local_download_path is not None:
            local_filename_with_path = self.local_download_path+"\\"+filename
            if os.path.exists(local_filename_with_path):
                os.remove(local_filename_with_path)
                print(f"File {local_filename_with_path} deleted successfully.")
                cleanup_result["local_file_deletion"] = True
        az_storage_deletion_status = self.input_storage_handler.delete_file_data(filename,self.input_directory_client)
        if az_storage_deletion_status:
            print(f"File {filename} deleted from storage successfully.")
            cleanup_result["az_storage_file_deletion"] = True
        else:
            print(f"An error occurred while deleting file {filename} from storage.")
            cleanup_result["az_storage_file_deletion"] = False
        return cleanup_result