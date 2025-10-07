# Email Spam Classifier

An intelligent email spam classification agent built with mcp-agent that automatically analyzes your Gmail inbox and identifies spam emails using LLM-powered classification.

## Features

- 📧 **Gmail Integration**: Connects directly to your Gmail inbox via MCP
- 🤖 **AI-Powered Classification**: Uses Claude/GPT to classify emails as spam or not spam
- 📊 **Detailed Analysis**: Provides confidence scores, spam types, and reasoning for each classification
- 🎯 **Actionable Insights**: Recommends specific actions (delete, mark spam, keep, review)
- 📈 **Batch Processing**: Efficiently processes multiple emails with statistics
- 🔍 **Flexible Filtering**: Supports Gmail labels and custom filters

## How It Works

1. **Connects to Gmail** using the MintMCP Gmail server
2. **Fetches emails** from your inbox (configurable number and labels)
3. **Analyzes each email** considering:
   - Sender reputation and authenticity
   - Subject line characteristics
   - Content quality and professionalism
   - Phishing indicators
   - Marketing/promotional patterns
4. **Classifies with structured output**:
   - Is spam (yes/no)
   - Confidence score (0-1)
   - Spam type (phishing, marketing, scam, malware, legitimate)
   - Detailed reasoning
   - Recommended action
5. **Returns comprehensive results** with statistics and individual classifications

## Setup

### 1. Google Cloud OAuth Setup

To access your Gmail, you need to set up Google OAuth credentials:

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the **Gmail API**
4. Go to **Credentials** → **Create Credentials** → **OAuth 2.0 Client ID**
5. Configure the OAuth consent screen
6. Create credentials for **Desktop application**
7. Download the credentials JSON file

### 2. Get Refresh Token

You'll need to obtain a refresh token using the OAuth flow. You can use the MintMCP Gmail setup tool:

```bash
npx @mintmcp/gmail setup
```

This will guide you through the OAuth flow and provide your refresh token.

### 3. Configure Secrets

Copy the example secrets file and fill in your values:

```bash
cp mcp_agent.secrets.yaml.example mcp_agent.secrets.yaml
```

Edit `mcp_agent.secrets.yaml` with your credentials:

```yaml
GOOGLE_CLIENT_ID: "your-client-id.apps.googleusercontent.com"
GOOGLE_CLIENT_SECRET: "your-client-secret"
GOOGLE_REDIRECT_URI: "http://localhost:3000/oauth2callback"
GOOGLE_REFRESH_TOKEN: "your-refresh-token"
ANTHROPIC_API_KEY: "sk-ant-your-api-key"
```

### 4. Get Anthropic API Key

1. Go to [Anthropic Console](https://console.anthropic.com/)
2. Create an account or sign in
3. Generate an API key
4. Add it to `mcp_agent.secrets.yaml`

### 5. Install Dependencies

```bash
pip install -r requirements.txt
```

## Usage

### Run Locally

```bash
python main.py
```

This will classify up to 20 emails from your INBOX by default.

### Customize Parameters

Edit the `main.py` file to adjust:

```python
result = asyncio.run(classify_spam_workflow(
    max_emails=50,      # Process up to 50 emails
    label="UNREAD"      # Only process unread emails
))
```

### Deploy to mcp-agent Cloud

Deploy this application to run it on mcp-agent cloud:

```bash
# Deploy command (replace with actual deployment method)
mcp-agent deploy
```

## Configuration

### Email Labels

You can filter emails by Gmail labels:

- `INBOX` - All inbox emails
- `UNREAD` - Only unread emails
- `SPAM` - Existing spam folder (for testing)
- `IMPORTANT` - Important emails
- Custom labels you've created

### LLM Provider

By default, the app uses Claude 3.5 Sonnet. To use OpenAI instead:

1. Uncomment OpenAI in `requirements.txt`
2. Update `mcp_agent.config.yaml`:

```yaml
llm:
  provider: openai
  model: gpt-4-turbo-preview
  api_key: ${OPENAI_API_KEY}
```

3. Add your OpenAI API key to secrets

## Output

The workflow returns a comprehensive report:

```json
{
  "total_processed": 20,
  "spam_count": 7,
  "not_spam_count": 13,
  "spam_percentage": 35.0,
  "emails": [
    {
      "email_id": "msg123",
      "subject": "Urgent: Verify Your Account",
      "from": "noreply@suspicious.com",
      "is_spam": true,
      "confidence": 0.95,
      "spam_type": "phishing",
      "reasoning": "Contains urgency tactics and suspicious sender...",
      "recommended_action": "delete"
    }
  ]
}
```

## Spam Types Detected

- **Phishing**: Attempts to steal credentials or personal information
- **Marketing**: Promotional emails and newsletters
- **Scam**: Fraudulent schemes (lottery, inheritance, etc.)
- **Malware**: Emails with potentially malicious attachments
- **Legitimate**: Not spam
- **Other**: Other types of unwanted email

## Recommended Actions

- **delete**: High-confidence spam, should be deleted
- **mark_spam**: Mark as spam and move to spam folder
- **keep**: Legitimate email, keep in inbox
- **review**: Low-confidence classification, manual review recommended

## Security Notes

- **Never commit** `mcp_agent.secrets.yaml` to version control
- Keep your OAuth credentials and API keys secure
- The Gmail server only has read access (cannot delete or modify emails)
- All processing happens securely via MCP protocol

## Troubleshooting

### Gmail Authentication Issues

If you get authentication errors:

1. Verify your OAuth credentials are correct
2. Ensure the Gmail API is enabled in Google Cloud
3. Check that your refresh token hasn't expired
4. Re-run the OAuth flow to get a new refresh token

### No Emails Found

If the workflow finds no emails:

1. Check that the label exists in your Gmail
2. Verify you have emails in the specified label
3. Try using `INBOX` as the label

### Classification Errors

If classifications fail:

1. Verify your Anthropic/OpenAI API key is valid
2. Check that you have API credits available
3. Review the logs for specific error messages

## Extending the Application

Ideas for enhancement:

1. **Auto-Action**: Automatically mark/delete spam emails
2. **Learning**: Fine-tune based on user feedback
3. **Scheduling**: Run periodically to keep inbox clean
4. **Reporting**: Generate daily/weekly spam reports
5. **Custom Rules**: Add domain/sender whitelists/blacklists
6. **Multi-Account**: Support multiple Gmail accounts

## License

MIT
