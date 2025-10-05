from fastapi import Query, APIRouter, HTTPException
from typing import Optional, Dict, Any, List
import pandas as pd
from enum import Enum
import os
from pathlib import Path

router = APIRouter(prefix="/banks", tags=["banks"])

class SortOrder(str, Enum):
    ASC = "asc"
    DESC = "desc"

# Global variable to store the DataFrame
app_data = {"df": None, "loaded": False}

def load_ifsc_csv() -> pd.DataFrame:
    """Load and clean IFSC.csv file data"""
    try:
        # Get the current file directory
        current_dir = Path(__file__).parent
        csv_file_path = current_dir / "IFSC.csv"
        
        if not csv_file_path.exists():
            raise FileNotFoundError(f"IFSC.csv not found in {current_dir}")
        
        # Try different encodings
        encodings_to_try = ['utf-8', 'latin-1', 'iso-8859-1', 'cp1252']
        
        df = None
        for encoding in encodings_to_try:
            try:
                df = pd.read_csv(csv_file_path, encoding=encoding)
                print(f"Successfully loaded IFSC.csv with encoding: {encoding}")
                break
            except UnicodeDecodeError:
                continue
        
        if df is None:
            raise Exception("Unable to read IFSC.csv file with any supported encoding")
        
        # Clean column names
        df.columns = df.columns.str.strip().str.replace('"', '')
        
        # Fill NaN values
        df = df.fillna('')
        
        # Clean string columns
        for col in df.select_dtypes(include=['object']).columns:
            df[col] = df[col].astype(str).str.strip().str.replace('"', '')
        
        # Standardize boolean columns for payment methods
        boolean_cols = ['IMPS', 'RTGS', 'NEFT', 'UPI']
        for col in boolean_cols:
            if col in df.columns:
                df[col] = df[col].astype(str).str.upper()
                df[col] = df[col].replace({
                    'TRUE': 'Y', 'FALSE': 'N', '1': 'Y', '0': 'N',
                    'YES': 'Y', 'NO': 'N', '': 'N', 'NAN': 'N'
                })
        
        # Remove completely empty rows and reset index
        df = df.dropna(how='all').reset_index(drop=True)
        
        print(f"Successfully loaded {len(df)} records from IFSC.csv")
        return df
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading IFSC.csv file: {str(e)}")

# Get distinct values for filter fields
@router.get("/filter-options/{field}")
async def get_filter_options(
    field: str,
    search: Optional[str] = Query(None, description="Search term for filtering options"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of options to return")
) -> Dict[str, Any]:
    """Get distinct values for a specific field with optional search filtering"""
    try:
        # Load data if not already loaded
        if not app_data["loaded"] or app_data["df"] is None:
            app_data["df"] = load_ifsc_csv()
            app_data["loaded"] = True
        
        df = app_data["df"]
        
        # Validate field exists
        if field.upper() not in df.columns:
            raise HTTPException(status_code=400, detail=f"Field '{field}' not found in data")
        
        field_upper = field.upper()
        
        # Get distinct non-empty values
        distinct_values = df[field_upper].dropna().astype(str)
        distinct_values = distinct_values[distinct_values.str.strip() != ''].unique()
        
        # Apply search filter if provided
        if search and search.strip():
            search_term = search.lower()
            distinct_values = [val for val in distinct_values if search_term in val.lower()]
        
        # Sort values
        distinct_values = sorted(distinct_values)
        
        # Apply limit
        distinct_values = distinct_values[:limit]
        
        return {
            "field": field,
            "options": [{"value": val, "label": val, "count": len(df[df[field_upper] == val])} for val in distinct_values],
            "total_options": len(distinct_values),
            "search_applied": search is not None and search.strip() != ""
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting filter options: {str(e)}")

# Get multiple filter options at once
@router.get("/filter-options")
async def get_all_filter_options() -> Dict[str, Any]:
    """Get distinct values for all filterable fields"""
    try:
        # Load data if not already loaded
        if not app_data["loaded"] or app_data["df"] is None:
            app_data["df"] = load_ifsc_csv()
            app_data["loaded"] = True
        
        df = app_data["df"]
        
        filterable_fields = ['BANK', 'STATE', 'CITY', 'DISTRICT', 'BRANCH', 'CENTRE']
        filter_options = {}
        
        for field in filterable_fields:
            if field in df.columns:
                distinct_values = df[field].dropna().astype(str)
                distinct_values = distinct_values[distinct_values.str.strip() != ''].unique()
                distinct_values = sorted(distinct_values)[:50]  # Limit to first 50
                
                filter_options[field.lower()] = [
                    {"value": val, "label": val} for val in distinct_values
                ]
        
        return {
            "filter_options": filter_options,
            "message": "Filter options loaded successfully"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting filter options: {str(e)}")

# FIXED: Main endpoint with proper filtering order
@router.get("/")
async def get_banks(
    # Pagination
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(10, ge=1, le=1000, description="Items per page"),
    
    # Text filters - now supporting multiple values
    bank: Optional[List[str]] = Query(None, description="Filter by bank names (multiple allowed)"),
    state: Optional[List[str]] = Query(None, description="Filter by states (multiple allowed)"),
    city: Optional[List[str]] = Query(None, description="Filter by cities (multiple allowed)"),
    district: Optional[List[str]] = Query(None, description="Filter by districts (multiple allowed)"),
    branch: Optional[List[str]] = Query(None, description="Filter by branches (multiple allowed)"),
    centre: Optional[List[str]] = Query(None, description="Filter by centres (multiple allowed)"),
    ifsc: Optional[str] = Query(None, description="Filter by IFSC code"),
    micr: Optional[str] = Query(None, description="Filter by MICR code"),
    address: Optional[str] = Query(None, description="Filter by address"),
    contact: Optional[str] = Query(None, description="Filter by contact"),
    swift: Optional[str] = Query(None, description="Filter by SWIFT code"),
    iso3166: Optional[str] = Query(None, description="Filter by ISO3166 code"),
    
    # Payment method filters
    imps_enabled: Optional[bool] = Query(None, description="Filter by IMPS availability"),
    rtgs_enabled: Optional[bool] = Query(None, description="Filter by RTGS availability"),
    neft_enabled: Optional[bool] = Query(None, description="Filter by NEFT availability"),
    upi_enabled: Optional[bool] = Query(None, description="Filter by UPI availability"),
    
    # Search
    search: Optional[str] = Query(None, description="Search across all text fields"),
    
    # Sorting
    sort_by: Optional[str] = Query("BANK", description="Field to sort by"),
    sort_order: SortOrder = Query(SortOrder.ASC, description="Sort order")
) -> Dict[str, Any]:
    """Get bank data from IFSC.csv with comprehensive filtering, sorting, and searching"""
    
    try:
        # Load IFSC.csv file if not already loaded
        if not app_data["loaded"] or app_data["df"] is None:
            print("Loading IFSC.csv file...")
            app_data["df"] = load_ifsc_csv()
            app_data["loaded"] = True
        
        df = app_data["df"].copy()
        
        # Apply multi-value text filters
        if bank:
            df = df[df['BANK'].isin(bank)]
        
        if state:
            df = df[df['STATE'].isin(state)]
        
        if city:
            df = df[df['CITY'].isin(city)]
        
        if district:
            df = df[df['DISTRICT'].isin(district)]
        
        if branch:
            df = df[df['BRANCH'].isin(branch)]
        
        if centre and 'CENTRE' in df.columns:
            df = df[df['CENTRE'].isin(centre)]
        
        # Apply single-value text filters (for exact matches)
        if ifsc:
            df = df[df['IFSC'].str.contains(ifsc, case=False, na=False)]
        
        if micr and 'MICR' in df.columns:
            df = df[df['MICR'].str.contains(micr, case=False, na=False)]
        
        if address and 'ADDRESS' in df.columns:
            df = df[df['ADDRESS'].str.contains(address, case=False, na=False)]
        
        if contact and 'CONTACT' in df.columns:
            df = df[df['CONTACT'].str.contains(contact, case=False, na=False)]
        
        if swift and 'SWIFT' in df.columns:
            df = df[df['SWIFT'].str.contains(swift, case=False, na=False)]
        
        if iso3166 and 'ISO3166' in df.columns:
            df = df[df['ISO3166'].str.contains(iso3166, case=False, na=False)]
        
        # Apply payment method filters
        if imps_enabled is not None:
            value = 'Y' if imps_enabled else 'N'
            if 'IMPS' in df.columns:
                df = df[df['IMPS'] == value]
        
        if rtgs_enabled is not None:
            value = 'Y' if rtgs_enabled else 'N'
            if 'RTGS' in df.columns:
                df = df[df['RTGS'] == value]
        
        if neft_enabled is not None:
            value = 'Y' if neft_enabled else 'N'
            if 'NEFT' in df.columns:
                df = df[df['NEFT'] == value]
        
        if upi_enabled is not None:
            value = 'Y' if upi_enabled else 'N'
            if 'UPI' in df.columns:
                df = df[df['UPI'] == value]
        
        # FIXED: Apply search across multiple columns on the already filtered DataFrame
        if search:
            search_term = search.lower()
            text_columns = ['BANK', 'BRANCH', 'CITY', 'STATE', 'DISTRICT', 'CENTRE', 
                          'ADDRESS', 'IFSC', 'CONTACT', 'MICR', 'SWIFT', 'ISO3166']
            
            # Create mask from the current filtered DataFrame (not original)
            search_mask = pd.Series([False] * len(df), index=df.index)
            
            for col in text_columns:
                if col in df.columns:
                    # Use the current df index for alignment
                    search_mask |= df[col].astype(str).str.lower().str.contains(search_term, na=False)
            
            # Apply the search mask
            df = df[search_mask]
        
        # Apply sorting
        if sort_by and sort_by in df.columns:
            ascending = sort_order == SortOrder.ASC
            df = df.sort_values(by=sort_by, ascending=ascending)
        
        # Get total count after filtering
        total_records = len(df)
        
        # Apply pagination
        start_idx = (page - 1) * size
        end_idx = start_idx + size
        paginated_df = df.iloc[start_idx:end_idx]
        
        # Convert to records
        data = paginated_df.to_dict('records')
        
        # Calculate pagination info
        total_pages = (total_records + size - 1) // size
        has_next = end_idx < total_records
        has_prev = page > 1
        
        # Get available columns from the loaded data
        available_columns = list(app_data["df"].columns) if app_data["df"] is not None else []
        
        return {
            "file_info": {
                "file_name": "IFSC.csv",
                "file_type": "CSV",
                "total_records_in_file": len(app_data["df"]) if app_data["df"] is not None else 0,
                "columns": available_columns
            },
            "data": data,
            "pagination": {
                "page": page,
                "size": size,
                "total_records": total_records,
                "total_pages": total_pages,
                "has_next": has_next,
                "has_prev": has_prev
            },
            "filters_applied": {
                "bank": bank,
                "state": state,
                "city": city,
                "district": district,
                "branch": branch,
                "centre": centre,
                "ifsc": ifsc,
                "micr": micr,
                "address": address,
                "contact": contact,
                "swift": swift,
                "iso3166": iso3166,
                "imps_enabled": imps_enabled,
                "rtgs_enabled": rtgs_enabled,
                "neft_enabled": neft_enabled,
                "upi_enabled": upi_enabled,
                "search": search,
                "sort_by": sort_by,
                "sort_order": sort_order.value
            },
            "summary": {
                "unique_banks": df['BANK'].nunique() if not df.empty and 'BANK' in df.columns else 0,
                "unique_states": df['STATE'].nunique() if not df.empty and 'STATE' in df.columns else 0,
                "unique_cities": df['CITY'].nunique() if not df.empty and 'CITY' in df.columns else 0,
                "unique_districts": df['DISTRICT'].nunique() if not df.empty and 'DISTRICT' in df.columns else 0,
                "payment_methods": {
                    "imps_enabled": len(df[df['IMPS'] == 'Y']) if not df.empty and 'IMPS' in df.columns else 0,
                    "rtgs_enabled": len(df[df['RTGS'] == 'Y']) if not df.empty and 'RTGS' in df.columns else 0,
                    "neft_enabled": len(df[df['NEFT'] == 'Y']) if not df.empty and 'NEFT' in df.columns else 0,
                    "upi_enabled": len(df[df['UPI'] == 'Y']) if not df.empty and 'UPI' in df.columns else 0,
                }
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}")

# Additional utility endpoint to reload the CSV file
@router.post("/reload")
async def reload_csv():
    """Reload the IFSC.csv file"""
    try:
        app_data["df"] = load_ifsc_csv()
        app_data["loaded"] = True
        return {
            "message": "IFSC.csv reloaded successfully",
            "records": len(app_data["df"]),
            "columns": list(app_data["df"].columns)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reloading file: {str(e)}")
