# AWS Configuration for Bedrock Athena Agent Demo
# This is a template file. Copy this to config.py and fill in your actual values.

# AWS Profile (recommended approach - use this OR credentials below, not both)
AWS_PROFILE = ""  # Example: "ai-account" or "default"

# AWS Credentials (alternative to profile - use this OR profile above, not both)
AWS_ACCESS_KEY_ID = ""  # Your AWS Access Key ID
AWS_SECRET_ACCESS_KEY = ""  # Your AWS Secret Access Key

# AWS Region
AWS_REGION = "us-east-1"  # Change to your preferred region

# Bedrock Agent Configuration
BEDROCK_AGENT_ID = ""  # Your Bedrock Agent ID (required)
BEDROCK_AGENT_ALIAS_ID = "TSTALIASID"  # Your Agent Alias ID

# Application Settings
DEBUG_MODE = False  # Set to True for debugging
MAX_CHAT_HISTORY = 50  # Maximum number of chat messages to keep