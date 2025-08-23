"""
Test configuration and fixtures for pytest.
"""
import os
import tempfile
import pytest
from pathlib import Path

# Add the src directory to the Python path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

# Test configuration
TEST_DATA_DIR = Path(__file__).parent / 'test_data'
os.makedirs(TEST_DATA_DIR, exist_ok=True)

# Fixtures
@pytest.fixture(scope='session')
def test_data_dir():
    """Fixture to provide the test data directory."""
    return TEST_DATA_DIR

@pytest.fixture(scope='session')
def temp_dir():
    """Create a temporary directory that will be cleaned up after tests."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)

@pytest.fixture(autouse=True)
def set_test_env(monkeypatch):
    """Set up test environment variables."""
    # Set test database URL
    test_db_path = str(Path(__file__).parent / 'test.db')
    monkeypatch.setenv('DATABASE_URL', f'sqlite:///{test_db_path}')
    
    # Set test-specific configurations
    monkeypatch.setenv('FLASK_ENV', 'testing')
    monkeypatch.setenv('TESTING', 'True')
    
    # Disable rate limiting for tests
    monkeypatch.setenv('RATELIMIT_ENABLED', 'False')

# Import fixtures from other test modules
pytest_plugins = [
    'tests.fixtures.test_env',
    'tests.fixtures.test_ocr_module',
    'tests.fixtures.test_fts_check',
]
