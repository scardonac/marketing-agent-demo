import streamlit as st
import time
from typing import Dict, List, Any, Optional
import json

class ChatInterface:
    """Component for handling chat interface functionality."""
    
    def __init__(self):
        """Initialize the chat interface."""
        self.max_messages = 50  # Limit chat history to prevent memory issues
    
    def display_message(self, message: Dict[str, Any], key: Optional[str] = None):
        """
        Display a single chat message.
        
        Args:
            message: Message dictionary with role and content
            key: Optional unique key for the message
        """
        role = message.get("role", "user")
        content = message.get("content", "")
        
        with st.chat_message(role):
            st.markdown(content)
            
            # Display any additional data if available
            if message.get("has_data_table"):
                self._display_data_table(message.get("data_table"))
            
            if message.get("has_error"):
                st.error(f"Error: {message.get('error_details', 'Unknown error')}")
            
            # Show response metadata for assistant messages
            if role == "assistant" and message.get("metadata"):
                with st.expander("📋 Response Details"):
                    metadata = message["metadata"]
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.text(f"Response Time: {metadata.get('response_time', 'N/A')}")
                        st.text(f"Agent ID: {metadata.get('agent_id', 'N/A')}")
                    
                    with col2:
                        st.text(f"Session ID: {metadata.get('session_id', 'N/A')}")
                        st.text(f"Status: {metadata.get('status', 'N/A')}")
    
    def _display_data_table(self, data_table: Dict[str, Any]):
        """Display a data table from the response."""
        try:
            if data_table and "rows" in data_table:
                st.subheader("📊 Query Results")
                
                # Convert to pandas DataFrame for better display
                import pandas as pd
                
                rows = data_table["rows"]
                if rows:
                    # First row is usually headers
                    headers = rows[0] if rows else []
                    data_rows = rows[1:] if len(rows) > 1 else []
                    
                    if data_rows:
                        df = pd.DataFrame(data_rows, columns=headers)
                        st.dataframe(df, use_container_width=True)
                    else:
                        st.info("Query executed successfully but returned no data rows.")
                else:
                    st.info("No data returned from query.")
        except Exception as e:
            st.error(f"Error displaying data table: {str(e)}")
    
    def get_user_input(self, placeholder: str = "Ask your Bedrock agent...") -> Optional[str]:
        """
        Get user input from the chat input field.
        
        Args:
            placeholder: Placeholder text for the input field
            
        Returns:
            User input string or None if no input
        """
        return st.chat_input(placeholder)
    
    def add_message_to_history(self, role: str, content: str, **kwargs):
        """
        Add a message to the chat history.
        
        Args:
            role: Message role (user, assistant)
            content: Message content
            **kwargs: Additional message metadata
        """
        message = {
            "role": role,
            "content": content,
            "timestamp": time.time(),
            **kwargs
        }
        
        # Initialize messages if not exists
        if 'messages' not in st.session_state:
            st.session_state.messages = []
        
        # Add message to history
        st.session_state.messages.append(message)
        
        # Limit message history to prevent memory issues
        if len(st.session_state.messages) > self.max_messages:
            st.session_state.messages = st.session_state.messages[-self.max_messages:]
    
    def display_chat_history(self):
        """Display the complete chat history."""
        if 'messages' not in st.session_state:
            st.session_state.messages = []
        
        for i, message in enumerate(st.session_state.messages):
            self.display_message(message, key=f"msg_{i}")
    
    def clear_chat_history(self):
        """Clear the chat history."""
        st.session_state.messages = []
        if 'current_response' in st.session_state:
            del st.session_state.current_response
    
    def export_chat_history(self) -> str:
        """
        Export chat history as JSON string.
        
        Returns:
            JSON string of chat history
        """
        if 'messages' not in st.session_state:
            return json.dumps({"messages": []})
        
        export_data = {
            "messages": st.session_state.messages,
            "export_timestamp": time.time(),
            "total_messages": len(st.session_state.messages)
        }
        
        return json.dumps(export_data, indent=2, default=str)
    
    def import_chat_history(self, json_data: str) -> bool:
        """
        Import chat history from JSON string.
        
        Args:
            json_data: JSON string containing chat history
            
        Returns:
            True if successful, False otherwise
        """
        try:
            data = json.loads(json_data)
            if "messages" in data and isinstance(data["messages"], list):
                st.session_state.messages = data["messages"]
                return True
            return False
        except Exception:
            return False
    
    def format_sql_response(self, response_text: str) -> Dict[str, Any]:
        """
        Format SQL query response text into structured data.
        
        Args:
            response_text: Raw response text from the agent
            
        Returns:
            Formatted response with extracted data
        """
        formatted_response = {
            "text": response_text,
            "has_data_table": False,
            "data_table": None
        }
        
        try:
            # Look for markdown table in response
            lines = response_text.split('\n')
            table_lines = []
            in_table = False
            
            for line in lines:
                if '|' in line and ('---' in line or in_table):
                    table_lines.append(line.strip())
                    in_table = True
                elif in_table and '|' not in line:
                    break
            
            if table_lines and len(table_lines) >= 2:
                # Parse the markdown table
                headers = [h.strip() for h in table_lines[0].split('|')[1:-1]]
                
                data_rows = []
                for line in table_lines[2:]:  # Skip separator line
                    if '|' in line:
                        row = [cell.strip() for cell in line.split('|')[1:-1]]
                        if len(row) == len(headers):
                            data_rows.append(row)
                
                if data_rows:
                    formatted_response["has_data_table"] = True
                    formatted_response["data_table"] = {
                        "headers": headers,
                        "rows": [headers] + data_rows,
                        "row_count": len(data_rows)
                    }
        
        except Exception as e:
            # If parsing fails, just return the original text
            formatted_response["parsing_error"] = str(e)
        
        return formatted_response
    
    def display_typing_indicator(self, text: str = "Agent is thinking..."):
        """Display a typing indicator while waiting for response."""
        with st.spinner(text):
            time.sleep(0.1)  # Small delay for visual effect
    
    def display_response_stats(self, response_data: Dict[str, Any]):
        """
        Display statistics about the response.
        
        Args:
            response_data: Response data from the agent
        """
        if response_data.get("status") == "success":
            metadata = response_data.get("metadata", {})
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Status", "✅ Success")
            
            with col2:
                response_time = metadata.get("response_time", "N/A")
                st.metric("Response Time", f"{response_time}ms" if response_time != "N/A" else "N/A")
            
            with col3:
                text_length = len(response_data.get("response_text", ""))
                st.metric("Response Length", f"{text_length} chars")
        
        else:
            st.error(f"❌ Error: {response_data.get('error', 'Unknown error')}")
    
    def suggest_queries(self) -> List[str]:
        """
        Get suggested queries based on context.
        
        Returns:
            List of suggested query strings
        """
        return [
            "Show me the top 10 customers by revenue this year",
            "What are the monthly sales trends for the last 6 months?",
            "List all products with low inventory (less than 100 units)",
            "Show me the order distribution by region",
            "What is the average order value by customer segment?",
            "Find customers who haven't placed orders in the last 90 days",
            "Show me the best performing products by category",
            "What are the peak sales hours during the week?"
        ]