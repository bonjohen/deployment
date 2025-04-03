# Web Server Configuration: User Guide

This guide provides instructions for installing, configuring, and running different web servers for Python web applications using the PythonWeb Installer.

## Table of Contents

- [Installation](#installation)
- [Gunicorn Configuration](#gunicorn-configuration)
- [uWSGI Configuration](#uwsgi-configuration)
- [Nginx Configuration](#nginx-configuration)
- [Apache Configuration](#apache-configuration)
- [WSGI/ASGI Setup](#wsgiasgi-setup)
- [Startup Scripts](#startup-scripts)
- [Common Configurations](#common-configurations)

## Installation

Before configuring a web server, you need to install the required packages:

### Gunicorn

```bash
pip install gunicorn
```

For async workers, you may need additional packages:

```bash
pip install gunicorn[gevent]  # For gevent workers
pip install gunicorn[eventlet]  # For eventlet workers
```

### uWSGI

```bash
pip install uwsgi
```

### Nginx

On Debian/Ubuntu:

```bash
sudo apt-get update
sudo apt-get install nginx
```

On CentOS/RHEL:

```bash
sudo yum install epel-release
sudo yum install nginx
```

On Windows, download and install from the [Nginx website](https://nginx.org/en/download.html).

### Apache

On Debian/Ubuntu:

```bash
sudo apt-get update
sudo apt-get install apache2 apache2-dev
pip install mod_wsgi
```

On CentOS/RHEL:

```bash
sudo yum install httpd httpd-devel
pip install mod_wsgi
```

On Windows, download and install from the [Apache website](https://httpd.apache.org/download.cgi).

## Gunicorn Configuration

Gunicorn is a Python WSGI HTTP server for UNIX. It's simple to set up and works well with most Python web frameworks.

### Basic Configuration

```python
from pythonweb_installer.server import generate_server_configuration

# Generate a basic Gunicorn configuration
success, message, content = generate_server_configuration(
    server_type='gunicorn',
    config_dir='/path/to/config',
    config_data={
        'workers': 4,
        'bind': '0.0.0.0:8000',
        'timeout': 30
    }
)
```

### Configuration Options

- `workers`: Number of worker processes (recommended: 2-4 × CPU cores)
- `worker_class`: Worker type ('sync', 'gevent', 'eventlet', 'tornado', 'gthread')
- `threads`: Number of threads per worker (for gthread worker)
- `bind`: Address to bind to ('hostname:port')
- `timeout`: Worker timeout in seconds
- `max_requests`: Maximum number of requests a worker will process before restarting
- `max_requests_jitter`: Maximum jitter to add to max_requests
- `keepalive`: Seconds to keep idle connections open
- `daemon`: Run in the background as a daemon
- `pidfile`: Path to the PID file
- `accesslog`: Access log file path
- `errorlog`: Error log file path
- `loglevel`: Log level ('debug', 'info', 'warning', 'error', 'critical')

### Example: Production Configuration

```python
config_data = {
    'workers': 8,
    'worker_class': 'gevent',
    'worker_connections': 1000,
    'max_requests': 10000,
    'max_requests_jitter': 1000,
    'timeout': 30,
    'keepalive': 2,
    'bind': '0.0.0.0:8000',
    'daemon': True,
    'pidfile': '/var/run/gunicorn.pid',
    'accesslog': '/var/log/gunicorn/access.log',
    'errorlog': '/var/log/gunicorn/error.log',
    'loglevel': 'info'
}
```

## uWSGI Configuration

uWSGI is a fast, self-healing application container server that supports multiple protocols.

### Basic Configuration

```python
from pythonweb_installer.server import generate_server_configuration

# Generate a basic uWSGI configuration
success, message, content = generate_server_configuration(
    server_type='uwsgi',
    config_dir='/path/to/config',
    config_data={
        'socket': '0.0.0.0:8000',
        'processes': 4,
        'threads': 2,
        'module': 'app:app'
    }
)
```

### Configuration Options

- `socket`: Address to bind to ('hostname:port')
- `processes`: Number of worker processes
- `threads`: Number of threads per worker
- `module`: WSGI module and callable
- `master`: Enable master process
- `vacuum`: Clean up sockets and PID files on exit
- `die-on-term`: Exit on SIGTERM
- `harakiri`: Worker timeout in seconds
- `max-requests`: Maximum number of requests a worker will process before restarting
- `buffer-size`: Buffer size for HTTP headers
- `logto`: Log file path
- `log-format`: Log format string

### Example: Production Configuration

```python
config_data = {
    'socket': '0.0.0.0:8000',
    'processes': 8,
    'threads': 2,
    'master': True,
    'vacuum': True,
    'die-on-term': True,
    'harakiri': 30,
    'max-requests': 10000,
    'buffer-size': 32768,
    'logto': '/var/log/uwsgi/uwsgi.log',
    'log-format': '%(addr) - %(user) [%(ltime)] "%(method) %(uri) %(proto)" %(status) %(size) "%(referer)" "%(uagent)"',
    'module': 'app:app'
}
```

## Nginx Configuration

Nginx is a high-performance HTTP server and reverse proxy that works well with WSGI/ASGI servers.

### Basic Configuration

```python
from pythonweb_installer.server import generate_server_configuration

# Generate a basic Nginx configuration
success, message, content = generate_server_configuration(
    server_type='nginx',
    config_dir='/path/to/config',
    config_data={
        'server_name': 'example.com',
        'proxy_pass': 'http://127.0.0.1:8000',
        'static_dir': '/path/to/static',
        'media_dir': '/path/to/media'
    }
)
```

### Configuration Options

- `server_name`: Server name (domain)
- `proxy_pass`: URL to proxy requests to (WSGI/ASGI server)
- `static_dir`: Directory for static files
- `media_dir`: Directory for media files
- `worker_processes`: Number of worker processes ('auto' or a number)
- `worker_connections`: Maximum number of connections per worker
- `keepalive_timeout`: Keepalive timeout in seconds
- `client_max_body_size`: Maximum client request body size
- `gzip_enabled`: Enable gzip compression
- `ssl_enabled`: Enable SSL/TLS
- `ssl_cert`: SSL certificate path
- `ssl_key`: SSL key path

### Example: Production Configuration with SSL

```python
config_data = {
    'server_name': 'example.com',
    'proxy_pass': 'http://127.0.0.1:8000',
    'static_dir': '/var/www/example.com/static',
    'media_dir': '/var/www/example.com/media',
    'worker_processes': 'auto',
    'worker_connections': 1024,
    'keepalive_timeout': 65,
    'client_max_body_size': '10m',
    'gzip_enabled': True,
    'ssl_enabled': True,
    'ssl_cert': '/etc/letsencrypt/live/example.com/fullchain.pem',
    'ssl_key': '/etc/letsencrypt/live/example.com/privkey.pem'
}
```

## Apache Configuration

Apache is a widely-used web server with extensive features and modules.

### Basic Configuration

```python
from pythonweb_installer.server import generate_server_configuration

# Generate a basic Apache configuration
success, message, content = generate_server_configuration(
    server_type='apache',
    config_dir='/path/to/config',
    config_data={
        'server_name': 'example.com',
        'document_root': '/var/www/example.com',
        'wsgi_script_alias': '/ /var/www/example.com/wsgi.py',
        'static_dir': '/var/www/example.com/static'
    }
)
```

### Configuration Options

- `server_name`: Server name (domain)
- `document_root`: Document root directory
- `wsgi_script_alias`: WSGI script alias mapping
- `static_dir`: Directory for static files
- `server_admin`: Server administrator email
- `error_log`: Error log file path
- `custom_log`: Custom log file path
- `ssl_enabled`: Enable SSL/TLS
- `ssl_certificate_file`: SSL certificate path
- `ssl_certificate_key_file`: SSL key path

### Example: Production Configuration with SSL

```python
config_data = {
    'server_name': 'example.com',
    'document_root': '/var/www/example.com',
    'wsgi_script_alias': '/ /var/www/example.com/wsgi.py',
    'static_dir': '/var/www/example.com/static',
    'server_admin': 'webmaster@example.com',
    'error_log': '/var/log/apache2/example.com_error.log',
    'custom_log': '/var/log/apache2/example.com_access.log combined',
    'ssl_enabled': True,
    'ssl_certificate_file': '/etc/letsencrypt/live/example.com/fullchain.pem',
    'ssl_certificate_key_file': '/etc/letsencrypt/live/example.com/privkey.pem'
}
```

## WSGI/ASGI Setup

The PythonWeb Installer can generate WSGI and ASGI files for your Python web application.

### WSGI File Generation

```python
from pythonweb_installer.server import generate_wsgi_configuration

# Generate a WSGI file
success, message, content = generate_wsgi_configuration(
    app_dir='/path/to/app',
    app_module='app:app',
    output_path='/path/to/app/wsgi.py',
    config_data={
        'static_dir': '/path/to/app/static',
        'static_url': '/static/',
        'debug': False
    }
)
```

### ASGI File Generation

```python
from pythonweb_installer.server import generate_asgi_configuration

# Generate an ASGI file
success, message, content = generate_asgi_configuration(
    app_dir='/path/to/app',
    app_module='app:app',
    output_path='/path/to/app/asgi.py',
    config_data={
        'static_dir': '/path/to/app/static',
        'static_url': '/static/',
        'debug': False
    }
)
```

## Startup Scripts

The PythonWeb Installer can generate startup scripts for your web server.

### Generating a Startup Script

```python
from pythonweb_installer.server import generate_startup_configuration

# Generate a startup script
success, message, content = generate_startup_configuration(
    server_type='gunicorn',
    app_dir='/path/to/app',
    script_dir='/path/to/scripts',
    script_data={
        'workers': 4,
        'bind': '0.0.0.0:8000',
        'app_module': 'app:app',
        'log_dir': '/path/to/logs'
    }
)
```

### Generating a Systemd Service

```python
from pythonweb_installer.server import generate_systemd_configuration

# Generate a systemd service file
success, message, content = generate_systemd_configuration(
    server_type='gunicorn',
    app_dir='/path/to/app',
    script_dir='/path/to/scripts',
    output_dir='/etc/systemd/system',
    script_data={
        'description': 'My Python Web Application',
        'user': 'www-data',
        'group': 'www-data',
        'environment': 'production'
    }
)
```

## Common Configurations

### Django Application

```python
# Gunicorn configuration for Django
gunicorn_config = {
    'workers': 4,
    'worker_class': 'sync',
    'bind': '0.0.0.0:8000',
    'timeout': 30,
    'max_requests': 1000,
    'app_module': 'myproject.wsgi:application'
}

# WSGI configuration for Django
wsgi_config = {
    'app_module': 'myproject.wsgi:application',
    'static_dir': '/path/to/app/static',
    'static_url': '/static/',
    'debug': False
}

# Nginx configuration for Django
nginx_config = {
    'server_name': 'example.com',
    'proxy_pass': 'http://127.0.0.1:8000',
    'static_dir': '/path/to/app/static',
    'media_dir': '/path/to/app/media',
    'static_url': '/static/',
    'media_url': '/media/'
}
```

### Flask Application

```python
# Gunicorn configuration for Flask
gunicorn_config = {
    'workers': 4,
    'worker_class': 'gevent',
    'bind': '0.0.0.0:8000',
    'timeout': 30,
    'max_requests': 1000,
    'app_module': 'app:app'
}

# WSGI configuration for Flask
wsgi_config = {
    'app_module': 'app:app',
    'static_dir': '/path/to/app/static',
    'static_url': '/static/',
    'debug': False
}

# Nginx configuration for Flask
nginx_config = {
    'server_name': 'example.com',
    'proxy_pass': 'http://127.0.0.1:8000',
    'static_dir': '/path/to/app/static',
    'static_url': '/static/'
}
```

### FastAPI Application

```python
# Uvicorn configuration for FastAPI
uvicorn_config = {
    'workers': 4,
    'host': '0.0.0.0',
    'port': 8000,
    'log_level': 'info',
    'app_module': 'app:app'
}

# ASGI configuration for FastAPI
asgi_config = {
    'app_module': 'app:app',
    'static_dir': '/path/to/app/static',
    'static_url': '/static/',
    'debug': False
}

# Nginx configuration for FastAPI
nginx_config = {
    'server_name': 'example.com',
    'proxy_pass': 'http://127.0.0.1:8000',
    'static_dir': '/path/to/app/static',
    'static_url': '/static/'
}
```
