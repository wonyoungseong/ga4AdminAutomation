# GA4 Admin Automation System - Test Suite

## Overview

This comprehensive test suite provides complete coverage for the GA4 Admin Automation System, including unit tests, integration tests, security tests, and performance benchmarks.

## Test Structure

```
tests/
├── conftest.py              # Test configuration and fixtures
├── test_auth.py            # Authentication system tests
├── test_users.py           # User management tests
├── test_permissions.py     # Permission management tests
├── test_security.py        # Security vulnerability tests
├── test_integration.py     # End-to-end workflow tests
├── test_performance.py     # Performance and scalability tests
└── README.md              # This file
```

## Test Categories

### 🔐 Authentication Tests (`test_auth.py`)
- JWT token generation and verification
- Login/logout workflows
- Password security and hashing
- Token refresh mechanisms
- Role-based authentication

### 👥 User Management Tests (`test_users.py`)
- User CRUD operations
- Role management and transitions
- User status changes
- Registration and approval workflows
- User search and pagination

### 🛡️ Permission Tests (`test_permissions.py`)
- Permission request creation and approval
- Permission grant lifecycle management
- Permission revocation and expiry
- GA4 API integration testing
- Auto-approval workflows

### 🔒 Security Tests (`test_security.py`)
- Brute force attack protection
- SQL injection prevention
- XSS attack prevention
- Authorization bypass attempts
- Input validation security
- Session security measures

### 🔄 Integration Tests (`test_integration.py`)
- Complete user registration workflow
- End-to-end permission request flow
- Client management workflows
- Audit logging verification
- Email notification integration

### ⚡ Performance Tests (`test_performance.py`)
- API response time benchmarks
- Database query performance
- Concurrent load testing
- Memory usage stability
- Scalability testing

## Installation and Setup

### Prerequisites

1. Python 3.11+
2. All project dependencies installed
3. Database available (SQLite for tests)

### Install Test Dependencies

```bash
# Install all dependencies including test requirements
pip install -r requirements.txt

# Or install test dependencies specifically
pip install pytest pytest-asyncio pytest-cov
```

### Environment Setup

Tests use in-memory SQLite databases and do not require external services. All external dependencies (Google API, email service) are mocked.

## Running Tests

### Run All Tests

```bash
# Run complete test suite
pytest

# Run with verbose output
pytest -v

# Run with coverage report
pytest --cov=src --cov-report=html
```

### Run by Category

```bash
# Authentication tests only
pytest tests/test_auth.py

# Security tests only
pytest tests/test_security.py -m security

# Performance tests only
pytest tests/test_performance.py -m performance

# Integration tests only
pytest tests/test_integration.py -m integration
```

### Run by Test Markers

```bash
# Unit tests only
pytest -m unit

# Integration tests only
pytest -m integration

# Security tests only
pytest -m security

# Performance tests only
pytest -m performance

# Slow tests only (for comprehensive testing)
pytest -m slow

# Skip slow tests (for quick development testing)
pytest -m "not slow"
```

### Run Specific Test Classes or Functions

```bash
# Run specific test class
pytest tests/test_auth.py::TestAuthService

# Run specific test function
pytest tests/test_auth.py::TestAuthService::test_hash_password

# Run tests matching pattern
pytest -k "password"
```

## Test Configuration

### Pytest Configuration (`../pytest.ini`)

The test suite is configured with:
- Automatic async test handling
- Code coverage reporting (minimum 80%)
- Test markers for categorization
- Warning filters
- HTML coverage reports

### Test Markers

Available markers for test categorization:
- `unit`: Unit tests for individual components
- `integration`: Integration tests across components
- `security`: Security vulnerability tests
- `performance`: Performance and benchmarks tests
- `auth`: Authentication-related tests
- `permissions`: Permission management tests
- `database`: Tests requiring database access
- `external`: Tests requiring external services (mocked)
- `slow`: Long-running tests

### Performance Thresholds

The test suite enforces performance requirements:
- API endpoints: < 200ms response time
- Authentication: < 400ms (due to password hashing)
- Database queries: < 100ms
- Health checks: < 50ms

## Test Data and Fixtures

### Database Fixtures
- In-memory SQLite database for each test
- Automatic schema creation and cleanup
- Transaction rollback between tests

### User Fixtures
- `test_user`: Regular user with Requester role
- `test_admin`: Admin user
- `test_super_admin`: Super Admin user
- `user_factory`: Factory for creating test users

### Authentication Fixtures
- `auth_headers`: Authentication headers for regular user
- `admin_auth_headers`: Authentication headers for admin
- `super_admin_auth_headers`: Authentication headers for super admin

### Mock Fixtures
- `mock_email_service`: Mocked email notifications
- `mock_google_api`: Mocked Google API interactions
- `malicious_payloads`: Security testing payloads

## Writing New Tests

### Test Naming Convention

```python
async def test_feature_scenario_expected_outcome(self, fixtures):
    """Test description explaining what is being tested."""
    # Arrange
    # Act  
    # Assert
```

### Test Structure (AAA Pattern)

```python
async def test_user_creation_with_valid_data_creates_user(self, db_session):
    """Test that valid user data creates a new user successfully."""
    # Arrange
    user_data = {
        "email": "test@example.com",
        "name": "Test User",
        "password": "ValidPassword123!"
    }
    
    # Act
    user = await create_user(db_session, user_data)
    
    # Assert
    assert user.email == user_data["email"]
    assert user.name == user_data["name"]
    assert user.password_hash != user_data["password"]
```

### Adding Test Markers

```python
@pytest.mark.security  # Security test
@pytest.mark.slow      # Long-running test
async def test_brute_force_protection(self, test_client):
    """Test system protection against brute force attacks."""
    # Test implementation
```

### Using Fixtures

```python
async def test_with_authenticated_user(
    self, 
    test_client: TestClient,
    auth_headers: Dict[str, str],
    test_user: User
):
    """Test that uses authenticated user fixture."""
    response = test_client.get("/api/auth/me", headers=auth_headers)
    assert response.status_code == 200
```

## Continuous Integration

### GitHub Actions Integration

Add to your `.github/workflows/test.yml`:

```yaml
name: Test Suite

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
      - name: Run tests
        run: |
          pytest --cov=src --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

### Pre-commit Hooks

Add to `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: local
    hooks:
      - id: pytest-fast
        name: pytest-fast
        entry: pytest -m "not slow"
        language: system
        pass_filenames: false
        always_run: true
```

## Coverage Requirements

The test suite maintains:
- **Overall coverage**: ≥80%
- **Unit test coverage**: ≥90%
- **Integration test coverage**: ≥70%
- **Security test coverage**: All security-critical paths
- **Performance benchmarks**: All API endpoints

### Viewing Coverage Reports

```bash
# Generate HTML coverage report
pytest --cov=src --cov-report=html

# Open coverage report
open htmlcov/index.html
```

## Troubleshooting

### Common Issues

1. **Database connection errors**
   ```bash
   # Ensure database is accessible
   pytest tests/test_auth.py::test_simple_function
   ```

2. **Async test issues**
   ```bash
   # Run with asyncio debug mode
   pytest --asyncio-mode=auto -v
   ```

3. **Import path issues**
   ```bash
   # Run from project root
   cd /path/to/ga4AdminAutomation/backend
   python -m pytest
   ```

4. **Performance test failures**
   - Performance tests may fail on slower systems
   - Use `pytest -m "not performance"` to skip
   - Adjust thresholds in `conftest.py` if needed

### Debug Mode

```bash
# Run tests with debugging
pytest --pdb  # Drop into debugger on failure

# Run specific test with print statements
pytest -s tests/test_auth.py::test_specific_function
```

## Test Metrics and Reporting

### Test Execution Time

Monitor test execution time to prevent test suite slowdown:

```bash
# Show slowest tests
pytest --durations=10

# Show all test durations
pytest --durations=0
```

### Coverage Analysis

```bash
# Show missing coverage
pytest --cov=src --cov-report=term-missing

# Generate detailed coverage report
pytest --cov=src --cov-report=html --cov-report=term
```

## Security Testing

### Automated Security Scans

The security test suite includes:
- SQL injection detection
- XSS prevention verification
- Authorization bypass attempts
- Input validation testing
- Authentication security measures

### Manual Security Testing

Additional manual security testing should include:
- Penetration testing
- Code security reviews
- Dependency vulnerability scans
- Infrastructure security assessment

## Performance Baselines

### Current Performance Baselines
- Health check: < 50ms
- User authentication: < 400ms
- User list retrieval: < 200ms
- Permission creation: < 200ms
- Database queries: < 100ms

### Performance Monitoring

```bash
# Run performance tests only
pytest -m performance -v

# Run with performance profiling
pytest --profile tests/test_performance.py
```

## Contributing

When adding new features:

1. **Write tests first** (TDD approach)
2. **Maintain coverage** above 80%
3. **Add appropriate markers** for test categorization
4. **Update fixtures** if needed
5. **Document test purpose** clearly
6. **Verify security implications** for new endpoints
7. **Add performance benchmarks** for new APIs

### Test Review Checklist

- [ ] Tests follow AAA pattern
- [ ] Appropriate test markers applied
- [ ] Security implications considered
- [ ] Performance benchmarks included
- [ ] Edge cases covered
- [ ] Error conditions tested
- [ ] Documentation updated
- [ ] Coverage maintained above 80%

## Support

For questions about the test suite:
- Review existing test examples
- Check `conftest.py` for available fixtures
- Refer to pytest documentation
- Check test markers and categories
- Review performance benchmarks