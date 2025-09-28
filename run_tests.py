#!/usr/bin/env python3
"""
Test runner script for wxmeow weather application.

This script provides a convenient way to run different types of tests
locally during development. It supports running unit, integration,
and functional tests with various options.

Usage:
    python run_tests.py                    # Run all tests
    python run_tests.py --unit             # Run only unit tests
    python run_tests.py --integration      # Run only integration tests
    python run_tests.py --functional       # Run only functional tests
    python run_tests.py --coverage         # Run with coverage report
    python run_tests.py --verbose          # Run with verbose output
    python run_tests.py --fast             # Skip slow tests
"""

import argparse
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import List, Optional


class TestRunner:
    """Test runner for wxmeow application."""

    def __init__(self):
        self.project_root = Path(__file__).parent.absolute()
        self.flask_process = None
        self.test_server_url = "http://localhost:5000"

    def run_command(self, cmd: List[str], cwd: Optional[Path] = None) -> int:
        """Run a shell command and return the exit code."""
        print(f"🔧 Running: {' '.join(cmd)}")
        result = subprocess.run(cmd, cwd=cwd or self.project_root)
        return result.returncode

    def start_test_server(self) -> bool:
        """Start Flask development server for integration/functional tests."""
        print("🚀 Starting Flask test server...")

        env = os.environ.copy()
        env.update(
            {
                "FLASK_APP": "wxmeow",
                "FLASK_ENV": "testing",
                "PYTHONPATH": str(self.project_root),
                "PICKLE_DIR": str(self.project_root / "data" / ".pkl"),
                "LOG_FILE": str(self.project_root / "logs" / "test_wxmeow.log"),
            }
        )

        try:
            self.flask_process = subprocess.Popen(
                [sys.executable, "-m", "wxmeow", "--host=0.0.0.0", "--port=5000"],
                cwd=self.project_root,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

            # Wait for server to start
            import requests

            for i in range(30):  # Wait up to 30 seconds
                try:
                    response = requests.get(self.test_server_url, timeout=2)
                    if response.status_code == 200:
                        print("✅ Flask test server started successfully")
                        return True
                except requests.exceptions.RequestException:
                    time.sleep(1)
                    continue

            print("❌ Failed to start Flask test server")
            return False

        except Exception as e:
            print(f"❌ Error starting Flask server: {e}")
            return False

    def stop_test_server(self):
        """Stop the Flask test server."""
        if self.flask_process:
            print("🛑 Stopping Flask test server...")
            self.flask_process.terminate()
            self.flask_process.wait()
            self.flask_process = None

    def install_test_dependencies(self):
        """Install test dependencies if needed."""
        print("📦 Installing test dependencies...")
        cmd = [sys.executable, "-m", "pip", "install", "-e", ".[dev,security]"]
        return self.run_command(cmd) == 0

    def run_linting(self) -> bool:
        """Run code linting checks."""
        print("\n🔍 Running code quality checks...")

        checks = [
            (["flake8", "wxmeow", "--max-line-length=127"], "Flake8 linting"),
            (["black", "--check", "--diff", "wxmeow/"], "Black formatting check"),
            (["isort", "--check-only", "--diff", "wxmeow/"], "Import sorting check"),
        ]

        all_passed = True
        for cmd, description in checks:
            print(f"  Running {description}...")
            if self.run_command(cmd) != 0:
                all_passed = False
                print(f"  ❌ {description} failed")
            else:
                print(f"  ✅ {description} passed")

        return all_passed

    def run_unit_tests(
        self, coverage: bool = False, verbose: bool = False, fast: bool = False
    ) -> bool:
        """Run unit tests."""
        print("\n🧪 Running unit tests...")

        cmd = [sys.executable, "-m", "pytest", "tests/unit/"]

        if verbose:
            cmd.append("-v")
        if coverage:
            cmd.extend(
                ["--cov=wxmeow", "--cov-report=html", "--cov-report=term-missing"]
            )
        if fast:
            cmd.extend(["-m", "not slow"])

        return self.run_command(cmd) == 0

    def run_integration_tests(self, verbose: bool = False, fast: bool = False) -> bool:
        """Run integration tests."""
        print("\n🔗 Running integration tests...")

        # Start Flask server for integration tests
        if not self.start_test_server():
            return False

        try:
            cmd = [sys.executable, "-m", "pytest", "tests/integration/"]

            if verbose:
                cmd.append("-v")
            if fast:
                cmd.extend(["-m", "not slow"])

            return self.run_command(cmd) == 0
        finally:
            self.stop_test_server()

    def run_functional_tests(self, verbose: bool = False, fast: bool = False) -> bool:
        """Run functional tests."""
        print("\n🌐 Running functional tests...")

        # Start Flask server for functional tests
        if not self.start_test_server():
            return False

        try:
            cmd = [sys.executable, "-m", "pytest", "tests/functional/"]

            if verbose:
                cmd.append("-v")
            if fast:
                cmd.extend(["-m", "not slow"])

            return self.run_command(cmd) == 0
        finally:
            self.stop_test_server()

    def run_all_tests(
        self, coverage: bool = False, verbose: bool = False, fast: bool = False
    ) -> bool:
        """Run all tests in sequence."""
        print("\n🎯 Running all tests...")

        results = []

        # Run unit tests first (fastest)
        results.append(
            self.run_unit_tests(coverage=coverage, verbose=verbose, fast=fast)
        )

        # Run integration tests
        results.append(self.run_integration_tests(verbose=verbose, fast=fast))

        # Run functional tests (slowest)
        results.append(self.run_functional_tests(verbose=verbose, fast=fast))

        return all(results)

    def generate_test_report(self):
        """Generate comprehensive test report."""
        print("\n📊 Generating test report...")

        cmd = [
            sys.executable,
            "-m",
            "pytest",
            "tests/",
            "--html=test-report.html",
            "--self-contained-html",
            "--cov=wxmeow",
            "--cov-report=html",
            "--junitxml=test-results.xml",
        ]

        if self.run_command(cmd) == 0:
            print("✅ Test report generated: test-report.html")
            print("✅ Coverage report generated: htmlcov/index.html")
            return True
        else:
            print("❌ Failed to generate test report")
            return False


def main():
    """Main entry point for test runner."""
    parser = argparse.ArgumentParser(description="Run wxmeow tests")

    # Test type selection
    parser.add_argument("--unit", action="store_true", help="Run unit tests only")
    parser.add_argument(
        "--integration", action="store_true", help="Run integration tests only"
    )
    parser.add_argument(
        "--functional", action="store_true", help="Run functional tests only"
    )
    parser.add_argument("--all", action="store_true", help="Run all tests (default)")

    # Test options
    parser.add_argument(
        "--coverage", action="store_true", help="Run with coverage report"
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--fast", action="store_true", help="Skip slow tests")
    parser.add_argument("--lint", action="store_true", help="Run linting checks")
    parser.add_argument(
        "--report", action="store_true", help="Generate comprehensive test report"
    )
    parser.add_argument(
        "--install-deps", action="store_true", help="Install test dependencies"
    )

    args = parser.parse_args()

    runner = TestRunner()

    # Install dependencies if requested
    if args.install_deps:
        if not runner.install_test_dependencies():
            print("❌ Failed to install test dependencies")
            sys.exit(1)

    success = True

    try:
        # Run linting if requested
        if args.lint:
            if not runner.run_linting():
                success = False

        # Determine which tests to run
        if args.unit:
            success = runner.run_unit_tests(
                coverage=args.coverage, verbose=args.verbose, fast=args.fast
            )
        elif args.integration:
            success = runner.run_integration_tests(verbose=args.verbose, fast=args.fast)
        elif args.functional:
            success = runner.run_functional_tests(verbose=args.verbose, fast=args.fast)
        elif args.report:
            success = runner.generate_test_report()
        else:
            # Default: run all tests
            success = runner.run_all_tests(
                coverage=args.coverage, verbose=args.verbose, fast=args.fast
            )

        # Print final results
        print("\n" + "=" * 60)
        if success:
            print("🎉 All tests completed successfully!")
            sys.exit(0)
        else:
            print("💥 Some tests failed!")
            sys.exit(1)

    except KeyboardInterrupt:
        print("\n⚠️ Test run interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        sys.exit(1)
    finally:
        # Ensure Flask server is stopped
        runner.stop_test_server()


if __name__ == "__main__":
    main()
