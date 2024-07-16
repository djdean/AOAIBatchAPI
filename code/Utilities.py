import json
import tiktoken
import os
from token_count import TokenCount
class Utils:
    def __init__(self):
        pass
    def get_file_name_only(self, file_name):
        file_name_split = file_name.split("/")
        file_name_with_extension = file_name_split[len(file_name_split)-1]
        file_name_with_extension_split = file_name_with_extension.split(".")
        file_name_only = file_name_with_extension_split[0]
        return file_name_only
    
    def read_json_data(self,file_name):
        with open(file_name) as json_file:
            data = json.load(json_file)
        return data
    def get_file_list(self,directory):
        file_list = []
        for file in os.listdir(directory):
            file_list.append(file)
        return file_list
    def num_tokens_from_string(self, string: str, encoding_name: str) -> int:
        encoding = tiktoken.encoding_for_model(encoding_name)
        num_tokens = len(encoding.encode(string))
        return num_tokens
    def get_tokens_in_file(self, file, model_family):
        tc = TokenCount(model_name=model_family)
        tokens = tc.num_tokens_from_file(file)
        return tokens

