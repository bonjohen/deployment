# Local Deployment Guide

This guide provides detailed instructions for deploying Python web applications locally using the PythonWeb Installer.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Project Setup](#project-setup)
- [Virtual Environment](#virtual-environment)
- [Dependencies](#dependencies)
- [Configuration](#configuration)
- [Database Setup](#database-setup)
- [Running the Application](#running-the-application)
- [Testing](#testing)
- [Troubleshooting](#troubleshooting)

## Prerequisites

Before deploying a Python web application locally, ensure you have the following prerequisites:

- Python 3.7 or higher
- pip (Python package installer)
- Git (for repository management)
- Database (SQLite for development, PostgreSQL for production)

## Installation

Install the PythonWeb Installer using pip:

```bash
pip install pythonweb-installer
```

Verify the installation:

```bash
pythonweb --version
```

## Project Setup

### Creating a New Project

To create a new project, use the `init` command:

```bash
pythonweb init my-project
```

This will create a new directory with the project name and initialize it with the necessary files.

### Using an Existing Project

To use an existing project, navigate to the project directory:

```bash
cd path/to/project
```

Then initialize the PythonWeb Installer:

```bash
pythonweb init --existing
```

### Cloning a Repository

To clone a repository, use the `repo clone` command:

```bash
pythonweb repo clone https://github.com/username/repository.git
```

## Virtual Environment

### Creating a Virtual Environment

Create a virtual environment for your project:

```bash
pythonweb venv create
```

By default, this will create a virtual environment in the `.venv` directory. You can specify a different path:

```bash
pythonweb venv create --path /path/to/venv
```

### Activating the Virtual Environment

Activate the virtual environment:

```bash
pythonweb venv activate
```

### Verifying the Virtual Environment

Verify that the virtual environment is active:

```bash
pythonweb venv status
```

## Dependencies

### Installing Dependencies

Install dependencies from a requirements file:

```bash
pythonweb deps install --requirements requirements.txt
```

### Managing Dependencies

List installed dependencies:

```bash
pythonweb deps list
```

Check for outdated dependencies:

```bash
pythonweb deps outdated
```

Update dependencies:

```bash
pythonweb deps update
```

## Configuration

### Setting Configuration Options

Set configuration options using the `config` command:

```bash
pythonweb config set KEY=VALUE
```

Common configuration options:

```bash
pythonweb config set DEBUG=true
pythonweb config set DATABASE_URL=sqlite:///app.db
pythonweb config set SECRET_KEY=your-secret-key
```

### Environment Variables

Set environment variables:

```bash
pythonweb env set KEY=VALUE
```

Load environment variables from a file:

```bash
pythonweb env load .env
```

## Database Setup

### SQLite (Development)

For development, SQLite is a good choice:

```bash
pythonweb db init --type sqlite --path app.db
```

### PostgreSQL (Production)

For production, PostgreSQL is recommended:

```bash
pythonweb db init --type postgresql --url postgresql://username:password@localhost/dbname
```

### Running Migrations

Run database migrations:

```bash
pythonweb db migrate
```

## Running the Application

### Development Server

Run the application using the development server:

```bash
pythonweb run
```

Specify the host and port:

```bash
pythonweb run --host 0.0.0.0 --port 8000
```

### Production Server

For production, use a WSGI server like Gunicorn:

```bash
pythonweb run --server gunicorn
```

## Testing

### Running Tests

Run tests:

```bash
pythonweb test
```

Run tests with coverage:

```bash
pythonweb test --coverage
```

### Linting

Lint the code:

```bash
pythonweb lint
```

## Troubleshooting

### Common Issues

#### Virtual Environment Issues

If you encounter issues with the virtual environment:

```bash
pythonweb venv recreate
```

#### Dependency Issues

If you encounter issues with dependencies:

```bash
pythonweb deps resolve
```

#### Database Issues

If you encounter issues with the database:

```bash
pythonweb db reset
```

### Logs

View logs:

```bash
pythonweb logs
```

### Debugging

Enable debug mode:

```bash
pythonweb config set DEBUG=true
```

Run the application in debug mode:

```bash
pythonweb run --debug
```

### Getting Help

For more information, use the help command:

```bash
pythonweb --help
```

Or for a specific command:

```bash
pythonweb COMMAND --help
```
