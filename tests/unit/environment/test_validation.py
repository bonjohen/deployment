"""
Unit tests for environment validation functionality.
"""
import os
import sys
import subprocess
import tempfile
import shutil
from unittest.mock import patch, MagicMock

import pytest

from pythonweb_installer.environment.validation import (
    validate_python_version,
    validate_virtual_environment,
    validate_dependencies,
    repair_virtual_environment,
    install_missing_dependencies
)


class TestEnvironmentValidation:
    """Tests for environment validation functionality."""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for test files."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)

    def test_validate_python_version_valid(self):
        """Test validating a valid Python version."""
        # Use a minimum version lower than the current version
        current_version = f"{sys.version_info.major}.{sys.version_info.minor}"
        min_version = f"{sys.version_info.major}.{sys.version_info.minor - 1}" if sys.version_info.minor > 0 else "3.0"

        valid, result = validate_python_version(min_version=min_version)

        assert valid is True
        assert result["valid"] is True
        assert result["current_version"] == f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        assert result["min_version"] == min_version
        assert result["meets_min"] is True
        assert result["meets_max"] is True

    def test_validate_python_version_invalid_min(self):
        """Test validating a Python version below the minimum."""
        # Use a minimum version higher than the current version
        current_version = f"{sys.version_info.major}.{sys.version_info.minor}"
        min_version = f"{sys.version_info.major}.{sys.version_info.minor + 1}"

        valid, result = validate_python_version(min_version=min_version)

        assert valid is False
        assert result["valid"] is False
        assert result["current_version"] == f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        assert result["min_version"] == min_version
        assert result["meets_min"] is False
        assert result["meets_max"] is True

    def test_validate_python_version_invalid_max(self):
        """Test validating a Python version above the maximum."""
        # Use a maximum version lower than the current version
        current_version = f"{sys.version_info.major}.{sys.version_info.minor}"
        max_version = f"{sys.version_info.major}.{sys.version_info.minor - 1}" if sys.version_info.minor > 0 else "2.7"

        valid, result = validate_python_version(max_version=max_version)

        assert valid is False
        assert result["valid"] is False
        assert result["current_version"] == f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        assert result["max_version"] == max_version
        assert result["meets_min"] is True
        assert result["meets_max"] is False

    @patch('os.path.exists')
    @patch('subprocess.run')
    def test_validate_virtual_environment_valid(self, mock_run, mock_exists, temp_dir):
        """Test validating a valid virtual environment."""
        # Configure the mocks
        mock_exists.return_value = True
        mock_process = MagicMock()
        mock_process.stdout = "Python 3.9.5\n"
        mock_run.return_value = mock_process

        env_path = os.path.join(temp_dir, "venv")
        valid, result = validate_virtual_environment(env_path)

        assert valid is True
        assert result["valid"] is True
        assert result["path"] == env_path
        assert result["exists"] is True
        assert result["has_pyvenv_cfg"] is True
        assert result["has_python_exe"] is True
        assert result["python_version"] == "Python 3.9.5"

    @patch('os.path.exists')
    def test_validate_virtual_environment_not_exists(self, mock_exists, temp_dir):
        """Test validating a non-existent virtual environment."""
        # Configure the mock
        mock_exists.return_value = False

        env_path = os.path.join(temp_dir, "nonexistent_venv")
        valid, result = validate_virtual_environment(env_path)

        assert valid is False
        assert result["valid"] is False
        assert result["path"] == env_path
        assert result["exists"] is False

    @patch('os.path.exists')
    def test_validate_virtual_environment_missing_pyvenv_cfg(self, mock_exists, temp_dir):
        """Test validating a directory without pyvenv.cfg."""
        # Configure the mock to simulate missing pyvenv.cfg
        def exists_side_effect(path):
            return "pyvenv.cfg" not in path

        mock_exists.side_effect = exists_side_effect

        env_path = os.path.join(temp_dir, "not_venv")
        valid, result = validate_virtual_environment(env_path)

        assert valid is False
        assert result["valid"] is False
        assert result["path"] == env_path
        assert result["exists"] is True
        assert result["has_pyvenv_cfg"] is False

    @patch('os.path.exists')
    def test_validate_virtual_environment_missing_python(self, mock_exists, temp_dir):
        """Test validating a virtual environment without Python executable."""
        # Configure the mock to simulate missing Python executable
        def exists_side_effect(path):
            if os.path.dirname(path) == temp_dir:
                return True  # Directory exists
            if "pyvenv.cfg" in path:
                return True  # pyvenv.cfg exists
            if "python" in path:
                return False  # Python executable doesn't exist
            return True

        mock_exists.side_effect = exists_side_effect

        env_path = os.path.join(temp_dir, "venv")
        valid, result = validate_virtual_environment(env_path)

        assert valid is False
        assert result["valid"] is False
        assert result["path"] == env_path
        assert result["exists"] is True
        assert result["has_pyvenv_cfg"] is True
        assert result["has_python_exe"] is False

    @patch('pythonweb_installer.environment.validation.list_installed_packages')
    def test_validate_dependencies_all_valid(self, mock_list_packages, temp_dir):
        """Test validating dependencies when all are installed with correct versions."""
        # Configure the mock
        mock_list_packages.return_value = (
            True,
            [
                {"name": "package1", "version": "1.0.0"},
                {"name": "package2", "version": "2.0.0"},
                {"name": "package3", "version": "3.0.0"},
            ]
        )

        env_path = os.path.join(temp_dir, "venv")
        required_packages = [
            {"name": "package1", "version": "1.0.0"},
            {"name": "package2", "version": "2.0.0"},
        ]

        valid, result = validate_dependencies(env_path, required_packages)

        assert valid is True
        assert result["valid"] is True
        assert len(result["missing_packages"]) == 0
        assert len(result["version_mismatches"]) == 0
        assert len(result["installed_packages"]) == 3

    @patch('pythonweb_installer.environment.validation.list_installed_packages')
    def test_validate_dependencies_missing_package(self, mock_list_packages, temp_dir):
        """Test validating dependencies when a package is missing."""
        # Configure the mock
        mock_list_packages.return_value = (
            True,
            [
                {"name": "package1", "version": "1.0.0"},
                {"name": "package2", "version": "2.0.0"},
            ]
        )

        env_path = os.path.join(temp_dir, "venv")
        required_packages = [
            {"name": "package1", "version": "1.0.0"},
            {"name": "package3", "version": "3.0.0"},  # Missing package
        ]

        valid, result = validate_dependencies(env_path, required_packages)

        assert valid is False
        assert result["valid"] is False
        assert len(result["missing_packages"]) == 1
        assert result["missing_packages"][0]["name"] == "package3"
        assert len(result["version_mismatches"]) == 0
        assert len(result["installed_packages"]) == 2

    @patch('pythonweb_installer.environment.validation.list_installed_packages')
    def test_validate_dependencies_version_mismatch(self, mock_list_packages, temp_dir):
        """Test validating dependencies when a package has a version mismatch."""
        # Configure the mock
        mock_list_packages.return_value = (
            True,
            [
                {"name": "package1", "version": "1.0.0"},
                {"name": "package2", "version": "2.0.0"},  # Different version
            ]
        )

        env_path = os.path.join(temp_dir, "venv")
        required_packages = [
            {"name": "package1", "version": "1.0.0"},
            {"name": "package2", "version": "2.1.0"},  # Required different version
        ]

        valid, result = validate_dependencies(env_path, required_packages)

        assert valid is False
        assert result["valid"] is False
        assert len(result["missing_packages"]) == 0
        assert len(result["version_mismatches"]) == 1
        assert result["version_mismatches"][0]["name"] == "package2"
        assert result["version_mismatches"][0]["required_version"] == "2.1.0"
        assert result["version_mismatches"][0]["installed_version"] == "2.0.0"
        assert len(result["installed_packages"]) == 2

    @patch('pythonweb_installer.environment.validation.list_installed_packages')
    def test_validate_dependencies_list_failure(self, mock_list_packages, temp_dir):
        """Test validating dependencies when listing packages fails."""
        # Configure the mock
        mock_list_packages.return_value = (False, [])

        env_path = os.path.join(temp_dir, "venv")
        required_packages = [
            {"name": "package1", "version": "1.0.0"},
        ]

        valid, result = validate_dependencies(env_path, required_packages)

        assert valid is False
        assert result["valid"] is False
        assert len(result["installed_packages"]) == 0

    @patch('pythonweb_installer.environment.validation.validate_virtual_environment')
    @patch('subprocess.run')
    def test_repair_virtual_environment_already_valid(self, mock_run, mock_validate, temp_dir):
        """Test repairing a virtual environment that's already valid."""
        # Configure the mock
        mock_validate.return_value = (True, {"valid": True})

        env_path = os.path.join(temp_dir, "venv")
        success, message = repair_virtual_environment(env_path)

        assert success is True
        assert "already valid" in message
        mock_run.assert_not_called()

    @patch('pythonweb_installer.environment.validation.validate_virtual_environment')
    def test_repair_virtual_environment_not_exists(self, mock_validate, temp_dir):
        """Test repairing a non-existent virtual environment."""
        # Configure the mock
        mock_validate.return_value = (False, {"valid": False, "exists": False})

        env_path = os.path.join(temp_dir, "nonexistent_venv")
        success, message = repair_virtual_environment(env_path)

        assert success is False
        assert "Cannot repair" in message

    @patch('pythonweb_installer.environment.validation.validate_virtual_environment')
    @patch('subprocess.run')
    def test_repair_virtual_environment_success(self, mock_run, mock_validate, temp_dir):
        """Test successfully repairing a virtual environment."""
        # Configure the mocks for initial validation (invalid) and after repair (valid)
        mock_validate.side_effect = [
            (False, {"valid": False, "exists": True, "has_pyvenv_cfg": True, "has_pip_exe": False}),
            (True, {"valid": True})
        ]
        mock_run.return_value = MagicMock(returncode=0)

        env_path = os.path.join(temp_dir, "venv")
        success, message = repair_virtual_environment(env_path)

        assert success is True
        assert "Successfully repaired" in message
        mock_run.assert_called_once()

    @patch('pythonweb_installer.environment.validation.validate_virtual_environment')
    @patch('subprocess.run')
    def test_repair_virtual_environment_failure(self, mock_run, mock_validate, temp_dir):
        """Test failing to repair a virtual environment."""
        # Configure the mocks for initial validation (invalid) and after repair (still invalid)
        mock_validate.side_effect = [
            (False, {"valid": False, "exists": True, "has_pyvenv_cfg": True, "has_pip_exe": False}),
            (False, {"valid": False})
        ]
        mock_run.side_effect = subprocess.CalledProcessError(1, "python", stderr=b"Command failed")

        env_path = os.path.join(temp_dir, "venv")
        success, message = repair_virtual_environment(env_path)

        assert success is False
        assert "Failed to install pip" in message

    @patch('pythonweb_installer.environment.validation.validate_dependencies')
    def test_install_missing_dependencies_already_valid(self, mock_validate, temp_dir):
        """Test installing dependencies when all are already installed."""
        # Configure the mock
        mock_validate.return_value = (True, {"valid": True})

        env_path = os.path.join(temp_dir, "venv")
        required_packages = [
            {"name": "package1", "version": "1.0.0"},
        ]

        success, result = install_missing_dependencies(env_path, required_packages)

        assert success is True
        assert "All dependencies are already installed" in result["message"]

    @patch('pythonweb_installer.environment.validation.validate_dependencies')
    @patch('os.path.exists')
    @patch('subprocess.run')
    def test_install_missing_dependencies_success(self, mock_run, mock_exists, mock_validate, temp_dir):
        """Test successfully installing missing dependencies."""
        # Configure the mocks
        mock_validate.side_effect = [
            (False, {
                "valid": False,
                "missing_packages": [{"name": "package3", "version": "3.0.0"}],
                "version_mismatches": [
                    {
                        "name": "package2",
                        "required_version": "2.1.0",
                        "installed_version": "2.0.0"
                    }
                ]
            }),
            (True, {"valid": True})
        ]
        mock_exists.return_value = True
        mock_run.return_value = MagicMock(returncode=0)

        env_path = os.path.join(temp_dir, "venv")
        required_packages = [
            {"name": "package1", "version": "1.0.0"},
            {"name": "package2", "version": "2.1.0"},
            {"name": "package3", "version": "3.0.0"},
        ]

        success, result = install_missing_dependencies(env_path, required_packages)

        assert success is True
        assert len(result["installed"]) == 1
        assert result["installed"][0]["name"] == "package3"
        assert len(result["upgraded"]) == 1
        assert result["upgraded"][0]["name"] == "package2"
        assert len(result["failed"]) == 0
        assert result["all_dependencies_valid"] is True
        assert mock_run.call_count == 2  # One for install, one for upgrade

    @patch('pythonweb_installer.environment.validation.validate_dependencies')
    @patch('os.path.exists')
    @patch('subprocess.run')
    def test_install_missing_dependencies_partial_failure(self, mock_run, mock_exists, mock_validate, temp_dir):
        """Test partially failing to install dependencies."""
        # Configure the mocks
        mock_validate.side_effect = [
            (False, {
                "valid": False,
                "missing_packages": [{"name": "package3", "version": "3.0.0"}],
                "version_mismatches": []
            }),
            (False, {"valid": False})
        ]
        mock_exists.return_value = True
        mock_run.side_effect = subprocess.CalledProcessError(1, "pip", stderr=b"Command failed")

        env_path = os.path.join(temp_dir, "venv")
        required_packages = [
            {"name": "package1", "version": "1.0.0"},
            {"name": "package3", "version": "3.0.0"},
        ]

        success, result = install_missing_dependencies(env_path, required_packages)

        assert success is False
        assert len(result["installed"]) == 0
        assert len(result["failed"]) == 1
        assert result["failed"][0]["name"] == "package3"
        assert result["all_dependencies_valid"] is False

    @patch('pythonweb_installer.environment.validation.validate_dependencies')
    @patch('os.path.exists')
    def test_install_missing_dependencies_no_pip(self, mock_exists, mock_validate, temp_dir):
        """Test installing dependencies when pip is not available."""
        # Configure the mocks
        mock_validate.return_value = (
            False,
            {
                "valid": False,
                "missing_packages": [{"name": "package3", "version": "3.0.0"}],
                "version_mismatches": []
            }
        )
        mock_exists.return_value = False

        env_path = os.path.join(temp_dir, "venv")
        required_packages = [
            {"name": "package1", "version": "1.0.0"},
            {"name": "package3", "version": "3.0.0"},
        ]

        success, result = install_missing_dependencies(env_path, required_packages)

        assert success is False
        assert "Pip executable not found" in result["error"]
