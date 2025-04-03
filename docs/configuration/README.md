# Configuration Guide

This guide provides detailed information about configuring the PythonWeb Installer.

## Table of Contents

- [Configuration File](#configuration-file)
- [Environment Variables](#environment-variables)
- [Command-Line Options](#command-line-options)
- [Configuration Options](#configuration-options)
- [Configuration Profiles](#configuration-profiles)
- [Validation](#validation)
- [Best Practices](#best-practices)

## Configuration File

The PythonWeb Installer uses a YAML configuration file named `pythonweb.yaml` in the project root directory. You can create or modify this file manually, or use the `config` command.

### Default Location

By default, the PythonWeb Installer looks for the configuration file in the following locations, in order:

1. The path specified by the `--config` command-line option
2. `./pythonweb.yaml` (current directory)
3. `~/.pythonweb/config.yaml` (user's home directory)
4. `/etc/pythonweb/config.yaml` (system-wide configuration)

### Creating a Configuration File

You can create a new configuration file using the `config init` command:

```bash
pythonweb config init
```

This will create a new configuration file with default values.

### Example Configuration File

```yaml
# PythonWeb Installer Configuration

# Application settings
app:
  name: my-app
  version: 0.1.0
  description: My Python Web Application

# Python settings
python:
  version: 3.9
  packages:
    - flask
    - sqlalchemy
    - gunicorn

# Virtual environment settings
venv:
  path: .venv
  system_site_packages: false

# Repository settings
repository:
  url: https://github.com/username/repository.git
  branch: main

# Database settings
database:
  type: sqlite
  path: app.db

# Server settings
server:
  host: 127.0.0.1
  port: 5000
  workers: 4

# Deployment settings
deployment:
  environment: production
  strategy: git-push

# Logging settings
logging:
  level: INFO
  file: logs/app.log
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
```

## Environment Variables

You can also configure the PythonWeb Installer using environment variables. All environment variables should be prefixed with `PYTHONWEB_`.

### Environment Variable Naming

Environment variables are named using the following convention:

- All uppercase
- Words separated by underscores
- Nested configuration options separated by double underscores

For example, the configuration option `app.name` would be set using the environment variable `PYTHONWEB_APP__NAME`.

### Setting Environment Variables

You can set environment variables in your shell:

```bash
export PYTHONWEB_APP__NAME=my-app
export PYTHONWEB_PYTHON__VERSION=3.9
export PYTHONWEB_SERVER__PORT=8000
```

Or you can use the `env` command:

```bash
pythonweb env set APP__NAME=my-app
pythonweb env set PYTHON__VERSION=3.9
pythonweb env set SERVER__PORT=8000
```

### Environment Variable Precedence

Environment variables take precedence over values in the configuration file. This allows you to override configuration options without modifying the configuration file.

## Command-Line Options

You can also configure the PythonWeb Installer using command-line options. Command-line options take precedence over environment variables and configuration file values.

### Global Options

These options can be used with any command:

| Option | Description |
|--------|-------------|
| `--config FILE` | Specify config file |
| `--verbose` | Increase verbosity |
| `--quiet` | Suppress output |
| `--no-color` | Disable colored output |

### Command-Specific Options

Each command has its own set of options. You can see the available options for a command using the `--help` option:

```bash
pythonweb COMMAND --help
```

## Configuration Options

The following table lists all available configuration options:

| Option | Description | Default | Environment Variable |
|--------|-------------|---------|---------------------|
| `app.name` | Name of the application | `pythonweb-app` | `PYTHONWEB_APP__NAME` |
| `app.version` | Version of the application | `0.1.0` | `PYTHONWEB_APP__VERSION` |
| `app.description` | Description of the application | `A Python web application` | `PYTHONWEB_APP__DESCRIPTION` |
| `python.version` | Python version to use | `3.9` | `PYTHONWEB_PYTHON__VERSION` |
| `python.packages` | List of Python packages to install | `[]` | `PYTHONWEB_PYTHON__PACKAGES` |
| `venv.path` | Path to the virtual environment | `.venv` | `PYTHONWEB_VENV__PATH` |
| `venv.system_site_packages` | Give access to system site-packages | `false` | `PYTHONWEB_VENV__SYSTEM_SITE_PACKAGES` |
| `repository.url` | URL of the Git repository | `None` | `PYTHONWEB_REPOSITORY__URL` |
| `repository.branch` | Branch to use | `main` | `PYTHONWEB_REPOSITORY__BRANCH` |
| `database.type` | Type of database to use | `sqlite` | `PYTHONWEB_DATABASE__TYPE` |
| `database.path` | Path to the database file (SQLite only) | `app.db` | `PYTHONWEB_DATABASE__PATH` |
| `database.url` | URL of the database | `None` | `PYTHONWEB_DATABASE__URL` |
| `server.host` | Host to bind to | `127.0.0.1` | `PYTHONWEB_SERVER__HOST` |
| `server.port` | Port to bind to | `5000` | `PYTHONWEB_SERVER__PORT` |
| `server.workers` | Number of worker processes | `4` | `PYTHONWEB_SERVER__WORKERS` |
| `deployment.environment` | Deployment environment | `production` | `PYTHONWEB_DEPLOYMENT__ENVIRONMENT` |
| `deployment.strategy` | Deployment strategy | `git-push` | `PYTHONWEB_DEPLOYMENT__STRATEGY` |
| `logging.level` | Logging level | `INFO` | `PYTHONWEB_LOGGING__LEVEL` |
| `logging.file` | Path to the log file | `logs/app.log` | `PYTHONWEB_LOGGING__FILE` |
| `logging.format` | Log message format | `%(asctime)s - %(name)s - %(levelname)s - %(message)s` | `PYTHONWEB_LOGGING__FORMAT` |

## Configuration Profiles

The PythonWeb Installer supports configuration profiles, which allow you to have different configurations for different environments.

### Creating a Profile

You can create a new profile using the `config profile create` command:

```bash
pythonweb config profile create development
```

This will create a new profile named `development` with default values.

### Switching Profiles

You can switch between profiles using the `config profile use` command:

```bash
pythonweb config profile use development
```

### Profile-Specific Configuration

You can set profile-specific configuration options:

```bash
pythonweb config set --profile development SERVER__PORT=8000
```

### Example Configuration File with Profiles

```yaml
# Default profile
app:
  name: my-app
  version: 0.1.0

# Development profile
profiles:
  development:
    server:
      host: 127.0.0.1
      port: 8000
    logging:
      level: DEBUG

  # Production profile
  production:
    server:
      host: 0.0.0.0
      port: 5000
    logging:
      level: WARNING
```

## Validation

The PythonWeb Installer validates the configuration to ensure it is valid.

### Validating the Configuration

You can validate the configuration using the `config validate` command:

```bash
pythonweb config validate
```

This will check the configuration for errors and warnings.

### Common Validation Errors

- **Missing required options**: Some options are required and must be set
- **Invalid values**: Some options have specific value constraints
- **Type errors**: Some options must be of a specific type (string, number, boolean, etc.)
- **Dependency errors**: Some options depend on other options being set

## Best Practices

Here are some best practices for configuring the PythonWeb Installer:

1. **Use version control**: Keep your configuration file in version control
2. **Use profiles**: Use different profiles for different environments
3. **Use environment variables for sensitive information**: Don't store sensitive information in the configuration file
4. **Document your configuration**: Add comments to your configuration file to explain non-obvious settings
5. **Validate your configuration**: Regularly validate your configuration to catch errors early
6. **Keep it simple**: Only set the options you need to change from the defaults
7. **Use the `config` command**: Use the `config` command to modify the configuration file instead of editing it manually
