"""
Unit tests for environment variables functionality.
"""
import os
import tempfile
import shutil
from unittest.mock import patch, MagicMock, mock_open

import pytest

from pythonweb_installer.environment.variables import (
    load_env_file,
    save_env_file,
    set_environment_variables,
    get_environment_variables,
    generate_env_file,
    find_env_files,
    merge_env_files
)


class TestEnvironmentVariables:
    """Tests for environment variables functionality."""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for test files."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def sample_env_content(self):
        """Sample .env file content."""
        return """
# This is a comment
KEY1=value1
KEY2="value with spaces"
KEY3='value with quotes'
EMPTY=
# Another comment
KEY4=value4
"""

    @pytest.fixture
    def sample_env_file(self, temp_dir, sample_env_content):
        """Create a sample .env file."""
        file_path = os.path.join(temp_dir, ".env")
        with open(file_path, "w") as f:
            f.write(sample_env_content)
        return file_path

    def test_load_env_file_success(self, sample_env_file):
        """Test loading environment variables from a file successfully."""
        success, env_vars = load_env_file(sample_env_file)

        assert success is True
        assert len(env_vars) == 5
        assert env_vars["KEY1"] == "value1"
        assert env_vars["KEY2"] == "value with spaces"
        assert env_vars["KEY3"] == "value with quotes"
        assert env_vars["KEY4"] == "value4"
        assert env_vars["EMPTY"] == ""

    def test_load_env_file_not_exists(self, temp_dir):
        """Test loading environment variables from a non-existent file."""
        file_path = os.path.join(temp_dir, "nonexistent.env")
        success, env_vars = load_env_file(file_path)

        assert success is False
        assert len(env_vars) == 0

    def test_load_env_file_invalid(self, temp_dir):
        """Test loading environment variables from an invalid file."""
        # Create an invalid .env file
        file_path = os.path.join(temp_dir, "invalid.env")
        with open(file_path, "w") as f:
            f.write("INVALID")

        success, env_vars = load_env_file(file_path)

        assert success is True  # Still returns success, just with no variables
        assert len(env_vars) == 0

    def test_save_env_file_success(self, temp_dir):
        """Test saving environment variables to a file successfully."""
        file_path = os.path.join(temp_dir, "output.env")
        env_vars = {
            "KEY1": "value1",
            "KEY2": "value with spaces",
            "KEY3": "value with quotes",
        }

        success, message = save_env_file(file_path, env_vars)

        assert success is True
        assert "Successfully saved" in message
        assert os.path.exists(file_path)

        # Verify file contents
        with open(file_path, "r") as f:
            content = f.read()
            assert "KEY1=value1" in content
            assert 'KEY2="value with spaces"' in content
            assert 'KEY3="value with quotes"' in content

    def test_save_env_file_already_exists(self, sample_env_file):
        """Test saving environment variables to a file that already exists."""
        env_vars = {"NEW_KEY": "new_value"}

        success, message = save_env_file(sample_env_file, env_vars, overwrite=False)

        assert success is False
        assert "already exists" in message

        # Test with overwrite=True
        success, message = save_env_file(sample_env_file, env_vars, overwrite=True)

        assert success is True
        assert "Successfully saved" in message

        # Verify file contents
        with open(sample_env_file, "r") as f:
            content = f.read()
            assert "NEW_KEY=new_value" in content
            assert "KEY1=value1" not in content  # Original content should be overwritten

    @patch("os.environ")
    def test_set_environment_variables_process_only(self, mock_environ):
        """Test setting environment variables in the current process only."""
        env_vars = {
            "TEST_KEY1": "test_value1",
            "TEST_KEY2": "test_value2",
        }

        success, message = set_environment_variables(env_vars, persistent=False)

        assert success is True
        assert "Successfully set" in message
        assert mock_environ.__setitem__.call_count == 2

    @patch("os.environ")
    @patch("platform.system")
    @patch("subprocess.run")
    def test_set_environment_variables_persistent_windows(self, mock_run, mock_platform, mock_environ):
        """Test setting persistent environment variables on Windows."""
        # Configure the mocks
        mock_platform.return_value = "Windows"
        mock_run.return_value = MagicMock(returncode=0)

        env_vars = {
            "TEST_KEY1": "test_value1",
            "TEST_KEY2": "test_value2",
        }

        success, message = set_environment_variables(env_vars, persistent=True)

        assert success is True
        assert "Successfully set" in message
        assert mock_environ.__setitem__.call_count == 2
        assert mock_run.call_count == 2

    @patch("os.environ")
    @patch("platform.system")
    @patch("os.path.exists")
    @patch("builtins.open", new_callable=mock_open)
    def test_set_environment_variables_persistent_unix(self, mock_file, mock_exists, mock_platform, mock_environ):
        """Test setting persistent environment variables on Unix-like systems."""
        # Configure the mocks
        mock_platform.return_value = "Linux"
        mock_exists.return_value = True

        env_vars = {
            "TEST_KEY1": "test_value1",
            "TEST_KEY2": "test_value2",
        }

        success, message = set_environment_variables(env_vars, persistent=True)

        assert success is True
        assert "Successfully set" in message
        assert mock_environ.__setitem__.call_count == 2
        mock_file.assert_called_once()
        mock_file().write.assert_called()

    def test_get_environment_variables_all(self):
        """Test getting all environment variables."""
        # Call the function with the real environment
        env_vars = get_environment_variables()

        # Verify that we got some environment variables
        assert len(env_vars) > 0
        # Check for some common environment variables
        assert any(k in env_vars for k in ['PATH', 'TEMP', 'HOME', 'USERPROFILE'])

    @patch("os.environ")
    def test_get_environment_variables_with_prefix(self, mock_environ):
        """Test getting environment variables with a specific prefix."""
        # Configure the mock
        mock_environ.items.return_value = [
            ("PREFIX_KEY1", "value1"),
            ("PREFIX_KEY2", "value2"),
            ("OTHER_KEY", "other_value"),
        ]
        # Set up the mock to behave like a dictionary
        mock_environ.__getitem__.side_effect = lambda key: dict(mock_environ.items.return_value).get(key)
        mock_environ.__iter__.return_value = iter([k for k, _ in mock_environ.items.return_value])

        # Call the function with a prefix
        env_vars = get_environment_variables(prefix="PREFIX_")

        # Verify that the function filtered the environment variables correctly
        mock_environ.items.assert_called_once()
        # We can verify the filtering logic by checking the keys in the result
        assert all(k.startswith("PREFIX_") for k in env_vars.keys())

    def test_generate_env_file_success(self, temp_dir):
        """Test generating an environment file from a template successfully."""
        # Create a template file
        template_path = os.path.join(temp_dir, "template.env")
        with open(template_path, "w") as f:
            f.write("""
# Template file
APP_NAME=${APP_NAME}
DB_HOST=${DB_HOST}
DB_PORT=$DB_PORT
API_KEY=${API_KEY}
""")

        output_path = os.path.join(temp_dir, "output.env")
        variables = {
            "APP_NAME": "MyApp",
            "DB_HOST": "localhost",
            "DB_PORT": "5432",
            "API_KEY": "secret_key",
        }

        success, message = generate_env_file(template_path, output_path, variables)

        assert success is True
        assert "Successfully generated" in message
        assert os.path.exists(output_path)

        # Verify file contents
        with open(output_path, "r") as f:
            content = f.read()
            assert "APP_NAME=MyApp" in content
            assert "DB_HOST=localhost" in content
            assert "DB_PORT=5432" in content
            assert "API_KEY=secret_key" in content

    def test_generate_env_file_template_not_exists(self, temp_dir):
        """Test generating an environment file from a non-existent template."""
        template_path = os.path.join(temp_dir, "nonexistent.env")
        output_path = os.path.join(temp_dir, "output.env")
        variables = {"KEY": "value"}

        success, message = generate_env_file(template_path, output_path, variables)

        assert success is False
        assert "Template file" in message
        assert "does not exist" in message

    def test_generate_env_file_output_exists(self, temp_dir):
        """Test generating an environment file when the output file already exists."""
        # Create a template file
        template_path = os.path.join(temp_dir, "template.env")
        with open(template_path, "w") as f:
            f.write("KEY=${VALUE}")

        # Create an output file
        output_path = os.path.join(temp_dir, "output.env")
        with open(output_path, "w") as f:
            f.write("EXISTING=value")

        variables = {"VALUE": "new_value"}

        success, message = generate_env_file(template_path, output_path, variables, overwrite=False)

        assert success is False
        assert "already exists" in message

        # Test with overwrite=True
        success, message = generate_env_file(template_path, output_path, variables, overwrite=True)

        assert success is True
        assert "Successfully generated" in message

        # Verify file contents
        with open(output_path, "r") as f:
            content = f.read()
            assert "KEY=new_value" in content
            assert "EXISTING=value" not in content  # Original content should be overwritten

    def test_find_env_files(self, temp_dir):
        """Test finding .env files in a directory."""
        # Create some .env files
        os.makedirs(os.path.join(temp_dir, "subdir"), exist_ok=True)

        with open(os.path.join(temp_dir, ".env"), "w") as f:
            f.write("ROOT=value")

        with open(os.path.join(temp_dir, "dev.env"), "w") as f:
            f.write("DEV=value")

        with open(os.path.join(temp_dir, "subdir", ".env"), "w") as f:
            f.write("SUBDIR=value")

        # Test recursive search
        env_files = find_env_files(temp_dir, recursive=True)

        assert len(env_files) == 3
        assert os.path.join(temp_dir, ".env") in env_files
        assert os.path.join(temp_dir, "dev.env") in env_files
        assert os.path.join(temp_dir, "subdir", ".env") in env_files

        # Test non-recursive search
        env_files = find_env_files(temp_dir, recursive=False)

        assert len(env_files) == 2
        assert os.path.join(temp_dir, ".env") in env_files
        assert os.path.join(temp_dir, "dev.env") in env_files
        assert os.path.join(temp_dir, "subdir", ".env") not in env_files

    def test_merge_env_files_success(self, temp_dir):
        """Test merging multiple .env files successfully."""
        # Create some .env files
        file1_path = os.path.join(temp_dir, "file1.env")
        with open(file1_path, "w") as f:
            f.write("KEY1=value1\nSHARED=file1")

        file2_path = os.path.join(temp_dir, "file2.env")
        with open(file2_path, "w") as f:
            f.write("KEY2=value2\nSHARED=file2")

        output_path = os.path.join(temp_dir, "merged.env")

        success, message = merge_env_files([file1_path, file2_path], output_path)

        assert success is True
        assert "Successfully saved" in message
        assert os.path.exists(output_path)

        # Verify file contents (file2 should override file1 for shared keys)
        with open(output_path, "r") as f:
            content = f.read()
            assert "KEY1=value1" in content
            assert "KEY2=value2" in content
            assert "SHARED=file2" in content  # file2 overrides file1

    def test_merge_env_files_output_exists(self, temp_dir):
        """Test merging .env files when the output file already exists."""
        # Create some .env files
        file1_path = os.path.join(temp_dir, "file1.env")
        with open(file1_path, "w") as f:
            f.write("KEY1=value1")

        output_path = os.path.join(temp_dir, "output.env")
        with open(output_path, "w") as f:
            f.write("EXISTING=value")

        success, message = merge_env_files([file1_path], output_path, overwrite=False)

        assert success is False
        assert "already exists" in message

        # Test with overwrite=True
        success, message = merge_env_files([file1_path], output_path, overwrite=True)

        assert success is True
        assert "Successfully saved" in message

        # Verify file contents
        with open(output_path, "r") as f:
            content = f.read()
            assert "KEY1=value1" in content
            assert "EXISTING=value" not in content  # Original content should be overwritten
