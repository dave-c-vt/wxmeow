# Manual Tests for wxmeow Weather Application

This directory contains manual tests and development artifacts that were moved from the project root to maintain a clean repository structure.

## Directory Structure

```
manual/
├── README.md                           # This file
├── html/                              # HTML test files for manual browser testing
│   ├── test-timezone-chart.html       # Timezone handling in charts
│   ├── test_chart_functionality.html  # Chart functionality testing
│   ├── test_fixes.html               # Chart and UI fixes validation
│   └── test_noon_centering.html      # Noon centering functionality
└── scripts/                          # Development and debug scripts
    ├── debug_charts.py               # Chart debugging utilities
    ├── quick_test.py                 # Quick functionality tests
    ├── simple_test.py                # Basic import and function tests
    ├── working_temperature_chart.js  # Development version of chart JS
    └── working_wx2json_noaa.py       # Development version of weather module
```

## HTML Test Files

These are standalone HTML files used for manual testing of chart functionality and UI components:

### test-timezone-chart.html
- Tests timezone handling in weather charts
- Includes Chart.js and jQuery for interactive testing
- Supports light/dark theme switching
- Use: Open in browser to manually test timezone-related chart features

### test_chart_functionality.html
- General chart functionality testing
- Tests chart rendering, data display, and interactions
- Use: Open in browser to validate chart components work correctly

### test_fixes.html
- Tests specific bug fixes and improvements
- Includes theme switching and chart integration testing
- References actual static assets from the application
- Use: Validate that reported bugs have been fixed

### test_noon_centering.html
- Specifically tests the noon centering feature in charts
- Validates that temperature peaks are properly centered at noon
- Use: Verify noon centering algorithm works correctly

## Python Scripts

Development and debugging scripts that were used during development:

### debug_charts.py
- Step-by-step chart functionality debugging
- Tests weather object creation and chart generation
- Useful for isolating chart-related issues
- Run: `python debug_charts.py`

### quick_test.py
- Quick verification of basic functionality
- Tests imports and basic operations without network calls
- Use for rapid development iteration
- Run: `python quick_test.py`

### simple_test.py
- Basic functionality tests without complex operations
- Tests weather data generation and HTML output
- Validates core application components
- Run: `python simple_test.py`

### working_temperature_chart.js
- Development version of the temperature chart JavaScript
- Contains experimental features or fixes being tested
- Compare with `wxmeow/static/js/charts/temperature-chart.js` for differences
- Reference only - not used in production

### working_wx2json_noaa.py
- Development version of the weather data module
- Contains experimental weather data processing logic
- Compare with `wxmeow/wx2json_noaa.py` for differences
- Reference only - not used in production

## Usage Guidelines

### When to Use Manual Tests

1. **Bug Investigation**: When automated tests don't catch visual or interactive issues
2. **Feature Development**: During development of new chart features or UI components
3. **Browser Testing**: Testing cross-browser compatibility for chart rendering
4. **Debug Sessions**: When you need to step through chart creation process manually

### Running HTML Tests

1. Start the wxmeow application:
   ```bash
   python -m wxmeow
   ```

2. Open the HTML files in your browser:
   ```bash
   # From the project root
   open tests/manual/html/test_fixes.html
   ```

3. Ensure the application is running so static assets load correctly

### Running Python Scripts

From the project root directory:

```bash
# Make sure you're in the project root
cd wxmeow/

# Run individual scripts
python tests/manual/scripts/debug_charts.py
python tests/manual/scripts/quick_test.py
python tests/manual/scripts/simple_test.py
```

## Integration with Automated Tests

While these are manual tests, some of their functionality should be converted to automated tests:

- **Chart rendering logic** → Integration tests
- **Weather data processing** → Unit tests  
- **UI component behavior** → Functional tests with Selenium

## Maintenance

### Cleanup Guidelines

Periodically review these files and:

1. **Remove obsolete files** that test features no longer in the application
2. **Convert useful tests** to automated test cases
3. **Update working files** if they contain important bug fixes or features
4. **Document any critical test cases** that should be preserved

### When to Add New Files

Add new manual test files when:

- Developing complex visual features that need manual verification
- Debugging issues that require step-by-step analysis
- Creating proof-of-concept implementations
- Testing browser-specific behaviors

Remember: Manual tests are valuable but should complement, not replace, automated testing!