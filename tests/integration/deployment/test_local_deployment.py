"""
Integration tests for local deployment.
"""
import os
import shutil
import tempfile
import subprocess
from unittest.mock import patch, MagicMock

import pytest

# Skip these tests if running in CI environment
pytestmark = pytest.mark.skipif(
    os.environ.get("CI") == "true",
    reason="Skipping integration tests in CI environment"
)


class TestLocalDeployment:
    """Integration tests for local deployment."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for test files."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def project_dir(self, temp_dir):
        """Create a project directory with necessary files."""
        project_dir = os.path.join(temp_dir, "test-project")
        os.makedirs(project_dir, exist_ok=True)
        
        # Create a simple requirements.txt file
        with open(os.path.join(project_dir, "requirements.txt"), "w") as f:
            f.write("flask==2.0.1\n")
            f.write("gunicorn==20.1.0\n")
        
        # Create a simple app.py file
        with open(os.path.join(project_dir, "app.py"), "w") as f:
            f.write("from flask import Flask\n")
            f.write("app = Flask(__name__)\n")
            f.write("\n")
            f.write("@app.route('/')\n")
            f.write("def hello():\n")
            f.write("    return 'Hello, World!'\n")
            f.write("\n")
            f.write("if __name__ == '__main__':\n")
            f.write("    app.run(debug=True)\n")
        
        return project_dir
    
    @patch("subprocess.run")
    def test_init_project(self, mock_run, project_dir):
        """Test initializing a project."""
        # Mock the subprocess.run function
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_process.stdout = "Project initialized successfully"
        mock_run.return_value = mock_process
        
        # Change to the project directory
        os.chdir(project_dir)
        
        # Run the init command
        result = subprocess.run(
            ["pythonweb", "init", "--existing"],
            capture_output=True,
            text=True,
            check=False
        )
        
        # Check that the command was called
        mock_run.assert_called_once()
        
        # Check that the command succeeded
        assert result.returncode == 0
        assert "initialized successfully" in result.stdout
    
    @patch("subprocess.run")
    def test_create_virtual_environment(self, mock_run, project_dir):
        """Test creating a virtual environment."""
        # Mock the subprocess.run function
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_process.stdout = "Virtual environment created successfully"
        mock_run.return_value = mock_process
        
        # Change to the project directory
        os.chdir(project_dir)
        
        # Run the venv create command
        result = subprocess.run(
            ["pythonweb", "venv", "create"],
            capture_output=True,
            text=True,
            check=False
        )
        
        # Check that the command was called
        mock_run.assert_called_once()
        
        # Check that the command succeeded
        assert result.returncode == 0
        assert "created successfully" in result.stdout
    
    @patch("subprocess.run")
    def test_install_dependencies(self, mock_run, project_dir):
        """Test installing dependencies."""
        # Mock the subprocess.run function
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_process.stdout = "Dependencies installed successfully"
        mock_run.return_value = mock_process
        
        # Change to the project directory
        os.chdir(project_dir)
        
        # Run the deps install command
        result = subprocess.run(
            ["pythonweb", "deps", "install"],
            capture_output=True,
            text=True,
            check=False
        )
        
        # Check that the command was called
        mock_run.assert_called_once()
        
        # Check that the command succeeded
        assert result.returncode == 0
        assert "installed successfully" in result.stdout
    
    @patch("subprocess.run")
    def test_run_application(self, mock_run, project_dir):
        """Test running the application."""
        # Mock the subprocess.run function
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_process.stdout = "Running on http://127.0.0.1:5000/"
        mock_run.return_value = mock_process
        
        # Change to the project directory
        os.chdir(project_dir)
        
        # Run the run command
        result = subprocess.run(
            ["pythonweb", "run"],
            capture_output=True,
            text=True,
            check=False
        )
        
        # Check that the command was called
        mock_run.assert_called_once()
        
        # Check that the command succeeded
        assert result.returncode == 0
        assert "Running on http://127.0.0.1:5000/" in result.stdout
    
    @patch("subprocess.run")
    def test_full_deployment_workflow(self, mock_run, project_dir):
        """Test the full deployment workflow."""
        # Mock the subprocess.run function for different commands
        def mock_run_side_effect(*args, **kwargs):
            command = args[0]
            mock_process = MagicMock()
            mock_process.returncode = 0
            
            if "init" in command:
                mock_process.stdout = "Project initialized successfully"
            elif "venv" in command and "create" in command:
                mock_process.stdout = "Virtual environment created successfully"
            elif "deps" in command and "install" in command:
                mock_process.stdout = "Dependencies installed successfully"
            elif "run" in command:
                mock_process.stdout = "Running on http://127.0.0.1:5000/"
            else:
                mock_process.stdout = "Command executed successfully"
            
            return mock_process
        
        mock_run.side_effect = mock_run_side_effect
        
        # Change to the project directory
        os.chdir(project_dir)
        
        # Run the full workflow
        commands = [
            ["pythonweb", "init", "--existing"],
            ["pythonweb", "venv", "create"],
            ["pythonweb", "deps", "install"],
            ["pythonweb", "run"]
        ]
        
        for command in commands:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=False
            )
            assert result.returncode == 0
        
        # Check that all commands were called
        assert mock_run.call_count == len(commands)
    
    @patch("subprocess.run")
    def test_deployment_with_custom_configuration(self, mock_run, project_dir):
        """Test deployment with custom configuration."""
        # Mock the subprocess.run function
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_process.stdout = "Configuration set successfully"
        mock_run.return_value = mock_process
        
        # Change to the project directory
        os.chdir(project_dir)
        
        # Set custom configuration
        config_commands = [
            ["pythonweb", "config", "set", "SERVER__HOST=0.0.0.0"],
            ["pythonweb", "config", "set", "SERVER__PORT=8000"],
            ["pythonweb", "config", "set", "LOGGING__LEVEL=DEBUG"]
        ]
        
        for command in config_commands:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=False
            )
            assert result.returncode == 0
        
        # Run the application with custom configuration
        run_result = subprocess.run(
            ["pythonweb", "run"],
            capture_output=True,
            text=True,
            check=False
        )
        
        # Check that the commands were called
        assert mock_run.call_count == len(config_commands) + 1
        
        # Check that the run command succeeded
        assert run_result.returncode == 0
    
    @patch("subprocess.run")
    def test_deployment_error_handling(self, mock_run, project_dir):
        """Test error handling during deployment."""
        # Mock the subprocess.run function to simulate an error
        mock_process = MagicMock()
        mock_process.returncode = 1
        mock_process.stderr = "Error: Could not install dependencies"
        mock_run.return_value = mock_process
        
        # Change to the project directory
        os.chdir(project_dir)
        
        # Run the deps install command
        result = subprocess.run(
            ["pythonweb", "deps", "install"],
            capture_output=True,
            text=True,
            check=False
        )
        
        # Check that the command was called
        mock_run.assert_called_once()
        
        # Check that the command failed
        assert result.returncode == 1
        assert "Error" in result.stderr
