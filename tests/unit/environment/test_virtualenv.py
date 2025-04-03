"""
Unit tests for virtual environment functionality.
"""
import os
import sys
import platform
import tempfile
import shutil
import subprocess
from unittest.mock import patch, MagicMock

import pytest

from pythonweb_installer.environment.virtualenv import (
    detect_python_version,
    find_python_executable,
    create_virtual_environment,
    get_activation_script,
    run_in_virtual_environment,
    upgrade_pip,
    list_installed_packages
)


class TestVirtualEnv:
    """Tests for virtual environment functionality."""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for test files."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)

    def test_detect_python_version(self):
        """Test detecting Python version."""
        success, version_info = detect_python_version()

        assert success is True
        assert "major" in version_info
        assert "minor" in version_info
        assert "micro" in version_info
        assert "version" in version_info
        assert "executable" in version_info
        assert "platform" in version_info
        assert "is_64bit" in version_info

        assert version_info["major"] == sys.version_info.major
        assert version_info["minor"] == sys.version_info.minor
        assert version_info["micro"] == sys.version_info.micro

    @patch('subprocess.run')
    def test_find_python_executable_current(self, mock_run):
        """Test finding the current Python executable."""
        success, executable = find_python_executable()

        assert success is True
        assert executable == sys.executable
        mock_run.assert_not_called()

    @patch('subprocess.run')
    def test_find_python_executable_specific_version_windows(self, mock_run):
        """Test finding a specific Python version on Windows."""
        # Skip if not on Windows
        if platform.system() != "Windows":
            pytest.skip("Test only applicable on Windows")

        # Configure the mock
        mock_process = MagicMock()
        mock_process.stdout = "C:\\Python39\\python.exe\n"
        mock_run.return_value = mock_process

        success, executable = find_python_executable("3.9")

        assert success is True
        assert executable == "C:\\Python39\\python.exe"
        mock_run.assert_called_once()

    @patch('subprocess.run')
    def test_find_python_executable_specific_version_unix(self, mock_run):
        """Test finding a specific Python version on Unix-like systems."""
        # Skip if on Windows
        if platform.system() == "Windows":
            pytest.skip("Test only applicable on Unix-like systems")

        # Configure the mock
        mock_process = MagicMock()
        mock_process.stdout = "/usr/bin/python3.9\n"
        mock_run.return_value = mock_process

        success, executable = find_python_executable("3.9")

        assert success is True
        assert executable == "/usr/bin/python3.9"
        mock_run.assert_called_once()

    @patch('subprocess.run')
    def test_find_python_executable_not_found(self, mock_run):
        """Test finding a Python version that doesn't exist."""
        # Configure the mock to raise an exception
        mock_run.side_effect = subprocess.CalledProcessError(1, "py", stderr=b"Command failed")

        success, message = find_python_executable("9.9")  # Unlikely version

        assert success is False
        assert "Could not find Python 9.9" in message

    @patch('subprocess.run')
    def test_create_virtual_environment_success(self, mock_run, temp_dir):
        """Test successful virtual environment creation."""
        # Configure the mock
        mock_run.return_value = MagicMock(returncode=0)

        env_path = os.path.join(temp_dir, "venv")
        success, message = create_virtual_environment(env_path)

        assert success is True
        assert "Successfully created virtual environment" in message
        mock_run.assert_called_once()

    @patch('subprocess.run')
    def test_create_virtual_environment_failure(self, mock_run, temp_dir):
        """Test virtual environment creation failure."""
        # Configure the mock to raise an exception
        mock_run.side_effect = subprocess.CalledProcessError(1, "venv", stderr=b"Command failed")

        env_path = os.path.join(temp_dir, "venv")
        success, message = create_virtual_environment(env_path)

        assert success is False
        assert "Failed to create virtual environment" in message

    @patch('os.path.exists')
    def test_create_virtual_environment_already_exists(self, mock_exists, temp_dir):
        """Test creating a virtual environment that already exists."""
        # Configure the mock to simulate an existing virtual environment
        mock_exists.side_effect = lambda path: True

        env_path = os.path.join(temp_dir, "venv")
        success, message = create_virtual_environment(env_path)

        assert success is True
        assert "Virtual environment already exists" in message

    @patch('os.path.exists')
    def test_get_activation_script_windows(self, mock_exists, temp_dir):
        """Test getting activation script on Windows."""
        # Skip if not on Windows
        if platform.system() != "Windows":
            pytest.skip("Test only applicable on Windows")

        # Configure the mock to simulate an existing virtual environment
        mock_exists.side_effect = lambda path: True

        env_path = os.path.join(temp_dir, "venv")
        success, script = get_activation_script(env_path)

        assert success is True
        assert "Scripts\\activate.bat" in script

    @patch('os.path.exists')
    def test_get_activation_script_unix(self, mock_exists, temp_dir):
        """Test getting activation script on Unix-like systems."""
        # Skip if on Windows
        if platform.system() == "Windows":
            pytest.skip("Test only applicable on Unix-like systems")

        # Configure the mock to simulate an existing virtual environment
        mock_exists.side_effect = lambda path: True

        env_path = os.path.join(temp_dir, "venv")
        success, script = get_activation_script(env_path)

        assert success is True
        assert "source" in script
        assert "bin/activate" in script

    @patch('os.path.exists')
    def test_get_activation_script_not_venv(self, mock_exists, temp_dir):
        """Test getting activation script for a directory that's not a virtual environment."""
        # Configure the mock to simulate a non-virtual environment directory
        mock_exists.side_effect = lambda path: "pyvenv.cfg" not in path

        env_path = os.path.join(temp_dir, "not_venv")
        success, message = get_activation_script(env_path)

        assert success is False
        assert "is not a virtual environment" in message

    @patch('os.path.exists')
    @patch('subprocess.run')
    def test_run_in_virtual_environment_success(self, mock_run, mock_exists, temp_dir):
        """Test running a command in a virtual environment successfully."""
        # Configure the mocks
        mock_exists.return_value = True
        mock_process = MagicMock()
        mock_process.stdout = "Command output\n"
        mock_run.return_value = mock_process

        env_path = os.path.join(temp_dir, "venv")
        success, output = run_in_virtual_environment(env_path, "import sys; print(sys.version)")

        assert success is True
        assert output == "Command output"
        mock_run.assert_called_once()

    @patch('os.path.exists')
    @patch('subprocess.run')
    def test_run_in_virtual_environment_failure(self, mock_run, mock_exists, temp_dir):
        """Test running a command in a virtual environment with failure."""
        # Configure the mocks
        mock_exists.return_value = True
        mock_run.side_effect = subprocess.CalledProcessError(1, "python", stderr=b"Command failed")

        env_path = os.path.join(temp_dir, "venv")
        success, message = run_in_virtual_environment(env_path, "invalid command")

        assert success is False
        assert "Command failed" in message

    @patch('os.path.exists')
    def test_run_in_virtual_environment_not_venv(self, mock_exists, temp_dir):
        """Test running a command in a directory that's not a virtual environment."""
        # Configure the mock to simulate a non-virtual environment directory
        mock_exists.side_effect = lambda path: "pyvenv.cfg" not in path

        env_path = os.path.join(temp_dir, "not_venv")
        success, message = run_in_virtual_environment(env_path, "command")

        assert success is False
        assert "is not a virtual environment" in message

    @patch('os.path.exists')
    @patch('subprocess.run')
    def test_upgrade_pip_success(self, mock_run, mock_exists, temp_dir):
        """Test upgrading pip successfully."""
        # Configure the mocks
        mock_exists.return_value = True
        mock_process = MagicMock()
        mock_process.stdout = "Successfully upgraded pip\n"
        mock_run.return_value = mock_process

        env_path = os.path.join(temp_dir, "venv")
        success, message = upgrade_pip(env_path)

        assert success is True
        assert "Successfully upgraded pip" in message
        mock_run.assert_called_once()

    @patch('os.path.exists')
    @patch('subprocess.run')
    def test_upgrade_pip_failure(self, mock_run, mock_exists, temp_dir):
        """Test upgrading pip with failure."""
        # Configure the mocks
        mock_exists.return_value = True
        mock_run.side_effect = subprocess.CalledProcessError(1, "pip", stderr=b"Command failed")

        env_path = os.path.join(temp_dir, "venv")
        success, message = upgrade_pip(env_path)

        assert success is False
        assert "Failed to upgrade pip" in message

    @patch('os.path.exists')
    def test_upgrade_pip_no_pip(self, mock_exists, temp_dir):
        """Test upgrading pip when pip is not installed."""
        # Configure the mock to simulate missing pip
        mock_exists.return_value = False

        env_path = os.path.join(temp_dir, "venv")
        success, message = upgrade_pip(env_path)

        assert success is False
        assert "Pip executable not found" in message

    @patch('os.path.exists')
    @patch('subprocess.run')
    def test_list_installed_packages_success(self, mock_run, mock_exists, temp_dir):
        """Test listing installed packages successfully."""
        # Configure the mocks
        mock_exists.return_value = True
        mock_process = MagicMock()
        mock_process.stdout = '[{"name": "pip", "version": "21.0.1"}, {"name": "setuptools", "version": "53.0.0"}]'
        mock_run.return_value = mock_process

        env_path = os.path.join(temp_dir, "venv")
        success, packages = list_installed_packages(env_path)

        assert success is True
        assert len(packages) == 2
        assert packages[0]["name"] == "pip"
        assert packages[0]["version"] == "21.0.1"
        assert packages[1]["name"] == "setuptools"
        assert packages[1]["version"] == "53.0.0"
        mock_run.assert_called_once()

    @patch('os.path.exists')
    @patch('subprocess.run')
    def test_list_installed_packages_failure(self, mock_run, mock_exists, temp_dir):
        """Test listing installed packages with failure."""
        # Configure the mocks
        mock_exists.return_value = True
        mock_run.side_effect = subprocess.CalledProcessError(1, "pip", stderr=b"Command failed")

        env_path = os.path.join(temp_dir, "venv")
        success, packages = list_installed_packages(env_path)

        assert success is False
        assert len(packages) == 0

    @patch('os.path.exists')
    def test_list_installed_packages_no_pip(self, mock_exists, temp_dir):
        """Test listing installed packages when pip is not installed."""
        # Configure the mock to simulate missing pip
        mock_exists.return_value = False

        env_path = os.path.join(temp_dir, "venv")
        success, packages = list_installed_packages(env_path)

        assert success is False
        assert len(packages) == 0
