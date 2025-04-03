# Command Reference

This document provides a comprehensive reference for all commands available in the PythonWeb Installer.

## Table of Contents

- [Global Options](#global-options)
- [Main Commands](#main-commands)
  - [init](#init)
  - [venv](#venv)
  - [deps](#deps)
  - [repo](#repo)
  - [config](#config)
  - [env](#env)
  - [db](#db)
  - [run](#run)
  - [deploy](#deploy)
  - [test](#test)
  - [lint](#lint)
  - [logs](#logs)

## Global Options

These options can be used with any command:

| Option | Description |
|--------|-------------|
| `--help`, `-h` | Show help message and exit |
| `--version`, `-v` | Show version and exit |
| `--quiet`, `-q` | Suppress output |
| `--verbose` | Increase verbosity |
| `--config FILE` | Specify config file |
| `--no-color` | Disable colored output |

## Main Commands

### init

Initialize a new project or an existing project.

```bash
pythonweb init [PROJECT_NAME] [OPTIONS]
```

#### Options

| Option | Description | Default |
|--------|-------------|---------|
| `--existing` | Initialize an existing project | `False` |
| `--template TEMPLATE` | Template to use | `basic` |
| `--python-version VERSION` | Python version to use | `3.9` |
| `--git` | Initialize Git repository | `True` |

#### Examples

```bash
# Initialize a new project
pythonweb init my-project

# Initialize an existing project
pythonweb init --existing

# Initialize a new project with a specific template
pythonweb init my-project --template flask
```

### venv

Manage virtual environments.

```bash
pythonweb venv COMMAND [OPTIONS]
```

#### Subcommands

| Command | Description |
|---------|-------------|
| `create` | Create a new virtual environment |
| `activate` | Activate the virtual environment |
| `deactivate` | Deactivate the virtual environment |
| `status` | Show the status of the virtual environment |
| `recreate` | Recreate the virtual environment |
| `exec` | Execute a command in the virtual environment |

#### Options for `create`

| Option | Description | Default |
|--------|-------------|---------|
| `--path PATH` | Path to the virtual environment | `.venv` |
| `--python PYTHON` | Python executable to use | `python3` |
| `--system-site-packages` | Give access to system site-packages | `False` |

#### Examples

```bash
# Create a virtual environment
pythonweb venv create

# Create a virtual environment with a specific path
pythonweb venv create --path /path/to/venv

# Execute a command in the virtual environment
pythonweb venv exec pip install flask
```

### deps

Manage dependencies.

```bash
pythonweb deps COMMAND [OPTIONS]
```

#### Subcommands

| Command | Description |
|---------|-------------|
| `install` | Install dependencies |
| `update` | Update dependencies |
| `list` | List installed dependencies |
| `outdated` | List outdated dependencies |
| `resolve` | Resolve dependency conflicts |
| `generate` | Generate requirements file |

#### Options for `install`

| Option | Description | Default |
|--------|-------------|---------|
| `--requirements FILE` | Requirements file | `requirements.txt` |
| `--upgrade` | Upgrade dependencies | `False` |
| `--no-deps` | Don't install dependencies | `False` |
| `--index-url URL` | Base URL of Python Package Index | `https://pypi.org/simple` |

#### Examples

```bash
# Install dependencies
pythonweb deps install

# Install dependencies from a specific file
pythonweb deps install --requirements requirements-dev.txt

# Update dependencies
pythonweb deps update

# List installed dependencies
pythonweb deps list
```

### repo

Manage repositories.

```bash
pythonweb repo COMMAND [OPTIONS]
```

#### Subcommands

| Command | Description |
|---------|-------------|
| `clone` | Clone a repository |
| `status` | Show repository status |
| `pull` | Pull changes from remote |
| `push` | Push changes to remote |
| `checkout` | Checkout a branch |

#### Options for `clone`

| Option | Description | Default |
|--------|-------------|---------|
| `--branch BRANCH` | Branch to checkout | `main` |
| `--path PATH` | Path to clone to | `.` |
| `--depth DEPTH` | Create a shallow clone | `None` |

#### Examples

```bash
# Clone a repository
pythonweb repo clone https://github.com/username/repository.git

# Clone a repository with a specific branch
pythonweb repo clone https://github.com/username/repository.git --branch develop

# Show repository status
pythonweb repo status
```

### config

Manage configuration.

```bash
pythonweb config COMMAND [OPTIONS]
```

#### Subcommands

| Command | Description |
|---------|-------------|
| `set` | Set a configuration option |
| `get` | Get a configuration option |
| `list` | List all configuration options |
| `reset` | Reset configuration to defaults |

#### Examples

```bash
# Set a configuration option
pythonweb config set DEBUG=true

# Get a configuration option
pythonweb config get DEBUG

# List all configuration options
pythonweb config list
```

### env

Manage environment variables.

```bash
pythonweb env COMMAND [OPTIONS]
```

#### Subcommands

| Command | Description |
|---------|-------------|
| `set` | Set an environment variable |
| `get` | Get an environment variable |
| `list` | List all environment variables |
| `load` | Load environment variables from a file |
| `save` | Save environment variables to a file |

#### Examples

```bash
# Set an environment variable
pythonweb env set DEBUG=true

# Get an environment variable
pythonweb env get DEBUG

# Load environment variables from a file
pythonweb env load .env
```

### db

Manage databases.

```bash
pythonweb db COMMAND [OPTIONS]
```

#### Subcommands

| Command | Description |
|---------|-------------|
| `init` | Initialize the database |
| `migrate` | Run database migrations |
| `upgrade` | Upgrade the database |
| `downgrade` | Downgrade the database |
| `reset` | Reset the database |
| `backup` | Backup the database |
| `restore` | Restore the database |

#### Options for `init`

| Option | Description | Default |
|--------|-------------|---------|
| `--type TYPE` | Database type | `sqlite` |
| `--path PATH` | Database path | `app.db` |
| `--url URL` | Database URL | `None` |

#### Examples

```bash
# Initialize the database
pythonweb db init

# Run database migrations
pythonweb db migrate

# Backup the database
pythonweb db backup --output backup.sql
```

### run

Run the application.

```bash
pythonweb run [OPTIONS]
```

#### Options

| Option | Description | Default |
|--------|-------------|---------|
| `--host HOST` | Host to bind to | `127.0.0.1` |
| `--port PORT` | Port to bind to | `5000` |
| `--server SERVER` | Server to use | `werkzeug` |
| `--debug` | Enable debug mode | `False` |
| `--reload` | Enable auto-reload | `False` |

#### Examples

```bash
# Run the application
pythonweb run

# Run the application with a specific host and port
pythonweb run --host 0.0.0.0 --port 8000

# Run the application with Gunicorn
pythonweb run --server gunicorn
```

### deploy

Deploy the application.

```bash
pythonweb deploy [OPTIONS]
```

#### Options

| Option | Description | Default |
|--------|-------------|---------|
| `--environment ENV` | Environment to deploy to | `production` |
| `--config FILE` | Configuration file | `deploy.yaml` |
| `--dry-run` | Perform a dry run | `False` |
| `--force` | Force deployment | `False` |

#### Examples

```bash
# Deploy the application
pythonweb deploy

# Deploy to a specific environment
pythonweb deploy --environment staging

# Perform a dry run
pythonweb deploy --dry-run
```

### test

Run tests.

```bash
pythonweb test [OPTIONS]
```

#### Options

| Option | Description | Default |
|--------|-------------|---------|
| `--path PATH` | Path to test files | `tests` |
| `--coverage` | Enable coverage | `False` |
| `--verbose` | Enable verbose output | `False` |
| `--junit-xml FILE` | Generate JUnit XML report | `None` |

#### Examples

```bash
# Run tests
pythonweb test

# Run tests with coverage
pythonweb test --coverage

# Run tests with verbose output
pythonweb test --verbose
```

### lint

Lint the code.

```bash
pythonweb lint [OPTIONS]
```

#### Options

| Option | Description | Default |
|--------|-------------|---------|
| `--path PATH` | Path to lint | `.` |
| `--fix` | Fix issues | `False` |
| `--format FORMAT` | Output format | `text` |
| `--ignore PATTERN` | Ignore pattern | `None` |

#### Examples

```bash
# Lint the code
pythonweb lint

# Lint a specific path
pythonweb lint --path src

# Lint and fix issues
pythonweb lint --fix
```

### logs

View logs.

```bash
pythonweb logs [OPTIONS]
```

#### Options

| Option | Description | Default |
|--------|-------------|---------|
| `--follow`, `-f` | Follow log output | `False` |
| `--lines LINES`, `-n LINES` | Number of lines to show | `10` |
| `--level LEVEL` | Minimum log level | `INFO` |
| `--output FILE` | Output file | `None` |

#### Examples

```bash
# View logs
pythonweb logs

# Follow logs
pythonweb logs --follow

# View the last 100 lines
pythonweb logs --lines 100

# View only error logs
pythonweb logs --level ERROR
```
