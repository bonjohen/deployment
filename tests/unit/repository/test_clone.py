"""
Unit tests for repository cloning functionality.
"""
import os
import shutil
import tempfile
from unittest.mock import patch, MagicMock

import pytest

from pythonweb_installer.repository.clone import (
    clone_repository,
    update_repository,
    check_repository_status
)


class TestRepositoryClone:
    """Tests for repository cloning functionality."""
    
    @pytest.fixture
    def temp_repo_dir(self):
        """Create a temporary directory for test repositories."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @patch('pythonweb_installer.repository.clone.run_command')
    def test_clone_repository_success(self, mock_run_command, temp_repo_dir):
        """Test successful repository cloning."""
        # Configure the mock
        mock_run_command.return_value = True
        
        # Call the function
        repo_url = "https://github.com/test/repo.git"
        target_path = os.path.join(temp_repo_dir, "repo")
        success, message = clone_repository(repo_url, target_path)
        
        # Verify the result
        assert success is True
        assert "Successfully cloned repository" in message
        mock_run_command.assert_called_once()
    
    @patch('pythonweb_installer.repository.clone.run_command')
    def test_clone_repository_failure(self, mock_run_command, temp_repo_dir):
        """Test repository cloning failure."""
        # Configure the mock
        mock_run_command.return_value = False
        
        # Call the function
        repo_url = "https://github.com/test/repo.git"
        target_path = os.path.join(temp_repo_dir, "repo")
        success, message = clone_repository(repo_url, target_path)
        
        # Verify the result
        assert success is False
        assert "Failed to clone repository" in message
        mock_run_command.assert_called_once()
    
    @patch('pythonweb_installer.repository.clone.run_command')
    def test_clone_repository_with_branch(self, mock_run_command, temp_repo_dir):
        """Test repository cloning with specific branch."""
        # Configure the mock
        mock_run_command.return_value = True
        
        # Call the function
        repo_url = "https://github.com/test/repo.git"
        target_path = os.path.join(temp_repo_dir, "repo")
        branch = "develop"
        success, message = clone_repository(repo_url, target_path, branch=branch)
        
        # Verify the result
        assert success is True
        assert "Successfully cloned repository" in message
        mock_run_command.assert_called_once()
        # Verify that the branch parameter was used
        call_args = mock_run_command.call_args[0][0]
        assert f"--branch {branch}" in call_args
    
    def test_clone_repository_existing_dir(self, temp_repo_dir):
        """Test cloning to an existing directory."""
        # Create a directory that's not a Git repository
        target_path = os.path.join(temp_repo_dir, "existing_dir")
        os.makedirs(target_path)
        
        # Call the function
        repo_url = "https://github.com/test/repo.git"
        success, message = clone_repository(repo_url, target_path)
        
        # Verify the result
        assert success is False
        assert "exists but is not a Git repository" in message
    
    @patch('os.path.exists')
    def test_clone_repository_existing_repo(self, mock_exists, temp_repo_dir):
        """Test cloning to an existing Git repository."""
        # Configure the mock to simulate an existing Git repository
        mock_exists.side_effect = lambda path: True
        
        # Call the function
        repo_url = "https://github.com/test/repo.git"
        target_path = os.path.join(temp_repo_dir, "existing_repo")
        success, message = clone_repository(repo_url, target_path)
        
        # Verify the result
        assert success is True
        assert "Repository already exists" in message
    
    @patch('pythonweb_installer.repository.clone.run_command')
    def test_update_repository_success(self, mock_run_command, temp_repo_dir):
        """Test successful repository update."""
        # Configure the mock
        mock_run_command.return_value = True
        
        # Create a fake Git repository
        repo_path = os.path.join(temp_repo_dir, "repo")
        os.makedirs(os.path.join(repo_path, ".git"))
        
        # Call the function
        success, message = update_repository(repo_path)
        
        # Verify the result
        assert success is True
        assert "Successfully updated repository" in message
        assert mock_run_command.call_count == 2  # fetch and pull
    
    @patch('pythonweb_installer.repository.clone.run_command')
    def test_update_repository_with_branch(self, mock_run_command, temp_repo_dir):
        """Test repository update with specific branch."""
        # Configure the mock
        mock_run_command.return_value = True
        
        # Create a fake Git repository
        repo_path = os.path.join(temp_repo_dir, "repo")
        os.makedirs(os.path.join(repo_path, ".git"))
        
        # Call the function
        branch = "develop"
        success, message = update_repository(repo_path, branch=branch)
        
        # Verify the result
        assert success is True
        assert "Successfully updated repository" in message
        assert mock_run_command.call_count == 3  # fetch, checkout, and pull
    
    def test_update_repository_not_git_repo(self, temp_repo_dir):
        """Test updating a directory that's not a Git repository."""
        # Create a directory that's not a Git repository
        repo_path = os.path.join(temp_repo_dir, "not_a_repo")
        os.makedirs(repo_path)
        
        # Call the function
        success, message = update_repository(repo_path)
        
        # Verify the result
        assert success is False
        assert "is not a Git repository" in message
    
    @patch('pythonweb_installer.repository.clone.run_command')
    def test_check_repository_status_success(self, mock_run_command, temp_repo_dir):
        """Test successful repository status check."""
        # Configure the mock
        mock_run_command.return_value = True
        
        # Create a fake Git repository
        repo_path = os.path.join(temp_repo_dir, "repo")
        os.makedirs(os.path.join(repo_path, ".git"))
        
        # Call the function
        success, repo_info = check_repository_status(repo_path)
        
        # Verify the result
        assert success is True
        assert "path" in repo_info
        assert repo_info["path"] == repo_path
        assert "branch" in repo_info
        assert "remote_url" in repo_info
        assert "last_commit" in repo_info
        assert "has_changes" in repo_info
    
    def test_check_repository_status_not_git_repo(self, temp_repo_dir):
        """Test checking status of a directory that's not a Git repository."""
        # Create a directory that's not a Git repository
        repo_path = os.path.join(temp_repo_dir, "not_a_repo")
        os.makedirs(repo_path)
        
        # Call the function
        success, repo_info = check_repository_status(repo_path)
        
        # Verify the result
        assert success is False
        assert "error" in repo_info
        assert "is not a Git repository" in repo_info["error"]
