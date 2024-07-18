from Utilities import Utils
from AzureStorageHandler import StorageHandler
from AOAIHandler import AOAIHandler
from AzureBatch import AzureBatch


def main():
    BATCH_PATH = "https://aoaibatch.blob.core.windows.net/input/"
    APP_CONFIG = r"C:\Users\dade\Desktop\BatchAPI\config\app_config.json"
    utils = Utils()
    app_config_data = utils.read_json_data(APP_CONFIG)
    storage_config_data = utils.read_json_data(app_config_data["storage_config"])
    storage_account_name = storage_config_data["storage_account_name"]
    storage_account_key = storage_config_data["storage_account_key"]
    input_filesystem_system_name =  storage_config_data["input_filesystem_system_name"]
    error_filesystem_system_name = storage_config_data["error_filesystem_system_name"]
    processed_filesystem_system_name = storage_config_data["processed_filesystem_system_name"]
    input_root_directory = storage_config_data["input_root_directory"]
    aoai_config_data = utils.read_json_data(app_config_data["AOAI_config"])
    aoai_file_client = AOAIHandler(aoai_config_data)
    aoai_batch_client = AOAIHandler(aoai_config_data, batch=True)
    input_storage_handler = StorageHandler(storage_account_name, storage_account_key, input_filesystem_system_name)
    error_storage_handler = StorageHandler(storage_account_name, storage_account_key, error_filesystem_system_name)
    processed_storage_handler = StorageHandler(storage_account_name, storage_account_key, processed_filesystem_system_name)
    files = input_storage_handler.get_file_list(input_root_directory)
    directory_client = input_storage_handler.get_directory_client(input_root_directory)
    local_download_path = app_config_data["local_download_path"]
    azure_batch = AzureBatch(aoai_file_client, aoai_batch_client, input_storage_handler, 
                             error_storage_handler, processed_storage_handler, BATCH_PATH, directory_client, 
                             local_download_path)
    for file in files:
        #TODO: Add micro-batching logic here - put batch size in config file
        print(f"Processing file {file}")
        file_processing_result = azure_batch.process_file(file)
        print(file_processing_result)           


          
           
if __name__ == "__main__":
    main()