"""
Environment validation functionality.
"""
import os
import sys
import logging
import platform
import subprocess
from typing import Tuple, Dict, Any, List, Optional

from pythonweb_installer.environment.virtualenv import list_installed_packages

logger = logging.getLogger(__name__)


def validate_python_version(
    min_version: str = "3.7",
    max_version: Optional[str] = None
) -> Tuple[bool, Dict[str, Any]]:
    """
    Validate that the Python version meets requirements.
    
    Args:
        min_version: Minimum required Python version
        max_version: Maximum allowed Python version (optional)
        
    Returns:
        Tuple[bool, Dict[str, Any]]: Success status and validation information
    """
    logger.info(f"Validating Python version (min: {min_version}, max: {max_version or 'none'})")
    
    # Get current Python version
    current_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    
    # Parse version strings
    min_parts = list(map(int, min_version.split('.')))
    while len(min_parts) < 3:
        min_parts.append(0)
    
    current_parts = [sys.version_info.major, sys.version_info.minor, sys.version_info.micro]
    
    max_parts = None
    if max_version:
        max_parts = list(map(int, max_version.split('.')))
        while len(max_parts) < 3:
            max_parts.append(0)
    
    # Compare versions
    meets_min = current_parts >= min_parts
    meets_max = True
    if max_parts:
        meets_max = current_parts <= max_parts
    
    valid = meets_min and meets_max
    
    result = {
        "valid": valid,
        "current_version": current_version,
        "min_version": min_version,
        "max_version": max_version,
        "meets_min": meets_min,
        "meets_max": meets_max,
    }
    
    if valid:
        logger.info(f"Python version {current_version} is valid")
    else:
        logger.error(f"Python version {current_version} does not meet requirements")
    
    return valid, result


def validate_virtual_environment(env_path: str) -> Tuple[bool, Dict[str, Any]]:
    """
    Validate that a directory is a valid virtual environment.
    
    Args:
        env_path: Path to the virtual environment
        
    Returns:
        Tuple[bool, Dict[str, Any]]: Success status and validation information
    """
    logger.info(f"Validating virtual environment at {env_path}")
    
    result = {
        "valid": False,
        "path": env_path,
        "exists": False,
        "has_pyvenv_cfg": False,
        "has_python_exe": False,
        "has_pip_exe": False,
        "python_version": None,
    }
    
    # Check if directory exists
    if not os.path.exists(env_path):
        logger.error(f"Virtual environment directory {env_path} does not exist")
        return False, result
    
    result["exists"] = True
    
    # Check for pyvenv.cfg
    pyvenv_cfg_path = os.path.join(env_path, "pyvenv.cfg")
    if not os.path.exists(pyvenv_cfg_path):
        logger.error(f"pyvenv.cfg not found in {env_path}")
        return False, result
    
    result["has_pyvenv_cfg"] = True
    
    # Check for Python executable
    if platform.system() == "Windows":
        python_exe = os.path.join(env_path, "Scripts", "python.exe")
    else:
        python_exe = os.path.join(env_path, "bin", "python")
    
    if not os.path.exists(python_exe):
        logger.error(f"Python executable not found at {python_exe}")
        return False, result
    
    result["has_python_exe"] = True
    
    # Check for pip executable
    if platform.system() == "Windows":
        pip_exe = os.path.join(env_path, "Scripts", "pip.exe")
    else:
        pip_exe = os.path.join(env_path, "bin", "pip")
    
    if not os.path.exists(pip_exe):
        logger.warning(f"Pip executable not found at {pip_exe}")
        # Not having pip is not a fatal error
    else:
        result["has_pip_exe"] = True
    
    # Get Python version
    try:
        version_cmd = f"{python_exe} --version"
        version_result = subprocess.run(
            version_cmd,
            shell=True,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        version_output = version_result.stdout.strip() or version_result.stderr.strip()
        result["python_version"] = version_output
    except subprocess.CalledProcessError:
        logger.warning("Could not determine Python version in virtual environment")
    
    # Environment is valid if it has pyvenv.cfg and a Python executable
    result["valid"] = result["has_pyvenv_cfg"] and result["has_python_exe"]
    
    if result["valid"]:
        logger.info(f"Virtual environment at {env_path} is valid")
    else:
        logger.error(f"Virtual environment at {env_path} is not valid")
    
    return result["valid"], result


def validate_dependencies(
    env_path: str,
    required_packages: List[Dict[str, str]]
) -> Tuple[bool, Dict[str, Any]]:
    """
    Validate that required packages are installed in the virtual environment.
    
    Args:
        env_path: Path to the virtual environment
        required_packages: List of required packages with name and version
        
    Returns:
        Tuple[bool, Dict[str, Any]]: Success status and validation information
    """
    logger.info(f"Validating dependencies in virtual environment at {env_path}")
    
    result = {
        "valid": False,
        "path": env_path,
        "missing_packages": [],
        "version_mismatches": [],
        "installed_packages": [],
    }
    
    # Get installed packages
    success, installed_packages = list_installed_packages(env_path)
    if not success:
        logger.error("Failed to list installed packages")
        return False, result
    
    result["installed_packages"] = installed_packages
    
    # Create a dictionary of installed packages for easier lookup
    installed_dict = {pkg["name"].lower(): pkg["version"] for pkg in installed_packages}
    
    # Check required packages
    for req_pkg in required_packages:
        pkg_name = req_pkg["name"].lower()
        req_version = req_pkg.get("version")
        
        if pkg_name not in installed_dict:
            logger.warning(f"Required package {pkg_name} is not installed")
            result["missing_packages"].append(req_pkg)
            continue
        
        if req_version and installed_dict[pkg_name] != req_version:
            logger.warning(
                f"Package {pkg_name} version mismatch: "
                f"required {req_version}, installed {installed_dict[pkg_name]}"
            )
            result["version_mismatches"].append({
                "name": pkg_name,
                "required_version": req_version,
                "installed_version": installed_dict[pkg_name],
            })
    
    # Environment is valid if there are no missing packages and no version mismatches
    result["valid"] = not result["missing_packages"] and not result["version_mismatches"]
    
    if result["valid"]:
        logger.info("All required packages are installed with correct versions")
    else:
        logger.error("Some required packages are missing or have version mismatches")
    
    return result["valid"], result


def repair_virtual_environment(env_path: str) -> Tuple[bool, str]:
    """
    Attempt to repair a virtual environment.
    
    Args:
        env_path: Path to the virtual environment
        
    Returns:
        Tuple[bool, str]: Success status and message
    """
    logger.info(f"Attempting to repair virtual environment at {env_path}")
    
    # Validate the environment first
    valid, validation_result = validate_virtual_environment(env_path)
    if valid:
        logger.info("Virtual environment is already valid, no repair needed")
        return True, "Virtual environment is already valid, no repair needed"
    
    # If the directory doesn't exist or is not a virtual environment, we can't repair it
    if not validation_result["exists"] or not validation_result["has_pyvenv_cfg"]:
        logger.error("Cannot repair non-existent or invalid virtual environment")
        return False, "Cannot repair non-existent or invalid virtual environment"
    
    # If pip is missing, try to install it
    if not validation_result["has_pip_exe"]:
        logger.info("Attempting to install pip")
        
        # Determine the Python executable in the virtual environment
        if platform.system() == "Windows":
            python_exe = os.path.join(env_path, "Scripts", "python.exe")
        else:
            python_exe = os.path.join(env_path, "bin", "python")
        
        try:
            # Download get-pip.py
            subprocess.run(
                f"{python_exe} -m ensurepip",
                shell=True,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            logger.info("Successfully installed pip")
        except subprocess.CalledProcessError as e:
            error_msg = e.stderr if hasattr(e, 'stderr') else str(e)
            logger.error(f"Failed to install pip: {error_msg}")
            return False, f"Failed to install pip: {error_msg}"
    
    # Validate again after repair attempts
    valid, validation_result = validate_virtual_environment(env_path)
    if valid:
        logger.info("Successfully repaired virtual environment")
        return True, "Successfully repaired virtual environment"
    else:
        logger.error("Failed to repair virtual environment")
        return False, "Failed to repair virtual environment"


def install_missing_dependencies(
    env_path: str,
    required_packages: List[Dict[str, str]]
) -> Tuple[bool, Dict[str, Any]]:
    """
    Install missing dependencies in the virtual environment.
    
    Args:
        env_path: Path to the virtual environment
        required_packages: List of required packages with name and version
        
    Returns:
        Tuple[bool, Dict[str, Any]]: Success status and installation information
    """
    logger.info(f"Installing missing dependencies in virtual environment at {env_path}")
    
    # Validate dependencies first
    valid, validation_result = validate_dependencies(env_path, required_packages)
    if valid:
        logger.info("All dependencies are already installed")
        return True, {"message": "All dependencies are already installed"}
    
    # Determine the pip executable in the virtual environment
    if platform.system() == "Windows":
        pip_exe = os.path.join(env_path, "Scripts", "pip.exe")
    else:
        pip_exe = os.path.join(env_path, "bin", "pip")
    
    if not os.path.exists(pip_exe):
        logger.error(f"Pip executable not found at {pip_exe}")
        return False, {"error": f"Pip executable not found at {pip_exe}"}
    
    # Install missing packages
    missing_packages = validation_result["missing_packages"]
    version_mismatches = validation_result["version_mismatches"]
    
    result = {
        "success": True,
        "installed": [],
        "failed": [],
        "upgraded": [],
    }
    
    # Install missing packages
    for pkg in missing_packages:
        pkg_name = pkg["name"]
        pkg_version = pkg.get("version", "")
        pkg_spec = f"{pkg_name}{f'=={pkg_version}' if pkg_version else ''}"
        
        logger.info(f"Installing {pkg_spec}")
        try:
            install_cmd = f"{pip_exe} install {pkg_spec}"
            subprocess.run(
                install_cmd,
                shell=True,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            result["installed"].append(pkg)
            logger.info(f"Successfully installed {pkg_spec}")
        except subprocess.CalledProcessError as e:
            error_msg = e.stderr if hasattr(e, 'stderr') else str(e)
            logger.error(f"Failed to install {pkg_spec}: {error_msg}")
            result["failed"].append({
                "name": pkg_name,
                "version": pkg_version,
                "error": error_msg,
            })
            result["success"] = False
    
    # Upgrade packages with version mismatches
    for pkg in version_mismatches:
        pkg_name = pkg["name"]
        pkg_version = pkg["required_version"]
        pkg_spec = f"{pkg_name}=={pkg_version}"
        
        logger.info(f"Upgrading {pkg_name} to {pkg_version}")
        try:
            upgrade_cmd = f"{pip_exe} install --upgrade {pkg_spec}"
            subprocess.run(
                upgrade_cmd,
                shell=True,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            result["upgraded"].append(pkg)
            logger.info(f"Successfully upgraded {pkg_name} to {pkg_version}")
        except subprocess.CalledProcessError as e:
            error_msg = e.stderr if hasattr(e, 'stderr') else str(e)
            logger.error(f"Failed to upgrade {pkg_name} to {pkg_version}: {error_msg}")
            result["failed"].append({
                "name": pkg_name,
                "version": pkg_version,
                "error": error_msg,
            })
            result["success"] = False
    
    # Validate dependencies again after installation
    valid, _ = validate_dependencies(env_path, required_packages)
    result["all_dependencies_valid"] = valid
    
    if result["success"] and valid:
        logger.info("Successfully installed all missing dependencies")
    else:
        logger.error("Failed to install some dependencies")
    
    return result["success"], result
