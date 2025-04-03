"""
Version control functionality for Git repositories.
"""
import os
import logging
import subprocess
from typing import List, Dict, Any, Tuple, Optional

from pythonweb_installer.utils import run_command

logger = logging.getLogger(__name__)


def get_available_branches(repo_path: str) -> Tuple[bool, List[str]]:
    """
    Get a list of available branches in the repository.
    
    Args:
        repo_path: Path to the local Git repository
        
    Returns:
        Tuple[bool, List[str]]: Success status and list of branch names
    """
    logger.info(f"Getting available branches for repository at {repo_path}")
    
    # Check if directory is a Git repository
    if not os.path.exists(os.path.join(repo_path, ".git")):
        logger.error(f"Directory {repo_path} is not a Git repository")
        return False, []
    
    # Get remote branches
    cmd = f"git -C {repo_path} branch -r"
    
    try:
        result = subprocess.run(
            cmd, 
            shell=True, 
            check=True, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Parse branch names
        branches = []
        for line in result.stdout.splitlines():
            branch = line.strip()
            if branch.startswith("origin/"):
                branch = branch.replace("origin/", "", 1)
                if branch != "HEAD":
                    branches.append(branch)
        
        logger.info(f"Found {len(branches)} branches")
        return True, branches
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to get branches: {e.stderr}")
        return False, []


def get_available_tags(repo_path: str) -> Tuple[bool, List[str]]:
    """
    Get a list of available tags in the repository.
    
    Args:
        repo_path: Path to the local Git repository
        
    Returns:
        Tuple[bool, List[str]]: Success status and list of tag names
    """
    logger.info(f"Getting available tags for repository at {repo_path}")
    
    # Check if directory is a Git repository
    if not os.path.exists(os.path.join(repo_path, ".git")):
        logger.error(f"Directory {repo_path} is not a Git repository")
        return False, []
    
    # Get tags
    cmd = f"git -C {repo_path} tag"
    
    try:
        result = subprocess.run(
            cmd, 
            shell=True, 
            check=True, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Parse tag names
        tags = [tag.strip() for tag in result.stdout.splitlines() if tag.strip()]
        
        logger.info(f"Found {len(tags)} tags")
        return True, tags
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to get tags: {e.stderr}")
        return False, []


def get_commit_history(
    repo_path: str, 
    branch: Optional[str] = None, 
    max_count: int = 10
) -> Tuple[bool, List[Dict[str, Any]]]:
    """
    Get the commit history for a repository.
    
    Args:
        repo_path: Path to the local Git repository
        branch: Branch to get history for (default: current branch)
        max_count: Maximum number of commits to retrieve
        
    Returns:
        Tuple[bool, List[Dict[str, Any]]]: Success status and list of commit information
    """
    logger.info(f"Getting commit history for repository at {repo_path}")
    
    # Check if directory is a Git repository
    if not os.path.exists(os.path.join(repo_path, ".git")):
        logger.error(f"Directory {repo_path} is not a Git repository")
        return False, []
    
    # Prepare branch specification
    branch_spec = branch if branch else "HEAD"
    
    # Get commit history
    cmd = f"git -C {repo_path} log {branch_spec} --pretty=format:'%H|%an|%ae|%at|%s' --max-count={max_count}"
    
    try:
        result = subprocess.run(
            cmd, 
            shell=True, 
            check=True, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Parse commit information
        commits = []
        for line in result.stdout.splitlines():
            if not line.strip():
                continue
                
            parts = line.split("|")
            if len(parts) >= 5:
                commit = {
                    "hash": parts[0],
                    "author": parts[1],
                    "email": parts[2],
                    "timestamp": int(parts[3]),
                    "message": parts[4],
                }
                commits.append(commit)
        
        logger.info(f"Found {len(commits)} commits")
        return True, commits
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to get commit history: {e.stderr}")
        return False, []


def checkout_version(
    repo_path: str, 
    version: str, 
    version_type: str = "branch"
) -> Tuple[bool, str]:
    """
    Checkout a specific version (branch, tag, or commit) in the repository.
    
    Args:
        repo_path: Path to the local Git repository
        version: Version identifier (branch name, tag name, or commit hash)
        version_type: Type of version ('branch', 'tag', or 'commit')
        
    Returns:
        Tuple[bool, str]: Success status and message
    """
    logger.info(f"Checking out {version_type} {version} in repository at {repo_path}")
    
    # Check if directory is a Git repository
    if not os.path.exists(os.path.join(repo_path, ".git")):
        logger.error(f"Directory {repo_path} is not a Git repository")
        return False, f"Directory {repo_path} is not a Git repository"
    
    # Fetch latest changes
    fetch_cmd = f"git -C {repo_path} fetch"
    success = run_command(fetch_cmd)
    
    if not success:
        return False, f"Failed to fetch latest changes"
    
    # Checkout the specified version
    checkout_cmd = f"git -C {repo_path} checkout {version}"
    success = run_command(checkout_cmd)
    
    if not success:
        return False, f"Failed to checkout {version_type} {version}"
    
    # Pull if it's a branch
    if version_type == "branch":
        pull_cmd = f"git -C {repo_path} pull origin {version}"
        success = run_command(pull_cmd)
        
        if not success:
            return False, f"Failed to pull latest changes for branch {version}"
    
    logger.info(f"Successfully checked out {version_type} {version}")
    return True, f"Successfully checked out {version_type} {version}"


def get_repository_version(repo_path: str) -> Tuple[bool, Dict[str, Any]]:
    """
    Get the current version information for a repository.
    
    Args:
        repo_path: Path to the local Git repository
        
    Returns:
        Tuple[bool, Dict[str, Any]]: Success status and version information
    """
    logger.info(f"Getting version information for repository at {repo_path}")
    
    # Check if directory is a Git repository
    if not os.path.exists(os.path.join(repo_path, ".git")):
        logger.error(f"Directory {repo_path} is not a Git repository")
        return False, {"error": f"Directory {repo_path} is not a Git repository"}
    
    # Get current commit hash
    hash_cmd = f"git -C {repo_path} rev-parse HEAD"
    
    try:
        hash_result = subprocess.run(
            hash_cmd, 
            shell=True, 
            check=True, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE,
            text=True
        )
        commit_hash = hash_result.stdout.strip()
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to get commit hash: {e.stderr}")
        return False, {"error": f"Failed to get commit hash: {e.stderr}"}
    
    # Get current branch
    branch_cmd = f"git -C {repo_path} rev-parse --abbrev-ref HEAD"
    
    try:
        branch_result = subprocess.run(
            branch_cmd, 
            shell=True, 
            check=True, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE,
            text=True
        )
        branch = branch_result.stdout.strip()
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to get branch: {e.stderr}")
        branch = "unknown"
    
    # Check if current commit is a tag
    tag_cmd = f"git -C {repo_path} describe --exact-match --tags {commit_hash} 2>/dev/null || echo ''"
    
    try:
        tag_result = subprocess.run(
            tag_cmd, 
            shell=True, 
            check=False,  # Don't check for errors as this command may fail if not on a tag
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE,
            text=True
        )
        tag = tag_result.stdout.strip()
    except subprocess.CalledProcessError:
        tag = ""
    
    # Get commit timestamp
    time_cmd = f"git -C {repo_path} show -s --format=%ct {commit_hash}"
    
    try:
        time_result = subprocess.run(
            time_cmd, 
            shell=True, 
            check=True, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE,
            text=True
        )
        timestamp = int(time_result.stdout.strip())
    except (subprocess.CalledProcessError, ValueError):
        timestamp = 0
    
    # Compile version information
    version_info = {
        "commit_hash": commit_hash,
        "branch": branch,
        "tag": tag if tag else None,
        "timestamp": timestamp,
    }
    
    logger.info(f"Repository version: {version_info}")
    return True, version_info
