import re
import json
# import pandas as pd
from typing import Dict, List, Any, Optional, Union
import streamlit as st

def format_response(response_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Format the response from the Bedrock agent for display.
    
    Args:
        response_data: Raw response data from the agent
        
    Returns:
        Formatted response with display-ready content
    """
    if response_data.get("status") == "error":
        return {
            "text": f"❌ Error: {response_data.get('error', 'Unknown error occurred')}",
            "has_error": True,
            "error_details": response_data.get('error')
        }
    
    response_text = response_data.get("response_text", "")
    
    # Clean up the response text
    formatted_text = clean_response_text(response_text)
    
    # Check if response contains a table
    has_table, table_data = extract_table_from_response(formatted_text)
    
    formatted_response = {
        "text": formatted_text,
        "has_table": has_table,
        "table_data": table_data,
        "metadata": response_data.get("metadata", {}),
        "session_id": response_data.get("session_id"),
        "status": response_data.get("status", "success")
    }
    
    return formatted_response

def clean_response_text(text: str) -> str:
    """
    Clean and format response text for better display.
    
    Args:
        text: Raw response text
        
    Returns:
        Cleaned text
    """
    if not text:
        return "No response received."
    
    # Remove excessive whitespace
    text = re.sub(r'\n\s*\n\s*\n', '\n\n', text)
    
    # Clean up markdown table formatting
    lines = text.split('\n')
    cleaned_lines = []
    
    for line in lines:
        # Fix table separator lines
        if re.match(r'^\s*\|[\s\-\|]*\|\s*$', line):
            # This is a table separator line, clean it up
            line = re.sub(r'\s+', '', line)
            if not line.startswith('|'):
                line = '|' + line
            if not line.endswith('|'):
                line = line + '|'
        
        cleaned_lines.append(line)
    
    return '\n'.join(cleaned_lines).strip()

def extract_table_from_response(text: str) -> tuple[bool, Optional[Dict[str, Any]]]:
    """
    Extract table data from response text.
    
    Args:
        text: Response text potentially containing a table
        
    Returns:
        Tuple of (has_table, table_data)
    """
    try:
        lines = text.split('\n')
        table_lines = []
        in_table = False
        
        for line in lines:
            line = line.strip()
            if '|' in line:
                if '---' in line or '═══' in line:
                    # This is a separator line, we're definitely in a table
                    in_table = True
                    continue
                elif '|' in line and (in_table or len([c for c in line if c == '|']) >= 2):
                    table_lines.append(line)
                    in_table = True
            elif in_table and line == '':
                # Empty line might end the table
                break
        
        if len(table_lines) < 2:
            return False, None
        
        # Parse the table
        headers = parse_table_row(table_lines[0])
        rows = [headers]
        
        for line in table_lines[1:]:
            row = parse_table_row(line)
            if len(row) == len(headers):
                rows.append(row)
        
        if len(rows) > 1:
            return True, {
                "headers": headers,
                "rows": rows,
                "row_count": len(rows) - 1
            }
    
    except Exception as e:
        st.error(f"Error parsing table: {str(e)}")
    
    return False, None

def parse_table_row(line: str) -> List[str]:
    """
    Parse a table row from markdown format.
    
    Args:
        line: Table row line
        
    Returns:
        List of cell values
    """
    # Split by | and clean up
    cells = line.split('|')
    
    # Remove leading/trailing empty cells
    if cells and cells[0].strip() == '':
        cells = cells[1:]
    if cells and cells[-1].strip() == '':
        cells = cells[:-1]
    
    # Clean up cell contents
    return [cell.strip() for cell in cells]

def format_number(value: Union[str, int, float]) -> str:
    """
    Format numbers for display.
    
    Args:
        value: Number to format
        
    Returns:
        Formatted number string
    """
    try:
        if isinstance(value, str):
            # Try to parse as number
            try:
                num_value = float(value)
            except ValueError:
                return value
        else:
            num_value = float(value)
        
        # Format based on magnitude
        if abs(num_value) >= 1_000_000:
            return f"{num_value / 1_000_000:.2f}M"
        elif abs(num_value) >= 1_000:
            return f"{num_value / 1_000:.1f}K"
        elif num_value == int(num_value):
            return str(int(num_value))
        else:
            return f"{num_value:.2f}"
    
    except:
        return str(value)

def validate_aws_credentials(access_key: str, secret_key: str, region: str) -> Dict[str, Any]:
    """
    Validate AWS credentials format.
    
    Args:
        access_key: AWS access key
        secret_key: AWS secret key
        region: AWS region
        
    Returns:
        Validation result dictionary
    """
    result = {
        "valid": True,
        "errors": [],
        "warnings": []
    }
    
    # Check access key format
    if access_key and not re.match(r'^AKIA[0-9A-Z]{16}$', access_key):
        result["errors"].append("Access key should start with 'AKIA' and be 20 characters long")
        result["valid"] = False
    
    # Check secret key length
    if secret_key and len(secret_key) != 40:
        result["warnings"].append("Secret key should typically be 40 characters long")
    
    # Check region format
    valid_regions = [
        'us-east-1', 'us-east-2', 'us-west-1', 'us-west-2',
        'eu-west-1', 'eu-west-2', 'eu-central-1',
        'ap-southeast-1', 'ap-southeast-2', 'ap-northeast-1'
    ]
    
    if region and region not in valid_regions:
        result["warnings"].append(f"Region '{region}' is not in the common regions list")
    
    return result

# def export_session_data(messages: List[Dict[str, Any]], response_data: Optional[Dict[str, Any]]) -> str:
#     """
#     Export session data for download.
    
#     Args:
#         messages: Chat messages
#         response_data: Current response data
        
#     Returns:
#         JSON string of session data
#     """
#     export_data = {
#         "export_timestamp": pd.Timestamp.now().isoformat(),
#         "messages": messages,
#         "current_response": response_data,
#         "total_messages": len(messages),
#         "version": "1.0"
#     }
    
#     return json.dumps(export_data, indent=2, default=str)

# def create_summary_statistics(df: pd.DataFrame) -> Dict[str, Any]:
#     """
#     Create summary statistics for a DataFrame.
    
#     Args:
#         df: Pandas DataFrame
        
#     Returns:
#         Dictionary with summary statistics
#     """
#     stats = {
#         "total_rows": len(df),
#         "total_columns": len(df.columns),
#         "numeric_columns": len(df.select_dtypes(include=['number']).columns),
#         "categorical_columns": len(df.select_dtypes(include=['object']).columns),
#         "missing_values": df.isnull().sum().sum(),
#     }
    
#     # Add column-specific stats for numeric columns only
#     numeric_cols = df.select_dtypes(include=['number']).columns
#     if len(numeric_cols) > 0:
#         stats["numeric_summary"] = df[numeric_cols].describe().to_dict()
    
#     return stats

# def clean_table_data(df: pd.DataFrame) -> pd.DataFrame:
#     """
#     Clean and format table data for better display.
    
#     Args:
#         df: Raw DataFrame
        
#     Returns:
#         Cleaned DataFrame
#     """
#     # Make a copy to avoid modifying the original
#     cleaned_df = df.copy()
    
#     # Clean up numeric columns
#     for col in cleaned_df.columns:
#         # Try to convert to numeric if it looks like numbers
#         if cleaned_df[col].dtype == 'object':
#             # Check if this column contains mostly numbers
#             numeric_values = pd.to_numeric(cleaned_df[col], errors='coerce')
#             if not numeric_values.isna().all() and numeric_values.notna().sum() > len(cleaned_df) * 0.7:
#                 cleaned_df[col] = numeric_values
    
#     # Format numeric columns for better display
#     for col in cleaned_df.select_dtypes(include=['number']).columns:
#         if cleaned_df[col].dtype in ['float64', 'float32']:
#             # Round floats to reasonable precision
#             if cleaned_df[col].max() > 1000:
#                 cleaned_df[col] = cleaned_df[col].round(2)
#             else:
#                 cleaned_df[col] = cleaned_df[col].round(4)
    
#     return cleaned_df