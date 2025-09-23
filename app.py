import streamlit as st
import sys
import os
import time
from typing import Dict, List, Any
# import json
# import pandas as pd

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.services.aws_agent_client import BedrockAgentClient
from src.utils.helpers import format_response

# Try to load configuration from config.py
try:
    import config
    DEFAULT_AGENT_ID = getattr(config, 'BEDROCK_AGENT_ID', '')
    DEFAULT_AGENT_ALIAS_ID = getattr(config, 'BEDROCK_AGENT_ALIAS_ID', 'TSTALIASID')
    DEFAULT_REGION = getattr(config, 'AWS_REGION', 'us-east-1')
    DEFAULT_ACCESS_KEY = getattr(config, 'AWS_ACCESS_KEY_ID', '')
    DEFAULT_SECRET_KEY = getattr(config, 'AWS_SECRET_ACCESS_KEY', '')
    DEFAULT_PROFILE = getattr(config, 'AWS_PROFILE', '')
except ImportError:
    # No config file found, try environment variables
    DEFAULT_AGENT_ID = os.getenv('BEDROCK_AGENT_ID', '')
    DEFAULT_AGENT_ALIAS_ID = os.getenv('BEDROCK_AGENT_ALIAS_ID', 'TSTALIASID')
    DEFAULT_REGION = os.getenv('AWS_DEFAULT_REGION', 'us-east-1')
    DEFAULT_ACCESS_KEY = os.getenv('AWS_ACCESS_KEY_ID', '')
    DEFAULT_SECRET_KEY = os.getenv('AWS_SECRET_ACCESS_KEY', '')
    DEFAULT_PROFILE = os.getenv('AWS_PROFILE', '')

# Automatically use environment variables if available
AUTO_INITIALIZE = bool(DEFAULT_AGENT_ID and DEFAULT_AGENT_ALIAS_ID and 
                      (DEFAULT_ACCESS_KEY and DEFAULT_SECRET_KEY or DEFAULT_PROFILE))

# Page configuration
st.set_page_config(
    page_title="🤖 Marketing Performance AI Agent",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': None,
        'Report a bug': None,
        'About': "# Marketing Performance AI Agent\nPowered by AWS Bedrock & Athena\n\nAsk intelligent questions about your marketing data and get instant insights!"
    }
)

# Custom CSS
try:
    css_path = os.path.join(os.path.dirname(__file__), 'static', 'css', 'styles.css')
    with open(css_path, 'r') as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
except FileNotFoundError:
    st.warning("Custom CSS file not found. Using default styling.")

# Initialize session state
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'agent_client' not in st.session_state:
    st.session_state.agent_client = None
if 'current_response' not in st.session_state:
    st.session_state.current_response = None
if 'examples_visible' not in st.session_state:
    st.session_state.examples_visible = False
if 'session_id' not in st.session_state:
    import uuid
    st.session_state.session_id = f"streamlit-chat-{uuid.uuid4().hex[:8]}"

def initialize_agent_client():
    """Initialize the Bedrock Agent client with user credentials."""
    try:
        agent_client = BedrockAgentClient(
            agent_id=st.session_state.get('agent_id'),
            agent_alias_id=st.session_state.get('agent_alias_id'),
            region=st.session_state.get('region', 'us-east-1'),
            aws_access_key_id=st.session_state.get('aws_access_key_id'),
            aws_secret_access_key=st.session_state.get('aws_secret_access_key'),
            aws_profile=st.session_state.get('aws_profile')
        )
        st.session_state.agent_client = agent_client
        return True
    except Exception as e:
        st.error(f"Failed to initialize agent client: {str(e)}")
        return False

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
                import re
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

def main():
    """Main application function."""
    
    # Auto-initialize if environment variables are available
    if AUTO_INITIALIZE and not st.session_state.agent_client:
        st.session_state.agent_id = DEFAULT_AGENT_ID
        st.session_state.agent_alias_id = DEFAULT_AGENT_ALIAS_ID
        st.session_state.region = DEFAULT_REGION
        st.session_state.aws_access_key_id = DEFAULT_ACCESS_KEY
        st.session_state.aws_secret_access_key = DEFAULT_SECRET_KEY
        st.session_state.aws_profile = DEFAULT_PROFILE
        initialize_agent_client()
    
    # Title and description with better typography
    st.markdown('<div class="text-center">', unsafe_allow_html=True)
    st.title("🤖 Marketing Performance Analyst")
    st.markdown('<p class="subtitle">Intelligent Data Analysis for Marketing Performance</p>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Sidebar for configuration
    with st.sidebar:
        st.header("")
        
        # Example Questions
        with st.expander("📋 Example Questions", expanded=True):
            st.markdown("""
**Quick Start Examples:**

• Which creatives generate the fastest engagement in the last year?

• Compare Ford OEM vs CSP performance this year

• Show the top 5 creatives by conversion rate this year

• What was the total number of engagements for Ford EXP in 2024?

• Which creative had the highest engagement rate in the last 6 months?

• Best cost per sale by creative in the past 12 months

• Top creatives by ROI this year
            """)
        
        # Tips for Better Results
        with st.expander("💡 Tips for Better Results", expanded=False):
            st.markdown("""
**For statistical reliability:**

• Specify minimum volume (e.g., "with at least 500 mails sent")

• Use time periods: "this year", "last 6 months"

**For specific formats:**

• "Show as a table" for tabular data

• "Include creative names and codes"

• "Group by policy type"

**Key metrics available:**

• Engagement rate, conversion rate, ROI

• Cost per sale, sales per mail

• Days to engage, days to sale
            """)
        
#         # System Status
#         with st.expander("⚙️ System Status", expanded=False):
#             st.markdown("""
# **Timeout Protection:**
# ✅ Extended timeouts (2 minutes)
# ✅ Automatic retry logic
# ✅ Connection error handling

# **Performance Tips:**
# • Break complex questions into parts
# • Use specific time periods
# • Try simpler wording if timeouts occur
#             """)
        
        # Session Info for debugging
        with st.expander("🔧 Debug Info", expanded=False):
            st.markdown(f"**Session ID:** `{st.session_state.session_id[:16]}...`")
            st.caption("This session ID maintains conversation context. All your questions in this session are connected.")
            if st.session_state.agent_client:
                st.success("✅ Agent Connected")
            else:
                st.error("❌ Agent Not Connected")


    # Enhanced question input area
    st.markdown("---")
    st.markdown("### 💬 Ask Your Marketing Questions")
    
    # Session context info
    # if st.session_state.messages:
    #     st.info("💡 **Conversation Context**: I remember our previous discussion! You can ask follow-up questions like 'show me the SQL query' or 'what about last month?' and I'll understand the context.")
    
    # Create columns for better layout
    col1, col2 = st.columns([5, 1])
    
    with col1:
        # Enhanced chat input with better placeholder
        placeholder_text = "Type your marketing question here... (e.g., 'Compare Ford OEM vs CSP performance this year')"
        prompt = st.chat_input(
            placeholder=placeholder_text,
            key="main_chat_input",
            max_chars=1000
        )
    
    
    if prompt:
        if not st.session_state.agent_client:
            st.error("⚠️ Please configure and connect to your Bedrock Agent first!")
            with st.expander("🔧 How to Connect"):
                st.markdown("""
                1. **Open the sidebar** (← left panel)
                2. **Enter your AWS configuration** (Agent ID, Region, etc.)
                3. **Click 'Save Configuration'** to connect
                4. **Come back here** and ask your question!
                """)
            st.stop()
        
        # Add user message to chat
        st.session_state.messages.append({
            "role": "user", 
            "content": prompt,
            "timestamp": time.time()
        })
        
        # Enhanced loading experience
        with st.spinner("🔍 Analyzing your question..."):
            # Create a placeholder for live updates
            status_placeholder = st.empty()
            progress_bar = st.progress(0)
            
            # Simulate progress for better UX
            import time as time_module
            status_placeholder.info("🧠 Processing your question...")
            progress_bar.progress(25)
            time_module.sleep(0.5)
            
            status_placeholder.info("🔗 Connecting to data sources...")
            progress_bar.progress(50)
            time_module.sleep(0.5)
            
            status_placeholder.info("📊 Executing analysis...")
            progress_bar.progress(75)
            
            try:
                # Pass the session ID to maintain conversation context
                status_placeholder.info("🤖 Sending request to AWS Bedrock Agent...")
                progress_bar.progress(85)
                
                response = st.session_state.agent_client.send_message(
                    prompt, 
                    session_id=st.session_state.session_id
                )
                
                progress_bar.progress(100)
                status_placeholder.success("✅ Analysis complete!")
                time_module.sleep(0.5)
                
                # Clear the loading indicators
                status_placeholder.empty()
                progress_bar.empty()
                
                # Format and display response
                formatted_response = format_response(response)
                
                # Store current response for visualization
                st.session_state.current_response = response
                
                # Add assistant message to chat
                message_data = {
                    "role": "assistant", 
                    "content": formatted_response["text"],
                    "raw_response": response,
                    "timestamp": time.time(),
                    "has_table": formatted_response.get("has_table", False),
                    "table_data": formatted_response.get("table_data", None)
                }
                
                st.session_state.messages.append(message_data)
                st.rerun()
                
            except Exception as e:
                progress_bar.empty()
                status_placeholder.empty()
                
                error_str = str(e)
                
                # Check for specific timeout errors
                if "read timed out" in error_str.lower() or "timeout" in error_str.lower():
                    st.error("⏰ **Request Timed Out** - The AWS Bedrock Agent took too long to respond.")
                    
                    with st.expander("🔧 Timeout Solutions", expanded=True):
                        st.markdown("""
                        **Why this happens:**
                        - Complex queries can take longer to process
                        - Network connectivity issues
                        - High load on AWS Bedrock service
                        
                        **What to try:**
                        1. **Simplify your question** - break complex queries into smaller parts
                        2. **Try again** - temporary network issues often resolve quickly
                        3. **Rephrase your question** - sometimes simpler wording helps
                        4. **Check your connection** - ensure stable internet connectivity
                        
                        **Technical details:** The system now retries failed requests automatically with extended timeouts (up to 2 minutes).
                        """)
                elif "connection" in error_str.lower():
                    st.error("🌐 **Connection Error** - Unable to reach AWS Bedrock service.")
                    
                    with st.expander("🔧 Connection Solutions"):
                        st.markdown("""
                        **Possible causes:**
                        - Internet connectivity issues
                        - AWS service temporary unavailability
                        - Firewall or proxy blocking requests
                        
                        **Solutions:**
                        1. Check your internet connection
                        2. Try again in a few moments
                        3. Verify AWS region is accessible from your location
                        """)
                else:
                    error_msg = f"❌ Error: {error_str}"
                    st.error(error_msg)
                    
                    # Show helpful error guidance
                    with st.expander("🔧 General Troubleshooting"):
                        st.markdown("""
                        **Common solutions:**
                        - Check your AWS credentials in the sidebar
                        - Verify your Agent ID and Alias ID are correct
                        - Ensure your AWS region is properly set
                        - Try rephrasing your question
                        - Check if your AWS account has Bedrock access
                        """)
                
                st.session_state.messages.append({
                    "role": "assistant", 
                    "content": error_msg,
                    "timestamp": time.time()
                })
                st.rerun()
    
    # Enhanced conversation history display
    if not st.session_state.messages:
        # Simple welcome message
        st.markdown("---")
        st.markdown("""
        <div style="text-align: center; padding: 2rem; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 10px; color: white; margin: 1rem 0;">
            <h2>👋 Welcome to Marketing Analytics!</h2>
            <p style="margin: 0; font-size: 1.1rem;">I'm your AI-powered marketing performance analyst. Ask me anything about campaigns, conversions, engagement rates, and performance metrics.</p>
            <p style="margin: 0.5rem 0 0 0; font-size: 0.9rem; opacity: 0.9;">� Check the sidebar for example questions and tips!</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        # Enhanced conversation display
        st.markdown("---")
        
        # Conversation header with stats
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("💬 Total Questions", len([m for m in st.session_state.messages if m["role"] == "user"]))
        with col2:
            st.metric("🤖 Responses", len([m for m in st.session_state.messages if m["role"] == "assistant"]))
        # with col3:
        #     tables_count = len([m for m in st.session_state.messages if m.get("has_table")])
        #     st.metric("📊 Data Tables", tables_count)
        with col4:
            if st.button("🔄 New Session", help="Start fresh conversation"):
                st.session_state.messages = []
                st.session_state.current_response = None
                st.session_state.examples_visible = False
                # Generate new session ID for fresh conversation
                import uuid
                st.session_state.session_id = f"streamlit-chat-{uuid.uuid4().hex[:8]}"
                st.rerun()
        
        st.markdown("### 📋 Conversation History")
        
        # Group messages by pairs and display newest first
        message_pairs = []
        i = 0
        while i < len(st.session_state.messages):
            if st.session_state.messages[i]["role"] == "user":
                pair = {"question": st.session_state.messages[i]}
                if i + 1 < len(st.session_state.messages) and st.session_state.messages[i + 1]["role"] == "assistant":
                    pair["answer"] = st.session_state.messages[i + 1]
                    i += 2
                else:
                    i += 1
                message_pairs.append(pair)
            else:
                i += 1
        
        # Display pairs in reverse order (newest first)
        for pair_index, pair in enumerate(reversed(message_pairs)):
            # Create a conversation container with enhanced styling
            with st.container():
                st.markdown('<div class="conversation-pair">', unsafe_allow_html=True)
                
                # Display question with enhanced styling
                with st.chat_message("user", avatar="👤"):
                    # Question header with timestamp
                    if pair["question"].get("timestamp"):
                        timestamp = time.strftime("%H:%M:%S", time.localtime(pair["question"]["timestamp"]))
                        st.caption(f"🕐 Asked at {timestamp}")
                    
                    # Question content with better formatting
                    question_text = pair["question"]["content"]
                    st.markdown(f"**Question:** {question_text}")
                
                # Then display answer with enhanced formatting
                if "answer" in pair:
                    with st.chat_message("assistant", avatar="🤖"):
                        # Answer header with timestamp and status
                        answer_col1, answer_col2 = st.columns([3, 1])
                        with answer_col1:
                            if pair["answer"].get("timestamp"):
                                timestamp = time.strftime("%H:%M:%S", time.localtime(pair["answer"]["timestamp"]))
                                st.caption(f"🕐 Answered at {timestamp}")
                        # with answer_col2:
                        #     if pair["answer"].get("has_table"):
                        #         st.caption("📊 Includes data table")
                        
                        # Main answer content
                        st.markdown("**Answer:**")
                        st.markdown(pair["answer"]["content"])
                        
                        # # Enhanced table display if available
                        # if pair["answer"].get("has_table") and pair["answer"].get("table_data"):
                        #     table_data = pair["answer"]["table_data"]
                        #     if table_data.get("headers") and table_data.get("rows"):
                        #         # Create a clean DataFrame for display
                        #         headers = table_data["headers"]
                        #         rows = table_data["rows"][1:]  # Skip header row since we already have headers
                                
                        #         if rows:
                        #             df = pd.DataFrame(rows, columns=headers)
                                    
                        #             # Clean the data for better display
                        #             cleaned_df = clean_table_data(df)
                                    
                        #             # Enhanced table display with container
                        #             st.markdown('<div class="data-table-container">', unsafe_allow_html=True)
                        #             st.markdown("#### 📊 Data Results")
                                    
                        #             # Table description
                        #             st.info(f"📋 Found {len(cleaned_df)} rows and {len(cleaned_df.columns)} columns of data")
                                    
                        #             # Display the table with enhanced formatting
                        #             st.dataframe(
                        #                 cleaned_df, 
                        #                 use_container_width=True,
                        #                 hide_index=True,
                        #                 height=min(600, max(250, (len(cleaned_df) + 1) * 45 + 80))  # Better dynamic height
                        #             )
                                    
                        #             # Enhanced summary metrics
                        #             st.markdown("#### 📈 Quick Stats")
                        #             metric_cols = st.columns(4)
                        #             with metric_cols[0]:
                        #                 st.metric("📝 Total Rows", f"{len(cleaned_df):,}")
                        #             with metric_cols[1]:
                        #                 st.metric("📊 Columns", len(cleaned_df.columns))
                        #             with metric_cols[2]:
                        #                 numeric_cols = len(cleaned_df.select_dtypes(include=['number']).columns)
                        #                 st.metric("🔢 Numeric Fields", numeric_cols)
                        #             with metric_cols[3]:
                        #                 text_cols = len(cleaned_df.select_dtypes(include=['object']).columns)
                        #                 st.metric("📝 Text Fields", text_cols)
                                    
                        #             # Data export option
                        #             if st.button("💾 Download Data as CSV", key=f"download_{pair_index}"):
                        #                 csv = cleaned_df.to_csv(index=False)
                        #                 st.download_button(
                        #                     label="📥 Click to Download",
                        #                     data=csv,
                        #                     file_name=f"marketing_data_{int(time.time())}.csv",
                        #                     mime="text/csv",
                        #                     key=f"download_btn_{pair_index}"
                        #                 )
                                    
                        #             st.markdown('</div>', unsafe_allow_html=True)
                        
                        # Enhanced SQL Query Display Section
                        if pair["answer"].get("raw_response") and pair["answer"]["raw_response"].get("raw_response", {}).get("trace_data"):
                            sql_query = extract_sql_query_from_trace(pair["answer"]["raw_response"]["raw_response"]["trace_data"])
                            if sql_query:
                                with st.expander("🔍 View SQL Query Used", expanded=False):
                                    st.markdown("**The AI agent executed this SQL query to get your results:**")
                                    st.code(sql_query, language="sql")
                                    
                                    # Copy to clipboard functionality
                                    st.markdown("*💡 Tip: You can copy this query to run it in your own SQL environment*")
                
                st.markdown('</div>', unsafe_allow_html=True)
                
                # Enhanced visual separator between conversations
                if pair_index < len(message_pairs) - 1:
                    st.markdown('<div class="conversation-separator"></div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()