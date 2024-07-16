from Utilities import Utils
from AzureStorageHandler import StorageHandler
from AOAIHandler import AOAIHandler
import json
import time

def main():
    utils = Utils()
    config_data_dir = r"C:\Users\dade\Desktop\BatchAPI\config"
    storage_config_filename = r"\storage_config.json"
    aoai_config_filename = r"\AOAI_config_gpt-4o.json"
    schema_directory = r"C:\Users\DeanD\Desktop\ContentExtraction\schemas"
    storage_config_data = utils.read_json_data(config_data_dir+storage_config_filename)
    storage_account_name = storage_config_data["storage_account_name"]
    storage_account_key = storage_config_data["storage_account_key"]
    file_system_name =  storage_config_data["file_system_name"]
    root_directory = storage_config_data["root_directory"]
    aoai_config_data = utils.read_json_data(config_data_dir+aoai_config_filename)
    aoai_handler = AOAIHandler(aoai_config_data)
    storage_handler = StorageHandler(storage_account_name, storage_account_key, file_system_name)
    directories = storage_handler.get_directories(root_directory)
    directory_client = None
    
            


          
           
if __name__ == "__main__":
    main()