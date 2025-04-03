"""
Mock Git repository for testing.
"""
import os
import shutil
import tempfile
from typing import Dict, Any, List, Optional


class MockRepository:
    """
    A mock Git repository for testing repository operations.
    
    This class simulates a Git repository without actually using Git,
    allowing tests to run without requiring Git to be installed.
    """
    
    def __init__(self, name: str = "mock_repo"):
        """
        Initialize a new mock repository.
        
        Args:
            name: Name of the repository
        """
        self.name = name
        self.temp_dir = tempfile.mkdtemp()
        self.path = os.path.join(self.temp_dir, name)
        self.git_dir = os.path.join(self.path, ".git")
        
        # Create repository structure
        os.makedirs(self.path)
        os.makedirs(self.git_dir)
        
        # Initialize repository state
        self.branches = ["main", "develop"]
        self.current_branch = "main"
        self.tags = ["v1.0.0", "v1.1.0"]
        self.commits = [
            {
                "hash": "abc123",
                "author": "Test User",
                "email": "test@example.com",
                "timestamp": 1620000000,
                "message": "Initial commit",
                "branch": "main"
            },
            {
                "hash": "def456",
                "author": "Test User",
                "email": "test@example.com",
                "timestamp": 1620100000,
                "message": "Add feature X",
                "branch": "main"
            },
            {
                "hash": "ghi789",
                "author": "Test User",
                "email": "test@example.com",
                "timestamp": 1620200000,
                "message": "Start development branch",
                "branch": "develop"
            }
        ]
        self.current_commit = self.commits[1]  # main branch, latest commit
        self.remote_url = "https://github.com/test/mock_repo.git"
        self.has_changes = False
        
        # Create some files
        with open(os.path.join(self.path, "README.md"), "w") as f:
            f.write("# Mock Repository\n\nThis is a mock repository for testing.")
        
        with open(os.path.join(self.path, "setup.py"), "w") as f:
            f.write("from setuptools import setup\n\nsetup(name='mock_repo')")
    
    def cleanup(self):
        """Remove the temporary directory."""
        shutil.rmtree(self.temp_dir)
    
    def add_branch(self, branch_name: str):
        """
        Add a new branch to the repository.
        
        Args:
            branch_name: Name of the branch to add
        """
        if branch_name not in self.branches:
            self.branches.append(branch_name)
    
    def add_tag(self, tag_name: str):
        """
        Add a new tag to the repository.
        
        Args:
            tag_name: Name of the tag to add
        """
        if tag_name not in self.tags:
            self.tags.append(tag_name)
    
    def add_commit(self, message: str, branch: Optional[str] = None):
        """
        Add a new commit to the repository.
        
        Args:
            message: Commit message
            branch: Branch to add the commit to (default: current branch)
        """
        branch = branch or self.current_branch
        if branch not in self.branches:
            self.add_branch(branch)
        
        commit = {
            "hash": f"commit_{len(self.commits) + 1}",
            "author": "Test User",
            "email": "test@example.com",
            "timestamp": 1620300000 + len(self.commits) * 100000,
            "message": message,
            "branch": branch
        }
        
        self.commits.append(commit)
        if branch == self.current_branch:
            self.current_commit = commit
    
    def checkout_branch(self, branch_name: str) -> bool:
        """
        Checkout a branch.
        
        Args:
            branch_name: Name of the branch to checkout
            
        Returns:
            bool: True if successful, False otherwise
        """
        if branch_name not in self.branches:
            return False
        
        self.current_branch = branch_name
        
        # Find the latest commit on this branch
        for commit in reversed(self.commits):
            if commit["branch"] == branch_name:
                self.current_commit = commit
                break
        
        return True
    
    def checkout_tag(self, tag_name: str) -> bool:
        """
        Checkout a tag.
        
        Args:
            tag_name: Name of the tag to checkout
            
        Returns:
            bool: True if successful, False otherwise
        """
        if tag_name not in self.tags:
            return False
        
        # In a real repository, we would need to find the commit associated with the tag
        # For simplicity, we'll just set the current commit to the first commit
        self.current_commit = self.commits[0]
        self.current_branch = "detached HEAD"
        
        return True
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get the current status of the repository.
        
        Returns:
            Dict[str, Any]: Repository status information
        """
        return {
            "path": self.path,
            "branch": self.current_branch,
            "remote_url": self.remote_url,
            "last_commit": self.current_commit["hash"],
            "has_changes": self.has_changes,
        }
    
    def get_commit_history(self, branch: Optional[str] = None, max_count: int = 10) -> List[Dict[str, Any]]:
        """
        Get the commit history for a branch.
        
        Args:
            branch: Branch to get history for (default: current branch)
            max_count: Maximum number of commits to retrieve
            
        Returns:
            List[Dict[str, Any]]: List of commit information
        """
        branch = branch or self.current_branch
        
        # Filter commits by branch
        branch_commits = [commit for commit in self.commits if commit["branch"] == branch]
        
        # Sort by timestamp (newest first)
        branch_commits.sort(key=lambda c: c["timestamp"], reverse=True)
        
        # Limit to max_count
        return branch_commits[:max_count]
