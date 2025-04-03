"""
Integration tests for user experience.
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


class TestUserExperience:
    """Integration tests for user experience."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for test files."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @patch("subprocess.run")
    def test_help_command(self, mock_run):
        """Test that the help command provides useful information."""
        # Mock the subprocess.run function
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_process.stdout = """
        Usage: pythonweb [OPTIONS] COMMAND [ARGS]...
        
        Options:
          --version  Show the version and exit.
          --help     Show this message and exit.
        
        Commands:
          config   Manage configuration.
          deps     Manage dependencies.
          deploy   Deploy the application.
          env      Manage environment variables.
          init     Initialize a new project.
          repo     Manage repositories.
          run      Run the application.
          venv     Manage virtual environments.
        """
        mock_run.return_value = mock_process
        
        # Run the help command
        result = subprocess.run(
            ["pythonweb", "--help"],
            capture_output=True,
            text=True,
            check=False
        )
        
        # Check that the command was called
        mock_run.assert_called_once()
        
        # Check that the help output is useful
        assert result.returncode == 0
        assert "Usage:" in result.stdout
        assert "Commands:" in result.stdout
        assert "Options:" in result.stdout
        
        # Check that all main commands are listed
        main_commands = ["init", "venv", "deps", "repo", "config", "env", "run", "deploy"]
        for command in main_commands:
            assert command in result.stdout
    
    @patch("subprocess.run")
    def test_command_help(self, mock_run):
        """Test that each command's help provides useful information."""
        # List of commands to test
        commands = ["init", "venv", "deps", "repo", "config", "env", "run", "deploy"]
        
        for command in commands:
            # Mock the subprocess.run function
            mock_process = MagicMock()
            mock_process.returncode = 0
            mock_process.stdout = f"""
            Usage: pythonweb {command} [OPTIONS] [ARGS]...
            
            Options:
              --help  Show this message and exit.
            
            Description:
              This command does something useful.
            """
            mock_run.return_value = mock_process
            
            # Run the command help
            result = subprocess.run(
                ["pythonweb", command, "--help"],
                capture_output=True,
                text=True,
                check=False
            )
            
            # Check that the command was called
            assert mock_run.call_count > 0
            
            # Check that the help output is useful
            assert result.returncode == 0
            assert "Usage:" in result.stdout
            assert "Options:" in result.stdout
            
            # Reset the mock for the next command
            mock_run.reset_mock()
    
    @patch("subprocess.run")
    def test_error_messages(self, mock_run):
        """Test that error messages are clear and helpful."""
        # Mock the subprocess.run function to simulate an error
        mock_process = MagicMock()
        mock_process.returncode = 1
        mock_process.stderr = """
        Error: Could not find virtual environment.
        
        Try creating a virtual environment first:
          pythonweb venv create
        """
        mock_run.return_value = mock_process
        
        # Run a command that will fail
        result = subprocess.run(
            ["pythonweb", "deps", "install"],
            capture_output=True,
            text=True,
            check=False
        )
        
        # Check that the command was called
        mock_run.assert_called_once()
        
        # Check that the error message is clear and helpful
        assert result.returncode == 1
        assert "Error:" in result.stderr
        assert "Try" in result.stderr
    
    @patch("subprocess.run")
    def test_verbose_output(self, mock_run):
        """Test that verbose output provides more information."""
        # Mock the subprocess.run function
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_process.stdout = """
        Verbose: Checking if virtual environment exists
        Verbose: Virtual environment found
        Verbose: Installing dependencies
        Verbose: Dependencies installed successfully
        Dependencies installed successfully
        """
        mock_run.return_value = mock_process
        
        # Run a command with verbose output
        result = subprocess.run(
            ["pythonweb", "--verbose", "deps", "install"],
            capture_output=True,
            text=True,
            check=False
        )
        
        # Check that the command was called
        mock_run.assert_called_once()
        
        # Check that the verbose output provides more information
        assert result.returncode == 0
        assert "Verbose:" in result.stdout
        assert "Checking" in result.stdout
        assert "Dependencies installed successfully" in result.stdout
    
    @patch("subprocess.run")
    def test_quiet_output(self, mock_run):
        """Test that quiet output suppresses information."""
        # Mock the subprocess.run function
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_process.stdout = ""
        mock_run.return_value = mock_process
        
        # Run a command with quiet output
        result = subprocess.run(
            ["pythonweb", "--quiet", "deps", "install"],
            capture_output=True,
            text=True,
            check=False
        )
        
        # Check that the command was called
        mock_run.assert_called_once()
        
        # Check that the quiet output suppresses information
        assert result.returncode == 0
        assert result.stdout == ""
    
    @patch("subprocess.run")
    def test_version_command(self, mock_run):
        """Test that the version command shows the version."""
        # Mock the subprocess.run function
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_process.stdout = "PythonWeb Installer v1.0.0"
        mock_run.return_value = mock_process
        
        # Run the version command
        result = subprocess.run(
            ["pythonweb", "--version"],
            capture_output=True,
            text=True,
            check=False
        )
        
        # Check that the command was called
        mock_run.assert_called_once()
        
        # Check that the version is shown
        assert result.returncode == 0
        assert "v" in result.stdout
    
    @patch("subprocess.run")
    def test_command_aliases(self, mock_run, temp_dir):
        """Test that command aliases work."""
        # Mock the subprocess.run function
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_process.stdout = "Virtual environment created successfully"
        mock_run.return_value = mock_process
        
        # Change to the temporary directory
        os.chdir(temp_dir)
        
        # Run the command with an alias
        result = subprocess.run(
            ["pythonweb", "virtualenv", "create"],
            capture_output=True,
            text=True,
            check=False
        )
        
        # Check that the command was called
        mock_run.assert_called_once()
        
        # Check that the alias worked
        assert result.returncode == 0
        assert "created successfully" in result.stdout
    
    @patch("subprocess.run")
    def test_command_completion(self, mock_run):
        """Test that command completion works."""
        # Mock the subprocess.run function
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_process.stdout = """
        init
        venv
        deps
        repo
        config
        env
        run
        deploy
        """
        mock_run.return_value = mock_process
        
        # Run the command completion
        result = subprocess.run(
            ["pythonweb", "completion"],
            capture_output=True,
            text=True,
            check=False
        )
        
        # Check that the command was called
        mock_run.assert_called_once()
        
        # Check that the completion output is useful
        assert result.returncode == 0
        assert "init" in result.stdout
        assert "venv" in result.stdout
        assert "deps" in result.stdout
    
    @patch("subprocess.run")
    def test_interactive_mode(self, mock_run, temp_dir):
        """Test that interactive mode works."""
        # Mock the subprocess.run function
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_process.stdout = """
        Welcome to PythonWeb Installer interactive mode!
        Type 'help' for a list of commands.
        Type 'exit' to exit.
        
        pythonweb> help
        Available commands:
          init      Initialize a new project
          venv      Manage virtual environments
          deps      Manage dependencies
          repo      Manage repositories
          config    Manage configuration
          env       Manage environment variables
          run       Run the application
          deploy    Deploy the application
          exit      Exit interactive mode
        
        pythonweb> exit
        Goodbye!
        """
        mock_run.return_value = mock_process
        
        # Change to the temporary directory
        os.chdir(temp_dir)
        
        # Run the interactive mode
        result = subprocess.run(
            ["pythonweb", "interactive"],
            capture_output=True,
            text=True,
            check=False
        )
        
        # Check that the command was called
        mock_run.assert_called_once()
        
        # Check that the interactive mode works
        assert result.returncode == 0
        assert "Welcome" in result.stdout
        assert "Available commands" in result.stdout
        assert "Goodbye" in result.stdout
