"""
Unit tests for package installation functionality.
"""
import os
import json
import tempfile
import shutil
import subprocess
from unittest.mock import patch, MagicMock

import pytest

from pythonweb_installer.dependencies.packages import (
    parse_requirements_file,
    parse_package_spec,
    install_package,
    install_requirements,
    uninstall_package,
    get_package_info,
    generate_requirements_file,
    check_outdated_packages
)


class TestPackages:
    """Tests for package installation functionality."""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for test files."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def requirements_file(self, temp_dir):
        """Create a sample requirements.txt file."""
        file_path = os.path.join(temp_dir, "requirements.txt")
        with open(file_path, "w") as f:
            f.write("""
# Sample requirements file
package1==1.0.0
package2>=2.0.0
package3<3.0.0
package4~=4.0.0
package5!=5.0.0
package6>1.0.0,<2.0.0
-e git+https://github.com/user/repo.git#egg=package7
http://example.com/package8-1.0.0.tar.gz
# Comment line
--find-links http://example.com/packages
--no-index
-r other-requirements.txt
            """)
        return file_path

    def test_parse_requirements_file(self, requirements_file):
        """Test parsing a requirements file."""
        success, packages = parse_requirements_file(requirements_file)

        assert success is True
        assert len(packages) == 7
        assert packages[0]["name"] == "package1"
        assert packages[0]["version"] == "1.0.0"
        assert packages[1]["name"] == "package2"
        assert "version_spec" in packages[1]
        assert packages[1]["version_spec"] == ">=2.0.0"
        assert packages[6]["direct_reference"] is True

    def test_parse_requirements_file_not_exists(self, temp_dir):
        """Test parsing a non-existent requirements file."""
        file_path = os.path.join(temp_dir, "nonexistent.txt")
        success, packages = parse_requirements_file(file_path)

        assert success is False
        assert len(packages) == 0

    def test_parse_package_spec_simple(self):
        """Test parsing a simple package specification."""
        package_info = parse_package_spec("package")

        assert package_info is not None
        assert package_info["name"] == "package"
        assert "version" not in package_info
        assert "version_spec" not in package_info

    def test_parse_package_spec_with_version(self):
        """Test parsing a package specification with version."""
        package_info = parse_package_spec("package==1.0.0")

        assert package_info is not None
        assert package_info["name"] == "package"
        assert package_info["version"] == "1.0.0"
        assert package_info["version_spec"] == "==1.0.0"

    def test_parse_package_spec_with_complex_version(self):
        """Test parsing a package specification with complex version constraints."""
        package_info = parse_package_spec("package>=1.0.0,<2.0.0")

        assert package_info is not None
        assert package_info["name"] == "package"
        assert "version" not in package_info
        assert package_info["version_spec"] == ">=1.0.0,<2.0.0"

    @patch('pythonweb_installer.dependencies.packages.re.search')
    def test_parse_package_spec_url(self, mock_search):
        """Test parsing a URL package specification."""
        # Configure the mock to simulate finding an egg fragment
        mock_match = MagicMock()
        mock_match.group.return_value = "package"
        mock_search.return_value = mock_match

        package_info = parse_package_spec("git+https://github.com/user/repo.git#egg=package")

        assert package_info is not None
        assert package_info["name"] == "package"
        assert package_info["direct_reference"] is True
        assert "url" in package_info

    def test_parse_package_spec_url_no_egg(self):
        """Test parsing a URL package specification without egg fragment."""
        package_info = parse_package_spec("https://example.com/package-1.0.0.tar.gz")

        assert package_info is not None
        assert "unknown" in package_info["name"]
        assert package_info["direct_reference"] is True
        assert "url" in package_info

    def test_parse_package_spec_invalid(self):
        """Test parsing an invalid package specification."""
        package_info = parse_package_spec("")
        assert package_info is None

        package_info = parse_package_spec("# Comment")
        assert package_info is None

    @patch('os.path.exists')
    @patch('subprocess.run')
    def test_install_package_success(self, mock_run, mock_exists, temp_dir):
        """Test successful package installation."""
        # Configure the mocks
        mock_exists.return_value = True
        mock_process = MagicMock()
        mock_process.stdout = "Successfully installed package1-1.0.0"
        mock_run.return_value = mock_process

        env_path = os.path.join(temp_dir, "venv")
        success, message = install_package(env_path, "package1==1.0.0")

        assert success is True
        assert "Successfully installed package" in message
        mock_run.assert_called_once()

    @patch('os.path.exists')
    @patch('subprocess.run')
    def test_install_package_with_options(self, mock_run, mock_exists, temp_dir):
        """Test package installation with additional options."""
        # Configure the mocks
        mock_exists.return_value = True
        mock_process = MagicMock()
        mock_process.stdout = "Successfully installed package1-1.0.0"
        mock_run.return_value = mock_process

        env_path = os.path.join(temp_dir, "venv")
        success, message = install_package(
            env_path,
            "package1==1.0.0",
            upgrade=True,
            index_url="https://pypi.org/simple",
            extra_index_url="https://example.com/simple",
            no_deps=True,
            user=True
        )

        assert success is True
        assert "Successfully installed package" in message
        mock_run.assert_called_once()

        # Check that the command includes all the options
        cmd = mock_run.call_args[0][0]
        assert "--upgrade" in cmd
        assert "--index-url" in cmd
        assert "https://pypi.org/simple" in cmd
        assert "--extra-index-url" in cmd
        assert "https://example.com/simple" in cmd
        assert "--no-deps" in cmd
        assert "--user" in cmd

    @patch('os.path.exists')
    @patch('subprocess.run')
    def test_install_package_failure(self, mock_run, mock_exists, temp_dir):
        """Test package installation failure."""
        # Configure the mocks
        mock_exists.return_value = True
        mock_run.side_effect = subprocess.CalledProcessError(1, "pip", stderr=b"Installation failed")

        env_path = os.path.join(temp_dir, "venv")
        success, message = install_package(env_path, "package1==1.0.0")

        assert success is False
        assert "Failed to install package" in message

    @patch('os.path.exists')
    def test_install_package_no_pip(self, mock_exists, temp_dir):
        """Test package installation when pip is not available."""
        # Configure the mock
        mock_exists.return_value = False

        env_path = os.path.join(temp_dir, "venv")
        success, message = install_package(env_path, "package1==1.0.0")

        assert success is False
        assert "Pip executable not found" in message

    @patch('os.path.exists')
    @patch('subprocess.run')
    def test_install_requirements_success(self, mock_run, mock_exists, temp_dir, requirements_file):
        """Test successful requirements installation."""
        # Configure the mocks
        mock_exists.return_value = True
        mock_process = MagicMock()
        mock_process.stdout = "Successfully installed package1-1.0.0 package2-2.0.0"
        mock_run.return_value = mock_process

        env_path = os.path.join(temp_dir, "venv")
        success, result = install_requirements(env_path, requirements_file)

        assert success is True
        assert "Successfully installed requirements" in result["message"]
        assert "installed_packages" in result
        mock_run.assert_called_once()

    @patch('os.path.exists')
    @patch('subprocess.run')
    def test_install_requirements_with_options(self, mock_run, mock_exists, temp_dir, requirements_file):
        """Test requirements installation with additional options."""
        # Configure the mocks
        mock_exists.return_value = True
        mock_process = MagicMock()
        mock_process.stdout = "Successfully installed package1-1.0.0 package2-2.0.0"
        mock_run.return_value = mock_process

        env_path = os.path.join(temp_dir, "venv")
        success, result = install_requirements(
            env_path,
            requirements_file,
            upgrade=True,
            index_url="https://pypi.org/simple",
            extra_index_url="https://example.com/simple"
        )

        assert success is True
        assert "Successfully installed requirements" in result["message"]
        mock_run.assert_called_once()

        # Check that the command includes all the options
        cmd = mock_run.call_args[0][0]
        assert "--upgrade" in cmd
        assert "--index-url" in cmd
        assert "https://pypi.org/simple" in cmd
        assert "--extra-index-url" in cmd
        assert "https://example.com/simple" in cmd

    @patch('os.path.exists')
    @patch('subprocess.run')
    def test_install_requirements_failure(self, mock_run, mock_exists, temp_dir, requirements_file):
        """Test requirements installation failure."""
        # Configure the mocks
        mock_exists.return_value = True
        mock_run.side_effect = subprocess.CalledProcessError(1, "pip", stderr=b"Installation failed")

        env_path = os.path.join(temp_dir, "venv")
        success, result = install_requirements(env_path, requirements_file)

        assert success is False
        assert "error" in result
        assert "Failed to install requirements" in result["error"]

    def test_install_requirements_file_not_exists(self, temp_dir):
        """Test requirements installation with a non-existent file."""
        file_path = os.path.join(temp_dir, "nonexistent.txt")
        env_path = os.path.join(temp_dir, "venv")
        success, result = install_requirements(env_path, file_path)

        assert success is False
        assert "error" in result
        assert "Requirements file not found" in result["error"]

    @patch('os.path.exists')
    @patch('subprocess.run')
    def test_uninstall_package_success(self, mock_run, mock_exists, temp_dir):
        """Test successful package uninstallation."""
        # Configure the mocks
        mock_exists.return_value = True
        mock_process = MagicMock()
        mock_process.stdout = "Successfully uninstalled package1-1.0.0"
        mock_run.return_value = mock_process

        env_path = os.path.join(temp_dir, "venv")
        success, message = uninstall_package(env_path, "package1")

        assert success is True
        assert "Successfully uninstalled package" in message
        mock_run.assert_called_once()

        # Check that the command includes the --yes option
        cmd = mock_run.call_args[0][0]
        assert "--yes" in cmd

    @patch('os.path.exists')
    @patch('subprocess.run')
    def test_uninstall_package_failure(self, mock_run, mock_exists, temp_dir):
        """Test package uninstallation failure."""
        # Configure the mocks
        mock_exists.return_value = True
        mock_run.side_effect = subprocess.CalledProcessError(1, "pip", stderr=b"Uninstallation failed")

        env_path = os.path.join(temp_dir, "venv")
        success, message = uninstall_package(env_path, "package1")

        assert success is False
        assert "Failed to uninstall package" in message

    @patch('os.path.exists')
    @patch('subprocess.run')
    def test_get_package_info_success(self, mock_run, mock_exists, temp_dir):
        """Test successful package information retrieval."""
        # Configure the mocks
        mock_exists.return_value = True
        mock_process = MagicMock()
        mock_process.stdout = """
Name: package1
Version: 1.0.0
Summary: Test package
Home-page: https://example.com
Author: Test Author
Author-email: author@example.com
License: MIT
Location: /path/to/site-packages
Requires: package2, package3
Required-by: package4, package5
"""
        mock_run.return_value = mock_process

        env_path = os.path.join(temp_dir, "venv")
        success, package_info = get_package_info(env_path, "package1")

        assert success is True
        assert package_info["name"] == "package1"
        assert package_info["version"] == "1.0.0"
        assert package_info["summary"] == "Test package"
        assert package_info["home_page"] == "https://example.com"
        assert package_info["author"] == "Test Author"
        assert package_info["author_email"] == "author@example.com"
        assert package_info["license"] == "MIT"
        assert package_info["location"] == "/path/to/site-packages"
        assert package_info["requires"] == ["package2", "package3"]
        assert package_info["required_by"] == ["package4", "package5"]

    @patch('os.path.exists')
    @patch('subprocess.run')
    def test_get_package_info_no_dependencies(self, mock_run, mock_exists, temp_dir):
        """Test package information retrieval with no dependencies."""
        # Configure the mocks
        mock_exists.return_value = True
        mock_process = MagicMock()
        mock_process.stdout = """
Name: package1
Version: 1.0.0
Summary: Test package
Home-page: https://example.com
Author: Test Author
Author-email: author@example.com
License: MIT
Location: /path/to/site-packages
Requires:
Required-by:
"""
        mock_run.return_value = mock_process

        env_path = os.path.join(temp_dir, "venv")
        success, package_info = get_package_info(env_path, "package1")

        assert success is True
        assert package_info["name"] == "package1"
        assert package_info["requires"] == []
        assert package_info["required_by"] == []

    @patch('os.path.exists')
    @patch('subprocess.run')
    def test_get_package_info_failure(self, mock_run, mock_exists, temp_dir):
        """Test package information retrieval failure."""
        # Configure the mocks
        mock_exists.return_value = True
        mock_run.side_effect = subprocess.CalledProcessError(1, "pip", stderr=b"Information retrieval failed")

        env_path = os.path.join(temp_dir, "venv")
        success, result = get_package_info(env_path, "package1")

        assert success is False
        assert "error" in result
        assert "Failed to get information for package" in result["error"]

    @patch('pythonweb_installer.dependencies.packages.list_installed_packages')
    def test_generate_requirements_file_success(self, mock_list_packages, temp_dir):
        """Test successful requirements file generation."""
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
        output_file = os.path.join(temp_dir, "requirements.txt")
        success, message = generate_requirements_file(env_path, output_file)

        assert success is True
        assert "Successfully generated requirements file" in message
        assert os.path.exists(output_file)

        # Verify file contents
        with open(output_file, "r") as f:
            content = f.read()
            assert "package1==1.0.0" in content
            assert "package2==2.0.0" in content
            assert "package3==3.0.0" in content

    @patch('pythonweb_installer.dependencies.packages.list_installed_packages')
    def test_generate_requirements_file_no_versions(self, mock_list_packages, temp_dir):
        """Test requirements file generation without version constraints."""
        # Configure the mock
        mock_list_packages.return_value = (
            True,
            [
                {"name": "package1", "version": "1.0.0"},
                {"name": "package2", "version": "2.0.0"},
            ]
        )

        env_path = os.path.join(temp_dir, "venv")
        output_file = os.path.join(temp_dir, "requirements.txt")
        success, message = generate_requirements_file(env_path, output_file, include_versions=False)

        assert success is True
        assert "Successfully generated requirements file" in message

        # Verify file contents
        with open(output_file, "r") as f:
            content = f.read()
            assert "package1" in content and "==" not in content
            assert "package2" in content and "==" not in content

    @patch('pythonweb_installer.dependencies.packages.list_installed_packages')
    def test_generate_requirements_file_with_exclusions(self, mock_list_packages, temp_dir):
        """Test requirements file generation with package exclusions."""
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
        output_file = os.path.join(temp_dir, "requirements.txt")
        success, message = generate_requirements_file(
            env_path,
            output_file,
            exclude_packages=["package2"]
        )

        assert success is True
        assert "Successfully generated requirements file" in message

        # Verify file contents
        with open(output_file, "r") as f:
            content = f.read()
            assert "package1==1.0.0" in content
            assert "package2==2.0.0" not in content
            assert "package3==3.0.0" in content

    @patch('pythonweb_installer.dependencies.packages.list_installed_packages')
    def test_generate_requirements_file_failure(self, mock_list_packages, temp_dir):
        """Test requirements file generation failure."""
        # Configure the mock
        mock_list_packages.return_value = (False, [])

        env_path = os.path.join(temp_dir, "venv")
        output_file = os.path.join(temp_dir, "requirements.txt")
        success, message = generate_requirements_file(env_path, output_file)

        assert success is False
        assert "Failed to list installed packages" in message

    @patch('os.path.exists')
    @patch('subprocess.run')
    def test_check_outdated_packages_success(self, mock_run, mock_exists, temp_dir):
        """Test successful outdated packages check."""
        # Configure the mocks
        mock_exists.return_value = True
        mock_process = MagicMock()
        mock_process.stdout = json.dumps([
            {
                "name": "package1",
                "version": "1.0.0",
                "latest_version": "2.0.0",
                "latest_filetype": "wheel"
            },
            {
                "name": "package2",
                "version": "2.0.0",
                "latest_version": "3.0.0",
                "latest_filetype": "wheel"
            }
        ])
        mock_run.return_value = mock_process

        env_path = os.path.join(temp_dir, "venv")
        success, outdated_packages = check_outdated_packages(env_path)

        assert success is True
        assert len(outdated_packages) == 2
        assert outdated_packages[0]["name"] == "package1"
        assert outdated_packages[0]["version"] == "1.0.0"
        assert outdated_packages[0]["latest_version"] == "2.0.0"
        assert outdated_packages[1]["name"] == "package2"

    @patch('os.path.exists')
    @patch('subprocess.run')
    def test_check_outdated_packages_none(self, mock_run, mock_exists, temp_dir):
        """Test outdated packages check with no outdated packages."""
        # Configure the mocks
        mock_exists.return_value = True
        mock_process = MagicMock()
        mock_process.stdout = "[]"
        mock_run.return_value = mock_process

        env_path = os.path.join(temp_dir, "venv")
        success, outdated_packages = check_outdated_packages(env_path)

        assert success is True
        assert len(outdated_packages) == 0

    @patch('os.path.exists')
    @patch('subprocess.run')
    def test_check_outdated_packages_failure(self, mock_run, mock_exists, temp_dir):
        """Test outdated packages check failure."""
        # Configure the mocks
        mock_exists.return_value = True
        mock_run.side_effect = subprocess.CalledProcessError(1, "pip", stderr=b"Check failed")

        env_path = os.path.join(temp_dir, "venv")
        success, outdated_packages = check_outdated_packages(env_path)

        assert success is False
        assert len(outdated_packages) == 0
