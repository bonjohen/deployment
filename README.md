# PythonWeb Installer

An automated deployment tool for the PythonWeb template application.

## Overview

The PythonWeb Installer automates the process of deploying the PythonWeb template application to various environments, from local development to production servers with custom domains.

## Features

- One-command deployment to development or production environments
- Automated database setup and migration
- Web server and domain configuration
- SSL/TLS setup with Let's Encrypt
- Backup and recovery management
- User-friendly installation wizard

## Getting Started

### Prerequisites

- Python 3.7 or higher
- pip (Python package installer)
- Git

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/deployment.git
cd deployment

# Install the installer
pip install -e .
```

### Basic Usage

```bash
# Start the installation wizard
pythonweb-install

# Or use command-line options for automated deployment
pythonweb-install --mode=production --domain=yourdomain.com --admin-email=admin@example.com
```

## Documentation

For detailed documentation, see the [docs](docs/) directory.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

