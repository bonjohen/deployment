"""
Unit tests for repository authentication functionality.
"""
import os
import tempfile
import subprocess
from unittest.mock import patch, MagicMock, mock_open

import pytest

from pythonweb_installer.repository.auth import (
    setup_https_auth,
    setup_ssh_auth,
    create_ssh_key,
    configure_git_credentials,
    convert_url_to_ssh,
    convert_url_to_https
)


class TestRepositoryAuth:
    """Tests for repository authentication functionality."""

    def test_setup_https_auth(self):
        """Test HTTPS authentication setup."""
        username = "testuser"
        password = "testpassword"

        auth_config = setup_https_auth(username, password)

        assert auth_config["method"] == "https"
        assert auth_config["username"] == username
        assert auth_config["password"] == password

    @patch('os.path.exists')
    def test_setup_ssh_auth_with_existing_key(self, mock_exists):
        """Test SSH authentication setup with an existing key."""
        # Configure the mock
        mock_exists.return_value = True

        private_key_path = "~/.ssh/id_rsa"
        passphrase = "testpassphrase"

        auth_config = setup_ssh_auth(private_key_path, passphrase)

        assert auth_config["method"] == "ssh"
        assert auth_config["private_key_path"] == private_key_path
        assert auth_config["passphrase"] == passphrase

    @patch('os.path.exists')
    def test_setup_ssh_auth_with_default_key(self, mock_exists):
        """Test SSH authentication setup with the default key."""
        # Configure the mock
        mock_exists.return_value = True

        auth_config = setup_ssh_auth()

        assert auth_config["method"] == "ssh"
        assert "~/.ssh/id_rsa" in auth_config["private_key_path"] or os.path.expanduser("~/.ssh/id_rsa") in auth_config["private_key_path"]
        assert auth_config["passphrase"] is None

    @patch('os.path.exists')
    def test_setup_ssh_auth_with_nonexistent_key(self, mock_exists):
        """Test SSH authentication setup with a nonexistent key."""
        # Configure the mock
        mock_exists.return_value = False

        private_key_path = "~/.ssh/nonexistent_key"

        with pytest.raises(FileNotFoundError):
            setup_ssh_auth(private_key_path)

    @patch('subprocess.run')
    @patch('os.makedirs')
    def test_create_ssh_key_success(self, mock_makedirs, mock_run):
        """Test successful SSH key creation."""
        # Configure the mock
        mock_run.return_value = MagicMock(returncode=0)

        key_path = "~/.ssh/new_key"
        passphrase = "testpassphrase"

        success, message = create_ssh_key(key_path, passphrase)

        assert success is True
        assert "SSH key pair created successfully" in message
        mock_run.assert_called_once()

    @patch('subprocess.run')
    def test_create_ssh_key_failure(self, mock_run):
        """Test SSH key creation failure."""
        # Configure the mock to raise an exception
        mock_run.side_effect = subprocess.CalledProcessError(1, "ssh-keygen", stderr=b"Command failed")

        key_path = "~/.ssh/new_key"

        success, message = create_ssh_key(key_path)

        assert success is False
        assert "Failed to create SSH key pair" in message

    @patch('tempfile.NamedTemporaryFile')
    @patch('subprocess.run')
    @patch('os.chmod')
    def test_configure_git_credentials_success(self, mock_chmod, mock_run, mock_temp_file):
        """Test successful Git credentials configuration."""
        # Configure the mocks
        mock_file = MagicMock()
        mock_file.name = "/tmp/git_credentials.sh"
        mock_temp_file.return_value.__enter__.return_value = mock_file
        mock_run.return_value = MagicMock(returncode=0)

        username = "testuser"
        password = "testpassword"

        success, message = configure_git_credentials(username, password)

        assert success is True
        assert "Git credentials configured successfully" in message
        mock_run.assert_called_once()

    @patch('tempfile.NamedTemporaryFile')
    @patch('subprocess.run')
    @patch('os.chmod')
    def test_configure_git_credentials_failure(self, mock_chmod, mock_run, mock_temp_file):
        """Test Git credentials configuration failure."""
        # Configure the mocks
        mock_file = MagicMock()
        mock_file.name = "/tmp/git_credentials.sh"
        mock_temp_file.return_value.__enter__.return_value = mock_file
        mock_run.side_effect = Exception("Command failed")

        username = "testuser"
        password = "testpassword"

        success, message = configure_git_credentials(username, password)

        assert success is False
        assert "Error in configure_git_credentials" in message

    def test_convert_url_to_ssh_github(self):
        """Test converting GitHub HTTPS URL to SSH."""
        https_url = "https://github.com/user/repo.git"
        ssh_url = convert_url_to_ssh(https_url)

        assert ssh_url == "git@github.com:user/repo.git"

    def test_convert_url_to_ssh_gitlab(self):
        """Test converting GitLab HTTPS URL to SSH."""
        https_url = "https://gitlab.com/user/repo.git"
        ssh_url = convert_url_to_ssh(https_url)

        assert ssh_url == "git@gitlab.com:user/repo.git"

    def test_convert_url_to_ssh_bitbucket(self):
        """Test converting Bitbucket HTTPS URL to SSH."""
        https_url = "https://bitbucket.org/user/repo.git"
        ssh_url = convert_url_to_ssh(https_url)

        assert ssh_url == "git@bitbucket.org:user/repo.git"

    def test_convert_url_to_ssh_custom_domain(self):
        """Test converting custom domain HTTPS URL to SSH."""
        https_url = "https://git.example.com/user/repo.git"
        ssh_url = convert_url_to_ssh(https_url)

        assert ssh_url == "git@git.example.com:user/repo.git"

    def test_convert_url_to_ssh_already_ssh(self):
        """Test converting an SSH URL (should remain unchanged)."""
        ssh_url = "git@github.com:user/repo.git"
        converted_url = convert_url_to_ssh(ssh_url)

        assert converted_url == ssh_url

    def test_convert_url_to_https_github(self):
        """Test converting GitHub SSH URL to HTTPS."""
        ssh_url = "git@github.com:user/repo.git"
        https_url = convert_url_to_https(ssh_url)

        assert https_url == "https://github.com/user/repo.git"

    def test_convert_url_to_https_gitlab(self):
        """Test converting GitLab SSH URL to HTTPS."""
        ssh_url = "git@gitlab.com:user/repo.git"
        https_url = convert_url_to_https(ssh_url)

        assert https_url == "https://gitlab.com/user/repo.git"

    def test_convert_url_to_https_bitbucket(self):
        """Test converting Bitbucket SSH URL to HTTPS."""
        ssh_url = "git@bitbucket.org:user/repo.git"
        https_url = convert_url_to_https(ssh_url)

        assert https_url == "https://bitbucket.org/user/repo.git"

    def test_convert_url_to_https_custom_domain(self):
        """Test converting custom domain SSH URL to HTTPS."""
        ssh_url = "git@git.example.com:user/repo.git"
        https_url = convert_url_to_https(ssh_url)

        assert https_url == "https://git.example.com/user/repo.git"

    def test_convert_url_to_https_already_https(self):
        """Test converting an HTTPS URL (should remain unchanged)."""
        https_url = "https://github.com/user/repo.git"
        converted_url = convert_url_to_https(https_url)

        assert converted_url == https_url
