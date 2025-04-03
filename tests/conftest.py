"""
Pytest configuration and fixtures for PythonWeb Installer tests.
"""
import os
import sys
import tempfile
import shutil
from typing import Dict, Any, Generator

import pytest
from click.testing import CliRunner

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from pythonweb_installer.config import Config


@pytest.fixture
def temp_dir() -> Generator[str, None, None]:
    """
    Create a temporary directory for test files.
    
    Returns:
        Generator yielding the path to the temporary directory
    """
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def test_config() -> Config:
    """
    Create a test configuration.
    
    Returns:
        Config: A test configuration object
    """
    config = Config()
    config.set("mode", "test")
    config.set("db_mode", "sqlite")
    config.set("template_repo", "https://github.com/test/PythonWeb.git")
    config.set("install_path", "/tmp/test_install")
    return config


@pytest.fixture
def cli_runner() -> CliRunner:
    """
    Create a Click CLI test runner.
    
    Returns:
        CliRunner: A Click test runner
    """
    return CliRunner()


@pytest.fixture
def mock_env_vars(monkeypatch) -> Dict[str, str]:
    """
    Set up mock environment variables for testing.
    
    Args:
        monkeypatch: Pytest monkeypatch fixture
        
    Returns:
        Dict[str, str]: Dictionary of environment variables
    """
    env_vars = {
        "PYTHONWEB_MODE": "test",
        "PYTHONWEB_DB_MODE": "sqlite",
        "PYTHONWEB_REPO": "https://github.com/test/PythonWeb.git",
        "PYTHONWEB_INSTALL_PATH": "/tmp/test_install",
    }
    
    for key, value in env_vars.items():
        monkeypatch.setenv(key, value)
    
    return env_vars
