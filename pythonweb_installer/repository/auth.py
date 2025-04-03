"""
Authentication methods for Git repositories.
"""
import os
import logging
import getpass
import subprocess
from typing import Dict, Any, Optional, Tuple
import tempfile
import stat

logger = logging.getLogger(__name__)


def setup_https_auth(username: str, password: str) -> Dict[str, Any]:
    """
    Set up HTTPS authentication for Git.

    Args:
        username: Git username
        password: Git password or token

    Returns:
        Dict[str, Any]: Authentication configuration
    """
    logger.info(f"Setting up HTTPS authentication for user {username}")

    # Create a credential helper that will provide the username and password
    auth_config = {
        "method": "https",
        "username": username,
        "password": password,
    }

    return auth_config


def setup_ssh_auth(
    private_key_path: Optional[str] = None,
    passphrase: Optional[str] = None
) -> Dict[str, Any]:
    """
    Set up SSH authentication for Git.

    Args:
        private_key_path: Path to SSH private key
        passphrase: Passphrase for the private key

    Returns:
        Dict[str, Any]: Authentication configuration
    """
    logger.info("Setting up SSH authentication")

    # If no private key is provided, use the default SSH key
    if not private_key_path:
        private_key_path = os.path.expanduser("~/.ssh/id_rsa")
        logger.info(f"Using default SSH key at {private_key_path}")

    # Check if the private key exists
    if not os.path.exists(private_key_path):
        logger.error(f"SSH private key not found at {private_key_path}")
        raise FileNotFoundError(f"SSH private key not found at {private_key_path}")

    auth_config = {
        "method": "ssh",
        "private_key_path": private_key_path,
        "passphrase": passphrase,
    }

    return auth_config


def create_ssh_key(
    key_path: str,
    passphrase: Optional[str] = None,
    key_type: str = "rsa",
    key_bits: int = 4096
) -> Tuple[bool, str]:
    """
    Create a new SSH key pair.

    Args:
        key_path: Path to save the private key
        passphrase: Passphrase for the private key
        key_type: Type of key to generate (rsa, ed25519, etc.)
        key_bits: Number of bits for the key (for RSA keys)

    Returns:
        Tuple[bool, str]: Success status and message
    """
    logger.info(f"Creating new SSH key pair at {key_path}")

    # Create directory if it doesn't exist
    key_dir = os.path.dirname(key_path)
    if key_dir and not os.path.exists(key_dir):
        os.makedirs(key_dir, exist_ok=True)

    # Generate the key
    cmd = ["ssh-keygen", "-t", key_type]

    if key_type == "rsa":
        cmd.extend(["-b", str(key_bits)])

    cmd.extend(["-f", key_path, "-N", passphrase or ""])

    try:
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        logger.info(f"SSH key pair created successfully at {key_path}")
        return True, f"SSH key pair created successfully at {key_path}"
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to create SSH key pair: {e.stderr.decode()}")
        return False, f"Failed to create SSH key pair: {e.stderr.decode()}"


def configure_git_credentials(
    username: str,
    password: str,
    global_config: bool = False
) -> Tuple[bool, str]:
    """
    Configure Git to store credentials.

    Args:
        username: Git username
        password: Git password or token
        global_config: Whether to configure globally or just for this repository

    Returns:
        Tuple[bool, str]: Success status and message
    """
    logger.info(f"Configuring Git credentials for user {username}")

    try:
        # Create a temporary credential helper script
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.sh') as f:
            f.write('#!/bin/sh\n')
            f.write(f'echo "username={username}"\n')
            f.write(f'echo "password={password}"\n')
            temp_file_path = f.name

        # Make the script executable (if not on Windows)
        if os.name != 'nt':
            os.chmod(temp_file_path, os.stat(temp_file_path).st_mode | stat.S_IEXEC)

        # Configure Git to use the credential helper
        scope = "--global" if global_config else ""
        cmd = f"git config {scope} credential.helper {temp_file_path}"

        try:
            subprocess.run(cmd, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            logger.info("Git credentials configured successfully")
            return True, "Git credentials configured successfully"
        except subprocess.CalledProcessError as e:
            error_msg = e.stderr.decode() if hasattr(e.stderr, 'decode') else str(e.stderr)
            logger.error(f"Failed to configure Git credentials: {error_msg}")
            return False, f"Failed to configure Git credentials: {error_msg}"
        finally:
            # Clean up the temporary file
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
    except Exception as e:
        logger.error(f"Error in configure_git_credentials: {str(e)}")
        return False, f"Error in configure_git_credentials: {str(e)}"


def get_credentials_interactive() -> Dict[str, Any]:
    """
    Prompt the user for Git credentials interactively.

    Returns:
        Dict[str, Any]: Authentication configuration
    """
    logger.info("Prompting for Git credentials")

    auth_method = input("Authentication method (https/ssh) [https]: ").strip() or "https"

    if auth_method.lower() == "https":
        username = input("Git username: ").strip()
        password = getpass.getpass("Git password or token: ")
        return setup_https_auth(username, password)
    elif auth_method.lower() == "ssh":
        private_key_path = input("SSH private key path [~/.ssh/id_rsa]: ").strip() or "~/.ssh/id_rsa"
        private_key_path = os.path.expanduser(private_key_path)
        passphrase = getpass.getpass("SSH key passphrase (leave empty if none): ")
        passphrase = passphrase if passphrase else None
        return setup_ssh_auth(private_key_path, passphrase)
    else:
        logger.error(f"Invalid authentication method: {auth_method}")
        raise ValueError(f"Invalid authentication method: {auth_method}")


def convert_url_to_ssh(https_url: str) -> str:
    """
    Convert an HTTPS Git URL to SSH format.

    Args:
        https_url: HTTPS Git URL

    Returns:
        str: SSH Git URL
    """
    if not https_url.startswith("https://"):
        return https_url

    # Extract the domain and path
    parts = https_url.replace("https://", "").split("/", 1)
    if len(parts) != 2:
        return https_url

    domain, path = parts

    # Handle GitHub, GitLab, and Bitbucket
    if domain == "github.com":
        return f"git@github.com:{path}"
    elif domain == "gitlab.com":
        return f"git@gitlab.com:{path}"
    elif domain == "bitbucket.org":
        return f"git@bitbucket.org:{path}"
    else:
        # Generic conversion
        return f"git@{domain}:{path}"


def convert_url_to_https(ssh_url: str) -> str:
    """
    Convert an SSH Git URL to HTTPS format.

    Args:
        ssh_url: SSH Git URL

    Returns:
        str: HTTPS Git URL
    """
    if not ssh_url.startswith("git@"):
        return ssh_url

    # Extract the domain and path
    parts = ssh_url.replace("git@", "").split(":", 1)
    if len(parts) != 2:
        return ssh_url

    domain, path = parts

    # Convert to HTTPS URL
    return f"https://{domain}/{path}"
