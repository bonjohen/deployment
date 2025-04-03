"""
Unit tests for dependency resolution functionality.
"""
import os
import json
import tempfile
import shutil
import subprocess
from unittest.mock import patch, MagicMock

import pytest

from pythonweb_installer.dependencies.resolution import (
    detect_dependency_conflicts,
    resolve_dependency_conflicts,
    build_dependency_graph,
    find_dependency_path,
    find_circular_dependencies
)


class TestDependencyResolution:
    """Tests for dependency resolution functionality."""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for test files."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def requirements_file(self, temp_dir):
        """Create a sample requirements.txt file."""
        file_path = os.path.join(temp_dir, "requirements.txt")
        with open(file_path, "w") as f:
            f.write("""
# Sample requirements file
package1==1.0.0
package2>=2.0.0
package3<3.0.0
            """)
        return file_path

    @pytest.fixture
    def package_specs(self):
        """Create sample package specifications."""
        return [
            {"name": "package1", "version": "1.0.0"},
            {"name": "package2", "version_spec": ">=2.0.0"},
            {"name": "package3", "version_spec": "<3.0.0"}
        ]

    @patch('os.path.exists')
    @patch('subprocess.run')
    def test_detect_dependency_conflicts_none(self, mock_run, mock_exists, temp_dir, package_specs):
        """Test detecting no dependency conflicts."""
        # Configure the mocks
        mock_exists.return_value = True
        mock_process = MagicMock()
        mock_process.stdout = ""
        mock_process.stderr = ""
        mock_run.return_value = mock_process

        env_path = os.path.join(temp_dir, "venv")
        success, result = detect_dependency_conflicts(env_path, package_specs=package_specs)

        assert success is True
        assert result["has_conflicts"] is False
        assert len(result["conflicts"]) == 0
        assert mock_run.call_count >= 1

    @patch('os.path.exists')
    @patch('subprocess.run')
    def test_detect_dependency_conflicts_with_conflicts(self, mock_run, mock_exists, temp_dir, package_specs):
        """Test detecting dependency conflicts."""
        # Configure the mocks
        mock_exists.return_value = True

        # First call to install pip-check succeeds
        first_process = MagicMock()
        first_process.stdout = ""
        first_process.stderr = ""

        # Second call to pip check returns conflicts
        second_process = MagicMock()
        second_process.stdout = "package1 1.0.0 has requirement package2>=2.0.0, which is incompatible with installed version package2 1.0.0."
        second_process.stderr = ""

        # Configure mock_run to return different results for each call
        mock_run.side_effect = [first_process, second_process]

        env_path = os.path.join(temp_dir, "venv")
        success, result = detect_dependency_conflicts(env_path, package_specs=package_specs)

        assert success is True
        assert result["has_conflicts"] is True
        assert len(result["conflicts"]) == 1
        assert "package1 1.0.0 has requirement package2>=2.0.0" in result["conflicts"][0]

    @patch('os.path.exists')
    @patch('subprocess.run')
    def test_detect_dependency_conflicts_from_file(self, mock_run, mock_exists, temp_dir, requirements_file):
        """Test detecting dependency conflicts from a requirements file."""
        # Configure the mocks
        mock_exists.return_value = True
        mock_process = MagicMock()
        mock_process.stdout = ""
        mock_process.stderr = ""
        mock_run.return_value = mock_process

        env_path = os.path.join(temp_dir, "venv")
        success, result = detect_dependency_conflicts(env_path, requirements_file=requirements_file)

        assert success is True
        assert result["has_conflicts"] is False
        assert len(result["conflicts"]) == 0
        assert mock_run.call_count >= 1

    @patch('os.path.exists')
    @patch('subprocess.run')
    def test_detect_dependency_conflicts_failure(self, mock_run, mock_exists, temp_dir, package_specs):
        """Test dependency conflict detection failure."""
        # Configure the mocks
        mock_exists.return_value = True
        mock_run.side_effect = subprocess.CalledProcessError(1, "pip", stderr=b"Detection failed")

        env_path = os.path.join(temp_dir, "venv")
        success, result = detect_dependency_conflicts(env_path, package_specs=package_specs)

        assert success is False
        assert "error" in result
        assert "Failed to check for dependency conflicts" in result["error"]

    def test_detect_dependency_conflicts_no_specs(self, temp_dir):
        """Test detecting dependency conflicts with no package specifications."""
        env_path = os.path.join(temp_dir, "venv")
        success, result = detect_dependency_conflicts(env_path)

        assert success is False
        assert "error" in result
        assert "No package specifications provided" in result["error"]

    @patch('os.path.exists')
    def test_detect_dependency_conflicts_no_pip(self, mock_exists, temp_dir, package_specs):
        """Test detecting dependency conflicts when pip is not available."""
        # Configure the mock
        mock_exists.return_value = False

        env_path = os.path.join(temp_dir, "venv")
        success, result = detect_dependency_conflicts(env_path, package_specs=package_specs)

        assert success is False
        assert "error" in result
        assert "Pip executable not found" in result["error"]

    @patch('pythonweb_installer.dependencies.resolution.install_package')
    def test_resolve_dependency_conflicts_upgrade_success(self, mock_install, temp_dir):
        """Test resolving dependency conflicts with upgrade strategy."""
        # Configure the mock
        mock_install.return_value = (True, "Successfully installed package2>=2.0.0")

        env_path = os.path.join(temp_dir, "venv")
        conflicts = [
            "package1 1.0.0 has requirement package2>=2.0.0, but you have package2 1.0.0."
        ]

        success, result = resolve_dependency_conflicts(env_path, conflicts, strategy="upgrade")

        assert success is True
        assert len(result["resolved"]) == 1
        assert result["resolved"][0]["package"] == "package2"
        assert result["resolved"][0]["action"] == "upgraded"
        assert len(result["failed"]) == 0
        mock_install.assert_called_once()

    @patch('pythonweb_installer.dependencies.resolution.get_package_info')
    @patch('pythonweb_installer.dependencies.resolution.uninstall_package')
    @patch('pythonweb_installer.dependencies.resolution.install_package')
    def test_resolve_dependency_conflicts_downgrade_success(self, mock_install, mock_uninstall, mock_get_info, temp_dir):
        """Test resolving dependency conflicts with downgrade strategy."""
        # Configure the mocks
        mock_get_info.return_value = (True, {"name": "package1", "version": "1.0.0"})
        mock_uninstall.return_value = (True, "Successfully uninstalled package1")
        mock_install.return_value = (True, "Successfully installed package1<1.0.0")

        env_path = os.path.join(temp_dir, "venv")
        conflicts = [
            "package1 1.0.0 has requirement package2>=2.0.0, but you have package2 1.0.0."
        ]

        success, result = resolve_dependency_conflicts(env_path, conflicts, strategy="downgrade")

        assert success is True
        assert len(result["resolved"]) == 1
        assert result["resolved"][0]["package"] == "package1"
        assert result["resolved"][0]["action"] == "downgraded"
        assert len(result["failed"]) == 0
        mock_get_info.assert_called_once()
        mock_uninstall.assert_called_once()
        mock_install.assert_called_once()

    @patch('pythonweb_installer.dependencies.resolution.uninstall_package')
    def test_resolve_dependency_conflicts_remove_success(self, mock_uninstall, temp_dir):
        """Test resolving dependency conflicts with remove strategy."""
        # Configure the mock
        mock_uninstall.return_value = (True, "Successfully uninstalled package2")

        env_path = os.path.join(temp_dir, "venv")
        conflicts = [
            "package1 1.0.0 has requirement package2>=2.0.0, but you have package2 1.0.0."
        ]

        success, result = resolve_dependency_conflicts(env_path, conflicts, strategy="remove")

        assert success is True
        assert len(result["resolved"]) == 1
        assert result["resolved"][0]["package"] == "package2"
        assert result["resolved"][0]["action"] == "removed"
        assert len(result["failed"]) == 0
        mock_uninstall.assert_called_once()

    @patch('pythonweb_installer.dependencies.resolution.install_package')
    def test_resolve_dependency_conflicts_partial_failure(self, mock_install, temp_dir):
        """Test partially failing to resolve dependency conflicts."""
        # Configure the mock
        mock_install.return_value = (False, "Failed to install package2>=2.0.0")

        env_path = os.path.join(temp_dir, "venv")
        conflicts = [
            "package1 1.0.0 has requirement package2>=2.0.0, but you have package2 1.0.0."
        ]

        success, result = resolve_dependency_conflicts(env_path, conflicts, strategy="upgrade")

        assert success is False
        assert len(result["resolved"]) == 0
        assert len(result["failed"]) == 1
        assert result["failed"][0]["package"] == "package2"
        assert result["failed"][0]["action"] == "upgrade"
        mock_install.assert_called_once()

    def test_resolve_dependency_conflicts_no_conflicts(self, temp_dir):
        """Test resolving when there are no conflicts."""
        env_path = os.path.join(temp_dir, "venv")
        conflicts = []

        success, result = resolve_dependency_conflicts(env_path, conflicts)

        assert success is True
        assert "No conflicts to resolve" in result["message"]

    @patch('os.path.exists')
    @patch('subprocess.run')
    @patch('pythonweb_installer.dependencies.resolution.get_package_info')
    def test_build_dependency_graph_success(self, mock_get_info, mock_run, mock_exists, temp_dir):
        """Test successful dependency graph building."""
        # Configure the mocks
        mock_exists.return_value = True
        mock_process = MagicMock()
        mock_process.stdout = json.dumps([
            {"name": "package1", "version": "1.0.0"},
            {"name": "package2", "version": "2.0.0"},
            {"name": "package3", "version": "3.0.0"}
        ])
        mock_run.return_value = mock_process

        # Mock package info responses
        def get_info_side_effect(env_path, package_name):
            if package_name == "package1":
                return True, {
                    "name": "package1",
                    "version": "1.0.0",
                    "requires": ["package2>=2.0.0"],
                    "required_by": []
                }
            elif package_name == "package2":
                return True, {
                    "name": "package2",
                    "version": "2.0.0",
                    "requires": ["package3>=3.0.0"],
                    "required_by": ["package1"]
                }
            elif package_name == "package3":
                return True, {
                    "name": "package3",
                    "version": "3.0.0",
                    "requires": [],
                    "required_by": ["package2"]
                }
            return False, {"error": f"Unknown package: {package_name}"}

        mock_get_info.side_effect = get_info_side_effect

        env_path = os.path.join(temp_dir, "venv")
        success, result = build_dependency_graph(env_path)

        assert success is True
        assert "graph" in result
        assert len(result["graph"]) == 3
        assert "package1" in result["graph"]
        assert "package2" in result["graph"]
        assert "package3" in result["graph"]
        assert result["graph"]["package1"]["dependencies"] == ["package2>=2.0.0"]
        assert result["graph"]["package2"]["dependencies"] == ["package3>=3.0.0"]
        assert result["graph"]["package3"]["dependencies"] == []

    @patch('os.path.exists')
    @patch('subprocess.run')
    def test_build_dependency_graph_with_root_packages(self, mock_run, mock_exists, temp_dir):
        """Test building a dependency graph with specified root packages."""
        # Configure the mocks
        mock_exists.return_value = True
        mock_process = MagicMock()
        mock_process.stdout = json.dumps([
            {"name": "package1", "version": "1.0.0"},
            {"name": "package2", "version": "2.0.0"},
            {"name": "package3", "version": "3.0.0"}
        ])
        mock_run.return_value = mock_process

        env_path = os.path.join(temp_dir, "venv")
        root_packages = ["package1"]
        success, result = build_dependency_graph(env_path, root_packages)

        assert success is True
        assert "root_packages" in result
        assert result["root_packages"] == ["package1"]

    @patch('os.path.exists')
    @patch('subprocess.run')
    def test_build_dependency_graph_failure(self, mock_run, mock_exists, temp_dir):
        """Test dependency graph building failure."""
        # Configure the mocks
        mock_exists.return_value = True
        mock_run.side_effect = subprocess.CalledProcessError(1, "pip", stderr=b"Graph building failed")

        env_path = os.path.join(temp_dir, "venv")
        success, result = build_dependency_graph(env_path)

        assert success is False
        assert "error" in result
        assert "Failed to build dependency graph" in result["error"]

    @patch('os.path.exists')
    def test_build_dependency_graph_no_pip(self, mock_exists, temp_dir):
        """Test building a dependency graph when pip is not available."""
        # Configure the mock
        mock_exists.return_value = False

        env_path = os.path.join(temp_dir, "venv")
        success, result = build_dependency_graph(env_path)

        assert success is False
        assert "error" in result
        assert "Pip executable not found" in result["error"]

    @patch('pythonweb_installer.dependencies.resolution.build_dependency_graph')
    def test_find_dependency_path_exists(self, mock_build_graph, temp_dir):
        """Test finding an existing dependency path."""
        # Configure the mock
        mock_build_graph.return_value = (
            True,
            {
                "graph": {
                    "package1": {
                        "name": "package1",
                        "version": "1.0.0",
                        "dependencies": ["package2>=2.0.0"],
                        "dependents": []
                    },
                    "package2": {
                        "name": "package2",
                        "version": "2.0.0",
                        "dependencies": ["package3>=3.0.0"],
                        "dependents": ["package1"]
                    },
                    "package3": {
                        "name": "package3",
                        "version": "3.0.0",
                        "dependencies": [],
                        "dependents": ["package2"]
                    }
                }
            }
        )

        env_path = os.path.join(temp_dir, "venv")
        success, result = find_dependency_path(env_path, "package1", "package3")

        assert success is True
        assert result["path_exists"] is True
        assert result["path"] == ["package1", "package2", "package3"]
        assert result["path_length"] == 3
        assert result["detailed_path"][0]["name"] == "package1"
        assert result["detailed_path"][0]["version"] == "1.0.0"
        assert result["detailed_path"][2]["name"] == "package3"
        assert result["detailed_path"][2]["version"] == "3.0.0"

    @patch('pythonweb_installer.dependencies.resolution.build_dependency_graph')
    def test_find_dependency_path_not_exists(self, mock_build_graph, temp_dir):
        """Test finding a non-existent dependency path."""
        # Configure the mock
        mock_build_graph.return_value = (
            True,
            {
                "graph": {
                    "package1": {
                        "name": "package1",
                        "version": "1.0.0",
                        "dependencies": [],
                        "dependents": []
                    },
                    "package4": {
                        "name": "package4",
                        "version": "4.0.0",
                        "dependencies": [],
                        "dependents": []
                    }
                }
            }
        )

        env_path = os.path.join(temp_dir, "venv")
        success, result = find_dependency_path(env_path, "package1", "package4")

        assert success is True
        assert result["path_exists"] is False
        assert "No dependency path found" in result["message"]

    @patch('pythonweb_installer.dependencies.resolution.build_dependency_graph')
    def test_find_dependency_path_package_not_found(self, mock_build_graph, temp_dir):
        """Test finding a dependency path with a non-existent package."""
        # Configure the mock
        mock_build_graph.return_value = (
            True,
            {
                "graph": {
                    "package1": {
                        "name": "package1",
                        "version": "1.0.0",
                        "dependencies": [],
                        "dependents": []
                    }
                }
            }
        )

        env_path = os.path.join(temp_dir, "venv")
        success, result = find_dependency_path(env_path, "package1", "nonexistent")

        assert success is False
        assert "error" in result
        assert "Package not found in graph" in result["error"]

    @patch('pythonweb_installer.dependencies.resolution.build_dependency_graph')
    def test_find_circular_dependencies_exists(self, mock_build_graph, temp_dir):
        """Test finding existing circular dependencies."""
        # Configure the mock
        mock_build_graph.return_value = (
            True,
            {
                "graph": {
                    "package1": {
                        "name": "package1",
                        "version": "1.0.0",
                        "dependencies": ["package2>=2.0.0"],
                        "dependents": ["package3"]
                    },
                    "package2": {
                        "name": "package2",
                        "version": "2.0.0",
                        "dependencies": ["package3>=3.0.0"],
                        "dependents": ["package1"]
                    },
                    "package3": {
                        "name": "package3",
                        "version": "3.0.0",
                        "dependencies": ["package1>=1.0.0"],
                        "dependents": ["package2"]
                    }
                }
            }
        )

        env_path = os.path.join(temp_dir, "venv")
        success, result = find_circular_dependencies(env_path)

        assert success is True
        assert "circular_dependencies" in result
        assert len(result["circular_dependencies"]) > 0
        assert result["count"] > 0

        # Check that at least one cycle contains all three packages
        found_cycle = False
        for cycle in result["circular_dependencies"]:
            if set(cycle) == {"package1", "package2", "package3"}:
                found_cycle = True
                break

        assert found_cycle is True

    @patch('pythonweb_installer.dependencies.resolution.build_dependency_graph')
    def test_find_circular_dependencies_none(self, mock_build_graph, temp_dir):
        """Test finding circular dependencies when none exist."""
        # Configure the mock
        mock_build_graph.return_value = (
            True,
            {
                "graph": {
                    "package1": {
                        "name": "package1",
                        "version": "1.0.0",
                        "dependencies": ["package2>=2.0.0"],
                        "dependents": []
                    },
                    "package2": {
                        "name": "package2",
                        "version": "2.0.0",
                        "dependencies": ["package3>=3.0.0"],
                        "dependents": ["package1"]
                    },
                    "package3": {
                        "name": "package3",
                        "version": "3.0.0",
                        "dependencies": [],
                        "dependents": ["package2"]
                    }
                }
            }
        )

        env_path = os.path.join(temp_dir, "venv")
        success, result = find_circular_dependencies(env_path)

        assert success is True
        assert "circular_dependencies" in result
        assert len(result["circular_dependencies"]) == 0
        assert result["count"] == 0

    @patch('pythonweb_installer.dependencies.resolution.build_dependency_graph')
    def test_find_circular_dependencies_failure(self, mock_build_graph, temp_dir):
        """Test circular dependencies detection failure."""
        # Configure the mock
        mock_build_graph.return_value = (False, {"error": "Graph building failed"})

        env_path = os.path.join(temp_dir, "venv")
        success, result = find_circular_dependencies(env_path)

        assert success is False
        assert "error" in result
        assert "Graph building failed" in result["error"]
