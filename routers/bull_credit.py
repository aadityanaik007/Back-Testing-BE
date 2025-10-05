from fastapi import APIRouter, HTTPException
from typing import List, Dict
import pandas as pd
from pathlib import Path

router = APIRouter(
    prefix="/api/bull-credit",
    tags=["bull-credit"]
)

CSV_FILE_PATH = Path("files/bull_credit.csv")

@router.get("/data")
async def get_bull_credit_data() -> Dict:
    """
    Get all data from the bull_credit.csv file
    """
    try:
        # Read the CSV file
        df = pd.read_csv(CSV_FILE_PATH)
        
        # Convert DataFrame to list of dictionaries
        data = df.to_dict(orient="records")
        
        return {
            "success": True,
            "data": data,
            "total_records": len(data)
        }
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Bull credit CSV file not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading bull credit data: {str(e)}")

@router.get("/summary")
async def get_bull_credit_summary() -> Dict:
    """
    Get summary statistics of the bull_credit.csv file
    """
    try:
        # Read the CSV file
        df = pd.read_csv(CSV_FILE_PATH)
        
        # Calculate basic statistics
        summary = {
            "total_records": len(df),
            "columns": df.columns.tolist(),
            "numeric_stats": {}
        }
        
        # Calculate statistics for numeric columns
        numeric_columns = df.select_dtypes(include=['int64', 'float64']).columns
        for col in numeric_columns:
            summary["numeric_stats"][col] = {
                "min": float(df[col].min()),
                "max": float(df[col].max()),
                "mean": float(df[col].mean()),
                "median": float(df[col].median())
            }
            
        return summary
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Bull credit CSV file not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating summary: {str(e)}")