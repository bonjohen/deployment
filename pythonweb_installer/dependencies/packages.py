"""
Package installation and management functionality.
"""
import os
import re
import json
import logging
import subprocess
import platform
from typing import List, Dict, Any, Tuple, Optional, Set

from pythonweb_installer.environment.virtualenv import list_installed_packages

logger = logging.getLogger(__name__)


def parse_requirements_file(file_path: str) -> Tuple[bool, List[Dict[str, str]]]:
    """
    Parse a requirements.txt file into a list of package specifications.

    Args:
        file_path: Path to the requirements.txt file

    Returns:
        Tuple[bool, List[Dict[str, str]]]: Success status and list of package specifications
    """
    logger.info(f"Parsing requirements file: {file_path}")

    if not os.path.exists(file_path):
        logger.error(f"Requirements file not found: {file_path}")
        return False, []

    packages = []

    try:
        with open(file_path, 'r') as f:
            for line in f:
                line = line.strip()

                # Skip empty lines and comments
                if not line or line.startswith('#'):
                    continue

                # Skip options (lines starting with -)
                if line.startswith('-'):
                    continue

                # Handle line continuations
                if line.endswith('\\'):
                    line = line[:-1].strip()

                # Extract package name and version
                package_info = parse_package_spec(line)
                if package_info:
                    packages.append(package_info)

        logger.info(f"Found {len(packages)} packages in requirements file")
        return True, packages
    except Exception as e:
        logger.error(f"Failed to parse requirements file: {str(e)}")
        return False, []


def parse_package_spec(package_spec: str) -> Optional[Dict[str, str]]:
    """
    Parse a package specification string into a dictionary.

    Args:
        package_spec: Package specification string (e.g., "package==1.0.0")

    Returns:
        Optional[Dict[str, str]]: Package information or None if invalid
    """
    # Remove any comments
    package_spec = package_spec.split('#')[0].strip()

    if not package_spec:
        return None

    # Handle direct references (URLs, paths, etc.)
    if package_spec.startswith(('http://', 'https://', 'git+', 'file:')):
        # Extract the package name from the URL if possible
        name_match = re.search(r'#egg=([a-zA-Z0-9_.-]+)', package_spec)
        if name_match:
            return {
                'name': name_match.group(1),
                'url': package_spec,
                'direct_reference': True
            }
        else:
            return {
                'name': f"unknown-{hash(package_spec) % 10000}",
                'url': package_spec,
                'direct_reference': True
            }

    # Handle standard package specifications
    # Match patterns like:
    # package
    # package==1.0.0
    # package>=1.0.0
    # package<=1.0.0
    # package~=1.0.0
    # package!=1.0.0
    # package>1.0.0,<2.0.0
    package_match = re.match(r'^([a-zA-Z0-9_.-]+)(.*)$', package_spec)

    if not package_match:
        logger.warning(f"Invalid package specification: {package_spec}")
        return None

    name, version_spec = package_match.groups()
    name = name.lower()  # Normalize package name

    package_info = {'name': name}

    if version_spec:
        version_spec = version_spec.strip()
        if version_spec:
            package_info['version_spec'] = version_spec

            # Extract exact version if specified
            exact_version_match = re.match(r'^==([a-zA-Z0-9_.-]+)$', version_spec)
            if exact_version_match:
                package_info['version'] = exact_version_match.group(1)

    return package_info


def install_package(
    env_path: str,
    package_spec: str,
    upgrade: bool = False,
    index_url: Optional[str] = None,
    extra_index_url: Optional[str] = None,
    no_deps: bool = False,
    user: bool = False
) -> Tuple[bool, str]:
    """
    Install a package in the virtual environment.

    Args:
        env_path: Path to the virtual environment
        package_spec: Package specification (name, version, URL)
        upgrade: Whether to upgrade the package if already installed
        index_url: Alternative package index URL
        extra_index_url: Additional package index URL
        no_deps: Whether to skip installing dependencies
        user: Whether to install in user site-packages

    Returns:
        Tuple[bool, str]: Success status and message
    """
    logger.info(f"Installing package: {package_spec}")

    # Determine the pip executable in the virtual environment
    if platform.system() == "Windows":
        pip_exe = os.path.join(env_path, "Scripts", "pip.exe")
    else:
        pip_exe = os.path.join(env_path, "bin", "pip")

    if not os.path.exists(pip_exe):
        logger.error(f"Pip executable not found at {pip_exe}")
        return False, f"Pip executable not found at {pip_exe}"

    # Prepare the installation command
    cmd = [pip_exe, "install"]

    if upgrade:
        cmd.append("--upgrade")

    if index_url:
        cmd.extend(["--index-url", index_url])

    if extra_index_url:
        cmd.extend(["--extra-index-url", extra_index_url])

    if no_deps:
        cmd.append("--no-deps")

    if user:
        cmd.append("--user")

    cmd.append(package_spec)

    # Execute the installation command
    try:
        result = subprocess.run(
            cmd,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        logger.info(f"Successfully installed package: {package_spec}")
        return True, f"Successfully installed package: {package_spec}"
    except subprocess.CalledProcessError as e:
        error_msg = e.stderr if hasattr(e, 'stderr') else str(e)
        logger.error(f"Failed to install package {package_spec}: {error_msg}")
        return False, f"Failed to install package {package_spec}: {error_msg}"


def install_requirements(
    env_path: str,
    requirements_file: str,
    upgrade: bool = False,
    index_url: Optional[str] = None,
    extra_index_url: Optional[str] = None
) -> Tuple[bool, Dict[str, Any]]:
    """
    Install packages from a requirements file.

    Args:
        env_path: Path to the virtual environment
        requirements_file: Path to the requirements.txt file
        upgrade: Whether to upgrade packages if already installed
        index_url: Alternative package index URL
        extra_index_url: Additional package index URL

    Returns:
        Tuple[bool, Dict[str, Any]]: Success status and installation results
    """
    logger.info(f"Installing requirements from {requirements_file}")

    if not os.path.exists(requirements_file):
        logger.error(f"Requirements file not found: {requirements_file}")
        return False, {"error": f"Requirements file not found: {requirements_file}"}

    # Determine the pip executable in the virtual environment
    if platform.system() == "Windows":
        pip_exe = os.path.join(env_path, "Scripts", "pip.exe")
    else:
        pip_exe = os.path.join(env_path, "bin", "pip")

    if not os.path.exists(pip_exe):
        logger.error(f"Pip executable not found at {pip_exe}")
        return False, {"error": f"Pip executable not found at {pip_exe}"}

    # Prepare the installation command
    cmd = [pip_exe, "install", "-r", requirements_file]

    if upgrade:
        cmd.append("--upgrade")

    if index_url:
        cmd.extend(["--index-url", index_url])

    if extra_index_url:
        cmd.extend(["--extra-index-url", extra_index_url])

    # Execute the installation command
    try:
        result = subprocess.run(
            cmd,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        logger.info(f"Successfully installed requirements from {requirements_file}")

        # Parse the output to get installed packages
        installed_packages = []
        for line in result.stdout.splitlines():
            if "Successfully installed" in line:
                packages_str = line.split("Successfully installed")[1].strip()
                installed_packages = [pkg.strip() for pkg in packages_str.split()]

        return True, {
            "message": f"Successfully installed requirements from {requirements_file}",
            "installed_packages": installed_packages
        }
    except subprocess.CalledProcessError as e:
        error_msg = e.stderr if hasattr(e, 'stderr') else str(e)
        logger.error(f"Failed to install requirements: {error_msg}")
        return False, {"error": f"Failed to install requirements: {error_msg}"}


def uninstall_package(
    env_path: str,
    package_name: str,
    yes: bool = True
) -> Tuple[bool, str]:
    """
    Uninstall a package from the virtual environment.

    Args:
        env_path: Path to the virtual environment
        package_name: Name of the package to uninstall
        yes: Whether to automatically confirm uninstallation

    Returns:
        Tuple[bool, str]: Success status and message
    """
    logger.info(f"Uninstalling package: {package_name}")

    # Determine the pip executable in the virtual environment
    if platform.system() == "Windows":
        pip_exe = os.path.join(env_path, "Scripts", "pip.exe")
    else:
        pip_exe = os.path.join(env_path, "bin", "pip")

    if not os.path.exists(pip_exe):
        logger.error(f"Pip executable not found at {pip_exe}")
        return False, f"Pip executable not found at {pip_exe}"

    # Prepare the uninstallation command
    cmd = [pip_exe, "uninstall"]

    if yes:
        cmd.append("--yes")

    cmd.append(package_name)

    # Execute the uninstallation command
    try:
        result = subprocess.run(
            cmd,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        logger.info(f"Successfully uninstalled package: {package_name}")
        return True, f"Successfully uninstalled package: {package_name}"
    except subprocess.CalledProcessError as e:
        error_msg = e.stderr if hasattr(e, 'stderr') else str(e)
        logger.error(f"Failed to uninstall package {package_name}: {error_msg}")
        return False, f"Failed to uninstall package {package_name}: {error_msg}"


def get_package_info(
    env_path: str,
    package_name: str
) -> Tuple[bool, Dict[str, Any]]:
    """
    Get detailed information about an installed package.

    Args:
        env_path: Path to the virtual environment
        package_name: Name of the package

    Returns:
        Tuple[bool, Dict[str, Any]]: Success status and package information
    """
    logger.info(f"Getting information for package: {package_name}")

    # Determine the pip executable in the virtual environment
    if platform.system() == "Windows":
        pip_exe = os.path.join(env_path, "Scripts", "pip.exe")
    else:
        pip_exe = os.path.join(env_path, "bin", "pip")

    if not os.path.exists(pip_exe):
        logger.error(f"Pip executable not found at {pip_exe}")
        return False, {"error": f"Pip executable not found at {pip_exe}"}

    # Execute the show command
    try:
        result = subprocess.run(
            [pip_exe, "show", package_name],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        # Parse the output
        package_info = {}
        for line in result.stdout.splitlines():
            if ":" in line:
                key, value = line.split(":", 1)
                package_info[key.strip().lower().replace("-", "_")] = value.strip()

        # Parse requires into a list
        if "requires" in package_info and package_info["requires"]:
            package_info["requires"] = [req.strip() for req in package_info["requires"].split(",")]
        else:
            package_info["requires"] = []

        # Parse required-by into a list
        if "required_by" in package_info and package_info["required_by"]:
            package_info["required_by"] = [req.strip() for req in package_info["required_by"].split(",")]
        else:
            package_info["required_by"] = []

        logger.info(f"Successfully retrieved information for package: {package_name}")
        return True, package_info
    except subprocess.CalledProcessError as e:
        error_msg = e.stderr if hasattr(e, 'stderr') else str(e)
        logger.error(f"Failed to get information for package {package_name}: {error_msg}")
        return False, {"error": f"Failed to get information for package {package_name}: {error_msg}"}


def generate_requirements_file(
    env_path: str,
    output_file: str,
    include_versions: bool = True,
    exclude_packages: Optional[List[str]] = None
) -> Tuple[bool, str]:
    """
    Generate a requirements.txt file from installed packages.

    Args:
        env_path: Path to the virtual environment
        output_file: Path to the output requirements.txt file
        include_versions: Whether to include version constraints
        exclude_packages: List of packages to exclude

    Returns:
        Tuple[bool, str]: Success status and message
    """
    logger.info(f"Generating requirements file: {output_file}")

    # Get installed packages
    success, packages = list_installed_packages(env_path)
    if not success:
        logger.error("Failed to list installed packages")
        return False, "Failed to list installed packages"

    # Filter out excluded packages
    if exclude_packages:
        exclude_packages = [pkg.lower() for pkg in exclude_packages]
        packages = [pkg for pkg in packages if pkg["name"].lower() not in exclude_packages]

    # Generate requirements file content
    try:
        with open(output_file, 'w') as f:
            f.write("# Generated by PythonWeb Installer\n")
            f.write("# This file contains the packages installed in the virtual environment\n\n")

            for package in sorted(packages, key=lambda p: p["name"].lower()):
                if include_versions:
                    f.write(f"{package['name']}=={package['version']}\n")
                else:
                    f.write(f"{package['name']}\n")

        logger.info(f"Successfully generated requirements file: {output_file}")
        return True, f"Successfully generated requirements file: {output_file}"
    except Exception as e:
        logger.error(f"Failed to generate requirements file: {str(e)}")
        return False, f"Failed to generate requirements file: {str(e)}"


def check_outdated_packages(env_path: str) -> Tuple[bool, List[Dict[str, str]]]:
    """
    Check for outdated packages in the virtual environment.

    Args:
        env_path: Path to the virtual environment

    Returns:
        Tuple[bool, List[Dict[str, str]]]: Success status and list of outdated packages
    """
    logger.info("Checking for outdated packages")

    # Determine the pip executable in the virtual environment
    if platform.system() == "Windows":
        pip_exe = os.path.join(env_path, "Scripts", "pip.exe")
    else:
        pip_exe = os.path.join(env_path, "bin", "pip")

    if not os.path.exists(pip_exe):
        logger.error(f"Pip executable not found at {pip_exe}")
        return False, []

    # Execute the list --outdated command
    try:
        result = subprocess.run(
            [pip_exe, "list", "--outdated", "--format=json"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        # Parse the JSON output
        outdated_packages = json.loads(result.stdout)

        logger.info(f"Found {len(outdated_packages)} outdated packages")
        return True, outdated_packages
    except subprocess.CalledProcessError as e:
        error_msg = e.stderr if hasattr(e, 'stderr') else str(e)
        logger.error(f"Failed to check for outdated packages: {error_msg}")
        return False, []
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse pip list output: {str(e)}")
        return False, []
