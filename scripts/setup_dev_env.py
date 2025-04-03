#!/usr/bin/env python
"""
Script to set up the development environment for PythonWeb Installer.
"""
import os
import sys
import subprocess
import argparse
from pathlib import Path


def run_command(command, cwd=None):
    """Run a shell command and print output."""
    print(f"Running: {command}")
    try:
        result = subprocess.run(
            command,
            shell=True,
            check=True,
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error: {e}")
        if e.stderr:
            print(f"Error details: {e.stderr}")
        return False


def setup_virtual_environment(venv_path):
    """Set up a virtual environment."""
    if os.path.exists(venv_path):
        print(f"Virtual environment already exists at {venv_path}")
        return True
    
    print("Creating virtual environment...")
    return run_command(f"python -m venv {venv_path}")


def install_dependencies(venv_path, dev_mode=True):
    """Install project dependencies."""
    # Determine the pip executable path based on the OS
    if sys.platform == "win32":
        pip_path = os.path.join(venv_path, "Scripts", "pip")
    else:
        pip_path = os.path.join(venv_path, "bin", "pip")
    
    print("Upgrading pip...")
    run_command(f'"{pip_path}" install --upgrade pip')
    
    print("Installing project in development mode...")
    run_command(f'"{pip_path}" install -e .')
    
    if dev_mode:
        print("Installing development dependencies...")
        run_command(f'"{pip_path}" install -r requirements-dev.txt')
    
    return True


def setup_pre_commit(venv_path):
    """Set up pre-commit hooks."""
    # Determine the pre-commit executable path based on the OS
    if sys.platform == "win32":
        pre_commit_path = os.path.join(venv_path, "Scripts", "pre-commit")
    else:
        pre_commit_path = os.path.join(venv_path, "bin", "pre-commit")
    
    print("Setting up pre-commit hooks...")
    return run_command(f'"{pre_commit_path}" install')


def create_env_file():
    """Create a .env file with default values if it doesn't exist."""
    env_path = Path(".env")
    
    if env_path.exists():
        print(".env file already exists")
        return True
    
    print("Creating .env file with default values...")
    default_env_content = """# Development environment variables
PYTHONWEB_MODE=development
PYTHONWEB_DB_MODE=sqlite
PYTHONWEB_REPO=https://github.com/yourusername/PythonWeb.git
PYTHONWEB_INSTALL_PATH=C:/Projects/templates/PythonWeb
"""
    
    try:
        with open(env_path, "w") as f:
            f.write(default_env_content)
        print(".env file created successfully")
        return True
    except Exception as e:
        print(f"Error creating .env file: {e}")
        return False


def main():
    """Main function to set up the development environment."""
    parser = argparse.ArgumentParser(description="Set up the development environment")
    parser.add_argument("--venv", default="venv", help="Path to virtual environment")
    parser.add_argument("--no-dev", action="store_true", help="Skip development dependencies")
    args = parser.parse_args()
    
    # Get the project root directory
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)
    
    print(f"Setting up development environment in {project_root}")
    
    # Setup steps
    venv_path = args.venv
    if not setup_virtual_environment(venv_path):
        print("Failed to create virtual environment")
        return 1
    
    if not install_dependencies(venv_path, not args.no_dev):
        print("Failed to install dependencies")
        return 1
    
    if not args.no_dev and not setup_pre_commit(venv_path):
        print("Failed to set up pre-commit hooks")
        return 1
    
    if not create_env_file():
        print("Failed to create .env file")
        return 1
    
    print("\nDevelopment environment setup complete!")
    
    # Print activation instructions
    if sys.platform == "win32":
        print(f"\nTo activate the virtual environment, run:\n{venv_path}\\Scripts\\activate")
    else:
        print(f"\nTo activate the virtual environment, run:\nsource {venv_path}/bin/activate")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
