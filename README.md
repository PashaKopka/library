# Library Management System

A modern FastAPI-based library management system that allows users to manage books, authors, and genres with JWT authentication.

## Technologies

- Python 3.12.11
- FastAPI 0.118.0
- SQLAlchemy 2.0 with async support
- PostgreSQL with asyncpg
- Alembic for database migrations
- JWT Authentication

## Setup Instructions

### Prerequisites

- Python 3.12.11
- PostgreSQL database
- Virtual environment tool (venv)

### Environment Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/PashaKopka/library.git
   cd library
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv-library
   source venv-library/bin/activate  # On Windows: venv-library\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Environment Configuration:
   - Rename `.env.example` to `.env` 
   - Update the variables with your configuration values:
     ```
     DATABASE_URL=postgresql+asyncpg://username:password@localhost/library
     TEST_DATABASE_URL=postgresql+asyncpg://username:password@localhost/library_test
     JWT_SECRET=your_secure_jwt_secret_key
     JWT_ALGORITHM=HS256
     ACCESS_TOKEN_EXPIRE_MINUTES=60
     ```

### Database Setup

1. Create the PostgreSQL databases:
   ```bash
   createdb library
   ```

2. Run database migrations:
   ```bash
   alembic upgrade head
   ```

### Running the Application

Start the application with uvicorn:
```bash
uvicorn app.main:app --reload --port 8000
```

## API Documentation

Once the application is running, you can access the interactive API documentation at:
- Swagger UI: http://localhost:8000/docs

## Authentication

The API uses JWT token-based authentication. To access protected endpoints:

1. Register a user at `/auth/register`
2. Get a token at `/auth/login`
3. Include the token in the Authorization header: `Bearer your_token_here`


## Testing

Run tests using pytest:

```bash
python -m pytest
```

Run specific tests:

```bash
python -m pytest tests/crud_tests/  # Run all CRUD tests
python -m pytest tests/api_tests/test_book.py  # Run specific test file
```

## Project Structure

- `app/` - Main application package
  - `core/` - Core components (config, database, security)
  - `crud/` - Database operations
  - `dependencies/` - FastAPI dependencies
  - `models/` - SQLAlchemy models
  - `routers/` - API endpoints
  - `schemas/` - Pydantic models for request/response validation
- `alembic/` - Database migration scripts
- `tests/` - Test suite
  - `api_tests/` - API endpoint tests
  - `crud_tests/` - Database operation tests
