import json
import tiktoken
import semchunk
import os
class Utils:
    def __init__(self):
        pass
    def get_file_name_only(self, file_name):
        file_name_split = file_name.split("/")
        file_name_with_extension = file_name_split[len(file_name_split)-1]
        file_name_with_extension_split = file_name_with_extension.split(".")
        file_name_only = file_name_with_extension_split[0]
        return file_name_only
    def get_status_map(self, paths, expression):
        file_status = {}
        for path in paths:
            file_name_only = self.get_file_name_only(path.name)
            if expression in file_name_only:
                file_name_only = file_name_only.replace(expression,"")
                file_status[file_name_only] = False
            else:
                file_status[file_name_only] = True
        return file_status
    def get_aoai_file_status_map(self, paths):
        file_status = {}
        for path in paths:
            file_name_only = self.get_file_name_only(path.name)
            if "_with_aoai" in file_name_only:
                file_name_only = file_name_only.replace("_with_aoai","")
                file_status[file_name_only] = False
            else:
                file_status[file_name_only] = True
        return file_status
    def get_aoai_insight_file_status_map(self, paths):
        file_status = {}
        for path in paths:
            file_name_only = self.get_file_name_only(path.name)
            if "_with_aoai_insights" in file_name_only:
                file_name_only = file_name_only.replace("_with_aoai_insights","")
                file_status[file_name_only] = False
            else:
                file_status[file_name_only] = True
        return file_status
    def get_formatting_file_status(self, paths):
        file_status = {}
        for path in paths:
            file_name_only = self.get_file_name_only(path.name)
            if "_formatted" in file_name_only:
                file_name_only = file_name_only.replace("_formatted","")
                file_status[file_name_only] = False
            else:
                file_status[file_name_only] = True
        return file_status
    def get_semantic_chunks(self, text, model, chunk_size=4000):
        encoder = tiktoken.encoding_for_model(model)
        token_counter = lambda text: len(encoder.encode(text))
        chunks = semchunk.chunk(text, chunk_size=chunk_size, token_counter=token_counter)
        return chunks
    def get_display_list(self,paths):
        display_list = []
        for path in paths:
            if "with_aoai_insights" in path.name:
                file_name_only = self.get_file_name_only(path.name)
                display_list.append(file_name_only)
        return display_list
    def get_pdf_file_status_map(self, paths):
        file_status = {}
        for path in paths:
            file_name_only = self.get_file_name_only(path.name)
            if not file_name_only in file_status:
                if not path.is_directory and ".json" in path.name:
                    file_status[file_name_only] = False
                elif not path.is_directory and ".pdf" in path.name:
                    file_status[file_name_only] = True
            else:
                if not path.is_directory and ".json" in path.name:
                    file_status[file_name_only] = False
        return file_status
    def read_json_data(self,file_name):
        with open(file_name) as json_file:
            data = json.load(json_file)
        return data
    def get_file_list(self,directory):
        file_list = []
        for file in os.listdir(directory):
            file_list.append(file)
        return file_list
    def get_schemas(self, schema_dir):
        files = self.get_file_list(schema_dir)
        schemas = {}
        for file in files:
            if ".json" in file:
                file_key = self.get_file_name_only(file)
                schema = self.read_json_data(schema_dir + "\\" + file)
                schemas[file_key] = schema
        return schemas
    def remove_non_json_content(self, text):
        json_only = text.replace("Formatted content: ", "").replace("`","")\
                    .replace("\n","").replace("\r","").replace("\t","").replace("json","")
        return json_only
    def num_tokens_from_string(self, string: str, encoding_name: str) -> int:
        encoding = tiktoken.encoding_for_model(encoding_name)
        num_tokens = len(encoding.encode(string))
        return num_tokens

