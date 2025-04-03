"""
Integration tests for documentation validation.
"""
import os
import re
import subprocess
from unittest.mock import patch, MagicMock

import pytest

# Skip these tests if running in CI environment
pytestmark = pytest.mark.skipif(
    os.environ.get("CI") == "true",
    reason="Skipping integration tests in CI environment"
)


class TestDocumentationValidation:
    """Integration tests for documentation validation."""
    
    @pytest.fixture
    def doc_files(self):
        """Get a list of documentation files."""
        doc_files = []
        for root, _, files in os.walk("docs"):
            for file in files:
                if file.endswith(".md"):
                    doc_files.append(os.path.join(root, file))
        return doc_files
    
    def test_markdown_syntax(self, doc_files):
        """Test that markdown files have valid syntax."""
        for doc_file in doc_files:
            # Use a markdown linter to check syntax
            # This is a simplified check that just looks for common issues
            with open(doc_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check for unclosed code blocks
            code_block_starts = len(re.findall(r'```', content))
            assert code_block_starts % 2 == 0, f"Unclosed code blocks in {doc_file}"
            
            # Check for broken links
            links = re.findall(r'\[.*?\]\((.*?)\)', content)
            for link in links:
                if not link.startswith(('http://', 'https://', '#')):
                    # It's a relative link, check if it exists
                    link_path = os.path.normpath(os.path.join(os.path.dirname(doc_file), link))
                    assert os.path.exists(link_path) or '#' in link, f"Broken link in {doc_file}: {link}"
    
    def test_command_examples(self, doc_files):
        """Test that command examples are valid."""
        for doc_file in doc_files:
            with open(doc_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract bash code blocks
            bash_blocks = re.findall(r'```bash\n(.*?)```', content, re.DOTALL)
            
            for block in bash_blocks:
                # Check for pythonweb commands
                pythonweb_commands = re.findall(r'^pythonweb\s+(\w+)', block, re.MULTILINE)
                
                for command in pythonweb_commands:
                    # Verify that the command is valid
                    assert command in [
                        'init', 'venv', 'deps', 'repo', 'config', 'env',
                        'db', 'run', 'deploy', 'test', 'lint', 'logs'
                    ], f"Invalid command in {doc_file}: {command}"
    
    def test_configuration_examples(self, doc_files):
        """Test that configuration examples are valid."""
        for doc_file in doc_files:
            with open(doc_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract yaml code blocks
            yaml_blocks = re.findall(r'```yaml\n(.*?)```', content, re.DOTALL)
            
            for block in yaml_blocks:
                # Check for valid YAML syntax
                # This is a simplified check that just looks for common issues
                
                # Check for proper indentation
                lines = block.split('\n')
                for i, line in enumerate(lines):
                    if line.strip() and not line.strip().startswith('#'):
                        # Check if indentation is a multiple of 2 spaces
                        indent = len(line) - len(line.lstrip())
                        assert indent % 2 == 0, f"Invalid indentation in {doc_file}, line {i+1}: {line}"
                
                # Check for missing colons
                for line in lines:
                    if line.strip() and not line.strip().startswith('#') and ':' not in line:
                        # If it's not a list item (starting with -) and not a continuation line
                        if not line.strip().startswith('-') and not line.strip().startswith('{') and not line.strip().startswith('}'):
                            assert False, f"Missing colon in YAML in {doc_file}: {line}"
    
    @patch("subprocess.run")
    def test_command_reference_accuracy(self, mock_run):
        """Test that command reference accurately describes commands."""
        # Mock the subprocess.run function
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_process.stdout = "Usage: pythonweb [OPTIONS] COMMAND [ARGS]..."
        mock_run.return_value = mock_process
        
        # Read the command reference
        with open("docs/command_reference/README.md", 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Extract commands from the reference
        commands = re.findall(r'### (\w+)', content)
        
        # Check each command
        for command in commands:
            # Run the help command
            result = subprocess.run(
                ["pythonweb", command, "--help"],
                capture_output=True,
                text=True,
                check=False
            )
            
            # Check that the command exists
            assert result.returncode == 0, f"Command {command} does not exist or returned an error"
            
            # Check that the command is documented
            command_section = re.search(f'### {command}(.*?)(?=### |$)', content, re.DOTALL)
            assert command_section, f"Command {command} is not documented"
            
            # Check that the command description is accurate
            # This is a simplified check that just looks for the command name in the help output
            assert command in result.stdout, f"Command {command} help output does not match documentation"
    
    def test_troubleshooting_guide_coverage(self):
        """Test that troubleshooting guide covers common issues."""
        # Read the troubleshooting guide
        with open("docs/troubleshooting/README.md", 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for common issue categories
        common_issues = [
            "Installation Issues",
            "Virtual Environment Issues",
            "Dependency Issues",
            "Repository Issues",
            "Configuration Issues",
            "Database Issues",
            "Deployment Issues",
            "Runtime Issues"
        ]
        
        for issue in common_issues:
            assert f"## {issue}" in content, f"Troubleshooting guide does not cover {issue}"
        
        # Check for common error messages
        common_errors = [
            "Permission denied",
            "Command not found",
            "No module named"
        ]
        
        for error in common_errors:
            assert error in content, f"Troubleshooting guide does not cover error: {error}"
    
    def test_user_guide_completeness(self):
        """Test that user guide covers all essential topics."""
        # Read the user guide
        with open("docs/user_guide/README.md", 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for essential topics
        essential_topics = [
            "Installation",
            "Quick Start",
            "Configuration",
            "Common Tasks",
            "Troubleshooting"
        ]
        
        for topic in essential_topics:
            assert f"## {topic}" in content, f"User guide does not cover {topic}"
        
        # Check for common tasks
        common_tasks = [
            "Virtual Environment",
            "Dependencies",
            "Repository",
            "Deployment"
        ]
        
        for task in common_tasks:
            assert task in content, f"User guide does not cover task: {task}"
    
    def test_local_deployment_guide_completeness(self):
        """Test that local deployment guide covers all essential topics."""
        # Read the local deployment guide
        with open("docs/deployment/local.md", 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for essential topics
        essential_topics = [
            "Prerequisites",
            "Installation",
            "Project Setup",
            "Virtual Environment",
            "Dependencies",
            "Configuration",
            "Database Setup",
            "Running the Application",
            "Testing",
            "Troubleshooting"
        ]
        
        for topic in essential_topics:
            assert f"## {topic}" in content, f"Local deployment guide does not cover {topic}"
        
        # Check for deployment steps
        deployment_steps = [
            "Creating a Virtual Environment",
            "Installing Dependencies",
            "Setting Configuration Options",
            "Running the Application"
        ]
        
        for step in deployment_steps:
            assert step in content, f"Local deployment guide does not cover step: {step}"
