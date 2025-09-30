import pandas as pd
import csv
import json
import sys
from typing import Dict, List, Optional, Union
import os

class BankCsvProcessor:
    def __init__(self):
        self.expected_columns = [
            'BANK', 'IFSC', 'BRANCH', 'CENTRE', 'DISTRICT', 'STATE',
            'ADDRESS', 'CONTACT', 'IMPS', 'RTGS', 'CITY', 'ISO3166',
            'NEFT', 'MICR', 'UPI', 'SWIFT'
        ]
    
    def read_csv_file(self, file_path: str, encoding: str = 'utf-8') -> pd.DataFrame:
        """
        Read CSV file and return DataFrame with bank data
        
        Args:
            file_path: Path to the CSV file
            encoding: File encoding (default: utf-8)
        
        Returns:
            pandas DataFrame with bank data
        """
        try:
            # Try different encodings if utf-8 fails
            encodings_to_try = [encoding, 'utf-8', 'latin-1', 'iso-8859-1', 'cp1252']
            
            df = None
            for enc in encodings_to_try:
                try:
                    df = pd.read_csv(file_path, encoding=enc)
                    print(f"Successfully read file with encoding: {enc}")
                    break
                except UnicodeDecodeError:
                    continue
            
            if df is None:
                raise Exception("Unable to read file with any supported encoding")
            
            # Clean column names (remove extra spaces, quotes)
            df.columns = df.columns.str.strip().str.replace('"', '')
            
            # Validate columns
            file_columns = df.columns.tolist()
            missing_columns = [col for col in self.expected_columns if col not in file_columns]
            if missing_columns:
                print(f"Warning: Missing columns: {missing_columns}")
            
            # Ensure all expected columns exist (add with NaN if missing)
            for col in self.expected_columns:
                if col not in df.columns:
                    df[col] = pd.NA
            
            # Reorder columns to match expected order
            available_expected_cols = [col for col in self.expected_columns if col in df.columns]
            other_cols = [col for col in df.columns if col not in self.expected_columns]
            df = df[available_expected_cols + other_cols]
            
            # Clean data
            df = df.dropna(how='all')  # Remove completely empty rows
            df = df.fillna('')  # Replace NaN with empty strings
            
            # Clean string columns
            for col in df.select_dtypes(include=['object']).columns:
                df[col] = df[col].astype(str).str.strip().str.replace('"', '')
            
            print(f"Successfully loaded {len(df)} records from {file_path}")
            return df
            
        except FileNotFoundError:
            raise FileNotFoundError(f"CSV file not found: {file_path}")
        except Exception as e:
            raise Exception(f"Error reading CSV file: {str(e)}")
    
    def validate_bank_data(self, df: pd.DataFrame) -> Dict[str, Union[int, List]]:
        """
        Validate bank data and return validation report
        
        Args:
            df: DataFrame with bank data
        
        Returns:
            Dictionary with validation results
        """
        validation_report = {
            'total_records': len(df),
            'missing_ifsc': [],
            'invalid_ifsc_format': [],
            'missing_bank_name': [],
            'missing_branch': [],
            'invalid_micr': [],
            'empty_rows': []
        }
        
        for index, row in df.iterrows():
            # Check for completely empty rows
            if row.isna().all() or all(str(val).strip() == '' for val in row):
                validation_report['empty_rows'].append(index)
                continue
            
            # Check for missing IFSC codes
            if pd.isna(row['IFSC']) or str(row['IFSC']).strip() == '':
                validation_report['missing_ifsc'].append(index)
            
            # Check IFSC format (should be 11 characters)
            elif len(str(row['IFSC']).strip()) != 11:
                validation_report['invalid_ifsc_format'].append({
                    'index': index,
                    'ifsc': str(row['IFSC']).strip()
                })
            
            # Check for missing bank name
            if pd.isna(row['BANK']) or str(row['BANK']).strip() == '':
                validation_report['missing_bank_name'].append(index)
            
            # Check for missing branch
            if pd.isna(row['BRANCH']) or str(row['BRANCH']).strip() == '':
                validation_report['missing_branch'].append(index)
            
            # Check MICR code format (should be 9 digits)
            micr = str(row['MICR']).strip()
            if micr and micr != '' and (not micr.isdigit() or len(micr) != 9):
                validation_report['invalid_micr'].append({
                    'index': index,
                    'micr': micr
                })
        
        return validation_report
    
    def filter_data(self, df: pd.DataFrame, filters: Dict) -> pd.DataFrame:
        """
        Filter bank data based on provided criteria
        
        Args:
            df: DataFrame with bank data
            filters: Dictionary with filter criteria
        
        Returns:
            Filtered DataFrame
        """
        filtered_df = df.copy()
        
        if 'state' in filters and filters['state']:
            filtered_df = filtered_df[filtered_df['STATE'].str.contains(filters['state'], case=False, na=False)]
        
        if 'city' in filters and filters['city']:
            filtered_df = filtered_df[filtered_df['CITY'].str.contains(filters['city'], case=False, na=False)]
        
        if 'bank' in filters and filters['bank']:
            filtered_df = filtered_df[filtered_df['BANK'].str.contains(filters['bank'], case=False, na=False)]
        
        if 'district' in filters and filters['district']:
            filtered_df = filtered_df[filtered_df['DISTRICT'].str.contains(filters['district'], case=False, na=False)]
        
        # Payment method filters
        for method in ['imps', 'rtgs', 'neft', 'upi']:
            if method in filters and filters[method]:
                col_name = method.upper()
                filtered_df = filtered_df[filtered_df[col_name].str.upper().isin(['Y', 'YES', 'TRUE', '1'])]
        
        return filtered_df
    
    def search_banks(self, df: pd.DataFrame, search_term: str) -> pd.DataFrame:
        """
        Search for banks matching the search term across all text columns
        
        Args:
            df: DataFrame with bank data
            search_term: Search term to look for
        
        Returns:
            Filtered DataFrame with matching records
        """
        if not search_term:
            return df
        
        search_term = search_term.lower()
        text_columns = ['BANK', 'BRANCH', 'CITY', 'STATE', 'DISTRICT', 'ADDRESS']
        
        mask = pd.Series([False] * len(df))
        for col in text_columns:
            if col in df.columns:
                mask |= df[col].astype(str).str.lower().str.contains(search_term, na=False)
        
        return df[mask]
    
    def export_to_csv(self, df: pd.DataFrame, output_path: str) -> None:
        """Export DataFrame to CSV"""
        df.to_csv(output_path, index=False, encoding='utf-8')
        print(f"Data exported to: {output_path}")
    
    def export_to_json(self, df: pd.DataFrame, output_path: str) -> None:
        """Export DataFrame to JSON"""
        df.to_json(output_path, orient='records', indent=2)
        print(f"Data exported to: {output_path}")
    
    def get_summary_stats(self, df: pd.DataFrame) -> Dict:
        """Get summary statistics of the bank data"""
        stats = {
            'total_records': len(df),
            'total_banks': df['BANK'].nunique() if 'BANK' in df.columns else 0,
            'total_states': df['STATE'].nunique() if 'STATE' in df.columns else 0,
            'total_cities': df['CITY'].nunique() if 'CITY' in df.columns else 0,
            'total_districts': df['DISTRICT'].nunique() if 'DISTRICT' in df.columns else 0,
        }
        
        # Payment method statistics
        for method in ['IMPS', 'RTGS', 'NEFT', 'UPI']:
            if method in df.columns:
                enabled_count = len(df[df[method].astype(str).str.upper().isin(['Y', 'YES', 'TRUE', '1'])])
                stats[f'{method.lower()}_enabled'] = enabled_count
        
        # Top counts
        if 'BANK' in df.columns:
            stats['top_5_banks'] = df['BANK'].value_counts().head().to_dict()
        if 'STATE' in df.columns:
            stats['top_5_states'] = df['STATE'].value_counts().head().to_dict()
        
        return stats

    def convert_to_standard_format(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Convert data to standard format and clean common issues
        """
        df_clean = df.copy()
        
        # Standardize boolean columns
        boolean_cols = ['IMPS', 'RTGS', 'NEFT', 'UPI']
        for col in boolean_cols:
            if col in df_clean.columns:
                df_clean[col] = df_clean[col].astype(str).str.upper()
                df_clean[col] = df_clean[col].replace({
                    'TRUE': 'Y', 'FALSE': 'N', '1': 'Y', '0': 'N',
                    'YES': 'Y', 'NO': 'N', '': 'N', 'NAN': 'N'
                })
        
        # Clean IFSC codes
        if 'IFSC' in df_clean.columns:
            df_clean['IFSC'] = df_clean['IFSC'].astype(str).str.upper().str.strip()
        
        # Clean and standardize text fields
        text_cols = ['BANK', 'BRANCH', 'CITY', 'STATE', 'DISTRICT']
        for col in text_cols:
            if col in df_clean.columns:
                df_clean[col] = df_clean[col].astype(str).str.title().str.strip()
        
        return df_clean

# Example usage and main function
def main():
    processor = BankCsvProcessor()
    
    try:
        # Read the CSV file
        file_path = "IFSC.csv"  # Replace with your file path
        
        if not os.path.exists(file_path):
            print(f"File not found: {file_path}")
            print("Please ensure the CSV file exists and update the file_path variable.")
            return
        
        df = processor.read_csv_file(file_path)
        
        # Convert to standard format
        df = processor.convert_to_standard_format(df)
        
        # Display basic info
        print(f"\n{'='*50}")
        print(f"BANK DATA ANALYSIS REPORT")
        print(f"{'='*50}")
        print(f"Loaded: {len(df)} bank records")
        print(f"Columns: {list(df.columns)}")
        
        # Validate data
        validation_report = processor.validate_bank_data(df)
        print(f"\n{'='*30}")
        print(f"VALIDATION REPORT")
        print(f"{'='*30}")
        print(f"Total records: {validation_report['total_records']}")
        print(f"Missing IFSC: {len(validation_report['missing_ifsc'])}")
        print(f"Invalid IFSC format: {len(validation_report['invalid_ifsc_format'])}")
        print(f"Missing bank names: {len(validation_report['missing_bank_name'])}")
        print(f"Invalid MICR codes: {len(validation_report['invalid_micr'])}")
        
        # Get summary statistics
        stats = processor.get_summary_stats(df)
        print(f"\n{'='*30}")
        print(f"SUMMARY STATISTICS")
        print(f"{'='*30}")
        print(f"Total Banks: {stats['total_banks']}")
        print(f"Total States: {stats['total_states']}")
        print(f"Total Cities: {stats['total_cities']}")
        if 'imps_enabled' in stats:
            print(f"IMPS Enabled: {stats['imps_enabled']}")
        if 'upi_enabled' in stats:
            print(f"UPI Enabled: {stats['upi_enabled']}")
        
        # Search example
        search_results = processor.search_banks(df, "State Bank")
        print(f"\nSearch results for 'State Bank': {len(search_results)} records")
        
        # Filter example - banks in Maharashtra with UPI enabled
        filters = {
            'state': 'Maharashtra',
            'upi': True
        }
        filtered_df = processor.filter_data(df, filters)
        print(f"Filtered data (Maharashtra + UPI): {len(filtered_df)} records")
        
        # Export examples
        processor.export_to_csv(df, "bank_data_processed.csv")
        if len(filtered_df) > 0:
            processor.export_to_json(filtered_df, "maharashtra_upi_banks.json")
        
        # Display sample data
        print(f"\n{'='*30}")
        print(f"SAMPLE DATA (First 5 records)")
        print(f"{'='*30}")
        display_cols = ['BANK', 'IFSC', 'BRANCH', 'CITY', 'STATE', 'UPI', 'ADDRESS', 'CONTACT' , 'CITY','MICR']
        available_cols = [col for col in display_cols if col in df.columns]
        print(df[available_cols].head().to_string())
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
