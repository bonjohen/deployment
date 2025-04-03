# Development Environment Setup

This document provides instructions for setting up a development environment for the PythonWeb Installer project.

## Prerequisites

Before you begin, ensure you have the following installed:

- Python 3.7 or higher
- pip (Python package installer)
- Git

## Initial Setup

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/deployment.git
cd deployment
```

### 2. Create a Virtual Environment

```bash
# On Windows
python -m venv venv
venv\Scripts\activate

# On macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Development Dependencies

```bash
# Install the package in development mode
pip install -e .

# Install development dependencies
pip install -r requirements-dev.txt
```

## Development Tools

### Code Formatting and Linting

The project uses several tools to ensure code quality:

1. **Black** for code formatting:
   ```bash
   # Format all Python files
   black .
   ```

2. **isort** for import sorting:
   ```bash
   # Sort imports in all Python files
   isort .
   ```

3. **flake8** for style guide enforcement:
   ```bash
   # Check code style
   flake8
   ```

4. **pylint** for code quality analysis:
   ```bash
   # Run pylint on the package
   pylint pythonweb_installer
   ```

5. **mypy** for static type checking:
   ```bash
   # Run type checking
   mypy pythonweb_installer
   ```

### Running Tests

The project uses pytest for testing:

```bash
# Run all tests
pytest

# Run tests with coverage report
pytest --cov=pythonweb_installer

# Run specific test file
pytest tests/unit/test_config.py

# Run tests matching a specific name pattern
pytest -k "config"
```

### Building Documentation

The project uses Sphinx for documentation:

```bash
# Build HTML documentation
cd docs
make html
```

## Project Structure

```
deployment/
 pythonweb_installer/       # Main package
    __init__.py
    cli.py                  # Command-line interface
    installer.py            # Core installer functionality
    config.py               # Configuration management
    utils.py                # Utility functions
    templates.py            # Template rendering
    repository/             # Repository management
    environment/            # Environment management
    dependencies/           # Dependency management
    database/               # Database operations
    server/                 # Server configuration
    security/               # Security features
    templates/              # Jinja2 templates
 tests/                     # Test package
    unit/                   # Unit tests
    integration/            # Integration tests
    functional/             # Functional tests
 docs/                      # Documentation
 setup.py                   # Package setup
 README.md                  # Project README
 PROJECT_PLAN.md            # Project plan
 requirements.md            # Project requirements
```

## Development Workflow

1. **Create a Feature Branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make Changes**
   - Write code following the project's coding standards
   - Add tests for new functionality
   - Update documentation as needed

3. **Run Tests and Linting**
   ```bash
   # Format code
   black .
   isort .
   
   # Run linting
   flake8
   pylint pythonweb_installer
   
   # Run type checking
   mypy pythonweb_installer
   
   # Run tests
   pytest
   ```

4. **Commit Changes**
   ```bash
   git add .
   git commit -m "Add your feature description"
   ```

5. **Push Changes**
   ```bash
   git push origin feature/your-feature-name
   ```

6. **Create a Pull Request**
   - Go to the repository on GitHub
   - Create a new pull request from your feature branch
   - Fill out the pull request template
   - Request a code review

## Environment Variables

The following environment variables can be used to configure the development environment:

| Variable | Description | Default |
|----------|-------------|---------|
| `PYTHONWEB_MODE` | Deployment mode (development, production, test) | development |
| `PYTHONWEB_DB_MODE` | Database mode (sqlite, postgres, auto) | auto |
| `PYTHONWEB_REPO` | Template repository URL | https://github.com/yourusername/PythonWeb.git |
| `PYTHONWEB_INSTALL_PATH` | Installation path | C:/Projects/templates/PythonWeb |

You can set these variables in a `.env` file in the project root:

```
PYTHONWEB_MODE=development
PYTHONWEB_DB_MODE=sqlite
PYTHONWEB_REPO=https://github.com/yourusername/PythonWeb.git
PYTHONWEB_INSTALL_PATH=C:/Projects/templates/PythonWeb
```

## Troubleshooting

### Common Issues

1. **Import Errors**
   - Ensure you have activated the virtual environment
   - Verify that the package is installed in development mode (`pip install -e .`)

2. **Test Failures**
   - Check that all dependencies are installed
   - Verify that environment variables are set correctly
   - Look for specific error messages in the test output

3. **Linting Errors**
   - Run `black .` and `isort .` to automatically fix formatting issues
   - Address specific issues reported by flake8 and pylint

### Getting Help

If you encounter issues not covered in this guide:

1. Check the project documentation
2. Look for similar issues in the project's issue tracker
3. Reach out to the development team
