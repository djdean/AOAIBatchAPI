import StorageHandler
##This class is not complete. It is a placeholder for the actual implementation
class AzureBlobStorageHandler(StorageHandler):
    def __init__(self, connection_string):
        pass
    def get_directories(self,path):
        pass

    def write_content_to_directory(self, file_content, directory_name, output_filename):
        pass

    def write_data_to_storage(self,output_name,output_data,directory_name):
        pass

    def check_directory_exists(self,directory_name):
        pass 

    def create_directory(self,directory_name):
        pass

    def get_file_list(self,path: str) -> list:
        pass

    def get_file_data(self,file_name,directory_name):
        pass

    def delete_file_data(self,file_name,directory_name):
        pass

    def save_file_to_local(self,file_name, directory_name, local_path):
        pass

