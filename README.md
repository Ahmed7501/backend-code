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

### Flow Engine Module
- Execute conversation flows node-by-node
- Support for send_message, wait, condition, and webhook_action nodes
- State persistence per contact
- Asynchronous execution with Celery
- Flow validation and testing utilities
- Complete execution logging and monitoring

### Automation Triggers Module
- Keyword triggers that match incoming messages
- Event triggers for system events (new contact, flow completed, etc.)
- Schedule triggers for time-based automation
- Priority-based trigger execution
- Complete trigger logging and analytics

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

### Flow Engine
- `POST /flows/execute` - Start flow execution for a contact
- `GET /flows/executions/{execution_id}` - Get execution details
- `GET /flows/executions/contact/{phone}` - Get contact's executions
- `POST /flows/executions/{execution_id}/resume` - Manually resume execution
- `POST /flows/executions/{execution_id}/cancel` - Cancel execution
- `POST /flows/executions/{execution_id}/input` - Handle user input
- `GET /flows/executions/{execution_id}/logs` - Get execution logs
- `GET /flows/statistics` - Get execution statistics
- `POST /flows/contacts/` - Create contact
- `GET /flows/contacts/` - Get all contacts

### Triggers
- `POST /triggers/` - Create new trigger
- `GET /triggers/` - Get all triggers
- `GET /triggers/{trigger_id}` - Get trigger by ID
- `GET /triggers/bot/{bot_id}` - Get triggers for a bot
- `PUT /triggers/{trigger_id}` - Update trigger
- `DELETE /triggers/{trigger_id}` - Delete trigger
- `POST /triggers/{trigger_id}/activate` - Activate trigger
- `POST /triggers/{trigger_id}/deactivate` - Deactivate trigger
- `POST /triggers/{trigger_id}/test` - Test trigger matching
- `GET /triggers/{trigger_id}/logs` - Get trigger execution logs
- `GET /triggers/statistics` - Get trigger statistics

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

## Flow Engine

### Setup
1. Install Redis server: `sudo apt-get install redis-server` (Ubuntu) or `brew install redis` (macOS)
2. Start Redis: `redis-server`
3. Start Celery worker: `python celery_worker.py`
4. Configure flow execution settings in `.env` file

### Usage Examples

#### Start a Flow Execution
```bash
curl -X POST "http://localhost:8000/flows/execute" \
  -H "Content-Type: application/json" \
  -d '{
    "flow_id": 1,
    "contact_phone": "1234567890",
    "bot_id": 1,
    "initial_state": {"custom_field": "value"}
  }'
```

#### Handle User Input
```bash
curl -X POST "http://localhost:8000/flows/executions/1/input" \
  -H "Content-Type: application/json" \
  -d '{
    "execution_id": 1,
    "message": "yes",
    "message_type": "text"
  }'
```

#### Get Execution Status
```bash
curl "http://localhost:8000/flows/executions/1"
```

### Node Types

#### Send Message Node
```json
{
  "type": "send_message",
  "config": {
    "message_type": "text",
    "content": {"text": "Hello {{contact.first_name}}!"},
    "next": 1
  }
}
```

#### Wait Node
```json
{
  "type": "wait",
  "config": {
    "duration": 5,
    "unit": "minutes",
    "next": 2
  }
}
```

#### Condition Node
```json
{
  "type": "condition",
  "config": {
    "variable": "state.user_response",
    "operator": "==",
    "value": "yes",
    "true_path": 3,
    "false_path": 4
  }
}
```

#### Webhook Action Node
```json
{
  "type": "webhook_action",
  "config": {
    "url": "https://api.example.com/webhook",
    "method": "POST",
    "headers": {"Authorization": "Bearer {{state.api_token}}"},
    "body": {"data": "{{state.user_data}}"},
    "store_response_in": "state.api_result",
    "next": 5
  }
}
```

## Automation Triggers

### Setup
1. Ensure Redis and Celery are running (same as Flow Engine)
2. Triggers are automatically processed when messages are received
3. Schedule triggers require Celery Beat to be running

### Trigger Types

#### Keyword Triggers
Match incoming messages against keywords and automatically launch flows.

```bash
curl -X POST "http://localhost:8000/triggers/" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Welcome Trigger",
    "bot_id": 1,
    "flow_id": 1,
    "trigger_type": "keyword",
    "keywords": ["hi", "hello", "hey"],
    "match_type": "exact",
    "case_sensitive": false,
    "priority": 10
  }'
```

#### Event Triggers
Automatically execute flows when system events occur.

```bash
curl -X POST "http://localhost:8000/triggers/" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "New Contact Welcome",
    "bot_id": 1,
    "flow_id": 2,
    "trigger_type": "event",
    "event_type": "new_contact",
    "event_conditions": {"source": "whatsapp"}
  }'
```

#### Schedule Triggers
Execute flows at specific times or intervals.

```bash
curl -X POST "http://localhost:8000/triggers/" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Daily Reminder",
    "bot_id": 1,
    "flow_id": 3,
    "trigger_type": "schedule",
    "schedule_type": "daily",
    "schedule_time": "09:00",
    "schedule_timezone": "UTC"
  }'
```

### Usage Examples

#### Test a Keyword Trigger
```bash
curl -X POST "http://localhost:8000/triggers/1/test" \
  -H "Content-Type: application/json" \
  -d '{
    "test_message": "hello there"
  }'
```

#### Get Trigger Statistics
```bash
curl "http://localhost:8000/triggers/statistics"
```

#### Get Trigger Execution Logs
```bash
curl "http://localhost:8000/triggers/1/logs"
```

### Supported Match Types
- **exact**: Exact string match
- **contains**: Message contains keyword
- **starts_with**: Message starts with keyword
- **ends_with**: Message ends with keyword
- **regex**: Regular expression match

### Supported Event Types
- `new_contact` - New contact created
- `message_received` - Message received
- `opt_in` - Contact opted in
- `opt_out` - Contact opted out
- `flow_completed` - Flow execution completed
- `flow_failed` - Flow execution failed

### Supported Schedule Types
- **once**: Single execution at specific datetime
- **daily**: Execute daily at specific time
- **weekly**: Execute weekly on specific day/time
- **monthly**: Execute monthly on specific day/time
- **cron**: Execute based on cron expression

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
