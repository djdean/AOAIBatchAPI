from Utilities import Utils
from AzureStorageHandler import StorageHandler
from AOAIHandler import AOAIHandler
import json
import time
import os
import stat

def main():
    APP_CONFIG = r"C:\Users\dade\Desktop\BatchAPI\config\app_config.json"
    utils = Utils()
    app_config_data = utils.read_json_data(APP_CONFIG)
    storage_config_data = utils.read_json_data(app_config_data["storage_config"])
    storage_account_name = storage_config_data["storage_account_name"]
    storage_account_key = storage_config_data["storage_account_key"]
    input_filesystem_system_name =  storage_config_data["input_filesystem_system_name"]
    input_root_directory = storage_config_data["input_root_directory"]
    aoai_config_data = utils.read_json_data(app_config_data["AOAI_config"])
    aoai_handler = AOAIHandler(aoai_config_data)
    storage_handler = StorageHandler(storage_account_name, storage_account_key, input_filesystem_system_name)
    files = storage_handler.get_file_list(input_root_directory)
    directory_client = storage_handler.get_directory_client(input_root_directory)
    local_download_path = app_config_data["local_download_path"]

    # Change the permissions of the directory to 777
    os.chmod(local_download_path, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)

    print(f"Permissions for {local_download_path} set to 777")

    # Print new permissions
    new_permissions = os.stat(local_download_path).st_mode
    print(f"New permissions: {oct(new_permissions)}")
    for file in files:
        print(f"Processing file {file}")
        batch_file = storage_handler.save_file_to_local(file, directory_client, local_download_path)
        
            


          
           
if __name__ == "__main__":
    main()