# Backend Django Project

A Django REST API backend with JWT authentication and MCP (Model Control Protocol) tools management.

## Features

- **Authentication**: JWT-based authentication with custom user model
- **MCP Tools**: Manage available tools and user-specific tool configurations
- **Database**: PostgreSQL with Docker support
- **Development Tools**: UV for dependency management, Ruff for linting
- **API**: RESTful API with Django REST Framework
- **Admin**: Django admin interface for easy management

## Quick Start

### Prerequisites

- Python 3.11+
- Docker and Docker Compose
- UV package manager

### Setup

1. **Clone and navigate to the project**:
   ```bash
   cd backend
   ```

2. **Copy environment file**:
   ```bash
   cp .env.example .env
   ```

3. **Update the `.env` file** with your settings:
   ```env
   DEBUG=True
   SECRET_KEY=your-super-secret-key-here
   DB_NAME=backend_db
   DB_USER=postgres
   DB_PASSWORD=postgres
   # ... other settings
   ```

4. **Start with Docker Compose**:
   ```bash
   docker-compose up --build
   ```

### Alternative: Local Development

1. **Create virtual environment with UV**:
   ```bash
   uv venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

2. **Install dependencies**:
   ```bash
   uv pip install -r requirements.txt
   ```

3. **Start PostgreSQL** (using Docker):
   ```bash
   docker run --name postgres-db -e POSTGRES_DB=backend_db -e POSTGRES_USER=postgres -e POSTGRES_PASSWORD=postgres -p 5432:5432 -d postgres:16
   ```

4. **Run migrations**:
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

5. **Create superuser**:
   ```bash
   python manage.py createsuperuser
   ```

6. **Run development server**:
   ```bash
   python manage.py runserver
   ```

## API Endpoints

### Authentication
- `POST /api/auth/register/` - User registration
- `POST /api/auth/login/` - User login
- `POST /api/auth/logout/` - User logout
- `POST /api/auth/token/refresh/` - Refresh JWT token
- `GET/PUT /api/auth/profile/` - User profile
- `POST /api/auth/change-password/` - Change password

### MCP Tools
- `GET /api/mcp/categories/` - List tool categories
- `GET /api/mcp/tools/` - List available tools
- `GET /api/mcp/tools/{id}/` - Get tool details
- `GET/POST /api/mcp/user-tools/` - List/create user tools
- `GET/PUT/DELETE /api/mcp/user-tools/{id}/` - Manage user tool
- `POST /api/mcp/user-tools/{id}/use/` - Record tool usage
- `GET /api/mcp/user-tools/stats/` - Get usage statistics

## Models

### Auth App
- **User**: Custom user model with email authentication
- **UserProfile**: Extended user profile information

### MCP App
- **ToolCategory**: Categories for organizing tools
- **Tool**: Available tools in the system
- **UserTool**: User-specific tool configurations

## Development

### Code Quality
```bash
# Run linting
ruff check .

# Auto-fix issues
ruff check --fix .

# Format code
ruff format .
```
