import os
import json
from Utilities import Utils
import asyncio
import time
class AzureBatch:
    def __init__(self, aoai_client, input_storage_handler, 
                 error_storage_handler, processed_storage_handler, batch_path,
                input_directory_client, local_download_path, output_directory, error_directory):
        self.aoai_client = aoai_client
        self.input_storage_handler = input_storage_handler
        self.error_storage_handler = error_storage_handler
        self.processed_storage_handler = processed_storage_handler
        self.batch_path = batch_path
        self.input_directory_client = input_directory_client
        self.local_download_path = local_download_path
        self.output_directory = output_directory
        self.error_directory = error_directory

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
        file_without_directory = Utils.strip_directory_name(file)
        file_extension = Utils.get_file_extension(file_without_directory)
        #Mark start time
        processing_result = {}
        batch_storage_path = self.batch_path + file
        if self.local_download_path is not None:
            output_path = os.path.join(self.local_download_path, file)
            batch_file_data = self.input_storage_handler.save_file_to_local(file, 
                                        self.input_directory_client, output_path)
            token_size = Utils.get_tokens_in_file(output_path,"gpt-4")
        else:
            batch_file_data = self.input_storage_handler.get_file_data(file_without_directory,self.input_directory_client)
            batch_file_string = str(batch_file_data)
            token_size = Utils.num_tokens_from_string(batch_file_string,"gpt-4")
        output_directory_name = self.output_directory+"/"+Utils.append_postfix(file_without_directory)
        error_directory_name = self.error_directory+"/"+Utils.append_postfix(file_without_directory)
        print(f"File {file} has {token_size} tokens")
        # Process the file
        upload_response = self.aoai_client.upload_batch_input_file(file,batch_storage_path)
        if not upload_response:
            print(f"An error occurred while uploading file {file}. Please check the file and try again. Code: {upload_response.status_code}")
            file_write_result = self.error_storage_handler.write_content_to_directory(batch_file_data,error_directory_name,file_without_directory)
            cleanup_status = self.cleanup_batch(file_without_directory,"")
            return
        file_content_json = upload_response.json()
        file_id = file_content_json['id']
        print(f"file_id: {file_content_json['id']}")
        #TODO: Check if the file was uploaded successfully, if not, move to error folder and cleanup
        await self.aoai_client.wait_for_file_upload(file_id)
        initial_batch_response = self.aoai_client.create_batch_job(file_id)
        #This takes start time as a param
        (finished_batch_response) = await self.aoai_client.wait_for_batch_job(initial_batch_response.id)
        batch_metadata = {
            "file_name": file,
            "input_file_id": finished_batch_response.input_file_id,
            "batch_job_id": initial_batch_response.id,
            "error_file_id": finished_batch_response.error_file_id,
            "output_file_id": finished_batch_response.output_file_id,
            "token_size": token_size
        }
        metadata_filename = f"{filename_only}_metadata."+file_extension
        if finished_batch_response.error_file_id is not None:
            error_file_content = self.aoai_client.aoai_client.files.content(finished_batch_response.error_file_id)
            error_file_content_string = str(error_file_content.text)
        else:
            errors = finished_batch_response.errors.data
            error_file_content = {}
            error_index = 1
            for error in errors:
                error_file_content["Error "+str(error_index)] = error.message
            error_file_content_string = json.dumps(error_file_content)
        if finished_batch_response.output_file_id is not None:
            output_file_content = self.aoai_client.aoai_client.files.content(finished_batch_response.output_file_id)  
            output_file_content_string = str(output_file_content.text)
        else:
            output_file_content = ""
            output_file_content_string = "" 
        if not error_file_content_string == "":
            error_filename = f"{filename_only}_error."+file_extension
            batch_metadata["error_file_name"] = error_filename
            error_file_content_json = json.dumps(error_file_content_string)
            error_file_metadata = json.dumps(batch_metadata)
            error_content_write_result = self.error_storage_handler.write_content_to_directory(error_file_content_json,output_directory_name,error_filename)
            error_metadata_write_result = self.error_storage_handler.write_content_to_directory(error_file_metadata,output_directory_name,metadata_filename)
            file_write_result = self.error_storage_handler.write_content_to_directory(batch_file_data,output_directory_name,file)
            if error_content_write_result and error_metadata_write_result:
                print(f"An error file with details written to the 'error' directory.")
            else:
                print(f"There was a problem processing file: {file} and details could not be written to storage. Please check {initial_batch_response.id} for more details.")
        if not output_file_content_string == "":
            output_filename = f"{filename_only}_output."+file_extension
            batch_metadata["output_file_name"] = output_filename
            output_file_content = self.aoai_client.aoai_client.files.content(finished_batch_response.output_file_id)   
            output_file_content_json = output_file_content_string
            output_file_metadata = json.dumps(batch_metadata)
            output_content_write_result = self.processed_storage_handler.write_content_to_directory(output_file_content_json,output_directory_name,output_filename)
            output_metadata_write_result = self.processed_storage_handler.write_content_to_directory(output_file_metadata,output_directory_name,metadata_filename)
            file_write_result = self.processed_storage_handler.write_content_to_directory(batch_file_data,output_directory_name,file_without_directory)
            if output_content_write_result and output_metadata_write_result:
                print(f"File: {file} has been processed successfully. Results are available in the 'processed' directory.")
            else:
                print(f"File: {file} has been processed successfully but could not be written to storage. Please check {initial_batch_response.id} for more details.")   
        cleanup_status = self.cleanup_batch(file_without_directory,file_id)
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