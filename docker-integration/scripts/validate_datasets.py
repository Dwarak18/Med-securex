#!/usr/bin/env python3
"""
Dataset validation script for the new CSV-based dataset structure
"""

import os
import pandas as pd
import sys
from pathlib import Path

def validate_csv_file(csv_path):
    """Validate a single CSV file with robust parsing"""
    df = None
    parsing_method = "standard"
    
    # Try different CSV reading strategies
    try:
        # First try standard reading
        df = pd.read_csv(csv_path, encoding='utf-8')
        parsing_method = "standard"
    except pd.errors.ParserError as e:
        try:
            # Try with error handling for bad lines
            df = pd.read_csv(csv_path, encoding='utf-8', on_bad_lines='skip')
            parsing_method = "skip_bad_lines"
        except Exception:
            try:
                # Try with different quoting and escaping
                df = pd.read_csv(csv_path, encoding='utf-8', quotechar='"', escapechar='\\', on_bad_lines='skip')
                parsing_method = "alternative_quoting"
            except Exception:
                try:
                    # Last resort - try with python engine
                    df = pd.read_csv(csv_path, encoding='utf-8', engine='python', on_bad_lines='skip')
                    parsing_method = "python_engine"
                except Exception as final_e:
                    return False, f"Failed all parsing methods: {final_e}"
    except Exception as e:
        return False, f"Error reading file: {e}"
    
    if df is None or df.empty:
        return False, "File is empty or could not be parsed"
    
    # Check required columns
    required_columns = ['Payload', 'Signature', 'AttackType', 'Severity', 'MITRE', 'Label', 'Description']
    available_columns = df.columns.tolist()
    missing_columns = [col for col in required_columns if col not in available_columns]
    
    if missing_columns:
        return False, f"Missing columns: {missing_columns}. Available: {available_columns}"
    
    # Check for null payloads
    null_payloads = df['Payload'].isnull().sum()
    empty_payloads = (df['Payload'] == '').sum()
    
    issues = []
    if null_payloads > 0:
        issues.append(f"{null_payloads} null payloads")
    if empty_payloads > 0:
        issues.append(f"{empty_payloads} empty payloads")
    
    # Check data quality
    total_records = len(df)
    valid_records = total_records - null_payloads - empty_payloads
    
    status_msg = f"Valid - {valid_records}/{total_records} records"
    if parsing_method != "standard":
        status_msg += f" (parsed with {parsing_method})"
    if issues:
        status_msg += f" - Issues: {', '.join(issues)}"
    
    return True, status_msg

def main():
    datasets_dir = "/workspaces/codespaces-blank/integration/datasets"
    
    if not os.path.exists(datasets_dir):
        print(f"❌ Datasets directory not found: {datasets_dir}")
        sys.exit(1)
    
    csv_files = list(Path(datasets_dir).glob("*.csv"))
    
    if not csv_files:
        print(f"❌ No CSV files found in {datasets_dir}")
        sys.exit(1)
    
    print(f"🔍 Validating {len(csv_files)} CSV files...")
    print("=" * 60)
    
    total_records = 0
    valid_files = 0
    
    for csv_file in sorted(csv_files):
        is_valid, message = validate_csv_file(csv_file)
        
        status = "✅" if is_valid else "❌"
        print(f"{status} {csv_file.name:25} - {message}")
        
        if is_valid:
            valid_files += 1
            # Extract record count from message
            try:
                # Handle different message formats
                if " - Valid - " in message:
                    count_part = message.split(" - Valid - ")[1]
                    if "/" in count_part:
                        records = int(count_part.split("/")[0])
                    else:
                        records = int(count_part.split(" ")[0])
                    total_records += records
            except Exception as e:
                print(f"Debug: Could not parse record count from '{message}': {e}")
    
    print("=" * 60)
    print(f"📊 Summary:")
    print(f"   • Total CSV files: {len(csv_files)}")
    print(f"   • Valid files: {valid_files}")
    print(f"   • Invalid files: {len(csv_files) - valid_files}")
    print(f"   • Total records: {total_records}")
    
    if valid_files == len(csv_files):
        print("🎉 All datasets are valid!")
        sys.exit(0)
    else:
        print("⚠️  Some datasets have issues - check above for details")
        sys.exit(1)

if __name__ == "__main__":
    main()