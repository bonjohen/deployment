"""
Unit tests for repository version control functionality.
"""
import os
import shutil
import tempfile
import subprocess
from unittest.mock import patch, MagicMock

import pytest

from pythonweb_installer.repository.version import (
    get_available_branches,
    get_available_tags,
    get_commit_history,
    checkout_version,
    get_repository_version
)


class TestRepositoryVersion:
    """Tests for repository version control functionality."""

    @pytest.fixture
    def temp_repo_dir(self):
        """Create a temporary directory for test repositories."""
        temp_dir = tempfile.mkdtemp()
        repo_path = os.path.join(temp_dir, "repo")
        os.makedirs(os.path.join(repo_path, ".git"))
        yield repo_path
        shutil.rmtree(temp_dir)

    @patch('subprocess.run')
    def test_get_available_branches_success(self, mock_run, temp_repo_dir):
        """Test successful retrieval of available branches."""
        # Configure the mock
        mock_process = MagicMock()
        mock_process.stdout = "  origin/main\n  origin/develop\n  origin/feature/test\n"
        mock_run.return_value = mock_process

        # Call the function
        success, branches = get_available_branches(temp_repo_dir)

        # Verify the result
        assert success is True
        assert len(branches) == 3
        assert "main" in branches
        assert "develop" in branches
        assert "feature/test" in branches
        mock_run.assert_called_once()

    @patch('subprocess.run')
    def test_get_available_branches_failure(self, mock_run, temp_repo_dir):
        """Test failure to retrieve available branches."""
        # Configure the mock to raise an exception
        mock_run.side_effect = subprocess.CalledProcessError(1, "git branch", stderr=b"Command failed")

        # Call the function
        success, branches = get_available_branches(temp_repo_dir)

        # Verify the result
        assert success is False
        assert len(branches) == 0
        mock_run.assert_called_once()

    def test_get_available_branches_not_git_repo(self, temp_repo_dir):
        """Test getting branches from a directory that's not a Git repository."""
        # Remove the .git directory
        shutil.rmtree(os.path.join(temp_repo_dir, ".git"))

        # Call the function
        success, branches = get_available_branches(temp_repo_dir)

        # Verify the result
        assert success is False
        assert len(branches) == 0

    @patch('subprocess.run')
    def test_get_available_tags_success(self, mock_run, temp_repo_dir):
        """Test successful retrieval of available tags."""
        # Configure the mock
        mock_process = MagicMock()
        mock_process.stdout = "v1.0.0\nv1.1.0\nv2.0.0\n"
        mock_run.return_value = mock_process

        # Call the function
        success, tags = get_available_tags(temp_repo_dir)

        # Verify the result
        assert success is True
        assert len(tags) == 3
        assert "v1.0.0" in tags
        assert "v1.1.0" in tags
        assert "v2.0.0" in tags
        mock_run.assert_called_once()

    @patch('subprocess.run')
    def test_get_available_tags_failure(self, mock_run, temp_repo_dir):
        """Test failure to retrieve available tags."""
        # Configure the mock to raise an exception
        mock_run.side_effect = subprocess.CalledProcessError(1, "git tag", stderr=b"Command failed")

        # Call the function
        success, tags = get_available_tags(temp_repo_dir)

        # Verify the result
        assert success is False
        assert len(tags) == 0
        mock_run.assert_called_once()

    def test_get_available_tags_not_git_repo(self, temp_repo_dir):
        """Test getting tags from a directory that's not a Git repository."""
        # Remove the .git directory
        shutil.rmtree(os.path.join(temp_repo_dir, ".git"))

        # Call the function
        success, tags = get_available_tags(temp_repo_dir)

        # Verify the result
        assert success is False
        assert len(tags) == 0

    @patch('subprocess.run')
    def test_get_commit_history_success(self, mock_run, temp_repo_dir):
        """Test successful retrieval of commit history."""
        # Configure the mock
        mock_process = MagicMock()
        mock_process.stdout = (
            "abc123|John Doe|john@example.com|1620000000|First commit\n"
            "def456|Jane Smith|jane@example.com|1620100000|Second commit\n"
            "ghi789|Bob Johnson|bob@example.com|1620200000|Third commit\n"
        )
        mock_run.return_value = mock_process

        # Call the function
        success, commits = get_commit_history(temp_repo_dir, max_count=3)

        # Verify the result
        assert success is True
        assert len(commits) == 3
        assert commits[0]["hash"] == "abc123"
        assert commits[0]["author"] == "John Doe"
        assert commits[0]["email"] == "john@example.com"
        assert commits[0]["timestamp"] == 1620000000
        assert commits[0]["message"] == "First commit"
        mock_run.assert_called_once()

    @patch('subprocess.run')
    def test_get_commit_history_with_branch(self, mock_run, temp_repo_dir):
        """Test retrieval of commit history for a specific branch."""
        # Configure the mock
        mock_process = MagicMock()
        mock_process.stdout = "abc123|John Doe|john@example.com|1620000000|First commit\n"
        mock_run.return_value = mock_process

        # Call the function
        branch = "develop"
        success, commits = get_commit_history(temp_repo_dir, branch=branch, max_count=1)

        # Verify the result
        assert success is True
        assert len(commits) == 1
        mock_run.assert_called_once()
        # Verify that the branch parameter was used
        call_args = mock_run.call_args[0][0]
        assert branch in call_args

    @patch('subprocess.run')
    def test_get_commit_history_failure(self, mock_run, temp_repo_dir):
        """Test failure to retrieve commit history."""
        # Configure the mock to raise an exception
        mock_run.side_effect = subprocess.CalledProcessError(1, "git log", stderr=b"Command failed")

        # Call the function
        success, commits = get_commit_history(temp_repo_dir)

        # Verify the result
        assert success is False
        assert len(commits) == 0
        mock_run.assert_called_once()

    def test_get_commit_history_not_git_repo(self, temp_repo_dir):
        """Test getting commit history from a directory that's not a Git repository."""
        # Remove the .git directory
        shutil.rmtree(os.path.join(temp_repo_dir, ".git"))

        # Call the function
        success, commits = get_commit_history(temp_repo_dir)

        # Verify the result
        assert success is False
        assert len(commits) == 0

    @patch('pythonweb_installer.repository.version.run_command')
    def test_checkout_version_branch_success(self, mock_run_command, temp_repo_dir):
        """Test successful checkout of a branch."""
        # Configure the mock
        mock_run_command.return_value = True

        # Call the function
        version = "develop"
        success, message = checkout_version(temp_repo_dir, version, version_type="branch")

        # Verify the result
        assert success is True
        assert f"Successfully checked out branch {version}" in message
        assert mock_run_command.call_count == 3  # fetch, checkout, pull

    @patch('pythonweb_installer.repository.version.run_command')
    def test_checkout_version_tag_success(self, mock_run_command, temp_repo_dir):
        """Test successful checkout of a tag."""
        # Configure the mock
        mock_run_command.return_value = True

        # Call the function
        version = "v1.0.0"
        success, message = checkout_version(temp_repo_dir, version, version_type="tag")

        # Verify the result
        assert success is True
        assert f"Successfully checked out tag {version}" in message
        assert mock_run_command.call_count == 2  # fetch, checkout

    @patch('pythonweb_installer.repository.version.run_command')
    def test_checkout_version_commit_success(self, mock_run_command, temp_repo_dir):
        """Test successful checkout of a commit."""
        # Configure the mock
        mock_run_command.return_value = True

        # Call the function
        version = "abc123"
        success, message = checkout_version(temp_repo_dir, version, version_type="commit")

        # Verify the result
        assert success is True
        assert f"Successfully checked out commit {version}" in message
        assert mock_run_command.call_count == 2  # fetch, checkout

    @patch('pythonweb_installer.repository.version.run_command')
    def test_checkout_version_failure(self, mock_run_command, temp_repo_dir):
        """Test failure to checkout a version."""
        # Configure the mock to fail on checkout
        mock_run_command.side_effect = [True, False]  # fetch succeeds, checkout fails

        # Call the function
        version = "develop"
        success, message = checkout_version(temp_repo_dir, version)

        # Verify the result
        assert success is False
        assert "Failed to checkout" in message
        assert mock_run_command.call_count == 2  # fetch, checkout

    def test_checkout_version_not_git_repo(self, temp_repo_dir):
        """Test checking out a version in a directory that's not a Git repository."""
        # Remove the .git directory
        shutil.rmtree(os.path.join(temp_repo_dir, ".git"))

        # Call the function
        version = "develop"
        success, message = checkout_version(temp_repo_dir, version)

        # Verify the result
        assert success is False
        assert "is not a Git repository" in message

    @patch('subprocess.run')
    def test_get_repository_version_success(self, mock_run, temp_repo_dir):
        """Test successful retrieval of repository version information."""
        # Configure the mock for multiple calls
        mock_run.side_effect = [
            MagicMock(stdout="abc123\n"),  # hash
            MagicMock(stdout="main\n"),    # branch
            MagicMock(stdout="v1.0.0\n"),  # tag
            MagicMock(stdout="1620000000\n")  # timestamp
        ]

        # Call the function
        success, version_info = get_repository_version(temp_repo_dir)

        # Verify the result
        assert success is True
        assert version_info["commit_hash"] == "abc123"
        assert version_info["branch"] == "main"
        assert version_info["tag"] == "v1.0.0"
        assert version_info["timestamp"] == 1620000000
        assert mock_run.call_count == 4

    @patch('subprocess.run')
    def test_get_repository_version_no_tag(self, mock_run, temp_repo_dir):
        """Test retrieval of repository version information without a tag."""
        # Configure the mock for multiple calls
        mock_run.side_effect = [
            MagicMock(stdout="abc123\n"),  # hash
            MagicMock(stdout="main\n"),    # branch
            MagicMock(stdout=""),          # no tag
            MagicMock(stdout="1620000000\n")  # timestamp
        ]

        # Call the function
        success, version_info = get_repository_version(temp_repo_dir)

        # Verify the result
        assert success is True
        assert version_info["commit_hash"] == "abc123"
        assert version_info["branch"] == "main"
        assert version_info["tag"] is None
        assert version_info["timestamp"] == 1620000000

    @patch('subprocess.run')
    def test_get_repository_version_failure(self, mock_run, temp_repo_dir):
        """Test failure to retrieve repository version information."""
        # Configure the mock to fail on the first call
        mock_run.side_effect = subprocess.CalledProcessError(1, "git rev-parse", stderr=b"Command failed")

        # Call the function
        success, version_info = get_repository_version(temp_repo_dir)

        # Verify the result
        assert success is False
        assert "error" in version_info

    def test_get_repository_version_not_git_repo(self, temp_repo_dir):
        """Test getting version information from a directory that's not a Git repository."""
        # Remove the .git directory
        shutil.rmtree(os.path.join(temp_repo_dir, ".git"))

        # Call the function
        success, version_info = get_repository_version(temp_repo_dir)

        # Verify the result
        assert success is False
        assert "error" in version_info
        assert "is not a Git repository" in version_info["error"]
