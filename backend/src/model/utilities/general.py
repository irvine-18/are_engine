import json
import os
import itertools
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Union

def expand_grid(data_dict: Dict) -> pd.DataFrame:
    """
    Create an expanded grid from a dictionary of lists.

    Args:
        data_dict (Dict[str, List[Any]]): Dictionary of lists to expand into a grid.

    Returns:
        pd.DataFrame: Expanded grid as a DataFrame.
    """
    rows = itertools.product(*data_dict.values())
    expanded_grid = pd.DataFrame.from_records(rows, columns=data_dict.keys())

    return expanded_grid

def left_join(left_df: pd.DataFrame, right_df: pd.DataFrame, left_on: List, right_on: List) -> pd.DataFrame:

    """
    Perform a left join operation between two DataFrames.

    Args:
        left_df (pd.DataFrame): Left DataFrame.
        right_df (pd.DataFrame): Right DataFrame.
        left_on (List]): Column(s) in the left DataFrame to join on.
        right_on (List]): Column(s) in the right DataFrame to join on.

    Returns:
        pd.DataFrame: Merged DataFrame.
    
    Raises:
        ValueError: If the merged DataFrame has a different length than the left DataFrame.
    """
    if isinstance(left_on, str):
        left_on = [left_on]

    overlapping_columns = set(left_df.columns).intersection(right_df.columns)
    overlapping_columns.difference_update(left_on)

    right_df = right_df.drop(overlapping_columns, axis=1)
    merged_df = pd.merge(left_df, right_df, left_on=left_on, right_on=right_on, how='left')

    if len(merged_df) != len(left_df):
        raise ValueError("Merged DataFrame has a different length than the left DataFrame.")

    return merged_df

def add_months_to_date(date_column: pd.Series, months_column: pd.Series) -> pd.Series:
    
    """
    Add months to a date column.

    Args:
        date_column (pd.Series): Series containing dates.
        months_column (pd.Series): Series containing the number of months to add.

    Returns:
        pd.Timestamp: Series containing the result dates.
    """

    result_date = (date_column.dt.to_period("M") + months_column).dt.to_timestamp()
    
    return result_date

def months_between_dates(date_start: pd.Series, date_end: pd.Series) -> pd.Series:
    
    """
    Calculate the number of months between two date series.

    Args:
        date_start (pd.Series): Series containing start dates.
        date_end (pd.Series): Series containing end dates.

    Returns:
        pd.Series: Series containing the number of months between dates.
    """
    months_between_dates = (date_end.dt.year - date_start.dt.year) * 12 + (
        date_end.dt.month - date_start.dt.month
    )
    
    return months_between_dates

def calc_years_360(date_start: pd.Series, date_end: pd.Series) -> pd.Series:
    """
    Calculate the number of years using the 360-day convention between two date series.

    Args:
        date_start (pd.Series): Series containing start dates.
        date_end (pd.Series): Series containing end dates.

    Returns:
        pd.Series: Series containing the calculated years based on the 360-day convention.
    """
    date_end2 = pd.Series(
        np.where(
            (date_end.dt.day == 31) & date_start.dt.day.isin([30, 31]),
            date_end.apply(lambda x: x.replace(day=30)),
            date_end,
        )
    )

    date_start2 = pd.Series(
        np.where(
            date_start.dt.day == 31,
            date_start.apply(lambda x: x.replace(day=30)),
            date_start,
        )
    )

    days360 = (
        360 * (date_end2.dt.year - date_start2.dt.year)
        + 30 * (date_end2.dt.month - date_start2.dt.month)
        + (date_end2.dt.day - date_start2.dt.day)
    )
    years360 = (days360 / 360.0).round(5)
    return years360

def get_file_paths_from_folder(input_folder_path: str, json_output_path: str=None):

    files = {}

    for dirpath, _, filenames in os.walk(input_folder_path):
        subfolder = os.path.relpath(dirpath, input_folder_path)
        
        # Skip the root directory itself
        if subfolder == '.':
            continue
        
        files_list = []
        for filename in filenames:
            file_path = os.path.join(dirpath, filename)
            files_list.append(file_path)
        
        files[subfolder] = files_list

    if json_output_path:
        with open(json_output_path, "w") as outfile:
            json.dump(files, outfile)   

    return files

def text_to_months(text):
    if 'Y' in text:
        return int(text[:-1]) * 12
    elif 'M' in text:
        return int(text[:-1])
    else:
        return None