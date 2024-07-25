from Utilities import Utils
from AzureStorageHandler import StorageHandler
from AOAIHandler import AOAIHandler
from AzureBatch import AzureBatch
import asyncio


def main():
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
    BATCH_PATH = "https://"+storage_account_name+".blob.core.windows.net/"+input_filesystem_system_name+"/"
    batch_size = int(app_config_data["batch_size"])
    aoai_client = AOAIHandler(aoai_config_data)
    input_storage_handler = StorageHandler(storage_account_name, storage_account_key, input_filesystem_system_name)
    error_storage_handler = StorageHandler(storage_account_name, storage_account_key, error_filesystem_system_name)
    processed_storage_handler = StorageHandler(storage_account_name, storage_account_key, processed_filesystem_system_name)
    files = input_storage_handler.get_file_list(input_root_directory)
    directory_client = input_storage_handler.get_directory_client(input_root_directory)
    download_to_local = app_config_data["download_to_local"]
    local_download_path = None
    if download_to_local:
        local_download_path = app_config_data["local_download_path"]
    azure_batch = AzureBatch(aoai_client, input_storage_handler, 
                             error_storage_handler, processed_storage_handler, BATCH_PATH, directory_client, 
                             local_download_path)
    azure_batch.aoai_client.delete_all_files()
    asyncio.run(azure_batch.process_all_files(files, batch_size))   
    #Cleanup
    azure_batch.aoai_client.delete_all_files()

    #TODO: 1) Support blob storage
    #      2) Remove BATCH_PATH parameter - DONE
    #      3) Add in memory processing option - Done
    #      4) Make local vs download configurable - DONE       


          
           
if __name__ == "__main__":
    main()