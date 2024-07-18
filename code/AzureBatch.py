import os
import json
from Utilities import Utils
class AzureBatch:
    def __init__(self, aoai_file_client, aoai_batch_client, input_storage_handler, 
                 error_storage_handler, processed_storage_handler, batch_path,
                input_directory_client, local_download_path):
        self.aoai_file_client = aoai_file_client
        self.aoai_batch_client = aoai_batch_client
        self.input_storage_handler = input_storage_handler
        self.error_storage_handler = error_storage_handler
        self.processed_storage_handler = processed_storage_handler
        self.batch_path = batch_path
        self.input_directory_client = input_directory_client
        self.local_download_path = local_download_path

    def process_file(self,file):
        processing_result = {}
        output_path = os.path.join(self.local_download_path, file)
        batch_storage_path = self.batch_path + file
        batch_file_data = self.input_storage_handler.save_file_to_local(file, self.input_directory_client, output_path)
        token_size = Utils.get_tokens_in_file(output_path,"gpt-4")
        print(f"File {file} has {token_size} tokens")
        # Process the file
        file_status = self.aoai_file_client.upload_batch_input_file(file,batch_storage_path)
        #TODO: Check if the file was uploaded successfully, if not, move to error folder and cleanup
        file_objects = self.aoai_file_client.aoai_client.files.list().data
        file_ids = [file_object.id for file_object in file_objects] 
        self.aoai_file_client.wait_for_file_upload(file_ids[0])
        initial_batch_response = self.aoai_batch_client.create_batch_job(file_ids[0])
        finished_batch_response = self.aoai_batch_client.wait_for_batch_job(initial_batch_response.id)
        print(f"Batch job {initial_batch_response.id} completed.")
        batch_metadata = {
            "file_name": file,
            "input_file_id": finished_batch_response.input_file_id,
            "batch_job_id": initial_batch_response.id,
            "error_file_id": finished_batch_response.error_file_id,
            "output_file_id": finished_batch_response.output_file_id,
            "token_size": token_size
        }
        metadata_filename = f"{file}_metadata.json"  
        error_file_content = self.aoai_file_client.aoai_client.files.content(finished_batch_response.error_file_id)
        error_file_content_string = str(error_file_content.content)
        output_file_content = self.aoai_file_client.aoai_client.files.content(finished_batch_response.output_file_id)  
        output_file_content_string = str(output_file_content.content)
        output_directory_name = Utils.append_postfix(file)
        #Broken currently, will work with 7-1-2024-preview API when released on the 29th of July. 
        #For now, we will create an error and completion file for each batch job. 
        #error_count = int(finished_batch_response.request_counts.failed)
        #output_count = int(finished_batch_response.request_counts.completed) 
        #if error_count > 0:
        if True:
            error_filename = f"{file}_error.json"
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
        #if output_count > 0:
        if True:
            output_filename = f"{file}_output.json"
            batch_metadata["output_file_name"] = output_filename
            output_file_content = self.aoai_file_client.aoai_client.files.content(finished_batch_response.output_file_id)   
            output_file_content_json = json.dumps(output_file_content_string)
            output_file_metadata = json.dumps(batch_metadata)
            output_content_write_result = self.processed_storage_handler.write_content_to_directory(output_file_content_json,output_directory_name,output_filename)
            output_metadata_write_result = self.processed_storage_handler.write_content_to_directory(output_file_metadata,output_directory_name,metadata_filename)
            file_write_result = self.error_storage_handler.write_content_to_directory(batch_file_data,output_directory_name,file)
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
        cleanup_status = self.cleanup_batch(file,file_ids[0])
        processing_result["cleanup_status"] = cleanup_status
        return processing_result
    def cleanup_batch(self,filename,file_id):
        cleanup_result = {}
        deletion_status = self.aoai_file_client.delete_single(file_id)
        local_filename_with_path = self.local_download_path+"\\"+filename
        if deletion_status:
            print(f"File {filename} deleted successfully.")
            cleanup_result["file_deletion"] = True
        else:
            print(f"An error occurred while deleting file {filename}.")
            cleanup_result["file_deletion"] = False
        if os.path.exists(local_filename_with_path):
            os.remove(local_filename_with_path)
            print(f"File {local_filename_with_path} deleted successfully.")
            cleanup_result["local_file_deletion"] = True
        else:
            print(f"An error occurred while deleting file {local_filename_with_path}.")
            cleanup_result["local_file_deletion"] = False
        az_storage_deletion_status = self.input_storage_handler.delete_file_data(filename,self.input_directory_client)
        if az_storage_deletion_status:
            print(f"File {filename} deleted from storage successfully.")
            cleanup_result["az_storage_file_deletion"] = True
        else:
            print(f"An error occurred while deleting file {filename} from storage.")
            cleanup_result["az_storage_file_deletion"] = False
        return cleanup_result