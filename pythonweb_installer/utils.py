"""
Utility functions for PythonWeb Installer.
"""
import os
import sys
import subprocess
import logging

logger = logging.getLogger(__name__)

def run_command(command, cwd=None, env=None, shell=True):
    """
    Run a shell command and handle errors.
    
    Args:
        command: Command to run
        cwd: Working directory
        env: Environment variables
        shell: Whether to use shell
        
    Returns:
        bool: True if command succeeded, False otherwise
    """
    try:
        logger.info(f"Running command: {command}")
        result = subprocess.run(
            command,
            shell=shell,
            check=True,
            cwd=cwd,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        logger.info(f"Command output: {result.stdout}")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Command failed with error: {e.stderr}")
        return False
