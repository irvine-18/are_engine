import os
import sys
import openpyxl
import xlrd
import time
import pandas as pd
import numpy as np

def extract_table_from_xls(filename, start_cell_value=None, capitalize_header=True):

    if isinstance(start_cell_value, str):
        start_cell_value = [start_cell_value]
    
    try:
        workbook = xlrd.open_workbook(filename)
        sheet = workbook.sheet_by_index(0)
        start_cell = None

        if start_cell_value:
            for row in range(sheet.nrows):
                for col in range(sheet.ncols):
                    if sheet.cell_value(row, col) in start_cell_value:
                        start_cell = (row, col)
                        break
                if start_cell:
                    break
        else:
            start_cell = (1, 1)

        if not start_cell:
            raise ValueError("Starting cell not found")

        max_row = None

        # Iterate through the rows of the column
        for row in range(start_cell[0], sheet.nrows):
            if sheet.cell_type(row, start_cell[1]) == 0:
                max_row = row 
                break  

        if max_row is None:
            raise ValueError("No data found in the column of the starting cell")

        table_data = []

        for row in range(start_cell[0], max_row):
            table_data.append(sheet.row_values(row))

        columns = table_data[0]  # Assuming the first row contains column headers
        table_data = table_data[1:]  # Exclude the header row

        table_df = pd.DataFrame(data=table_data, columns=columns)

        # print(f"Successfully extracted table of size: {table_df.shape} from {filename}")
        
        if capitalize_header:
            table_df.columns = table_df.columns.str.upper()

        column_to_drop = ''

        if column_to_drop in table_df.columns:
            table_df.drop(columns=column_to_drop, inplace=True)

        table_df.replace('', np.nan, inplace=True)

        return table_df

    except Exception as e:
        print(f"Error: {e}")
        return None

def extract_table_from_xlsx(filename, sheet_name=None, start_cell_range=None, start_cell_value=None, first_row_headers=True, capitalize_header=False):

    if isinstance(start_cell_value, str):
        start_cell_value = [start_cell_value]
    
    try:
        workbook = openpyxl.load_workbook(filename, data_only=True)

        if sheet_name is None:
            sheet = workbook.active
        else:
            sheet = workbook[sheet_name]

        start_cell = None

        if start_cell_value:
            for row in sheet.iter_rows():
                for cell in row:
                    if cell.value in start_cell_value:
                        start_cell = cell
                        break
                if start_cell:
                    break
        elif start_cell_range:
            start_cell = sheet[start_cell_range]
        else:
            start_cell = sheet["A1"]

        if not start_cell:
            raise ValueError("Starting cell not found")

        max_row = None

        # Iterate through the rows of the column
        for row in sheet.iter_rows(min_row=start_cell.row, min_col=start_cell.column, max_col=start_cell.column):
            for cell in row:
                if (cell.value is None) or (cell.value == ''):
                    max_row = cell.row - 1
                    break  
            if max_row is not None:
                break  

        if max_row is None:
            max_row = sheet.max_row
              
        table_data = []

        rows = sheet.iter_rows(
            min_row=start_cell.row,
            max_row=max_row,  
            min_col=start_cell.column, 
            max_col=sheet.max_column
        )

        for row in rows:
            row_data = [cell.value for cell in row]
            table_data.append(row_data)

        if first_row_headers:
            header = table_data[0]  
        else:
            header = None

        data = table_data[1:]  
        
        table_df = pd.DataFrame(data=data, columns=header)

        # print(f"Successfully extracted table of size: {table_df.shape} from {filename}")
        
        if capitalize_header:
            table_df.columns = table_df.columns.str.upper()

        columns_to_drop = [None, '', ' ']

        for col in columns_to_drop:
            if col in table_df.columns:
                table_df.drop(columns=[col], inplace=True)

        table_df.replace('', np.nan, inplace=True)

        return table_df

    except Exception as e:
        print(f"Error: {e}")
        return None

def export_dict_to_xlsx(
    data_dict,
    file_path
):

    print("Exporting...")

    start_time = time.time()
    
    writer = pd.ExcelWriter(
        file_path, 
        engine='xlsxwriter'
    )

    for sheet_name, df in data_dict.items():
        if df is not None:
            df.to_excel(writer, sheet_name=sheet_name, index=False)

    writer.close()

    print(f"Finished exporting in: {(time.time() - start_time) / 60:.2f} minutes")

def load_config(data_specs_file, file_type, capitalize_raw_columns=False):

    data_types = None
    new_column_names = None

    data_dictionary_df = pd.read_excel(data_specs_file, sheet_name=file_type)

    used_columns = data_dictionary_df[data_dictionary_df['used_column'] == 1]

    if capitalize_raw_columns:
        used_columns['raw_column_name'] = used_columns['raw_column_name'].str.upper()

    new_column_names = used_columns.set_index('raw_column_name')['model_column_name'].to_dict()
    data_types = used_columns.set_index('raw_column_name')['data_type'].to_dict()

    return {
        'data_types': data_types, 
        'new_column_names': new_column_names
    }

def column_clean_up(data_df):

    cleaned_columns = data_df.columns.str.upper()

    # Trim
    cleaned_columns = cleaned_columns.str.strip()

    # # Convert column names to uppercase and strip whitespace
    # cleaned_columns = data_df.columns.str.upper().str.strip()

    # Remove slashes
    cleaned_columns = cleaned_columns.str.replace('/', '').str.replace('\\', '')

    # Remove brackets
    cleaned_columns = cleaned_columns.str.replace('(', '').str.replace(')', '')

    # Replace spaces with underscores
    cleaned_columns = cleaned_columns.str.replace(r'\s+', '_', regex=True)
    
    # Remove consecutive underscores
    cleaned_columns = cleaned_columns.str.replace(r'_{2,}', '_', regex=True)
    
    # Remove line breaks
    cleaned_columns = cleaned_columns.str.replace(r'[\r\n]+', '', regex=True)
    
    # Replace columns
    data_df.columns = cleaned_columns

    return data_df

def clean_dataframe(df_raw_data, data_specs, column_cleanup=True):

    date_columns = data_specs["date_columns"]
    non_date_columns = data_specs["non_date_columns"]
    new_column_names = data_specs["new_column_names"]
    column_numbers = data_specs["column_numbers"]
    
    df_clean_data = df_raw_data.copy()

    # Filter only used columns
    if column_numbers is not None:
        df_clean_data = df_clean_data[column_numbers.values()]
        df_clean_data.columns = new_column_names.keys()
    else:
        df_clean_data = df_raw_data[new_column_names.keys()].copy()

    # Rename columns
    df_clean_data = df_clean_data.rename(columns=new_column_names)

    # Format date columns
    for column, format_str in date_columns.items():
        df_clean_data[column] = pd.to_datetime(df_clean_data[column], errors='ignore', format=format_str)

    # Format non-date columns
    df_clean_data = df_clean_data.astype(non_date_columns)

    return df_clean_data

