"""Root-level pytest configuration for cross-language E2E testing."""

import os
import tempfile
from pathlib import Path
from typing import Generator, Optional, Dict, Any

import pytest

# Import the e2e framework
from tests.e2e.framework import TerminalApp
from tests.e2e.framework.utils import create_test_repo, cleanup_test_repo
from tests.e2e.framework.assertions import save_display_on_failure


# Configuration for different tigs implementations
TIGS_IMPLEMENTATIONS = {
    "python": {
        "command": ["uv", "run", "--project", "python", "python", "-c", "from src.cli import main; main()"],
        "cwd": Path(__file__).parent.parent,
        "description": "Python implementation via uv"
    },
    # Future implementations can be added here
    # "rust": {
    #     "command": ["cargo", "run", "--manifest-path", "rust/Cargo.toml", "--"],
    #     "cwd": Path(__file__).parent.parent,
    #     "description": "Rust implementation via cargo"
    # },
    # "go": {
    #     "command": ["go", "run", "go/main.go"],
    #     "cwd": Path(__file__).parent.parent,
    #     "description": "Go implementation"
    # },
}


def pytest_addoption(parser):
    """Add command line options for test configuration."""
    parser.addoption(
        "--implementation",
        action="store", 
        default="python",
        choices=list(TIGS_IMPLEMENTATIONS.keys()),
        help="Which tigs implementation to test"
    )
    parser.addoption(
        "--tigs-timeout",
        action="store",
        type=float,
        default=10.0,
        help="Default timeout for tigs commands"
    )


@pytest.fixture(scope="session")
def implementation(request) -> str:
    """Get the selected implementation name."""
    return request.config.getoption("--implementation")


@pytest.fixture(scope="session") 
def implementation_config(implementation) -> Dict[str, Any]:
    """Get configuration for the selected implementation."""
    return TIGS_IMPLEMENTATIONS[implementation]


@pytest.fixture(scope="session")
def fixtures_dir() -> Path:
    """Get the directory containing test fixtures."""
    return Path(__file__).parent / "e2e" / "fixtures"


@pytest.fixture(scope="session") 
def screens_dir(fixtures_dir) -> Path:
    """Get the directory containing expected screen captures."""
    return fixtures_dir / "screens"


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


@pytest.fixture
def empty_repo(temp_dir) -> Generator[Path, None, None]:
    """Create an empty Git repository for testing."""
    repo_path = temp_dir / "empty_repo"
    create_test_repo(repo_path)
    yield repo_path


@pytest.fixture
def terminal_app_factory(implementation_config, temp_dir, request):
    """Factory to create TerminalApp instances for any implementation."""
    created_apps = []
    
    def create_app(
        args: Optional[list] = None,
        repo: Optional[Path] = None,
        **kwargs
    ) -> TerminalApp:
        """Create a TerminalApp instance for the selected implementation.
        
        Args:
            args: Command arguments (e.g., ["store"])
            repo: Repository path to use as working directory
            **kwargs: Additional TerminalApp arguments
            
        Returns:
            Configured TerminalApp instance
        """
        # Default arguments
        if args is None:
            args = ["store"]
            
        # Get implementation config
        base_command = implementation_config["command"][:]
        full_command = base_command + args
        
        # Set up environment
        env = kwargs.get('env', {})
        
        # Use repository as working directory if provided, otherwise implementation cwd
        if repo:
            cwd = repo
        else:
            cwd = kwargs.get('cwd', implementation_config.get("cwd", temp_dir))
        
        # Get timeout from command line or default
        timeout = kwargs.get('timeout', request.config.getoption("--tigs-timeout"))
        
        # Create the app - use bash wrapper for complex commands
        if len(full_command) > 1:
            # Complex command - wrap in bash
            bash_command = " ".join(f'"{arg}"' if " " in arg else arg for arg in full_command)
            app = TerminalApp(
                command="bash",
                args=["-c", f"cd {implementation_config['cwd']} && {bash_command}"],
                cwd=cwd,
                env=env,
                timeout=timeout,
                lines=kwargs.get('lines', 30),
                columns=kwargs.get('columns', 80)
            )
        else:
            # Simple command
            app = TerminalApp(
                command=full_command[0],
                args=full_command[1:] if len(full_command) > 1 else [],
                cwd=cwd,
                env=env,
                timeout=timeout,
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
        # Check if this is a terminal test (has terminal app fixture)
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
                fixtures_dir = Path(__file__).parent / "e2e" / "failures"
                save_display_on_failure(display_content, test_name, fixtures_dir)
                
            except Exception as e:
                # Don't let fixture cleanup errors mask the real test failure
                print(f"\\nWarning: Failed to save display on failure: {e}")


def pytest_configure(config):
    """Configure pytest for E2E testing."""
    # Add custom markers
    config.addinivalue_line(
        "markers", "python: tests for Python implementation"
    )
    config.addinivalue_line(
        "markers", "rust: tests for Rust implementation" 
    )
    config.addinivalue_line(
        "markers", "go: tests for Go implementation"
    )
    config.addinivalue_line(
        "markers", "cross_lang: cross-language compatibility tests"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers automatically."""
    implementation = config.getoption("--implementation")
    
    for item in items:
        # Auto-mark E2E tests
        if "e2e" in str(item.fspath):
            item.add_marker(pytest.mark.e2e)
            
        # Auto-mark implementation-specific tests
        item.add_marker(getattr(pytest.mark, implementation))
            
        # Auto-mark slow tests (terminal tests are typically slow)
        if any(fixture in item.fixturenames for fixture in ['tigs_app', 'terminal_app_factory']):
            item.add_marker(pytest.mark.slow)
            item.add_marker(pytest.mark.terminal)