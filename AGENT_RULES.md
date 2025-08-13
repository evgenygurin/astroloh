# 🚀 Intelligent FastAPI Ecosystem - Agent Rules

This document defines the rules and guidelines for AI agents working with the Intelligent FastAPI Ecosystem project. These rules ensure consistent, high-quality code that follows project standards and best practices.

## 🏗️ Architecture & Design Principles

### Clean Architecture
- **Repository Pattern**: Data access must be isolated in repository classes
- **Service Layer**: Business logic belongs in service classes, not in API endpoints
- **Dependency Injection**: Use FastAPI's dependency injection system for all services
- **Separation of Concerns**: Keep API, business logic, and data access separate

### Type Safety
- **Type Hints Required**: All functions must have complete type annotations
- **Pydantic Models**: Use Pydantic v2 for all data validation and serialization
- **SQLAlchemy Types**: Use SQLAlchemy 2.0 type annotations for all database models
- **Mypy Validation**: All code must pass mypy type checking with strict mode

### Async First
- **Async/Await**: Use async/await for all I/O operations
- **Non-Blocking**: Avoid blocking operations in request handlers
- **Connection Pooling**: Use connection pools for database and external services
- **Backpressure Handling**: Implement rate limiting and backpressure mechanisms

## 🧩 Code Structure & Organization

### Project Structure
- **Feature-Based Organization**: Group related files by feature, not by type
- **Consistent Naming**: Use snake_case for files, functions, and variables
- **Module Boundaries**: Respect module boundaries and avoid circular imports
- **Explicit Imports**: Use explicit imports (no `import *`)

### File Organization
- **API Routes**: `/app/api/v1/endpoints/{feature}.py`
- **Schemas**: `/app/api/v1/schemas/{feature}.py`
- **Models**: `/app/models/{feature}.py`
- **Repositories**: `/app/repositories/{feature}.py`
- **Services**: `/app/services/{feature}.py`
- **Utils**: `/app/utils/{utility}.py`
- **MCP Tools**: `/app/mcp/tools/{tool_name}.py`

## 🔒 Security Practices

### Input Validation
- **Validate All Inputs**: Use Pydantic models for all API inputs
- **Sanitize User Data**: Sanitize all user-provided data before use
- **Parameter Validation**: Use path and query parameter validation
- **Content Type Validation**: Validate content types for all requests

### Authentication & Authorization
- **JWT Implementation**: Use JWT tokens with proper expiration
- **Password Hashing**: Use bcrypt for password hashing
- **Role-Based Access**: Implement role-based access control
- **Scope Validation**: Validate token scopes for each protected endpoint

### Data Protection
- **PII Handling**: Encrypt or hash all personally identifiable information
- **Sensitive Data**: Never log sensitive data or credentials
- **HTTPS Only**: All endpoints must require HTTPS
- **CORS Configuration**: Implement proper CORS policies

## 🧪 Testing Requirements

### Test Coverage
- **Minimum Coverage**: Maintain minimum 80% test coverage
- **Unit Tests**: Write unit tests for all services and utilities
- **Integration Tests**: Write integration tests for all API endpoints
- **Test Isolation**: Tests must be isolated and not depend on each other

### Test Types
- **Unit Tests**: `/tests/unit/{module}/{feature}_test.py`
- **Integration Tests**: `/tests/integration/{feature}_test.py`
- **API Tests**: `/tests/api/v1/{endpoint}_test.py`
- **Performance Tests**: `/tests/performance/{feature}_test.py`

### Test Commands
- **Run All Tests**: `make test`
- **Unit Tests Only**: `make test-unit`
- **Integration Tests Only**: `make test-integration`
- **With Coverage**: `make test-coverage`

## 🤖 AI Integration Guidelines

### MCP Implementation
- **Tool Registration**: Register all MCP tools in `app/mcp/__init__.py`
- **Tool Interface**: Implement the `MCPTool` interface for all tools
- **Error Handling**: Provide clear error messages for tool failures
- **Documentation**: Document all tool parameters and return values

### Memory Management
- **Use Vercel-Mem0**: Implement persistent memory with vercel-mem0
- **Memory Schemas**: Define clear schemas for all memory objects
- **TTL Settings**: Configure appropriate TTL for different memory types
- **Memory Isolation**: Ensure proper isolation between user contexts

### Tool Development
- **Tool Categories**: Organize tools by category (filesystem, database, search, etc.)
- **Input Validation**: Validate all tool inputs with Pydantic models
- **Async Support**: All tools must support async execution
- **Error Handling**: Implement proper error handling and reporting

## 📊 Observability & Monitoring

### Logging
- **Structured Logging**: Use structured JSON logging
- **Log Levels**: Use appropriate log levels (DEBUG, INFO, WARNING, ERROR)
- **Context Enrichment**: Enrich logs with request IDs and user context
- **PII Protection**: Never log personally identifiable information

### Metrics
- **Prometheus Integration**: Expose metrics via Prometheus endpoint
- **Request Metrics**: Track request counts, latencies, and error rates
- **Business Metrics**: Track key business metrics
- **Resource Metrics**: Monitor CPU, memory, and I/O usage

### Health Checks
- **Liveness Probe**: Implement `/health` endpoint for basic health check
- **Readiness Probe**: Implement `/api/v1/health-detailed` for detailed health
- **Dependency Checks**: Check health of all dependencies (DB, Redis, etc.)
- **Custom Checks**: Implement custom health checks for critical services

## 🚀 Performance Optimization

### Database Optimization
- **Query Optimization**: Use optimized queries with proper indexing
- **Connection Pooling**: Configure appropriate connection pool sizes
- **Batch Operations**: Use batch operations for bulk data processing
- **Pagination**: Implement pagination for all list endpoints

### Caching Strategy
- **Redis Caching**: Use Redis for caching frequently accessed data
- **Cache Invalidation**: Implement proper cache invalidation strategies
- **TTL Configuration**: Configure appropriate TTL for different cache types
- **Cache Headers**: Set proper cache headers for HTTP responses

### Resource Management
- **Connection Pooling**: Use connection pools for all external services
- **Resource Cleanup**: Ensure proper cleanup of resources in finally blocks
- **Timeout Configuration**: Configure appropriate timeouts for all operations
- **Circuit Breakers**: Implement circuit breakers for external service calls

## 📝 Documentation Standards

### Code Documentation
- **Docstrings**: Use Google-style docstrings for all functions and classes
- **Type Hints**: Include type hints in all function signatures
- **Examples**: Include usage examples in docstrings for complex functions
- **Module Documentation**: Add module-level docstrings explaining purpose

### API Documentation
- **OpenAPI**: Maintain complete OpenAPI documentation
- **Endpoint Descriptions**: Document all endpoints with clear descriptions
- **Parameter Documentation**: Document all parameters with types and constraints
- **Response Documentation**: Document all response schemas and status codes

### Project Documentation
- **README**: Keep README up-to-date with setup and usage instructions
- **Architecture Docs**: Maintain architecture documentation
- **Deployment Guides**: Provide clear deployment instructions
- **Contributing Guide**: Document contribution process and standards

## 🛠️ Development Workflow

### Code Quality
- **Formatting**: Use `ruff` for code formatting
- **Linting**: Run linting before committing code
- **Type Checking**: Run mypy type checking before committing
- **Pre-commit Hooks**: Use pre-commit hooks for quality checks

### Git Workflow
- **Branch Naming**: Use `feature/`, `bugfix/`, `hotfix/` prefixes
- **Commit Messages**: Follow conventional commits format
- **PR Process**: Create PRs with clear descriptions and linked issues
- **CI Validation**: Ensure all CI checks pass before merging

### Environment Setup
- **Use UV**: Prefer UV package manager for dependency management
- **Virtual Environments**: Use isolated virtual environments
- **Docker Development**: Use Docker for development environment
- **Environment Variables**: Use `.env` files for local configuration

## 🚢 Deployment & Operations

### Docker Configuration
- **Multi-Stage Builds**: Use multi-stage builds for production images
- **Minimal Base Images**: Use minimal base images (Python slim or alpine)
- **Health Checks**: Include health checks in Docker configuration
- **Resource Limits**: Configure appropriate resource limits

### CI/CD Pipeline
- **Automated Testing**: Run all tests in CI pipeline
- **Security Scanning**: Include security scanning in CI pipeline
- **Deployment Automation**: Automate deployment process
- **Environment Promotion**: Implement proper environment promotion

### Production Readiness
- **Graceful Shutdown**: Handle graceful shutdown signals
- **Horizontal Scaling**: Design for horizontal scaling
- **Configuration Management**: Use environment variables for configuration
- **Secret Management**: Use secure secret management

## 🔧 Maintenance & Support

### Dependency Management
- **Dependency Updates**: Regularly update dependencies
- **Vulnerability Scanning**: Scan for vulnerabilities in dependencies
- **Compatibility Testing**: Test compatibility with new dependency versions
- **Dependency Documentation**: Document purpose of each dependency

### Troubleshooting
- **Logging Strategy**: Implement comprehensive logging for troubleshooting
- **Error Reporting**: Configure proper error reporting
- **Debugging Tools**: Provide tools for debugging production issues
- **Runbooks**: Create runbooks for common issues

### Performance Monitoring
- **APM Integration**: Integrate with Application Performance Monitoring
- **Performance Baselines**: Establish performance baselines
- **Load Testing**: Regularly perform load testing
- **Performance Regression Testing**: Test for performance regressions

## 🧠 AI Agent Specific Guidelines

### Code Generation
- **Follow Patterns**: Follow existing code patterns in the repository
- **Respect Architecture**: Maintain clean architecture principles
- **Complete Implementation**: Provide complete implementations, not stubs
- **Test Coverage**: Include tests for all generated code

### PR Creation
- **Descriptive Titles**: Use clear, descriptive PR titles
- **Detailed Descriptions**: Provide detailed PR descriptions
- **Issue References**: Reference related issues in PR description
- **Self-Review**: Perform self-review before submitting PR

### Issue Handling
- **Issue Analysis**: Thoroughly analyze issues before proposing solutions
- **Root Cause Identification**: Identify root causes, not just symptoms
- **Solution Options**: Present multiple solution options when appropriate
- **Implementation Plan**: Provide clear implementation plans

### Documentation Updates
- **Keep Docs Updated**: Update documentation when changing code
- **Example Updates**: Update examples to reflect code changes
- **Schema Documentation**: Update schema documentation when changing models
- **API Documentation**: Update API documentation when changing endpoints

## 📚 Learning Resources

### Project References
- **FastAPI Documentation**: [https://fastapi.tiangolo.com/](https://fastapi.tiangolo.com/)
- **SQLAlchemy 2.0 Documentation**: [https://docs.sqlalchemy.org/en/20/](https://docs.sqlalchemy.org/en/20/)
- **Pydantic v2 Documentation**: [https://docs.pydantic.dev/latest/](https://docs.pydantic.dev/latest/)
- **Model Context Protocol**: [https://github.com/vercel/mcp](https://github.com/vercel/mcp)

### Best Practices
- **FastAPI Best Practices**: [https://github.com/zhanymkanov/fastapi-best-practices](https://github.com/zhanymkanov/fastapi-best-practices)
- **Python Type Hints Cheat Sheet**: [https://mypy.readthedocs.io/en/stable/cheat_sheet_py3.html](https://mypy.readthedocs.io/en/stable/cheat_sheet_py3.html)
- **Async Python Guide**: [https://realpython.com/async-io-python/](https://realpython.com/async-io-python/)
- **Clean Architecture in Python**: [https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)

## 🔄 Continuous Improvement

### Feedback Loop
- **Code Review Feedback**: Incorporate feedback from code reviews
- **User Feedback**: Consider user feedback for improvements
- **Performance Metrics**: Use performance metrics to guide optimizations
- **Security Audits**: Address findings from security audits

### Knowledge Sharing
- **Documentation Updates**: Keep documentation up-to-date with learnings
- **Pattern Libraries**: Document common patterns and solutions
- **Anti-Pattern Documentation**: Document anti-patterns to avoid
- **Best Practice Evolution**: Evolve best practices based on experience

---

These rules are designed to ensure consistent, high-quality code that follows project standards and best practices. All AI agents working with the Intelligent FastAPI Ecosystem project should adhere to these guidelines.

