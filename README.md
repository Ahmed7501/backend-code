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
- Support for send_message, wait, condition, webhook_action, and set_attribute nodes
- State persistence per contact
- Contact attribute management (key/value pairs)
- Asynchronous execution with Celery
- Flow validation and testing utilities
- Complete execution logging and monitoring

### Automation Triggers Module
- Keyword triggers that match incoming messages
- Event triggers for system events (new contact, flow completed, etc.)
- Schedule triggers for time-based automation
- Priority-based trigger execution
- Complete trigger logging and analytics

### Analytics & Reporting Module
- Daily and hourly message statistics aggregation
- Real-time analytics dashboard data
- Delivery rate monitoring and trends
- Active contacts tracking and growth analysis
- Flow performance metrics and completion rates
- Bot performance comparison and insights
- Automated data aggregation via Celery
- Redis caching for fast analytics queries

### Team Management Module
- Multi-tenant organization structure
- Role-based access control (RBAC)
- Organization creation and management
- Team member invitation system
- Permission-based endpoint protection
- Organization-scoped resource access
- Admin endpoints for user management
- Email-based invitation workflow

### Notifications Module
- Real-time WebSocket notifications
- Message status change notifications
- Flow event notifications
- System announcements
- User mention notifications
- Notification preferences management
- Persistent notification storage
- Organization-scoped delivery

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

### Contact Attributes
- `POST /contacts/{contact_id}/attributes` - Set single contact attribute
- `POST /contacts/{contact_id}/attributes/bulk` - Set multiple contact attributes
- `GET /contacts/{contact_id}/attributes` - Get all contact attributes
- `GET /contacts/{contact_id}/attributes/{key}` - Get single contact attribute
- `DELETE /contacts/{contact_id}/attributes/{key}` - Delete contact attribute
- `GET /contacts/search/by-attribute` - Search contacts by attribute
- `GET /contacts/{contact_id}` - Get contact with optional attributes

### Analytics & Reporting
- `GET /analytics/overview` - Get analytics overview for period
- `GET /analytics/trends` - Get analytics trends over date range
- `GET /analytics/bots/{bot_id}/performance` - Get bot performance metrics
- `GET /analytics/delivery-rates` - Get delivery rate statistics
- `GET /analytics/active-contacts` - Get active contacts statistics
- `GET /analytics/message-distribution` - Get message type distribution
- `POST /analytics/aggregate-now` - Manually trigger statistics aggregation
- `GET /analytics/health` - Analytics system health check

### Team Management
- `POST /team/organizations` - Create organization
- `GET /team/organizations/{org_id}` - Get organization details
- `PUT /team/organizations/{org_id}` - Update organization
- `DELETE /team/organizations/{org_id}` - Delete organization
- `GET /team/organizations/{org_id}/members` - Get organization members
- `POST /team/organizations/{org_id}/members` - Add organization member
- `PUT /team/organizations/{org_id}/members/{user_id}` - Update member role
- `DELETE /team/organizations/{org_id}/members/{user_id}` - Remove member
- `POST /team/organizations/{org_id}/invitations` - Create invitation
- `GET /team/organizations/{org_id}/invitations` - Get pending invitations
- `POST /team/invitations/{token}/accept` - Accept invitation
- `DELETE /team/invitations/{invitation_id}/revoke` - Revoke invitation
- `GET /team/organizations/{org_id}/stats` - Get organization statistics
- `GET /team/my-organizations` - Get user's organizations
- `GET /team/permissions/check` - Check user permissions
- `GET /team/roles` - Get available roles

### Notifications
- `GET /notifications/` - Get user notifications
- `GET /notifications/unread` - Get unread notifications
- `GET /notifications/count` - Get notification count
- `PUT /notifications/{notification_id}/read` - Mark notification as read
- `PUT /notifications/read-all` - Mark all notifications as read
- `DELETE /notifications/{notification_id}` - Delete notification
- `GET /notifications/preferences` - Get notification preferences
- `PUT /notifications/preferences` - Update notification preferences
- `GET /notifications/summary` - Get notification summary
- `POST /notifications/bulk-action` - Perform bulk action on notifications
- `DELETE /notifications/clear` - Clear all notifications
- `GET /notifications/stats` - Get notification statistics
- `GET /notifications/by-type/{type}` - Get notifications by type
- `POST /notifications/test` - Create test notification
- `WebSocket /ws` - Real-time notifications WebSocket endpoint

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

# Flow Engine Settings
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
FLOW_EXECUTION_TIMEOUT=1800
CELERY_TASK_TIME_LIMIT=1800
CELERY_TASK_SOFT_TIME_LIMIT=1500
CELERY_TASK_DEFAULT_RETRY_DELAY=60
CELERY_TASK_MAX_RETRIES=3
CELERY_RESULT_EXPIRES=3600

# Trigger System Settings
TRIGGER_CHECK_INTERVAL=60
TRIGGER_SCHEDULE_UPDATE_INTERVAL=3600
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

## Contact Attributes

### Overview
Contact attributes allow you to store custom key/value pairs for each contact, enabling personalized conversations and data persistence across flow executions.

### Attribute Types
- **string**: Text values (default)
- **number**: Numeric values (integers or floats)
- **boolean**: True/false values
- **json**: Complex data structures

### API Usage Examples

#### Set Single Attribute
```bash
curl -X POST "http://localhost:8000/contacts/1/attributes" \
  -H "Content-Type: application/json" \
  -d '{
    "key": "preferred_language",
    "value": "English",
    "value_type": "string"
  }'
```

#### Set Multiple Attributes
```bash
curl -X POST "http://localhost:8000/contacts/1/attributes/bulk" \
  -H "Content-Type: application/json" \
  -d '{
    "attributes": [
      {"key": "age", "value": "25", "value_type": "number"},
      {"key": "is_vip", "value": "true", "value_type": "boolean"},
      {"key": "preferences", "value": "{\"theme\": \"dark\", \"notifications\": true}", "value_type": "json"}
    ]
  }'
```

#### Get All Attributes
```bash
curl "http://localhost:8000/contacts/1/attributes"
```

#### Search Contacts by Attribute
```bash
curl "http://localhost:8000/contacts/search/by-attribute?key=preferred_language&value=English"
```

### Using Attributes in Flows

#### set_attribute Node
Set contact attributes during flow execution:

```json
{
  "type": "set_attribute",
  "config": {
    "attribute_key": "last_interaction",
    "attribute_value": "{{state.current_time}}",
    "value_type": "string",
    "next": 1
  }
}
```

#### Variable Interpolation
Use attributes in messages and other nodes:

```json
{
  "type": "send_message",
  "config": {
    "message_type": "text",
    "content": {
      "text": "Hello {{contact.first_name}}, your preferred language is {{contact.attribute.preferred_language}}"
    },
    "next": 2
  }
}
```

### Attribute Access Patterns
- `{{contact.attribute.key_name}}` - Access contact attributes
- `{{contact.first_name}}` - Access contact fields
- `{{state.variable_name}}` - Access execution state variables

## Analytics & Reporting

### Overview
The Analytics & Reporting system provides comprehensive insights into bot performance, message delivery rates, user engagement, and flow effectiveness through automated data aggregation and real-time dashboards.

### Setup
1. Ensure Redis and Celery are running (same as Flow Engine)
2. Analytics data is automatically aggregated daily at 00:05 UTC
3. Hourly aggregation runs every hour for real-time insights
4. Historical data is retained for 90 days (daily) and 7 days (hourly)

### Key Metrics

#### Message Statistics
- **Total Messages**: All inbound and outbound messages
- **Message Types**: Breakdown by text, template, media, interactive
- **Delivery Rates**: Sent, delivered, read, failed percentages
- **Response Times**: Average time to respond to messages

#### Contact Analytics
- **Active Contacts**: Unique contacts who sent/received messages
- **New Contacts**: Contacts created during the period
- **Returning Contacts**: Previously active contacts engaging again
- **Growth Rates**: Period-over-period contact growth

#### Flow Performance
- **Flow Completion Rate**: Percentage of started flows that complete
- **Average Flows per Contact**: Engagement depth metric
- **Flow Failure Analysis**: Common failure points and reasons

#### Bot Performance
- **Per-Bot Metrics**: Individual bot performance comparison
- **System-Wide Analytics**: Overall platform performance
- **Trend Analysis**: Growth patterns and seasonal insights

### API Usage Examples

#### Get Analytics Overview
```bash
curl "http://localhost:8000/analytics/overview?period=7days&bot_id=1"
```

Response:
```json
{
  "period": "7days",
  "bot_id": 1,
  "total_messages": 1523,
  "active_contacts": 245,
  "delivery_rate": 94.5,
  "average_response_time": 2.3,
  "top_message_types": {
    "text": 890,
    "template": 456,
    "media": 177
  },
  "flow_completion_rate": 87.2,
  "trends": {
    "messages_growth": 12.5,
    "contacts_growth": 8.3,
    "delivery_rate_change": 1.2
  }
}
```

#### Get Trends Data
```bash
curl "http://localhost:8000/analytics/trends?start_date=2024-01-01T00:00:00&end_date=2024-01-07T23:59:59&bot_id=1"
```

#### Get Bot Performance
```bash
curl "http://localhost:8000/analytics/bots/1/performance?period=30days"
```

#### Get Delivery Rates
```bash
curl "http://localhost:8000/analytics/delivery-rates?start_date=2024-01-01T00:00:00&end_date=2024-01-07T23:59:59&granularity=daily"
```

#### Get Active Contacts Stats
```bash
curl "http://localhost:8000/analytics/active-contacts?period=7days&bot_id=1"
```

#### Get Message Distribution
```bash
curl "http://localhost:8000/analytics/message-distribution?period=7days&bot_id=1"
```

#### Manual Aggregation Trigger
```bash
curl -X POST "http://localhost:8000/analytics/aggregate-now" \
  -H "Content-Type: application/json" \
  -d '{
    "date": "2024-01-15T00:00:00",
    "bot_id": 1,
    "force_recalculate": false
  }'
```

### Analytics Data Models

#### DailyMessageStats
Aggregated daily statistics per bot:
- Message counts (total, inbound, outbound)
- Message types breakdown
- Delivery statistics (sent, delivered, read, failed)
- Contact metrics (active, new)
- Flow statistics (started, completed, failed)
- Trigger activity

#### HourlyMessageStats
Real-time hourly statistics:
- Message counts per hour
- Inbound/outbound breakdown
- Used for real-time dashboards

### Performance Optimization

#### Caching Strategy
- **Overview Stats**: Cached for 5 minutes
- **Trends Data**: Cached for 15 minutes
- **Bot Performance**: Cached for 10 minutes
- **Delivery Rates**: Cached for 10 minutes
- **Active Contacts**: Cached for 10 minutes

#### Data Retention
- **Daily Stats**: Retained for 90 days
- **Hourly Stats**: Retained for 7 days
- **Automatic Cleanup**: Runs daily at 02:00 UTC

### Monitoring and Health

#### Health Check
```bash
curl "http://localhost:8000/analytics/health"
```

#### Cache Statistics
The system provides cache statistics and Redis health monitoring.

### Custom Analytics

#### Adding Custom Metrics
Extend the analytics system by:
1. Adding new fields to `DailyMessageStats` model
2. Updating aggregation logic in `crud.py`
3. Adding new API endpoints in `router.py`
4. Implementing caching for new metrics

#### Integration with External Tools
Analytics data can be exported to external BI tools:
- Export daily stats as CSV/JSON
- Real-time webhook notifications for key metrics
- Integration with Grafana, Tableau, or custom dashboards

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
