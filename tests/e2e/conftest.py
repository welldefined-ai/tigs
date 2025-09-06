"""Pytest configuration and fixtures for E2E testing."""

import os
import tempfile
import shutil
from pathlib import Path
from typing import Generator, Optional

import pytest

from .framework import TerminalApp
from .framework.utils import create_test_repo, cleanup_test_repo
from .framework.assertions import save_display_on_failure


@pytest.fixture(scope="session")
def e2e_fixtures_dir() -> Path:
    """Get the directory containing E2E test fixtures."""
    return Path(__file__).parent / "fixtures"


@pytest.fixture(scope="session") 
def e2e_screens_dir(e2e_fixtures_dir) -> Path:
    """Get the directory containing expected screen captures."""
    return e2e_fixtures_dir / "screens"


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Provide a temporary directory for test use."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def test_repo(temp_dir) -> Generator[Path, None, None]:
    """Create a temporary Git repository for testing."""
    repo_path = temp_dir / "test_repo"
    
    # Create repository with some test commits
    commits = [
        "Initial commit",
        "Add feature A",
        "Fix bug in feature A", 
        "Add feature B",
        "Refactor code structure",
        "Add tests",
        "Update documentation",
        "Release version 1.0"
    ]
    
    create_test_repo(repo_path, commits)
    
    yield repo_path
    
    # Cleanup happens automatically via temp_dir


@pytest.fixture
def empty_repo(temp_dir) -> Generator[Path, None, None]:
    """Create an empty Git repository for testing."""
    repo_path = temp_dir / "empty_repo"
    create_test_repo(repo_path)
    yield repo_path


@pytest.fixture
def terminal_app_factory(temp_dir):
    """Factory to create TerminalApp instances."""
    created_apps = []
    
    def create_app(
        command: str = "tigs",
        args: Optional[list] = None,
        repo: Optional[Path] = None,
        **kwargs
    ) -> TerminalApp:
        """Create a TerminalApp instance.
        
        Args:
            command: Command to run (default: "tigs")
            args: Command arguments
            repo: Repository path to use as working directory
            **kwargs: Additional TerminalApp arguments
            
        Returns:
            Configured TerminalApp instance
        """
        # Default arguments
        if args is None:
            args = ["store"]
            
        # Set up environment
        env = kwargs.get('env', {})
        
        # Use repository as working directory if provided
        cwd = repo if repo else temp_dir
        
        # Create the app
        app = TerminalApp(
            command=command,
            args=args,
            cwd=cwd,
            env=env,
            timeout=kwargs.get('timeout', 10.0),
            lines=kwargs.get('lines', 30),
            columns=kwargs.get('columns', 80)
        )
        
        created_apps.append(app)
        return app
        
    yield create_app
    
    # Cleanup all created apps
    for app in created_apps:
        try:
            app.stop()
        except Exception:
            pass  # Ignore cleanup errors


@pytest.fixture  
def tigs_app(terminal_app_factory, test_repo):
    """Create a TerminalApp instance running tigs store command."""
    app = terminal_app_factory(repo=test_repo)
    app.start()
    
    # Wait for initial load
    app.wait_for_output(timeout=5.0)
    
    yield app
    
    app.stop()


@pytest.fixture
def tigs_app_empty_repo(terminal_app_factory, empty_repo):
    """Create a TerminalApp instance running tigs on an empty repository."""
    app = terminal_app_factory(repo=empty_repo)
    app.start()
    
    # Wait for initial load
    app.wait_for_output(timeout=5.0)
    
    yield app
    
    app.stop()


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Hook to save display content when E2E tests fail."""
    outcome = yield
    report = outcome.get_result()
    
    # Only handle test failures during the call phase (not setup/teardown)
    if report.when == "call" and report.failed:
        # Check if this is an E2E test (has terminal app fixture)
        terminal_app = None
        for fixture_name in item.fixturenames:
            if fixture_name.endswith('_app') and hasattr(item, 'funcargs'):
                terminal_app = item.funcargs.get(fixture_name)
                break
                
        if terminal_app and hasattr(terminal_app, 'capture_display'):
            try:
                # Capture final display state
                display_content = terminal_app.capture_display()
                
                # Save to fixtures directory
                test_name = item.name
                fixtures_dir = Path(__file__).parent / "failures"
                save_display_on_failure(display_content, test_name, fixtures_dir)
                
            except Exception as e:
                # Don't let fixture cleanup errors mask the real test failure
                print(f"\\nWarning: Failed to save display on failure: {e}")


@pytest.fixture
def capture_on_failure(request):
    """Fixture that automatically captures display on test failure.
    
    This fixture can be used in tests that create their own terminal apps
    and want automatic failure capture.
    
    Usage:
        def test_something(capture_on_failure):
            app = TerminalApp(...)
            capture_on_failure.register(app)
            # ... test code ...
    """
    registered_apps = []
    
    class CaptureManager:
        def register(self, terminal_app):
            """Register a terminal app for capture on failure."""
            registered_apps.append(terminal_app)
            
    manager = CaptureManager()
    
    yield manager
    
    # Check if test failed and capture if needed
    if hasattr(request.node, 'rep_call') and request.node.rep_call.failed:
        for app in registered_apps:
            try:
                display_content = app.capture_display()
                test_name = request.node.name
                fixtures_dir = Path(__file__).parent / "failures"
                save_display_on_failure(display_content, test_name, fixtures_dir)
            except Exception as e:
                print(f"\\nWarning: Failed to save display for app: {e}")


# Configure pytest-specific settings for E2E tests
def pytest_configure(config):
    """Configure pytest for E2E testing."""
    # Add custom markers
    config.addinivalue_line(
        "markers", "e2e: mark test as end-to-end integration test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers automatically."""
    for item in items:
        # Auto-mark E2E tests
        if "e2e" in str(item.fspath):
            item.add_marker(pytest.mark.e2e)
            
        # Auto-mark slow tests (terminal tests are typically slow)
        if any(fixture in item.fixturenames for fixture in ['tigs_app', 'terminal_app_factory']):
            item.add_marker(pytest.mark.slow)