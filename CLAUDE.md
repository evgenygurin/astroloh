# Claude Development Guidelines

This file contains guidelines and instructions for Claude AI when working with the Astroloh project.

## Project Overview

Astroloh is a voice skill for Yandex Alice that provides personalized astrological forecasts and consultations. The project is built with Python 3.11, FastAPI, PostgreSQL, and integrates with Swiss Ephemeris for astronomical calculations.

## Development Environment Setup

### Installation

For development work, use the appropriate installation command based on your system:

**Linux/Windows (full installation):**

```bash
pip install -e ".[full,dev]"
```

**macOS (without C library compilation):**

```bash
pip install -e ".[macos,dev]"
```

**Minimal installation:**

```bash
pip install -e ".[minimal,dev]"
```

### Running the Application

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Code Quality and Testing

### Formatting

Always run code formatting before committing:

```bash
black app/ tests/
isort app/ tests/
```

### Linting

Run linting to ensure code quality:

```bash
flake8 app/ tests/
mypy app/
```

### Testing

Run the full test suite:

```bash
pytest
```

The project maintains 80% test coverage minimum. Tests are organized by categories:

- Unit tests: `pytest -m unit`
- Integration tests: `pytest -m integration`
- Performance tests: `pytest -m performance`
- Security tests: `pytest -m security`

## Project Structure

```
astroloh/
├── app/                    # Main application code
│   ├── api/               # API routers (Yandex Dialogs integration)
│   ├── core/              # Configuration and settings
│   ├── models/            # Data models
│   ├── services/          # Business logic (astrology, lunar calendar, etc.)
│   ├── utils/             # Utilities
│   └── main.py           # FastAPI entry point
├── tests/                 # Test suite
├── docs/                  # Documentation
├── migrations/            # Database migrations
└── docker-compose.yml    # Docker configuration
```

## Key Services

- **astrology_calculator.py**: Core astrological calculations
- **conversation_manager.py**: Dialog flow management
- **horoscope_generator.py**: Horoscope generation
- **lunar_calendar.py**: Lunar calendar functionality
- **natal_chart.py**: Birth chart calculations
- **session_manager.py**: User session handling

## Security Considerations

- Personal data is encrypted (encryption.py)
- GDPR compliance implemented (gdpr_compliance.py)
- Input validation through validators.py
- Security tests are mandatory for sensitive areas

## Astronomical Libraries

The project supports multiple astronomical calculation libraries with automatic fallbacks:

- **pyswisseph**: Primary library (high accuracy, requires C compilation)
- **skyfield**: Alternative (good accuracy, pure Python)
- **astropy**: Professional astronomy (full-featured)

## API Integration

- Main webhook: `POST /api/v1/yandex/webhook`
- Health check: `GET /health`
- API documentation available at `/docs`

## Development Workflow

1. Always run formatting and linting before commits
2. Ensure tests pass with minimum 80% coverage
3. Follow existing code patterns and service architecture
4. Use type hints consistently (mypy enforced)
5. Handle errors gracefully with proper logging (loguru)

## Database

- Uses PostgreSQL with SQLAlchemy 2.0
- Migrations managed with Alembic
- Async operations with asyncpg

## Deployment

- Docker-based deployment with docker-compose
- Environment variables configured via .env
- CI/CD pipeline enforces quality checks

When making changes, always consider the astrological domain context and maintain the existing service-oriented architecture.
