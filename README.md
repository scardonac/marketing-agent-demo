# AWS Bedrock Athena Agent Demo

A Streamlit web application that provides an interactive chat interface for communicating with your AWS Bedrock Agent and visualizing Athena query results.

## Features

🤖 **Interactive Chat Interface**
- Real-time conversation with your AWS Bedrock Agent
- **Conversation memory** - agent remembers context within each session
- Message history and session management
- Support for complex SQL queries and data analysis

📊 **Data Visualization**
- Automatic chart generation from Athena query results
- Multiple chart types: bar, line, scatter, pie, histogram
- Interactive dashboards with customizable visualizations
- Data export capabilities (CSV, PNG)

🎨 **User-Friendly Interface**
- Clean, responsive design
- Real-time status indicators
- Configurable AWS settings
- Organized sidebar with examples and tips
- Automatic agent initialization from environment variables

## New in This Version

✨ **Enhanced User Experience**
- **Sidebar Organization**: Example questions and tips are now conveniently located in the sidebar for easy reference
- **Auto-Initialization**: If environment variables are set, the agent connects automatically when you start the app
- **Conversation Memory**: Maintains session context so you can ask follow-up questions like "show me the SQL" or "what about last month?"
- **Simplified Main Interface**: The main area focuses purely on conversation, making it cleaner and more intuitive
- **Improved SQL Extraction**: Updated to handle the latest AWS Bedrock Agent trace format for better query visibility

## Installation and Setup

### 1. Install Dependencies
```bash
cd streamlit-demo
pip install -r requirements.txt
```

### 2. Configure AWS Credentials and Agent Information

The application now supports **automatic initialization** with **Streamlit secrets** as the preferred method. You have **five options**:

#### Option A: Streamlit Secrets (Recommended for Production)
**For Streamlit Cloud deployment:**
1. Go to your Streamlit Cloud app settings
2. Click "Secrets" in the sidebar
3. Add your configuration in TOML format:
   ```toml
   BEDROCK_AGENT_ID = "your-agent-id"
   BEDROCK_AGENT_ALIAS_ID = "TSTALIASID"
   AWS_REGION = "us-east-1"
   AWS_ACCESS_KEY_ID = "your-access-key"
   AWS_SECRET_ACCESS_KEY = "your-secret-key"
   ```

**For local development:**
1. Create `.streamlit/secrets.toml` in your project root
2. Add the same configuration as above

**✨ With Streamlit secrets configured, the agent will connect automatically and securely!**

See [STREAMLIT_SECRETS_SETUP.md](STREAMLIT_SECRETS_SETUP.md) for detailed instructions.

#### Option B: Environment Variables
1. Copy the environment template:
   ```bash
   copy .env.template .env
   ```
2. Edit `.env` and fill in your actual values
3. Set environment variables in PowerShell:
   ```powershell
   $env:BEDROCK_AGENT_ID='your-agent-id-here'
   $env:BEDROCK_AGENT_ALIAS_ID='TSTALIASID'
   $env:AWS_DEFAULT_REGION='us-east-1'
   $env:AWS_ACCESS_KEY_ID='your-access-key-here'
   $env:AWS_SECRET_ACCESS_KEY='your-secret-key-here'
   ```

**✨ With environment variables set, the agent will connect automatically when you start the app!**

#### Option C: Interactive Setup
Run the setup script to create a configuration file:
```bash
python setup.py
```
This will create a `config.py` file with your settings.

#### Option D: Manual Configuration File
1. Copy `config_template.py` to `config.py`:
   ```bash
   copy config_template.py config.py
   ```
2. Edit `config.py` and fill in your values:
   ```python
   # Your actual values
   AWS_ACCESS_KEY_ID = "AKIAIOSFODNN7EXAMPLE"
   AWS_SECRET_ACCESS_KEY = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
   AWS_REGION = "us-east-1"
   BEDROCK_AGENT_ID = "ABCD1234EF"
   BEDROCK_AGENT_ALIAS_ID = "TSTALIASID"
   ```

#### Option E: Manual Entry in Web Interface
If you don't set up secrets, a config file, or environment variables, you can enter your credentials directly in the sidebar of the web application.

### 3. Run the Application
```bash
streamlit run app.py
```

**🚀 If you set up environment variables in Option A, the agent will connect automatically and you're ready to go!**

## Usage

1. **Start the application**
   ```bash
   streamlit run app.py
   ```

2. **Configure AWS Settings**
   - Enter your Bedrock Agent ID
   - Set the Agent Alias ID (default: TSTALIASID)
   - Choose your AWS region
   - Optionally provide AWS credentials

3. **Start Chatting**
   - Use the chat interface to ask questions
   - Try sample queries or create your own
   - View automatic visualizations of query results

4. **Conversation Memory**
   - The agent remembers your conversation context within each session
   - Ask follow-up questions like "show me the SQL query" or "what about last month?"
   - Use "🔄 New Session" to start a fresh conversation when needed

## Configuration

### Required AWS Resources

Before using this demo, ensure you have:

1. **AWS Bedrock Agent** configured with:
   - Athena query execution permissions
   - Proper IAM roles and policies
   - Action group configured for SQL execution

2. **Amazon Athena** setup with:
   - Database and tables configured
   - S3 bucket for query results
   - Proper data sources

3. **AWS Credentials** with permissions for:
   - `bedrock:InvokeAgent`
   - `athena:StartQueryExecution`
   - `athena:GetQueryResults`
   - `s3:GetObject` (for query results)

### Environment Variables (Optional)

You can set these environment variables instead of using the UI:

```bash
export AWS_ACCESS_KEY_ID=your_access_key
export AWS_SECRET_ACCESS_KEY=your_secret_key
export AWS_DEFAULT_REGION=us-east-1
export BEDROCK_AGENT_ID=your_agent_id
export BEDROCK_AGENT_ALIAS_ID=TSTALIASID
```

## Project Structure

```
streamlit-demo/
├── app.py                          # Main Streamlit application
├── requirements.txt                # Python dependencies
├── README.md                       # This file
├── static/
│   └── css/
│       └── styles.css             # Custom CSS styling
└── src/
    ├── components/
    │   ├── __init__.py
    │   ├── chat_interface.py       # Chat UI components
    │   └── image_viewer.py         # Visualization components
    ├── services/
    │   ├── __init__.py
    │   └── aws_agent_client.py     # AWS Bedrock client
    └── utils/
        ├── __init__.py
        └── helpers.py              # Utility functions
```

## Features in Detail

### Chat Interface
- **Message History**: Persistent chat history during session
- **Response Formatting**: Clean display of agent responses
- **Error Handling**: User-friendly error messages
- **Export/Import**: Save and load conversation data

### Visualization Engine
- **Automatic Detection**: Identifies tabular data in responses
- **Chart Generation**: Creates appropriate visualizations
- **Interactive Charts**: Plotly-powered interactive charts
- **Data Export**: Download charts as PNG or data as CSV
- **Custom Charts**: Create custom visualizations from data

### AWS Integration
- **Secure Authentication**: Support for multiple credential methods
- **Connection Testing**: Validates credentials and agent connectivity
- **Session Management**: Maintains conversation context
- **Error Recovery**: Handles AWS service errors gracefully

## Sample Queries

Try these sample queries with your agent:

- "Show me the top 10 customers by revenue this year"
- "What are the monthly sales trends for the last 6 months?"
- "List all products with inventory below 100 units"
- "Show me the order distribution by region"
- "What is the average order value by customer segment?"

## Troubleshooting

### Common Issues

1. **"Agent not found" error**
   - Verify your Agent ID is correct
   - Check that the agent is deployed
   - Ensure you're using the correct AWS region

2. **"Access Denied" error**
   - Check AWS credentials are valid
   - Verify IAM permissions for Bedrock and Athena
   - Ensure the agent has proper execution roles

3. **"No visualization" message**
   - Ensure your query returns tabular data
   - Check that the response contains a properly formatted table
   - Verify numeric columns are present for chart generation

4. **Connection timeouts**
   - Check your internet connection
   - Verify AWS service availability in your region
   - Try increasing timeout values in the code

### Debug Mode

Enable debug mode by adding this to your environment:
```bash
export STREAMLIT_DEBUG=true
```

This will show additional logging information in the console.

## Customization

### Adding New Chart Types
1. Extend the `ImageViewer` class in `src/components/image_viewer.py`
2. Add new chart types to `supported_chart_types` list
3. Implement chart creation logic in `_create_plotly_chart` method

### Custom Styling
1. Modify `static/css/styles.css` for visual customization
2. Update colors, fonts, and layout to match your brand
3. Add custom CSS classes for specific components

### Extended Functionality
1. Add new components in `src/components/`
2. Extend the AWS client in `src/services/aws_agent_client.py`
3. Add utility functions in `src/utils/helpers.py`

## Security Notes

- Never commit AWS credentials to version control
- Use IAM roles with minimal required permissions
- Consider using AWS STS for temporary credentials
- Enable CloudTrail logging for audit purposes

## Performance Tips

- Limit query result sizes for better visualization performance
- Use data sampling for large datasets
- Cache frequently used data when possible
- Monitor AWS service quotas and limits

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is provided as-is for demonstration purposes. Please review and comply with AWS service terms and your organization's policies when using this code.

## Support

For issues related to:
- **AWS Bedrock**: Check AWS documentation and support
- **Amazon Athena**: Refer to Athena troubleshooting guides
- **This Demo**: Create an issue in the project repository

## Version History

- **v1.0.0**: Initial release with basic chat and visualization features
- **v1.1.0**: Added custom chart creation and data export
- **v1.2.0**: Enhanced error handling and AWS integration