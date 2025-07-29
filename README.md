# AI Chatbot MVP

A multi-provider, multi-user AI chatbot built with Streamlit, featuring conversation memory, token tracking, and admin analytics.

## Features

- **Multi-Provider Support**: OpenAI, Anthropic (Claude), and Google Gemini
- **User Authentication**: Secure login/registration with bcrypt password hashing
- **Conversation Memory**: Vector-based memory storage using pgvector for context-aware responses
- **Token Tracking**: Real-time token usage monitoring and cost estimation
- **Export Functionality**: Download conversations in JSON or Markdown format
- **Auto-Summarization**: Automatic conversation summarization after 20 messages
- **Admin Dashboard**: Comprehensive analytics and user management
- **Cloud Storage**: All data stored in Supabase (PostgreSQL + pgvector)

## Architecture

```
chatbot/
├── app.py                 # Main Streamlit application
├── pages/
│   ├── chat.py           # Chat interface
│   ├── login.py          # Login page
│   ├── register.py       # Registration page
│   └── admin.py          # Admin dashboard
├── core/
│   ├── providers.py      # LLM provider integrations
│   ├── memory.py         # Vector memory management
│   ├── auth.py           # Authentication functions
│   ├── counters.py       # Token counting utilities
│   └── utils.py          # Helper functions
├── assets/
│   └── style.css         # Custom CSS styling
├── requirements.txt      # Python dependencies
├── schema.sql           # Database schema
└── .env.sample          # Environment variables template
```

## Setup Instructions

### 1. Prerequisites

- Python 3.8 or higher
- A Supabase account and project
- API keys for the AI providers you want to use:
  - OpenAI API key
  - Anthropic API key
  - Google AI Studio API key

### 2. Clone and Install

```bash
git clone <repository-url>
cd chatbot-shiro
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Database Setup

1. Create a new project in [Supabase](https://supabase.com)
2. Go to the SQL Editor in your Supabase dashboard
3. Run the SQL commands from `schema.sql` to create tables and functions
4. Note down your Supabase URL and service role key

### 4. Environment Configuration

1. Copy `.env.sample` to `.env`
2. Fill in your Supabase credentials:

```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
SUPABASE_ANON_KEY=your-anon-key
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
SESSION_TIMEOUT_MINUTES=30
```

### 5. Run the Application

```bash
streamlit run app.py
```

The application will be available at `http://localhost:8501`

## Usage

### First Time Setup

1. Register a new account or use the default admin account:
   - Username: `admin`
   - Password: `admin123` (change this immediately!)

### Using the Chat Interface

1. Login to your account
2. Select an AI provider (OpenAI, Anthropic, or Gemini)
3. Choose a model from the available options
4. Enter your API key for the selected provider
5. Adjust temperature and max tokens as needed
6. Enable conversation memory for context-aware responses
7. Start chatting!

### Admin Features

Admins can access the admin dashboard to view:
- User activity statistics
- Token usage analytics
- Cost estimates
- Provider and model usage distribution
- User management

## API Key Management

Each user must provide their own API keys for the AI providers they want to use. Keys are not stored permanently and must be entered each session for security.

### Supported Providers and Models

**OpenAI:**
- GPT-4
- GPT-4 Turbo
- GPT-3.5 Turbo
- GPT-3.5 Turbo 16K

**Anthropic:**
- Claude 3 Opus
- Claude 3 Sonnet
- Claude 3 Haiku

**Google Gemini:**
- Gemini Pro
- Gemini Pro Vision

## Memory System

The application uses a sophisticated memory system:

1. **Vector Storage**: Messages are embedded using sentence-transformers and stored in pgvector
2. **Similarity Search**: Relevant past conversations are retrieved for context
3. **Auto-Summarization**: After 20 messages, older conversations are summarized and pruned
4. **Per-User Memory**: Each user has isolated conversation memory

## Token Tracking

- Real-time token counting for all providers
- Cost estimation based on current pricing
- Session-level usage tracking
- Historical analytics in admin dashboard

## Export Features

Users can export their conversations in two formats:
- **JSON**: Machine-readable format for archival
- **Markdown**: Human-readable format for documentation

## Deployment

### VPS Deployment

1. Set up a VPS with Python 3.8+
2. Clone the repository and install dependencies
3. Set up environment variables
4. Use a process manager like PM2 or systemd
5. Set up a reverse proxy (Caddy, Nginx) for HTTPS

Example with Caddy:

```bash
# Install Caddy
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | sudo tee /etc/apt/trusted.gpg.d/caddy-stable.asc
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | sudo tee /etc/apt/sources.list.d/caddy-stable.list
sudo apt update && sudo apt install caddy

# Create Caddyfile
echo "yourdomain.com {
    reverse_proxy localhost:8501
}" | sudo tee /etc/caddy/Caddyfile

# Start services
sudo systemctl enable caddy
sudo systemctl start caddy
```

Run the Streamlit app:

```bash
streamlit run app.py --server.port 8501 --server.address 0.0.0.0
```

## Security Considerations

- All passwords are hashed using bcrypt
- Row Level Security (RLS) is enabled in Supabase
- API keys are not persisted (entered per session)
- Session timeout prevents unauthorized access
- Admin privileges are properly controlled

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure all dependencies are installed: `pip install -r requirements.txt`
2. **Database Errors**: Verify Supabase credentials and run schema.sql
3. **API Errors**: Check API key validity and format
4. **Memory Issues**: Ensure pgvector extension is enabled in Supabase

### Environment Variables

Make sure all required environment variables are set:
- `SUPABASE_URL`
- `SUPABASE_SERVICE_ROLE_KEY`
- `SUPABASE_ANON_KEY`

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License. See LICENSE file for details.

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review Supabase logs for database issues
3. Check Streamlit logs for application issues
4. Open an issue on GitHub

## Changelog

### v1.0.0
- Initial MVP release
- Multi-provider LLM support
- Vector memory system
- User authentication
- Admin dashboard
- Export functionality
- Auto-summarization
