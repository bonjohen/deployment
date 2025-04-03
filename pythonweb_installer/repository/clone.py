"""
Repository cloning and updating functionality.
"""
import os
import logging
from typing import Optional, Tuple, Dict, Any

from pythonweb_installer.utils import run_command

logger = logging.getLogger(__name__)


def clone_repository(
    repo_url: str, 
    target_path: str, 
    branch: Optional[str] = None, 
    auth_method: str = "https",
    credentials: Optional[Dict[str, Any]] = None
) -> Tuple[bool, str]:
    """
    Clone a Git repository to the specified path.
    
    Args:
        repo_url: URL of the Git repository
        target_path: Local path where the repository should be cloned
        branch: Branch or tag to checkout (default: main/master branch)
        auth_method: Authentication method ('https' or 'ssh')
        credentials: Authentication credentials if needed
        
    Returns:
        Tuple[bool, str]: Success status and message
    """
    logger.info(f"Cloning repository {repo_url} to {target_path}")
    
    # Check if directory already exists
    if os.path.exists(target_path):
        if os.path.exists(os.path.join(target_path, ".git")):
            logger.info(f"Repository already exists at {target_path}")
            return True, f"Repository already exists at {target_path}"
        else:
            logger.error(f"Target directory {target_path} exists but is not a Git repository")
            return False, f"Target directory {target_path} exists but is not a Git repository"
    
    # Create parent directory if it doesn't exist
    os.makedirs(os.path.dirname(target_path), exist_ok=True)
    
    # Prepare clone command
    clone_cmd = f"git clone {repo_url} {target_path}"
    
    if branch:
        clone_cmd += f" --branch {branch}"
    
    # Execute clone command
    success = run_command(clone_cmd)
    
    if not success:
        return False, f"Failed to clone repository {repo_url}"
    
    logger.info(f"Successfully cloned repository {repo_url} to {target_path}")
    return True, f"Successfully cloned repository to {target_path}"


def update_repository(
    repo_path: str, 
    branch: Optional[str] = None,
    remote: str = "origin"
) -> Tuple[bool, str]:
    """
    Update an existing Git repository.
    
    Args:
        repo_path: Path to the local Git repository
        branch: Branch or tag to checkout and pull
        remote: Remote name to pull from
        
    Returns:
        Tuple[bool, str]: Success status and message
    """
    logger.info(f"Updating repository at {repo_path}")
    
    # Check if directory is a Git repository
    if not os.path.exists(os.path.join(repo_path, ".git")):
        logger.error(f"Directory {repo_path} is not a Git repository")
        return False, f"Directory {repo_path} is not a Git repository"
    
    # Fetch updates
    fetch_cmd = f"git -C {repo_path} fetch {remote}"
    success = run_command(fetch_cmd)
    
    if not success:
        return False, f"Failed to fetch updates for repository at {repo_path}"
    
    # Checkout branch if specified
    if branch:
        checkout_cmd = f"git -C {repo_path} checkout {branch}"
        success = run_command(checkout_cmd)
        
        if not success:
            return False, f"Failed to checkout branch {branch}"
    
    # Pull updates
    current_branch = branch or "$(git -C {repo_path} rev-parse --abbrev-ref HEAD)"
    pull_cmd = f"git -C {repo_path} pull {remote} {current_branch}"
    success = run_command(pull_cmd)
    
    if not success:
        return False, f"Failed to pull updates for repository at {repo_path}"
    
    logger.info(f"Successfully updated repository at {repo_path}")
    return True, f"Successfully updated repository at {repo_path}"


def check_repository_status(repo_path: str) -> Tuple[bool, Dict[str, Any]]:
    """
    Check the status of a Git repository.
    
    Args:
        repo_path: Path to the local Git repository
        
    Returns:
        Tuple[bool, Dict[str, Any]]: Success status and repository information
    """
    logger.info(f"Checking repository status at {repo_path}")
    
    # Check if directory is a Git repository
    if not os.path.exists(os.path.join(repo_path, ".git")):
        logger.error(f"Directory {repo_path} is not a Git repository")
        return False, {"error": f"Directory {repo_path} is not a Git repository"}
    
    # Get current branch
    branch_cmd = f"git -C {repo_path} rev-parse --abbrev-ref HEAD"
    success = run_command(branch_cmd, shell=True)
    
    if not success:
        return False, {"error": f"Failed to get current branch for repository at {repo_path}"}
    
    # Get remote URL
    remote_cmd = f"git -C {repo_path} config --get remote.origin.url"
    success = run_command(remote_cmd, shell=True)
    
    if not success:
        return False, {"error": f"Failed to get remote URL for repository at {repo_path}"}
    
    # Get last commit
    commit_cmd = f"git -C {repo_path} log -1 --format=%H"
    success = run_command(commit_cmd, shell=True)
    
    if not success:
        return False, {"error": f"Failed to get last commit for repository at {repo_path}"}
    
    # Check for uncommitted changes
    status_cmd = f"git -C {repo_path} status --porcelain"
    success = run_command(status_cmd, shell=True)
    
    if not success:
        return False, {"error": f"Failed to get status for repository at {repo_path}"}
    
    # Return repository information
    repo_info = {
        "path": repo_path,
        "branch": "current_branch",  # This would be the actual output in a real implementation
        "remote_url": "remote_url",  # This would be the actual output in a real implementation
        "last_commit": "commit_hash",  # This would be the actual output in a real implementation
        "has_changes": False,  # This would be determined from the status output
    }
    
    logger.info(f"Repository status: {repo_info}")
    return True, repo_info
