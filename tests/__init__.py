"""
Test package for wxmeow weather application.

This package contains organized tests for the wxmeow Flask application:

- unit/: Unit tests using unittest framework
- integration/: Integration tests for component interactions
- functional/: Functional tests for end-to-end scenarios

Test Structure:
- All tests should inherit from appropriate base classes
- Use pytest or unittest for test discovery and execution
- Integration tests may require a running Flask application
- Functional tests may require external dependencies
"""

import sys
import os
from pathlib import Path

# Ensure the parent directory is in the Python path for imports
project_root = Path(__file__).parent.parent.absolute()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
