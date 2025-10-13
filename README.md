# ChatBoost Backend API

A comprehensive backend system with authentication and WhatsApp bot builder functionality.

## Project Structure

```
backend-code/
├── src/
│   ├── auth/                 # Authentication module
│   │   ├── __init__.py
│   │   ├── auth.py          # JWT and password utilities
│   │   ├── crud.py          # User CRUD operations
│   │   └── router.py        # Auth API endpoints
│   ├── bot_builder/         # Bot builder module
│   │   ├── __init__.py
│   │   ├── crud.py          # Bot CRUD operations
│   │   └── router.py        # Bot API endpoints
│   └── shared/              # Shared components
│       ├── database/        # Database configuration
│       ├── models/          # SQLAlchemy models
│       └── schemas/         # Pydantic schemas
├── tests/                   # Test files
├── config/                  # Configuration files
├── docs/                    # Documentation
├── main.py                  # Main application entry point
└── requirements.txt         # Project dependencies
```

## Features

### Authentication Module
- User registration and login
- JWT token-based authentication
- Password hashing with bcrypt
- User management endpoints

### Bot Builder Module
- Bot creation and management
- Flow design and management
- Node-based conversation flows
- Template system for reusable flows

### WhatsApp Integration Module
- Send template messages via WhatsApp Cloud API
- Send text, media, and interactive messages
- Receive and process incoming WhatsApp messages
- Webhook handling for message status updates
- Per-bot WhatsApp credential management

## Getting Started

### Prerequisites
- Python 3.8+
- pip

### Installation

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the application:
   ```bash
   python main.py
   ```

The API will be available at `http://localhost:8000`

### API Documentation

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## API Endpoints

### Authentication
- `POST /auth/register` - Register a new user
- `POST /auth/token` - Login and get access token
- `GET /auth/me` - Get current user info
- `GET /auth/users` - Get all users (protected)

### Bot Builder
- `POST /bots/` - Create a new bot
- `GET /bots/` - Get all bots
- `GET /bots/{bot_id}` - Get bot by ID
- `PUT /bots/{bot_id}` - Update bot
- `DELETE /bots/{bot_id}` - Delete bot
- `POST /bots/flows/` - Create a flow
- `GET /bots/flows/` - Get all flows
- `POST /bots/nodes/` - Create a node
- `POST /bots/templates/` - Create a template

### WhatsApp
- `POST /whatsapp/send/template` - Send template message
- `POST /whatsapp/send/text` - Send text message
- `POST /whatsapp/send/media` - Send media message
- `POST /whatsapp/send/interactive` - Send interactive message
- `POST /whatsapp/webhook` - Receive webhook events
- `GET /whatsapp/webhook` - Webhook verification
- `GET /whatsapp/messages/{bot_id}` - Get message history

## Environment Variables

Create a `.env` file in the root directory:

```env
SECRET_KEY=your-secret-key-here
DATABASE_URL=sqlite+aiosqlite:///./chatboost.db
ACCESS_TOKEN_EXPIRE_MINUTES=30
ENVIRONMENT=development
DEBUG=true

# WhatsApp API Settings
WHATSAPP_ACCESS_TOKEN=your-whatsapp-access-token-here
WHATSAPP_PHONE_NUMBER_ID=your-phone-number-id-here
WHATSAPP_BUSINESS_ACCOUNT_ID=your-business-account-id-here
WHATSAPP_WEBHOOK_VERIFY_TOKEN=your-webhook-verify-token-here
WHATSAPP_API_VERSION=v22.0
```

## WhatsApp Integration

### Setup
1. Create a WhatsApp Business Account and get your API credentials
2. Add your credentials to the `.env` file
3. Configure webhook URL in Meta Developer Console: `https://your-domain.com/whatsapp/webhook`

### Usage Examples

#### Send a Template Message
```bash
curl -X POST "http://localhost:8000/whatsapp/send/template?bot_id=1" \
  -H "Content-Type: application/json" \
  -d '{
    "to": "1234567890",
    "template_name": "hello_world",
    "language_code": "en_US"
  }'
```

#### Send a Text Message
```bash
curl -X POST "http://localhost:8000/whatsapp/send/text?bot_id=1" \
  -H "Content-Type: application/json" \
  -d '{
    "to": "1234567890",
    "text": "Hello from ChatBoost!"
  }'
```

#### Get Message History
```bash
curl "http://localhost:8000/whatsapp/messages/1?limit=10"
```

### Bot Configuration
Each bot can have its own WhatsApp credentials or use the default ones from environment variables:

```json
{
  "name": "My Bot",
  "description": "A WhatsApp bot",
  "is_whatsapp_enabled": true,
  "whatsapp_access_token": "optional-custom-token",
  "whatsapp_phone_number_id": "optional-custom-phone-id"
}
```

## Development

### Running Tests
```bash
pytest
```

### Database Migrations
The application uses SQLAlchemy with automatic table creation. For production, consider using Alembic for migrations.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License.
