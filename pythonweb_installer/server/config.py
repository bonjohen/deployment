"""
Web server configuration functionality.
"""
import os
import re
import logging
import shutil
import tempfile
from typing import Dict, Any, List, Tuple, Optional, Union

from pythonweb_installer.utils.templates import render_template

logger = logging.getLogger(__name__)


class ServerConfig:
    """
    Web server configuration.
    """

    def __init__(self, server_type: str, config_dir: str):
        """
        Initialize the server configuration.

        Args:
            server_type: Server type (gunicorn, uwsgi, nginx, apache)
            config_dir: Configuration directory
        """
        self.server_type = server_type.lower()
        self.config_dir = config_dir
        self.config_file = None
        self.config_template = None
        self.config_data = {}

        # Set default configuration values
        self._set_defaults()

    def _set_defaults(self) -> None:
        """
        Set default configuration values.
        """
        # Common defaults
        self.config_data = {
            'host': '0.0.0.0',
            'port': 8000,
            'workers': 4,
            'threads': 2,
            'timeout': 30,
            'max_requests': 1000,
            'app_module': 'app:app',
            'static_dir': 'static',
            'log_dir': 'logs',
            'log_level': 'info',
            'server_name': 'localhost',
            'ssl_enabled': False,
            'ssl_cert': None,
            'ssl_key': None,
            'cors_enabled': False,
            'cors_origins': '*',
            'cors_methods': 'GET,POST,PUT,DELETE,OPTIONS',
            'cors_headers': 'Content-Type,Authorization',
            'security_headers': True,
            'gzip_enabled': True,
            'cache_enabled': False,
            'cache_dir': 'cache',
            'cache_time': 3600,
            'debug': False
        }

        # Server-specific defaults
        if self.server_type == 'gunicorn':
            self.config_file = 'gunicorn.conf.py'
            self.config_template = 'gunicorn.conf.py.j2'
            self.config_data.update({
                'worker_class': 'sync',
                'preload_app': True,
                'daemon': False,
                'accesslog': 'logs/access.log',
                'errorlog': 'logs/error.log',
                'loglevel': 'info',
                'proc_name': 'gunicorn'
            })

        elif self.server_type == 'uwsgi':
            self.config_file = 'uwsgi.ini'
            self.config_template = 'uwsgi.ini.j2'
            self.config_data.update({
                'processes': 4,
                'threads': 2,
                'master': True,
                'vacuum': True,
                'die-on-term': True,
                'harakiri': 30,
                'max-requests': 1000,
                'buffer-size': 32768,
                'logto': 'logs/uwsgi.log',
                'log-format': '%(addr) - %(user) [%(ltime)] "%(method) %(uri) %(proto)" %(status) %(size) "%(referer)" "%(uagent)"'
            })

        elif self.server_type == 'nginx':
            self.config_file = 'nginx.conf'
            self.config_template = 'nginx.conf.j2'
            self.config_data.update({
                'worker_processes': 'auto',
                'worker_connections': 1024,
                'keepalive_timeout': 65,
                'sendfile': 'on',
                'tcp_nopush': 'on',
                'tcp_nodelay': 'on',
                'types_hash_max_size': 2048,
                'server_tokens': 'off',
                'client_max_body_size': '10M',
                'gzip': 'on',
                'gzip_types': 'text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript',
                'proxy_pass': 'http://127.0.0.1:8000',
                'proxy_set_header': {
                    'Host': '$host',
                    'X-Real-IP': '$remote_addr',
                    'X-Forwarded-For': '$proxy_add_x_forwarded_for',
                    'X-Forwarded-Proto': '$scheme'
                }
            })

        elif self.server_type == 'apache':
            self.config_file = 'apache.conf'
            self.config_template = 'apache.conf.j2'
            self.config_data.update({
                'server_admin': 'webmaster@localhost',
                'document_root': '/var/www/html',
                'error_log': '${APACHE_LOG_DIR}/error.log',
                'custom_log': '${APACHE_LOG_DIR}/access.log combined',
                'wsgi_daemon_process': 'pythonweb processes=4 threads=2 display-name=%{GROUP}',
                'wsgi_process_group': 'pythonweb',
                'wsgi_script_alias': '/ /var/www/app/wsgi.py',
                'alias': {
                    '/static/': '/var/www/app/static/'
                },
                'directory': {
                    '/var/www/app': {
                        'require': 'all granted'
                    },
                    '/var/www/app/static': {
                        'require': 'all granted'
                    }
                }
            })

        else:
            raise ValueError(f"Unsupported server type: {self.server_type}")

    def set_config(self, key: str, value: Any) -> None:
        """
        Set a configuration value.

        Args:
            key: Configuration key
            value: Configuration value
        """
        self.config_data[key] = value

    def get_config(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value.

        Args:
            key: Configuration key
            default: Default value

        Returns:
            Any: Configuration value
        """
        return self.config_data.get(key, default)

    def update_config(self, config_data: Dict[str, Any]) -> None:
        """
        Update configuration values.

        Args:
            config_data: Configuration data
        """
        self.config_data.update(config_data)

    def generate_config(self) -> Tuple[bool, str, Optional[str]]:
        """
        Generate the server configuration.

        Returns:
            Tuple[bool, str, Optional[str]]: Success status, message, and configuration content
        """
        try:
            # Create the configuration directory if it doesn't exist
            os.makedirs(self.config_dir, exist_ok=True)

            # Generate the configuration file path
            config_path = os.path.join(self.config_dir, self.config_file)

            # Render the configuration template
            config_content = render_template(
                self.config_template,
                self.config_data
            )

            # Write the configuration file
            with open(config_path, 'w') as f:
                f.write(config_content)

            logger.info(f"Generated {self.server_type} configuration: {config_path}")
            return True, f"Generated {self.server_type} configuration: {config_path}", config_content

        except Exception as e:
            logger.error(f"Failed to generate {self.server_type} configuration: {str(e)}")
            return False, f"Failed to generate {self.server_type} configuration: {str(e)}", None

    def validate_config(self) -> Tuple[bool, List[str]]:
        """
        Validate the server configuration.

        Returns:
            Tuple[bool, List[str]]: Validation status and list of errors
        """
        errors = []

        try:
            # Validate common configuration
            if not isinstance(self.config_data.get('port'), int):
                errors.append("Port must be an integer")

            if not isinstance(self.config_data.get('workers'), int):
                errors.append("Workers must be an integer")

            if not isinstance(self.config_data.get('threads'), int):
                errors.append("Threads must be an integer")

            if not isinstance(self.config_data.get('timeout'), int):
                errors.append("Timeout must be an integer")

            # Validate SSL configuration
            if self.config_data.get('ssl_enabled'):
                if not self.config_data.get('ssl_cert'):
                    errors.append("SSL certificate path is required when SSL is enabled")

                if not self.config_data.get('ssl_key'):
                    errors.append("SSL key path is required when SSL is enabled")

            # Validate server-specific configuration
            if self.server_type == 'gunicorn':
                if not self.config_data.get('app_module'):
                    errors.append("Application module is required for Gunicorn")

                if self.config_data.get('worker_class') not in ['sync', 'eventlet', 'gevent', 'tornado', 'gthread']:
                    errors.append("Invalid worker class for Gunicorn")

            elif self.server_type == 'uwsgi':
                if not self.config_data.get('app_module'):
                    errors.append("Application module is required for uWSGI")

            elif self.server_type == 'nginx':
                if not self.config_data.get('proxy_pass'):
                    errors.append("Proxy pass URL is required for Nginx")

            elif self.server_type == 'apache':
                if not self.config_data.get('wsgi_script_alias'):
                    errors.append("WSGI script alias is required for Apache")

            return len(errors) == 0, errors

        except Exception as e:
            errors.append(f"Failed to validate configuration: {str(e)}")
            return False, errors

    def test_config(self) -> Tuple[bool, str]:
        """
        Test the server configuration.

        Returns:
            Tuple[bool, str]: Success status and message
        """
        try:
            # Create a temporary directory
            temp_dir = tempfile.mkdtemp()

            try:
                # Generate a temporary configuration file
                temp_config_path = os.path.join(temp_dir, self.config_file)

                # Render the configuration template
                config_content = render_template(
                    self.config_template,
                    self.config_data
                )

                # Write the configuration file
                with open(temp_config_path, 'w') as f:
                    f.write(config_content)

                # Test the configuration based on the server type
                if self.server_type == 'gunicorn':
                    # For testing purposes, we'll just check if the content contains required attributes
                    required_attrs = ['bind', 'workers', 'worker_class', 'timeout']

                    for attr in required_attrs:
                        if attr not in config_content:
                            return False, f"Missing required attribute in Gunicorn configuration: {attr}"

                    return True, "Gunicorn configuration is valid"

                elif self.server_type == 'uwsgi':
                    # For testing purposes, we'll just check if the content contains required sections and options
                    if '[uwsgi]' not in config_content:
                        return False, "Missing required section in uWSGI configuration: uwsgi"

                    # Check if the content has the required options
                    required_options = ['socket', 'processes', 'threads', 'module']

                    for option in required_options:
                        if option not in config_content:
                            return False, f"Missing required option in uWSGI configuration: {option}"

                    return True, "uWSGI configuration is valid"

                elif self.server_type == 'nginx':
                    # Check if the configuration has the required directives
                    required_directives = ['server {', 'listen', 'server_name', 'location']

                    for directive in required_directives:
                        if directive not in config_content:
                            return False, f"Missing required directive in Nginx configuration: {directive}"

                    return True, "Nginx configuration is valid"

                elif self.server_type == 'apache':
                    # Check if the configuration has the required directives
                    required_directives = ['<VirtualHost', 'ServerName', 'DocumentRoot', 'WSGIScriptAlias']

                    for directive in required_directives:
                        if directive not in config_content:
                            return False, f"Missing required directive in Apache configuration: {directive}"

                    return True, "Apache configuration is valid"

                else:
                    return False, f"Unsupported server type: {self.server_type}"

            finally:
                # Clean up the temporary directory
                shutil.rmtree(temp_dir)

        except Exception as e:
            logger.error(f"Failed to test {self.server_type} configuration: {str(e)}")
            return False, f"Failed to test {self.server_type} configuration: {str(e)}"


def create_server_config(server_type: str, config_dir: str) -> ServerConfig:
    """
    Create a server configuration.

    Args:
        server_type: Server type (gunicorn, uwsgi, nginx, apache)
        config_dir: Configuration directory

    Returns:
        ServerConfig: Server configuration
    """
    return ServerConfig(server_type, config_dir)


def generate_server_config(server_type: str, config_dir: str,
                          config_data: Optional[Dict[str, Any]] = None) -> Tuple[bool, str, Optional[str]]:
    """
    Generate a server configuration.

    Args:
        server_type: Server type (gunicorn, uwsgi, nginx, apache)
        config_dir: Configuration directory
        config_data: Configuration data

    Returns:
        Tuple[bool, str, Optional[str]]: Success status, message, and configuration content
    """
    try:
        # Create a server configuration
        server_config = create_server_config(server_type, config_dir)

        # Update the configuration data
        if config_data:
            server_config.update_config(config_data)

        # Generate the configuration
        return server_config.generate_config()

    except Exception as e:
        logger.error(f"Failed to generate {server_type} configuration: {str(e)}")
        return False, f"Failed to generate {server_type} configuration: {str(e)}", None


def validate_server_config(server_type: str, config_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate a server configuration.

    Args:
        server_type: Server type (gunicorn, uwsgi, nginx, apache)
        config_data: Configuration data

    Returns:
        Tuple[bool, List[str]]: Validation status and list of errors
    """
    try:
        # Create a server configuration
        server_config = create_server_config(server_type, '')

        # Update the configuration data
        server_config.update_config(config_data)

        # Validate the configuration
        return server_config.validate_config()

    except Exception as e:
        logger.error(f"Failed to validate {server_type} configuration: {str(e)}")
        return False, [f"Failed to validate {server_type} configuration: {str(e)}"]
