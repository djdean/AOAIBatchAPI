class FileGenerator:
    def __init__(self,input_mode) -> None:
        self.input_mode = input_mode
    def generate_batch_file(self,file,header,delim):
        if self.input_mode == "CSV":
            csv_parsed = self.read_and_parse_CSV(file,header,delim)
            print("Done")
    def read_and_parse_CSV(self,filename, header, delim):
        csv_parsed = []
        headers = []
        with open(filename,"r") as csv_file:
            csv_data = csv_file.readline().replace("\n","")
            if header:
                csv_headers_split = csv_data.split(delim)
                for header in csv_headers_split:
                    headers.append(header)
                csv_data = csv_file.readline().replace("\n","")
            while csv_data != '':
                current_row_data_split = csv_data.split(delim)
                column_index = 0
                row_data_dict = {}
                for column_index in range(len(current_row_data_split)):
                    row_data_dict[headers[column_index]] = current_row_data_split[column_index]
                csv_parsed.append(row_data_dict)
                csv_data = csv_file.readline().replace("\n","")
        return csv_parsed



