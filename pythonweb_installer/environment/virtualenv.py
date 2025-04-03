"""
Virtual environment creation and management functionality.
"""
import os
import sys
import json
import logging
import subprocess
import platform
from typing import Tuple, Optional, Dict, Any, List

from pythonweb_installer.utils import run_command

logger = logging.getLogger(__name__)


def detect_python_version() -> Tuple[bool, Dict[str, Any]]:
    """
    Detect the installed Python version.

    Returns:
        Tuple[bool, Dict[str, Any]]: Success status and Python version information
    """
    logger.info("Detecting Python version")

    try:
        # Get Python version
        version_info = {
            "major": sys.version_info.major,
            "minor": sys.version_info.minor,
            "micro": sys.version_info.micro,
            "version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            "executable": sys.executable,
            "platform": platform.system(),
            "is_64bit": sys.maxsize > 2**32,
        }

        logger.info(f"Detected Python {version_info['version']} on {version_info['platform']}")
        return True, version_info
    except Exception as e:
        logger.error(f"Failed to detect Python version: {str(e)}")
        return False, {"error": f"Failed to detect Python version: {str(e)}"}


def find_python_executable(version: Optional[str] = None) -> Tuple[bool, str]:
    """
    Find the Python executable for a specific version.

    Args:
        version: Python version to find (e.g., "3.9"). If None, use the current Python.

    Returns:
        Tuple[bool, str]: Success status and path to Python executable
    """
    logger.info(f"Finding Python executable for version {version or 'current'}")

    if not version:
        # Use the current Python executable
        return True, sys.executable

    # Try to find the specified Python version
    if platform.system() == "Windows":
        # On Windows, try common installation paths
        python_cmd = f"py -{version}"
        try:
            result = subprocess.run(
                f"{python_cmd} -c \"import sys; print(sys.executable)\"",
                shell=True,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            executable = result.stdout.strip()
            logger.info(f"Found Python {version} at {executable}")
            return True, executable
        except subprocess.CalledProcessError:
            # Try direct executable names
            for exe in [f"python{version}", f"python{version.replace('.', '')}"]:
                try:
                    result = subprocess.run(
                        f"{exe} -c \"import sys; print(sys.executable)\"",
                        shell=True,
                        check=True,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True
                    )
                    executable = result.stdout.strip()
                    logger.info(f"Found Python {version} at {executable}")
                    return True, executable
                except subprocess.CalledProcessError:
                    continue
    else:
        # On Unix-like systems, try common executable names
        for exe in [f"python{version}", f"python{version.split('.')[0]}.{version.split('.')[1]}", "python3"]:
            try:
                result = subprocess.run(
                    f"{exe} -c \"import sys; print(sys.executable)\"",
                    shell=True,
                    check=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                executable = result.stdout.strip()

                # Verify the version
                version_result = subprocess.run(
                    f"{executable} --version",
                    shell=True,
                    check=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                version_output = version_result.stdout.strip()

                if version in version_output:
                    logger.info(f"Found Python {version} at {executable}")
                    return True, executable
            except subprocess.CalledProcessError:
                continue

    logger.error(f"Could not find Python {version}")
    return False, f"Could not find Python {version}"


def create_virtual_environment(
    env_path: str,
    python_version: Optional[str] = None,
    system_site_packages: bool = False,
    with_pip: bool = True
) -> Tuple[bool, str]:
    """
    Create a new virtual environment.

    Args:
        env_path: Path where the virtual environment should be created
        python_version: Python version to use (e.g., "3.9"). If None, use the current Python.
        system_site_packages: Whether to give access to system site packages
        with_pip: Whether to include pip in the virtual environment

    Returns:
        Tuple[bool, str]: Success status and message
    """
    logger.info(f"Creating virtual environment at {env_path}")

    # Find the Python executable
    if python_version:
        success, python_exe = find_python_executable(python_version)
        if not success:
            return False, python_exe
    else:
        python_exe = sys.executable

    # Check if the directory already exists
    if os.path.exists(env_path):
        if os.path.exists(os.path.join(env_path, "pyvenv.cfg")):
            logger.info(f"Virtual environment already exists at {env_path}")
            return True, f"Virtual environment already exists at {env_path}"
        else:
            logger.error(f"Directory {env_path} exists but is not a virtual environment")
            return False, f"Directory {env_path} exists but is not a virtual environment"

    # Create parent directory if it doesn't exist
    os.makedirs(os.path.dirname(os.path.abspath(env_path)), exist_ok=True)

    # Prepare command
    cmd = [python_exe, "-m", "venv"]

    if system_site_packages:
        cmd.append("--system-site-packages")

    if not with_pip:
        cmd.append("--without-pip")

    cmd.append(env_path)

    # Execute command
    try:
        subprocess.run(
            cmd,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        logger.info(f"Successfully created virtual environment at {env_path}")
        return True, f"Successfully created virtual environment at {env_path}"
    except subprocess.CalledProcessError as e:
        error_msg = e.stderr if hasattr(e, 'stderr') else str(e)
        logger.error(f"Failed to create virtual environment: {error_msg}")
        return False, f"Failed to create virtual environment: {error_msg}"


def get_activation_script(env_path: str) -> Tuple[bool, str]:
    """
    Get the appropriate activation script for the virtual environment.

    Args:
        env_path: Path to the virtual environment

    Returns:
        Tuple[bool, str]: Success status and activation script path or command
    """
    logger.info(f"Getting activation script for virtual environment at {env_path}")

    # Check if the directory is a virtual environment
    if not os.path.exists(os.path.join(env_path, "pyvenv.cfg")):
        logger.error(f"Directory {env_path} is not a virtual environment")
        return False, f"Directory {env_path} is not a virtual environment"

    # Determine the activation script based on the platform
    if platform.system() == "Windows":
        activate_script = os.path.join(env_path, "Scripts", "activate")
        activate_cmd = f"{activate_script}.bat"
    else:
        activate_script = os.path.join(env_path, "bin", "activate")
        activate_cmd = f"source {activate_script}"

    if not os.path.exists(activate_script + (".bat" if platform.system() == "Windows" else "")):
        logger.error(f"Activation script not found at {activate_script}")
        return False, f"Activation script not found at {activate_script}"

    logger.info(f"Activation script: {activate_cmd}")
    return True, activate_cmd


def run_in_virtual_environment(
    env_path: str,
    command: str,
    cwd: Optional[str] = None
) -> Tuple[bool, str]:
    """
    Run a command in the virtual environment.

    Args:
        env_path: Path to the virtual environment
        command: Command to run
        cwd: Working directory for the command

    Returns:
        Tuple[bool, str]: Success status and command output
    """
    logger.info(f"Running command in virtual environment: {command}")

    # Check if the directory is a virtual environment
    if not os.path.exists(os.path.join(env_path, "pyvenv.cfg")):
        logger.error(f"Directory {env_path} is not a virtual environment")
        return False, f"Directory {env_path} is not a virtual environment"

    # Determine the Python executable in the virtual environment
    if platform.system() == "Windows":
        python_exe = os.path.join(env_path, "Scripts", "python.exe")
    else:
        python_exe = os.path.join(env_path, "bin", "python")

    if not os.path.exists(python_exe):
        logger.error(f"Python executable not found at {python_exe}")
        return False, f"Python executable not found at {python_exe}"

    # Execute the command using the virtual environment's Python
    try:
        result = subprocess.run(
            f"{python_exe} -c \"{command}\"" if command.startswith("import") or command.startswith("print") else command,
            shell=True,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=cwd
        )
        output = result.stdout.strip()
        logger.info(f"Command output: {output}")
        return True, output
    except subprocess.CalledProcessError as e:
        error_msg = e.stderr if hasattr(e, 'stderr') else str(e)
        logger.error(f"Command failed: {error_msg}")
        return False, f"Command failed: {error_msg}"


def upgrade_pip(env_path: str) -> Tuple[bool, str]:
    """
    Upgrade pip in the virtual environment.

    Args:
        env_path: Path to the virtual environment

    Returns:
        Tuple[bool, str]: Success status and message
    """
    logger.info(f"Upgrading pip in virtual environment at {env_path}")

    # Determine the pip executable in the virtual environment
    if platform.system() == "Windows":
        pip_exe = os.path.join(env_path, "Scripts", "pip.exe")
    else:
        pip_exe = os.path.join(env_path, "bin", "pip")

    if not os.path.exists(pip_exe):
        logger.error(f"Pip executable not found at {pip_exe}")
        return False, f"Pip executable not found at {pip_exe}"

    # Upgrade pip
    try:
        result = subprocess.run(
            f"{pip_exe} install --upgrade pip",
            shell=True,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        output = result.stdout.strip()
        logger.info(f"Pip upgrade output: {output}")
        return True, "Successfully upgraded pip"
    except subprocess.CalledProcessError as e:
        error_msg = e.stderr if hasattr(e, 'stderr') else str(e)
        logger.error(f"Failed to upgrade pip: {error_msg}")
        return False, f"Failed to upgrade pip: {error_msg}"


def list_installed_packages(env_path: str) -> Tuple[bool, List[Dict[str, str]]]:
    """
    List installed packages in the virtual environment.

    Args:
        env_path: Path to the virtual environment

    Returns:
        Tuple[bool, List[Dict[str, str]]]: Success status and list of installed packages
    """
    logger.info(f"Listing installed packages in virtual environment at {env_path}")

    # Determine the pip executable in the virtual environment
    if platform.system() == "Windows":
        pip_exe = os.path.join(env_path, "Scripts", "pip.exe")
    else:
        pip_exe = os.path.join(env_path, "bin", "pip")

    if not os.path.exists(pip_exe):
        logger.error(f"Pip executable not found at {pip_exe}")
        return False, []

    # List installed packages
    try:
        result = subprocess.run(
            f"{pip_exe} list --format=json",
            shell=True,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        import json
        packages = json.loads(result.stdout)
        logger.info(f"Found {len(packages)} installed packages")
        return True, packages
    except subprocess.CalledProcessError as e:
        error_msg = e.stderr if hasattr(e, 'stderr') else str(e)
        logger.error(f"Failed to list installed packages: {error_msg}")
        return False, []
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse pip list output: {str(e)}")
        return False, []
