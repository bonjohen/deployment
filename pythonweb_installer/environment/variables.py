"""
Environment variables management functionality.
"""
import os
import re
import logging
import platform
from typing import Dict, Any, Tuple, List, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


def load_env_file(file_path: str) -> Tuple[bool, Dict[str, str]]:
    """
    Load environment variables from a .env file.
    
    Args:
        file_path: Path to the .env file
        
    Returns:
        Tuple[bool, Dict[str, str]]: Success status and environment variables
    """
    logger.info(f"Loading environment variables from {file_path}")
    
    env_vars = {}
    
    if not os.path.exists(file_path):
        logger.error(f"Environment file {file_path} does not exist")
        return False, {}
    
    try:
        with open(file_path, 'r') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                
                # Parse key-value pairs
                match = re.match(r'^([A-Za-z0-9_]+)=(.*)$', line)
                if match:
                    key, value = match.groups()
                    
                    # Remove quotes if present
                    if value and value[0] == value[-1] and value[0] in ('"', "'"):
                        value = value[1:-1]
                    
                    env_vars[key] = value
                    logger.debug(f"Loaded environment variable: {key}")
        
        logger.info(f"Loaded {len(env_vars)} environment variables from {file_path}")
        return True, env_vars
    except Exception as e:
        logger.error(f"Failed to load environment variables: {str(e)}")
        return False, {}


def save_env_file(file_path: str, env_vars: Dict[str, str], overwrite: bool = False) -> Tuple[bool, str]:
    """
    Save environment variables to a .env file.
    
    Args:
        file_path: Path to the .env file
        env_vars: Dictionary of environment variables
        overwrite: Whether to overwrite an existing file
        
    Returns:
        Tuple[bool, str]: Success status and message
    """
    logger.info(f"Saving environment variables to {file_path}")
    
    if os.path.exists(file_path) and not overwrite:
        logger.error(f"Environment file {file_path} already exists and overwrite is False")
        return False, f"Environment file {file_path} already exists"
    
    try:
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)
        
        with open(file_path, 'w') as f:
            for key, value in env_vars.items():
                # Add quotes if value contains spaces or special characters
                if re.search(r'[\s\'"\\]', value):
                    value = f'"{value}"'
                
                f.write(f"{key}={value}\n")
        
        logger.info(f"Saved {len(env_vars)} environment variables to {file_path}")
        return True, f"Successfully saved environment variables to {file_path}"
    except Exception as e:
        logger.error(f"Failed to save environment variables: {str(e)}")
        return False, f"Failed to save environment variables: {str(e)}"


def set_environment_variables(env_vars: Dict[str, str], persistent: bool = False) -> Tuple[bool, str]:
    """
    Set environment variables in the current process and optionally make them persistent.
    
    Args:
        env_vars: Dictionary of environment variables
        persistent: Whether to make the variables persistent across sessions
        
    Returns:
        Tuple[bool, str]: Success status and message
    """
    logger.info(f"Setting {len(env_vars)} environment variables (persistent: {persistent})")
    
    # Set variables in the current process
    for key, value in env_vars.items():
        os.environ[key] = value
        logger.debug(f"Set environment variable: {key}")
    
    # Make variables persistent if requested
    if persistent:
        if platform.system() == "Windows":
            # On Windows, use setx command
            for key, value in env_vars.items():
                try:
                    import subprocess
                    subprocess.run(
                        f'setx {key} "{value}"',
                        shell=True,
                        check=True,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True
                    )
                except subprocess.CalledProcessError as e:
                    logger.error(f"Failed to set persistent environment variable {key}: {str(e)}")
                    return False, f"Failed to set persistent environment variables: {str(e)}"
        else:
            # On Unix-like systems, add to .profile or .bash_profile
            home_dir = os.path.expanduser("~")
            profile_path = os.path.join(home_dir, ".bash_profile")
            
            if not os.path.exists(profile_path):
                profile_path = os.path.join(home_dir, ".profile")
            
            if not os.path.exists(profile_path):
                profile_path = os.path.join(home_dir, ".bashrc")
            
            if not os.path.exists(profile_path):
                logger.error("Could not find a profile file to update")
                return False, "Could not find a profile file to update"
            
            try:
                with open(profile_path, 'a') as f:
                    f.write("\n# Environment variables added by PythonWeb Installer\n")
                    for key, value in env_vars.items():
                        f.write(f'export {key}="{value}"\n')
            except Exception as e:
                logger.error(f"Failed to update profile file: {str(e)}")
                return False, f"Failed to update profile file: {str(e)}"
    
    logger.info(f"Successfully set {len(env_vars)} environment variables")
    return True, f"Successfully set {len(env_vars)} environment variables"


def get_environment_variables(prefix: Optional[str] = None) -> Dict[str, str]:
    """
    Get environment variables, optionally filtered by prefix.
    
    Args:
        prefix: Prefix to filter environment variables
        
    Returns:
        Dict[str, str]: Dictionary of environment variables
    """
    logger.info(f"Getting environment variables (prefix: {prefix or 'none'})")
    
    if prefix:
        env_vars = {k: v for k, v in os.environ.items() if k.startswith(prefix)}
    else:
        env_vars = dict(os.environ)
    
    logger.info(f"Found {len(env_vars)} environment variables")
    return env_vars


def generate_env_file(
    template_path: str,
    output_path: str,
    variables: Dict[str, str],
    overwrite: bool = False
) -> Tuple[bool, str]:
    """
    Generate a .env file from a template.
    
    Args:
        template_path: Path to the template file
        output_path: Path to the output .env file
        variables: Dictionary of variables to substitute in the template
        overwrite: Whether to overwrite an existing file
        
    Returns:
        Tuple[bool, str]: Success status and message
    """
    logger.info(f"Generating .env file from template {template_path}")
    
    if os.path.exists(output_path) and not overwrite:
        logger.error(f"Output file {output_path} already exists and overwrite is False")
        return False, f"Output file {output_path} already exists"
    
    if not os.path.exists(template_path):
        logger.error(f"Template file {template_path} does not exist")
        return False, f"Template file {template_path} does not exist"
    
    try:
        with open(template_path, 'r') as f:
            template_content = f.read()
        
        # Replace variables in the template
        for key, value in variables.items():
            template_content = template_content.replace(f"${{{key}}}", value)
            template_content = template_content.replace(f"${key}", value)
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        
        with open(output_path, 'w') as f:
            f.write(template_content)
        
        logger.info(f"Successfully generated .env file at {output_path}")
        return True, f"Successfully generated .env file at {output_path}"
    except Exception as e:
        logger.error(f"Failed to generate .env file: {str(e)}")
        return False, f"Failed to generate .env file: {str(e)}"


def find_env_files(directory: str, recursive: bool = True) -> List[str]:
    """
    Find .env files in a directory.
    
    Args:
        directory: Directory to search in
        recursive: Whether to search recursively
        
    Returns:
        List[str]: List of .env file paths
    """
    logger.info(f"Finding .env files in {directory} (recursive: {recursive})")
    
    env_files = []
    
    if recursive:
        for root, _, files in os.walk(directory):
            for file in files:
                if file == ".env" or file.endswith(".env"):
                    env_files.append(os.path.join(root, file))
    else:
        for file in os.listdir(directory):
            if file == ".env" or file.endswith(".env"):
                env_files.append(os.path.join(directory, file))
    
    logger.info(f"Found {len(env_files)} .env files")
    return env_files


def merge_env_files(
    file_paths: List[str],
    output_path: str,
    overwrite: bool = False
) -> Tuple[bool, str]:
    """
    Merge multiple .env files into one.
    
    Args:
        file_paths: List of .env file paths
        output_path: Path to the output .env file
        overwrite: Whether to overwrite an existing file
        
    Returns:
        Tuple[bool, str]: Success status and message
    """
    logger.info(f"Merging {len(file_paths)} .env files into {output_path}")
    
    if os.path.exists(output_path) and not overwrite:
        logger.error(f"Output file {output_path} already exists and overwrite is False")
        return False, f"Output file {output_path} already exists"
    
    merged_vars = {}
    
    # Load variables from each file
    for file_path in file_paths:
        success, env_vars = load_env_file(file_path)
        if success:
            merged_vars.update(env_vars)
        else:
            logger.warning(f"Failed to load environment variables from {file_path}")
    
    # Save merged variables to output file
    return save_env_file(output_path, merged_vars, overwrite=overwrite)
