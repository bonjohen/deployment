"""
Dependency resolution functionality.
"""
import os
import re
import json
import logging
import subprocess
import platform
from typing import List, Dict, Any, Tuple, Optional, Set

from pythonweb_installer.dependencies.packages import (
    parse_requirements_file,
    get_package_info,
    install_package,
    uninstall_package
)

logger = logging.getLogger(__name__)


def detect_dependency_conflicts(
    env_path: str,
    requirements_file: Optional[str] = None,
    package_specs: Optional[List[Dict[str, str]]] = None
) -> Tuple[bool, Dict[str, Any]]:
    """
    Detect potential dependency conflicts.

    Args:
        env_path: Path to the virtual environment
        requirements_file: Path to the requirements.txt file
        package_specs: List of package specifications

    Returns:
        Tuple[bool, Dict[str, Any]]: Success status and conflict information
    """
    logger.info("Detecting dependency conflicts")

    # Get package specifications from requirements file if provided
    if requirements_file and not package_specs:
        success, package_specs = parse_requirements_file(requirements_file)
        if not success:
            logger.error(f"Failed to parse requirements file: {requirements_file}")
            return False, {"error": f"Failed to parse requirements file: {requirements_file}"}

    if not package_specs:
        logger.error("No package specifications provided")
        return False, {"error": "No package specifications provided"}

    # Determine the pip executable in the virtual environment
    if platform.system() == "Windows":
        pip_exe = os.path.join(env_path, "Scripts", "pip.exe")
    else:
        pip_exe = os.path.join(env_path, "bin", "pip")

    if not os.path.exists(pip_exe):
        logger.error(f"Pip executable not found at {pip_exe}")
        return False, {"error": f"Pip executable not found at {pip_exe}"}

    # Check for conflicts using pip-check
    try:
        # First, try to install pip-check if not already installed
        subprocess.run(
            [pip_exe, "install", "pip-check"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        # Run pip-check to detect conflicts
        result = subprocess.run(
            [pip_exe, "check"],
            check=False,  # Don't raise an exception if conflicts are found
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        # Parse the output
        conflicts = []
        for line in result.stdout.splitlines() + result.stderr.splitlines():
            if "has requirement" in line and "which is incompatible with" in line:
                conflicts.append(line.strip())

        if conflicts:
            logger.warning(f"Found {len(conflicts)} dependency conflicts")
            return True, {
                "has_conflicts": True,
                "conflicts": conflicts
            }
        else:
            logger.info("No dependency conflicts found")
            return True, {
                "has_conflicts": False,
                "conflicts": []
            }
    except subprocess.CalledProcessError as e:
        error_msg = e.stderr if hasattr(e, 'stderr') else str(e)
        logger.error(f"Failed to check for dependency conflicts: {error_msg}")
        return False, {"error": f"Failed to check for dependency conflicts: {error_msg}"}


def resolve_dependency_conflicts(
    env_path: str,
    conflicts: List[str],
    strategy: str = "upgrade"
) -> Tuple[bool, Dict[str, Any]]:
    """
    Resolve dependency conflicts using the specified strategy.

    Args:
        env_path: Path to the virtual environment
        conflicts: List of conflict descriptions
        strategy: Resolution strategy ("upgrade", "downgrade", or "remove")

    Returns:
        Tuple[bool, Dict[str, Any]]: Success status and resolution results
    """
    logger.info(f"Resolving dependency conflicts using strategy: {strategy}")

    if not conflicts:
        logger.info("No conflicts to resolve")
        return True, {"message": "No conflicts to resolve"}

    # Parse conflicts to extract package information
    conflict_info = []
    for conflict in conflicts:
        # Example conflict: "package1 1.0.0 has requirement package2>=2.0.0, but you have package2 1.0.0."
        match = re.match(
            r"([a-zA-Z0-9_.-]+)\s+([a-zA-Z0-9_.-]+)\s+has requirement\s+([a-zA-Z0-9_.-]+)([>=<~!]+)([a-zA-Z0-9_.-]+),\s+but you have\s+([a-zA-Z0-9_.-]+)\s+([a-zA-Z0-9_.-]+)",
            conflict
        )

        if match:
            pkg1_name, pkg1_version, pkg2_name, operator, required_version, actual_pkg_name, actual_version = match.groups()
            conflict_info.append({
                "dependent_package": pkg1_name,
                "dependent_version": pkg1_version,
                "required_package": pkg2_name,
                "required_operator": operator,
                "required_version": required_version,
                "actual_package": actual_pkg_name,
                "actual_version": actual_version
            })

    # Apply resolution strategy
    resolved = []
    failed = []

    for conflict in conflict_info:
        if strategy == "upgrade":
            # Upgrade the conflicting package to meet the requirement
            package_spec = f"{conflict['actual_package']}{conflict['required_operator']}{conflict['required_version']}"
            success, message = install_package(env_path, package_spec, upgrade=True)

            if success:
                resolved.append({
                    "package": conflict['actual_package'],
                    "action": "upgraded",
                    "from_version": conflict['actual_version'],
                    "to_spec": package_spec
                })
            else:
                failed.append({
                    "package": conflict['actual_package'],
                    "action": "upgrade",
                    "error": message
                })

        elif strategy == "downgrade":
            # Downgrade the dependent package to a version that doesn't have the conflict
            success, pkg_info = get_package_info(env_path, conflict['dependent_package'])

            if success:
                # Uninstall and reinstall an earlier version
                uninstall_package(env_path, conflict['dependent_package'])

                # Try to find an earlier version
                package_spec = f"{conflict['dependent_package']}<{conflict['dependent_version']}"
                install_success, install_message = install_package(env_path, package_spec)

                if install_success:
                    resolved.append({
                        "package": conflict['dependent_package'],
                        "action": "downgraded",
                        "from_version": conflict['dependent_version'],
                        "to_spec": package_spec
                    })
                else:
                    failed.append({
                        "package": conflict['dependent_package'],
                        "action": "downgrade",
                        "error": install_message
                    })
            else:
                failed.append({
                    "package": conflict['dependent_package'],
                    "action": "downgrade",
                    "error": "Failed to get package information"
                })

        elif strategy == "remove":
            # Remove the conflicting package
            success, message = uninstall_package(env_path, conflict['actual_package'])

            if success:
                resolved.append({
                    "package": conflict['actual_package'],
                    "action": "removed",
                    "version": conflict['actual_version']
                })
            else:
                failed.append({
                    "package": conflict['actual_package'],
                    "action": "remove",
                    "error": message
                })

    # Check if all conflicts were resolved
    if not failed:
        logger.info(f"Successfully resolved all {len(resolved)} conflicts")
        return True, {
            "message": f"Successfully resolved all {len(resolved)} conflicts",
            "resolved": resolved,
            "failed": []
        }
    else:
        logger.warning(f"Resolved {len(resolved)} conflicts, but {len(failed)} failed")
        return False, {
            "message": f"Resolved {len(resolved)} conflicts, but {len(failed)} failed",
            "resolved": resolved,
            "failed": failed
        }


def build_dependency_graph(
    env_path: str,
    root_packages: Optional[List[str]] = None
) -> Tuple[bool, Dict[str, Any]]:
    """
    Build a dependency graph for installed packages.

    Args:
        env_path: Path to the virtual environment
        root_packages: List of root package names to start from (if None, use all packages)

    Returns:
        Tuple[bool, Dict[str, Any]]: Success status and dependency graph
    """
    logger.info("Building dependency graph")

    # Determine the pip executable in the virtual environment
    if platform.system() == "Windows":
        pip_exe = os.path.join(env_path, "Scripts", "pip.exe")
    else:
        pip_exe = os.path.join(env_path, "bin", "pip")

    if not os.path.exists(pip_exe):
        logger.error(f"Pip executable not found at {pip_exe}")
        return False, {"error": f"Pip executable not found at {pip_exe}"}

    # Get list of installed packages
    try:
        result = subprocess.run(
            [pip_exe, "list", "--format=json"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        import json
        installed_packages = json.loads(result.stdout)
        installed_package_names = [pkg["name"].lower() for pkg in installed_packages]

        # If no root packages specified, use all installed packages
        if not root_packages:
            root_packages = installed_package_names
        else:
            root_packages = [pkg.lower() for pkg in root_packages]
            # Filter out packages that are not installed
            root_packages = [pkg for pkg in root_packages if pkg in installed_package_names]

        # Build dependency graph
        graph = {}
        visited = set()

        def build_graph_recursive(package_name):
            if package_name in visited:
                return

            visited.add(package_name)

            # Get package information
            success, pkg_info = get_package_info(env_path, package_name)

            if success:
                # Add package to graph
                graph[package_name] = {
                    "name": package_name,
                    "version": pkg_info.get("version", "unknown"),
                    "dependencies": pkg_info.get("requires", []),
                    "dependents": pkg_info.get("required_by", [])
                }

                # Recursively process dependencies
                for dep in pkg_info.get("requires", []):
                    # Extract package name from dependency specification
                    dep_name = re.split(r'[<>=!~]', dep)[0].strip().lower()
                    if dep_name in installed_package_names:
                        build_graph_recursive(dep_name)
            else:
                logger.warning(f"Failed to get information for package: {package_name}")

        # Build graph starting from root packages
        for package in root_packages:
            build_graph_recursive(package)

        logger.info(f"Successfully built dependency graph with {len(graph)} packages")
        return True, {
            "graph": graph,
            "root_packages": root_packages,
            "package_count": len(graph)
        }
    except subprocess.CalledProcessError as e:
        error_msg = e.stderr if hasattr(e, 'stderr') else str(e)
        logger.error(f"Failed to build dependency graph: {error_msg}")
        return False, {"error": f"Failed to build dependency graph: {error_msg}"}
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse pip list output: {str(e)}")
        return False, {"error": f"Failed to parse pip list output: {str(e)}"}


def find_dependency_path(
    env_path: str,
    from_package: str,
    to_package: str
) -> Tuple[bool, Dict[str, Any]]:
    """
    Find the dependency path between two packages.

    Args:
        env_path: Path to the virtual environment
        from_package: Starting package name
        to_package: Target package name

    Returns:
        Tuple[bool, Dict[str, Any]]: Success status and path information
    """
    logger.info(f"Finding dependency path from {from_package} to {to_package}")

    # Build dependency graph
    success, graph_info = build_dependency_graph(env_path)

    if not success:
        return False, graph_info

    graph = graph_info["graph"]
    from_package = from_package.lower()
    to_package = to_package.lower()

    # Check if both packages exist in the graph
    if from_package not in graph:
        logger.error(f"Package not found in graph: {from_package}")
        return False, {"error": f"Package not found in graph: {from_package}"}

    if to_package not in graph:
        logger.error(f"Package not found in graph: {to_package}")
        return False, {"error": f"Package not found in graph: {to_package}"}

    # Breadth-first search to find the shortest path
    queue = [(from_package, [from_package])]
    visited = {from_package}

    while queue:
        current, path = queue.pop(0)

        # Check if we've reached the target
        if current == to_package:
            logger.info(f"Found dependency path: {' -> '.join(path)}")

            # Build detailed path with version information
            detailed_path = []
            for pkg in path:
                detailed_path.append({
                    "name": pkg,
                    "version": graph[pkg]["version"]
                })

            return True, {
                "path_exists": True,
                "path": path,
                "detailed_path": detailed_path,
                "path_length": len(path)
            }

        # Add dependencies to the queue
        for dep_spec in graph[current]["dependencies"]:
            # Extract package name from dependency specification
            dep_name = re.split(r'[<>=!~]', dep_spec)[0].strip().lower()

            if dep_name in graph and dep_name not in visited:
                visited.add(dep_name)
                queue.append((dep_name, path + [dep_name]))

    logger.info(f"No dependency path found from {from_package} to {to_package}")
    return True, {
        "path_exists": False,
        "message": f"No dependency path found from {from_package} to {to_package}"
    }


def find_circular_dependencies(env_path: str) -> Tuple[bool, Dict[str, Any]]:
    """
    Find circular dependencies in the installed packages.

    Args:
        env_path: Path to the virtual environment

    Returns:
        Tuple[bool, Dict[str, Any]]: Success status and circular dependency information
    """
    logger.info("Finding circular dependencies")

    # Build dependency graph
    success, graph_info = build_dependency_graph(env_path)

    if not success:
        return False, graph_info

    graph = graph_info["graph"]

    # Find circular dependencies using depth-first search
    circular_deps = []
    visited = set()
    path = []
    path_set = set()

    def dfs(package):
        if package in path_set:
            # Found a cycle
            cycle_start = path.index(package)
            cycle = path[cycle_start:] + [package]
            circular_deps.append(cycle)
            return

        if package in visited:
            return

        visited.add(package)
        path.append(package)
        path_set.add(package)

        for dep_spec in graph.get(package, {}).get("dependencies", []):
            # Extract package name from dependency specification
            dep_name = re.split(r'[<>=!~]', dep_spec)[0].strip().lower()

            if dep_name in graph:
                dfs(dep_name)

        path.pop()
        path_set.remove(package)

    # Run DFS from each package
    for package in graph:
        dfs(package)

    # Remove duplicate cycles (same cycle starting from different points)
    unique_cycles = []
    cycle_sets = []

    for cycle in circular_deps:
        cycle_set = frozenset(cycle)
        if cycle_set not in cycle_sets:
            cycle_sets.append(cycle_set)
            unique_cycles.append(cycle)

    logger.info(f"Found {len(unique_cycles)} circular dependencies")
    return True, {
        "circular_dependencies": unique_cycles,
        "count": len(unique_cycles)
    }
