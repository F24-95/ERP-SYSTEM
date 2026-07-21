# School ERP API Test Suite

## Overview

Comprehensive test suite for the Modern School ERP API.

## Prerequisites

- Python 3.11+
- PostgreSQL database
- Dependencies installed: `pip install -r requirements.txt`
- Test database configured in `.env` as `TEST_DATABASE_URL`

## Setup

1. Create a test database:
```bash
createdb faizan20_test
```

2. Configure test database URL in `.env`:
```env
TEST_DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/faizan20_test
```

## Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=src --cov-report=term-missing

# Run specific test file
pytest tests/test_public.py -v

# Run by marker
pytest tests/ -v -m public
pytest tests/ -v -m admin
pytest tests/ -v -m teacher
pytest tests/ -v -m student
pytest tests/ -v -m security

# Run with verbose output
pytest tests/ -v --tb=long
```

## Test Structure

| File | Role | Description |
|------|------|-------------|
| `test_public.py` | Public | Login, registration, health, forgot-password |
| `test_admin.py` | Admin | User management, academics, operations, fees |
| `test_teacher.py` | Teacher | Profile, classes, attendance, assignments |
| `test_student.py` | Student | Profile, classes, attendance, fees, results |
| `conftest.py` | All | Fixtures, database setup, auth tokens |
| `helpers.py` | All | Utility functions, constants, payloads |
| `test_config.py` | All | Environment configuration validation |

## Test Coverage

Each API endpoint is tested for:

- **Positive tests**: Valid request, correct auth, expected response
- **Negative tests**: Invalid data, missing fields, wrong types
- **Authorization tests**: Wrong role, expired token, missing token
- **Validation tests**: Required fields, empty values, null values
- **Edge cases**: Duplicate entries, boundary values, large payloads
- **Security tests**: SQL injection, XSS payloads, invalid JSON
