import boto3
import json
import time
from typing import Dict, Any, Optional
import streamlit as st

class BedrockAgentClient:
    """Client for interacting with AWS Bedrock Agent."""
    
    def __init__(
        self, 
        agent_id: str, 
        agent_alias_id: str,
        region: str = "us-east-1",
        aws_access_key_id: Optional[str] = None,
        aws_secret_access_key: Optional[str] = None,
        aws_profile: Optional[str] = None
    ):
        """
        Initialize the Bedrock Agent client.
        
        Args:
            agent_id: The Bedrock Agent ID
            agent_alias_id: The Bedrock Agent Alias ID
            region: AWS region
            aws_access_key_id: AWS access key (optional, uses default profile if not provided)
            aws_secret_access_key: AWS secret key (optional, uses default profile if not provided)
            aws_profile: AWS profile name (optional, uses default if not provided)
        """
        self.agent_id = agent_id
        self.agent_alias_id = agent_alias_id
        self.region = region
        
        # Initialize session with credentials or profile
        session_kwargs = {"region_name": region}
        
        if aws_profile:
            # Use specific AWS profile
            session_kwargs["profile_name"] = aws_profile
        elif aws_access_key_id and aws_secret_access_key:
            # Use provided credentials
            session_kwargs.update({
                "aws_access_key_id": aws_access_key_id,
                "aws_secret_access_key": aws_secret_access_key
            })
        # Otherwise, use default profile
        
        try:
            self.session = boto3.Session(**session_kwargs)
            
            # Configure client with timeout settings
            config = boto3.session.Config(
                read_timeout=500,  # 2 minutes read timeout
                connect_timeout=100,  # 1 minute connect timeout
                retries={
                    'max_attempts': 3,
                    'mode': 'adaptive'
                }
            )
            
            self.bedrock_agent_runtime = self.session.client(
                'bedrock-agent-runtime',
                config=config
            )
            
            # Test the connection
            self._test_connection()
            
        except Exception as e:
            raise Exception(f"Failed to initialize Bedrock client: {str(e)}")
    
    def _test_connection(self):
        """Test the connection to AWS Bedrock."""
        try:
            # Try to call the service (this will fail if credentials are invalid)
            response = self.bedrock_agent_runtime.invoke_agent(
                agentId=self.agent_id,
                agentAliasId=self.agent_alias_id,
                sessionId="test-connection",
                inputText="test"
            )
            # If we get here, connection is valid
        except Exception as e:
            if "UnauthorizedOperation" in str(e) or "AccessDenied" in str(e):
                raise Exception("Invalid AWS credentials or insufficient permissions")
            elif "ResourceNotFound" in str(e):
                raise Exception(f"Agent ID {self.agent_id} not found")
            else:
                # For other errors, we'll assume connection is OK and the error is agent-specific
                pass
    
    def send_message(self, message: str, session_id: Optional[str] = None, max_retries: int = 2) -> Dict[str, Any]:
        """
        Send a message to the Bedrock Agent and return the response with retry logic.
        
        Args:
            message: The message to send to the agent
            session_id: Optional session ID for conversation continuity
            max_retries: Maximum number of retry attempts
            
        Returns:
            Dictionary containing the agent's response
        """
        if not session_id:
            session_id = f"streamlit-demo-{int(time.time())}"
        
        last_error = None
        
        for attempt in range(max_retries + 1):
            try:
                # Invoke the Bedrock Agent
                response = self.bedrock_agent_runtime.invoke_agent(
                    agentId=self.agent_id,
                    agentAliasId=self.agent_alias_id,
                    sessionId=session_id,
                    inputText=message
                )
                
                # Process the streaming response
                full_response = self._process_streaming_response(response)
                
                return {
                    "status": "success",
                    "response_text": full_response.get("text", ""),
                    "session_id": session_id,
                    "raw_response": full_response,
                    "metadata": {
                        "agent_id": self.agent_id,
                        "agent_alias_id": self.agent_alias_id,
                        "timestamp": time.time(),
                        "attempt": attempt + 1
                    }
                }
                
            except Exception as e:
                last_error = e
                error_str = str(e)
                
                # Check if it's a timeout or connection error that we should retry
                if attempt < max_retries and any(keyword in error_str.lower() for keyword in 
                    ['timeout', 'connection', 'read timed out', 'connection pool']):
                    
                    # Wait before retrying (exponential backoff)
                    wait_time = (2 ** attempt) * 1  # 1, 2, 4 seconds
                    time.sleep(wait_time)
                    continue
                
                # If we're here, either max retries reached or non-retryable error
                break
        
        # Return error response
        return {
            "status": "error",
            "error": f"Failed after {max_retries + 1} attempts. Last error: {str(last_error)}",
            "session_id": session_id,
            "metadata": {
                "agent_id": self.agent_id,
                "agent_alias_id": self.agent_alias_id,
                "timestamp": time.time(),
                "attempts": max_retries + 1
            }
        }
    
    def _process_streaming_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process the streaming response from Bedrock Agent.
        
        Args:
            response: The streaming response from Bedrock
            
        Returns:
            Processed response data
        """
        full_text = ""
        chunks = []
        citations = []
        trace_data = []
        
        try:
            # Get the event stream
            event_stream = response.get('completion', [])
            
            for event in event_stream:
                if 'chunk' in event:
                    chunk_data = event['chunk']
                    
                    # Extract text from chunk
                    if 'bytes' in chunk_data:
                        chunk_text = chunk_data['bytes'].decode('utf-8')
                        full_text += chunk_text
                        chunks.append({
                            "text": chunk_text,
                            "timestamp": time.time()
                        })
                
                elif 'trace' in event:
                    # Extract trace information (useful for debugging)
                    trace_info = event['trace']
                    trace_data.append(trace_info)
                
                elif 'returnControl' in event:
                    # Handle return control events
                    control_data = event['returnControl']
                    trace_data.append({
                        "type": "return_control",
                        "data": control_data
                    })
        
        except Exception as e:
            st.error(f"Error processing streaming response: {str(e)}")
            full_text = f"Error processing response: {str(e)}"
        
        return {
            "text": full_text,
            "chunks": chunks,
            "citations": citations,
            "trace_data": trace_data
        }
    
    def get_session_history(self, session_id: str) -> Dict[str, Any]:
        """
        Get the conversation history for a session.
        
        Args:
            session_id: The session ID to retrieve history for
            
        Returns:
            Session history data
        """
        # Note: This would need to be implemented based on your specific
        # conversation storage mechanism (DynamoDB, etc.)
        return {
            "session_id": session_id,
            "messages": [],
            "status": "not_implemented"
        }
    
    def list_available_functions(self) -> Dict[str, Any]:
        """
        List the available functions/capabilities of the agent.
        
        Returns:
            Dictionary of available functions
        """
        # This would typically come from the agent's configuration
        return {
            "functions": [
                {
                    "name": "execute_athena_query",
                    "description": "Execute SQL queries against Athena database",
                    "parameters": ["sql_query"]
                }
            ],
            "capabilities": [
                "SQL query execution",
                "Data analysis",
                "Result formatting"
            ]
        }