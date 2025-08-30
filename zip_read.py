import zipfile
import os
from datetime import datetime
import pandas as pd

# base_folder = r"D:\2023"

# def fetch_csv_from_zip(target_csv_name, date_str, symbol):
#     # print (target_csv_name, date_str)
#     # Date and folder details
#     date = datetime.strptime(date_str, "%d/%m/%Y")
#     year_folder = str(date.year)
#     month_folder = date.strftime("%b_%Y").upper()  # e.g., "JAN_2024"
#     date_folder = f"GFDLNFO_TICK_OPTIONS_{date.strftime('%d%m%Y')}"  # e.g., "GFDLNFO_TICK_OPTIONS_30012024"

#     # Construct the path to the year and month ZIP file
#     month_zip_path = os.path.join(base_folder, year_folder, f"{month_folder}.zip")

#     # Check if the ZIP file for the month exists
#     if not os.path.exists(month_zip_path):
#         return None

#     with zipfile.ZipFile(month_zip_path, 'r') as outer_zip:
#         inner_zip_file = next((file for file in outer_zip.namelist() if file.startswith(date_folder) and file.endswith('.zip')), None)
#         if inner_zip_file:
#             with outer_zip.open(inner_zip_file) as inner_zip_file_obj:
#                 with zipfile.ZipFile(inner_zip_file_obj) as inner_zip:
#                     target_csv_path = f"{date_folder}/Options/{target_csv_name}.NFO.csv"
#                     csv_files = [file for file in inner_zip.namelist() if file.startswith(date_folder) and file.endswith('.csv') and target_csv_path in file]
#                     # print (csv_files)
#                     # print (target_csv_path)
#                     if target_csv_path in csv_files:
#                         try:
#                             with inner_zip.open(target_csv_path) as f:
#                                 df = pd.read_csv(f)
#                                 df.rename(columns = {'Time':'time'}, inplace = True)
#                                 return df  # Return the DataFrame
#                         except Exception as e:
#                             print(f"Error reading CSV: {e}")  # Log the error if needed

#     return None  

from functools import lru_cache

base_folder = r"D:\FNODATA"
zip_cache = {}  # Cache for opened ZIP files
inner_zip_cache = {}  # Cache for inner ZIP file names
csv_cache = {}  # Cache for CSV DataFrames

def get_monthly_zip(year, month_folder):
    """ Open the monthly ZIP file and cache it """
    month_zip_path = os.path.join(base_folder, "NIFTY"+year, f"{month_folder}.zip")
    print("======",month_zip_path)
    if month_zip_path not in zip_cache:
        if not os.path.exists(month_zip_path):
            return None
        zip_cache[month_zip_path] = zipfile.ZipFile(month_zip_path, 'r')
    
    return zip_cache[month_zip_path]

def get_inner_zip_name(outer_zip, date_folder):
    """ Cache inner ZIP file names to reduce redundant lookups """
    if date_folder in inner_zip_cache:
        return inner_zip_cache[date_folder]

    inner_zip_file = next((file for file in outer_zip.namelist() if file.startswith(date_folder) and file.endswith('.zip')), None)
    
    if inner_zip_file:
        inner_zip_cache[date_folder] = inner_zip_file
    return inner_zip_file

def fetch_csv_from_zip(target_csv_name, date_str, symbol):
    """ Fetch CSV from ZIP with caching optimizations """
    # Parse date
    date = datetime.strptime(date_str, "%d/%m/%Y")
    year_folder = str(date.year)
    month_folder = date.strftime("%b_%Y").upper()  # e.g., "JAN_2024"
    date_folder = f"GFDLNFO_TICK_OPTIONS_{date.strftime('%d%m%Y')}"  # e.g., "GFDLNFO_TICK_OPTIONS_30012024"

    # Check cache for already extracted CSV
    cache_key = f"{date_folder}_{target_csv_name}"
    if cache_key in csv_cache:
        return csv_cache[cache_key]

    # Open monthly ZIP file
    outer_zip = get_monthly_zip(year_folder, month_folder)
    if not outer_zip:
        return None

    # Get inner ZIP file name
    inner_zip_file = get_inner_zip_name(outer_zip, date_folder)
    if not inner_zip_file:
        return None

    # Open inner ZIP file
    with outer_zip.open(inner_zip_file) as inner_zip_file_obj:
        with zipfile.ZipFile(inner_zip_file_obj) as inner_zip:
            target_csv_path = f"{date_folder}/Options/{target_csv_name}.NFO.csv"
            if target_csv_path in inner_zip.namelist():
                try:
                    with inner_zip.open(target_csv_path) as f:
                        df = pd.read_csv(f)
                        df.rename(columns={'Time': 'time'}, inplace=True)
                        csv_cache[cache_key] = df  # Store in cache
                        return df
                except Exception as e:
                    print(f"Error reading CSV: {e}")

    return None


def create_symbol_format(data,date_str):
    expiry_date = datetime.strptime(data['expiry'], '%Y-%m-%d')
    date_str = datetime.strptime(date_str, '%Y-%m-%d')
    formatted_expiry = date_str.strftime('%d/%m/%Y')
    formatted_symbol = f"{data['name']}{expiry_date.strftime('%d%b%y').upper()}{data['strike']}{data['instrument_type']}"
    return formatted_symbol, formatted_expiry,data['name']

# print(fetch_csv_from_zip('NIFTY05DEC2424400CE','05/12/2024','NIFTY'))

# Example usage
# print(fetch_csv_from_zip('NIFTY05DEC2424250PE', '02/12/2024', 'NIFTY'))





# print (fetch_csv_from_zip('NIFTY07NOV2424150CE', '04/11/2024', 'NIFTY'))









# fetch_csv_from_zip('BANKNIFTY24N1351800PE', '', symbol)

# Set the base folder path

# symbol = "NIFTY"
# # #  30/01/2024 
# df = fetch_csv_from_zip('NIFTY29FEB2421800PE', '30/01/2024', symbol)
# print(df)