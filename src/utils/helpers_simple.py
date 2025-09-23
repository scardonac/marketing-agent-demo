import re
import json
from typing import Dict, List, Any, Optional, Union

def simple_format_response(response_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Simple format the response from the Bedrock agent for display without pandas.
    
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
    
    return {
        "text": formatted_text,
        "has_table": False,
        "table_data": None,
        "metadata": response_data.get("metadata", {})
    }

def clean_response_text(text: str) -> str:
    """Clean and format response text."""
    if not text:
        return "No response received."
    
    # Replace escaped newlines with actual newlines
    text = text.replace('\\n', '\n')
    text = text.replace('\\t', '\t')
    
    # Remove excessive whitespace but preserve structure
    lines = text.split('\n')
    cleaned_lines = []
    
    for line in lines:
        cleaned_line = line.strip()
        if cleaned_line:  # Keep non-empty lines
            cleaned_lines.append(cleaned_line)
        elif cleaned_lines and cleaned_lines[-1]:  # Add empty line for spacing
            cleaned_lines.append("")
    
    return '\n'.join(cleaned_lines)

def extract_sql_query_from_trace(trace_data):
    """Extract SQL query from agent trace data with improved parsing for AWS Bedrock Agent format."""
    if not trace_data:
        return None
    
    def search_for_sql_in_structure(data):
        """Recursively search for SQL query in nested structure."""
        if isinstance(data, dict):
            # Check for the new AWS Bedrock Agent format
            # Look for invocationInput -> actionGroupInvocationInput -> requestBody -> content -> application/json
            if 'invocationInput' in data:
                invocation_input = data['invocationInput']
                if isinstance(invocation_input, list) and len(invocation_input) > 0:
                    for invocation in invocation_input:
                        if isinstance(invocation, dict) and 'actionGroupInvocationInput' in invocation:
                            action_group = invocation['actionGroupInvocationInput']
                            if 'requestBody' in action_group:
                                request_body = action_group['requestBody']
                                if 'content' in request_body:
                                    content = request_body['content']
                                    if 'application/json' in content:
                                        json_content = content['application/json']
                                        if isinstance(json_content, list):
                                            for item in json_content:
                                                if isinstance(item, dict) and item.get('name') == 'sql_query':
                                                    sql_query = item.get('value', '')
                                                    if sql_query and any(keyword in sql_query.lower() for keyword in ['select', 'with', 'insert', 'update', 'delete']):
                                                        # Clean up the SQL query
                                                        sql_query = sql_query.replace('\\n', '\n').replace('\\t', '\t')
                                                        return sql_query.strip()
            
            # Check for other SQL-related keys
            for key, value in data.items():
                if key.lower() in ['sql_query', 'query', 'sql'] and isinstance(value, str):
                    if any(keyword in value.lower() for keyword in ['select', 'with', 'insert', 'update', 'delete']):
                        return value.replace('\\n', '\n').replace('\\t', '\t').strip()
                
                # Recursively search in nested structures
                if isinstance(value, (dict, list)):
                    result = search_for_sql_in_structure(value)
                    if result:
                        return result
        
        elif isinstance(data, list):
            for item in data:
                result = search_for_sql_in_structure(item)
                if result:
                    return result
        
        elif isinstance(data, str):
            # Fallback: use regex to find SQL patterns in strings
            if any(keyword in data.lower() for keyword in ['select', 'with', 'insert', 'update', 'delete']):
                sql_patterns = [
                    r'WITH\s+.*?SELECT\s+.*?(?:;|$)',
                    r'SELECT\s+.*?(?:;|$)',
                    r'INSERT\s+.*?(?:;|$)',
                    r'UPDATE\s+.*?(?:;|$)',
                    r'DELETE\s+.*?(?:;|$)'
                ]
                
                for pattern in sql_patterns:
                    match = re.search(pattern, data, re.IGNORECASE | re.DOTALL)
                    if match:
                        sql_query = match.group(0)
                        sql_query = sql_query.replace('\\n', '\n').replace('\\t', '\t')
                        return sql_query.strip()
        
        return None
    
    return search_for_sql_in_structure(trace_data)