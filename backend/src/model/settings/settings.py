
import os
import pandas as pd
from pathlib import Path

class Settings:

    parent_dir = Path(__file__).parent  
    file_parameters = "Model Parameters.xlsx"
    file_data_specifications  = "Data Specifications.xlsx"
    
    def __init__(
        self,
        file_parameters=None,
        file_data_specifications=None
    ) -> None:

        self.file_parameters = os.path.join(self.parent_dir, self.file_parameters) if file_parameters is None else file_parameters
        self.file_data_specifications = os.path.join(self.parent_dir, self.file_data_specifications) if file_data_specifications is None else file_data_specifications 

        self.parameters = self.get_parameters()
        self.data_specs = self.get_data_specifications()

    def get_parameters(self):
        
        # Load raw parameters file
        parameters = pd.read_excel(
            self.file_parameters, 
            sheet_name=None
        )

        self.parameters = parameters

        return parameters
    
    def get_data_specification(
        self, 
        df_data_spec
    ):

        # Filter only used columns
        df_used_columns = df_data_spec[df_data_spec['used_column'] == 1]

        # Seperate date columns to make it possible to assign different formats for each column
        df_date_columns = df_used_columns[df_used_columns['data_type'] == "date"]
        date_columns = df_date_columns.set_index('model_column_name')['date_format'].to_dict()

        # Non date column
        df_non_date_columns = df_used_columns[df_used_columns['data_type'] != "date"]
        non_date_columns = df_non_date_columns.set_index('model_column_name')['data_type'].to_dict()

        # New column names
        new_column_names = df_used_columns.set_index('raw_column_name')['model_column_name'].to_dict()   

        # Column numbers 
        if "column_number" in df_used_columns.columns:
            column_numbers = df_used_columns.set_index('model_column_name')['column_number'].to_dict()
        else:
            column_numbers = None

        dict_data_spec = {
            'date_columns': date_columns, 
            'non_date_columns': non_date_columns, 
            'new_column_names': new_column_names,
            'column_numbers': column_numbers
        }

        return dict_data_spec
    
    def get_data_specifications(self):
        
        raw_data_specs = pd.read_excel(
            self.file_data_specifications, 
            sheet_name=None
        )

        data_specs = {}

        for file in raw_data_specs.keys():

            df_data_spec = raw_data_specs[file]
            
            if len(df_data_spec) > 0:
                data_spec = self.get_data_specification(df_data_spec)
                data_specs[file] = data_spec

        return data_specs
