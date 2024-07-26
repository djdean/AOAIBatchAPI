import abc
# Abstract class for storage handler
class StorageHandler(abc.ABC):
    @abc.abstractmethod
    def get_directories(self,path):
        pass
    @abc.abstractmethod
    def write_content_to_directory(self, file_content, directory_name, output_filename):
        pass
    @abc.abstractmethod
    def write_data_to_storage(self,output_name,output_data,directory_name):
        pass
    @abc.abstractmethod
    def check_directory_exists(self,directory_name):
        pass 
    @abc.abstractmethod
    def create_directory(self,directory_name):
        pass
    @abc.abstractmethod
    def get_file_list(self,path: str) -> list:
        pass
    @abc.abstractmethod
    def get_file_data(self,file_name,directory_name):
        pass
    @abc.abstractmethod
    def delete_file_data(self,file_name,directory_name):
        pass
    @abc.abstractmethod
    def save_file_to_local(self,file_name, directory_name, local_path):
        pass

