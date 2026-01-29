# Testing Structure for WxMeow Weather Application

This directory contains all tests for the WxMeow weather application, organized by test type and framework.

## Directory Structure

```
tests/
├── unit/                 # Unit tests - test individual components in isolation
├── integration/         # Integration tests - test component interactions
├── functional/         # Functional tests - test complete user workflows
├── manual/            # Manual tests and development scripts
│   ├── html/         # HTML test files for manual browser testing
│   └── scripts/      # Manual test scripts and debug tools
└── README.md         # This file
```

## Test Types

### Unit Tests (`unit/`)
Tests that verify individual components work correctly in isolation:
- `test_app.py` - Flask application initialization
- `test_functionality.py` - Core weather functionality
- `test_history.py` - Weather history features
- `test_location.py` - Location handling
- `test_theme.py` - Theme and styling
- `test_chart_data_processing.py` - Chart data processing logic

**Markers**: `@pytest.mark.unit`

### Integration Tests (`integration/`)
Tests that verify multiple components work together correctly:
- `test_chart_centering_and_alignment.py` - Chart rendering integration
- `test_chart_loading.py` - Chart loading and data integration
- `test_chart_rendering.py` - Full chart rendering pipeline

**Markers**: `@pytest.mark.integration`

### Functional Tests (`functional/`)
End-to-end tests that simulate complete user workflows:
- `test_chart_functionality_comprehensive.py` - Complete chart workflows
- `test_day_picker_fixes.py` - Day picker functionality
- `test_final_fixes.py` - Final integration scenarios
- `test_final_integration.py` - Complete application integration
- `test_final_plot_fix.py` - Plot display fixes
- `test_fixes.py` - General bug fixes verification
- `test_noon_centering_fix.py` - Noon centering functionality
- `test_specific_fixes.py` - Specific issue fixes

**Markers**: `@pytest.mark.functional`

### Manual Tests (`manual/`)
Tests and scripts that require manual execution or verification:

#### HTML Tests (`manual/html/`)
- `test-timezone-chart.html` - Manual timezone chart testing
- `test_chart_functionality.html` - Manual chart functionality testing
- `test_fixes.html` - Manual verification of fixes
- `test_noon_centering.html` - Manual noon centering testing

#### Scripts (`manual/scripts/`)
- `debug_charts.py` - Debug script for chart issues
- `quick_test.py` - Quick verification script
- `simple_test.py` - Simple functionality test
- `test_chart_fixes_manual.py` - Manual chart fixes verification
- `working_temperature_chart.js` - Working chart implementation reference
- `working_wx2json_noaa.py` - Working weather data processor reference

## Running Tests

### Using pytest directly

```bash
# Run all tests
pytest

# Run specific test types
pytest tests/unit/          # Unit tests only
pytest tests/integration/   # Integration tests only
pytest tests/functional/    # Functional tests only

# Run with markers
pytest -m unit              # All unit tests
pytest -m integration      # All integration tests
pytest -m functional       # All functional tests
pytest -m "not slow"       # Skip slow tests

# Run with coverage
pytest --cov=wxmeow --cov-report=html
```

### Using the test runner script

```bash
# Run all tests with the custom test runner
python run_tests.py

# Run specific test types
python run_tests.py --unit
python run_tests.py --integration
python run_tests.py --functional

# Run with options
python run_tests.py --coverage --verbose
python run_tests.py --fast          # Skip slow tests
python run_tests.py --lint          # Include linting
python run_tests.py --report        # Generate HTML report
```

### Manual Tests

Manual tests require human interaction or visual verification:

```bash
# Run manual test scripts
cd tests/manual/scripts/
python debug_charts.py
python quick_test.py
python simple_test.py

# Open HTML tests in browser
# Navigate to tests/manual/html/ and open files in browser
```

## Test Configuration

Tests are configured via:
- `pytest.ini` - Main pytest configuration
- `requirements-test.txt` - Test dependencies
- `run_tests.py` - Custom test runner

### Key Configuration Features

- **Coverage**: Minimum 80% coverage required
- **Timeouts**: 300 second timeout for long-running tests
- **Markers**: Tests are categorized with pytest markers
- **Logging**: Test execution logging enabled
- **Parallel**: Tests can run in parallel where appropriate

## CI/CD Integration

Tests are automatically run in the GitHub Actions CI/CD pipeline:

### Test Matrix
- Python versions: 3.9, 3.10, 3.11
- Test types: unit, integration, functional
- Environments: Ubuntu Latest

### Pipeline Stages
1. **Unit Tests**: Run on all Python versions with linting and type checking
2. **Integration Tests**: Run with Flask test server
3. **Functional Tests**: Run with Chrome for browser automation
4. **Coverage**: Upload coverage reports to Codecov

## Test Development Guidelines

### Writing New Tests

1. **Choose the right test type**:
   - Unit: Testing individual functions/classes
   - Integration: Testing component interactions
   - Functional: Testing complete user workflows

2. **Use appropriate markers**:
   ```python
   import pytest
   
   @pytest.mark.unit
   def test_individual_function():
       pass
   
   @pytest.mark.slow
   @pytest.mark.integration
   def test_complex_integration():
       pass
   ```

3. **Follow naming conventions**:
   - Test files: `test_*.py`
   - Test functions: `test_*`
   - Test classes: `Test*`

4. **Use fixtures for setup/teardown**:
   ```python
   @pytest.fixture
   def sample_weather_data():
       return {"temperature": 72, "humidity": 60}
   ```

### Test Data

- Use fixtures for reusable test data
- Store test data files in appropriate test subdirectories
- Use factories for generating test data variations

### Mocking

- Mock external API calls in unit and integration tests
- Use `pytest-mock` for mocking functionality
- Mock time-dependent code for consistent results

## Dependencies

Test dependencies are managed in `requirements-test.txt`:

- `pytest` - Main testing framework
- `pytest-cov` - Coverage reporting
- `pytest-mock` - Mocking support
- `pytest-html` - HTML test reports
- `requests` - HTTP testing
- `beautifulsoup4` - HTML parsing for web tests
- `selenium` - Browser automation (functional tests)

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure project root is in Python path
2. **Flask Server Issues**: Check if port 5000 is available
3. **Browser Tests Failing**: Ensure Chrome/ChromeDriver is installed
4. **Coverage Issues**: Check if all source files are included

### Debug Mode

Enable debug mode for troubleshooting:

```bash
pytest -v --tb=long --log-cli-level=DEBUG
```

### Test Isolation

If tests interfere with each other:
- Use fixtures for clean setup/teardown
- Clear caches between tests
- Use separate test databases/files

## Contributing

When adding new tests:

1. Place tests in the appropriate directory (unit/integration/functional)
2. Add appropriate pytest markers
3. Include docstrings explaining what the test verifies
4. Update this README if adding new test categories
5. Ensure tests pass in CI/CD pipeline

## Contact

For questions about the testing structure or issues with tests, please create an issue in the repository or contact the development team.