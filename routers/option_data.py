from fastapi import APIRouter, HTTPException
from typing import List, Dict
import os
from datetime import datetime
import pandas as pd
from pathlib import Path

router = APIRouter(
    prefix="/api/option-data",
    tags=["option-data"]
)

# Base directory for option data
OPTION_DATA_DIR = Path("../Option-Data")

@router.get("/available-dates")
async def get_available_dates() -> Dict[str, List[str]]:
    """
    Get all available dates for which option data exists.
    Returns a dictionary with years as keys and lists of dates as values.
    """
    try:
        available_dates = {}
        
        # Walk through the Option-Data directory
        for year in os.listdir(OPTION_DATA_DIR):
            year_path = OPTION_DATA_DIR / year
            if not year_path.is_dir():
                continue
                
            available_dates[year] = []
            for month in os.listdir(year_path):
                month_path = year_path / month
                if not month_path.is_dir():
                    continue
                    
                for date_folder in os.listdir(month_path):
                    if date_folder.startswith("GFDLNFO_TICK_OPTIONS_"):
                        # Extract date from folder name (e.g., GFDLNFO_TICK_OPTIONS_01082023)
                        date_str = date_folder.split("_")[-1]
                        formatted_date = datetime.strptime(date_str, "%d%m%Y").strftime("%Y-%m-%d")
                        available_dates[year].append(formatted_date)
                        
            # Sort dates within each year
            available_dates[year].sort()
            
        return available_dates
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching available dates: {str(e)}")

@router.get("/data/{date}")
async def get_option_data(date: str) -> Dict:
    """
    Get option data for a specific date.
    Date should be in YYYY-MM-DD format.
    """
    try:
        # Convert date to the format used in folder names
        date_obj = datetime.strptime(date, "%Y-%m-%d")
        folder_date = date_obj.strftime("%d%m%Y")
        year = date_obj.strftime("%Y")
        month = date_obj.strftime("%b").upper()
        
        # Construct path to the data folder
        data_path = OPTION_DATA_DIR / year / month / f"GFDLNFO_TICK_OPTIONS_{folder_date}"
        
        if not data_path.exists():
            raise HTTPException(status_code=404, detail=f"No data found for date {date}")
            
        # Read all CSV files in the folder and combine them
        all_data = []
        for file in data_path.glob("*.csv"):
            try:
                df = pd.read_csv(file)
                all_data.append(df)
            except Exception as e:
                print(f"Error reading file {file}: {str(e)}")
                continue
                
        if not all_data:
            raise HTTPException(status_code=404, detail=f"No valid data found for date {date}")
            
        # Combine all dataframes
        combined_df = pd.concat(all_data, ignore_index=True)
        
        # Convert DataFrame to dictionary format
        data = combined_df.to_dict(orient="records")
        
        return {
            "date": date,
            "data": data
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching option data: {str(e)}")

@router.get("/summary/{date}")
async def get_option_data_summary(date: str) -> Dict:
    """
    Get a summary of option data for a specific date.
    Includes basic statistics and overview of available data.
    """
    try:
        data = await get_option_data(date)
        if not data["data"]:
            return {
                "date": date,
                "total_records": 0,
                "status": "No data available"
            }
            
        df = pd.DataFrame(data["data"])
        
        return {
            "date": date,
            "total_records": len(df),
            "symbols": df["Symbol"].unique().tolist() if "Symbol" in df.columns else [],
            "strike_prices": sorted(df["Strike_Price"].unique().tolist()) if "Strike_Price" in df.columns else [],
            "option_types": df["Option_Type"].unique().tolist() if "Option_Type" in df.columns else []
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating summary: {str(e)}")