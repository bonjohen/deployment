"""
Unit tests for utility functions.
"""
import subprocess
import pytest
from unittest.mock import patch, MagicMock

from pythonweb_installer.utils import run_command


class TestUtils:
    """Tests for utility functions."""

    @patch('subprocess.run')
    def test_run_command_success(self, mock_run):
        """Test successful command execution."""
        # Configure the mock
        mock_process = MagicMock()
        mock_process.stdout = "Command output"
        mock_run.return_value = mock_process

        # Call the function
        result = run_command("echo 'test'")

        # Verify the result
        assert result is True
        mock_run.assert_called_once()

    @patch('subprocess.run')
    def test_run_command_failure(self, mock_run):
        """Test command execution failure."""
        # Configure the mock to raise an exception
        mock_run.side_effect = subprocess.CalledProcessError(1, "invalid_command", stderr="Command failed")

        # Call the function
        result = run_command("invalid_command")

        # Verify the result
        assert result is False
        mock_run.assert_called_once()
