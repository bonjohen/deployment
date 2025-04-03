"""
Unit tests for server configuration functionality.
"""
import os
import tempfile
from unittest.mock import patch, MagicMock

import pytest

from pythonweb_installer.server.config import (
    ServerConfig,
    create_server_config,
    generate_server_config,
    validate_server_config
)


class TestServerConfig:
    """Tests for server configuration functionality."""

    @pytest.fixture
    def temp_config_dir(self):
        """Create a temporary configuration directory."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir

        # Clean up
        import shutil
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def server_config_gunicorn(self, temp_config_dir):
        """Create a Gunicorn server configuration."""
        return ServerConfig('gunicorn', temp_config_dir)

    @pytest.fixture
    def server_config_uwsgi(self, temp_config_dir):
        """Create a uWSGI server configuration."""
        return ServerConfig('uwsgi', temp_config_dir)

    @pytest.fixture
    def server_config_nginx(self, temp_config_dir):
        """Create a Nginx server configuration."""
        return ServerConfig('nginx', temp_config_dir)

    @pytest.fixture
    def server_config_apache(self, temp_config_dir):
        """Create an Apache server configuration."""
        return ServerConfig('apache', temp_config_dir)

    def test_create_server_config(self, temp_config_dir):
        """Test creating a server configuration."""
        # Create a server configuration
        server_config = create_server_config('gunicorn', temp_config_dir)

        assert server_config is not None
        assert isinstance(server_config, ServerConfig)
        assert server_config.server_type == 'gunicorn'
        assert server_config.config_dir == temp_config_dir

    def test_create_server_config_invalid_type(self, temp_config_dir):
        """Test creating a server configuration with an invalid type."""
        # Create a server configuration with an invalid type
        with pytest.raises(ValueError):
            create_server_config('invalid', temp_config_dir)

    def test_set_config(self, server_config_gunicorn):
        """Test setting a configuration value."""
        # Set a configuration value
        server_config_gunicorn.set_config('workers', 8)

        assert server_config_gunicorn.get_config('workers') == 8

    def test_get_config(self, server_config_gunicorn):
        """Test getting a configuration value."""
        # Get a configuration value
        workers = server_config_gunicorn.get_config('workers')

        assert workers is not None
        assert isinstance(workers, int)

    def test_get_config_default(self, server_config_gunicorn):
        """Test getting a configuration value with a default."""
        # Get a configuration value with a default
        value = server_config_gunicorn.get_config('nonexistent', 'default')

        assert value == 'default'

    def test_update_config(self, server_config_gunicorn):
        """Test updating configuration values."""
        # Update configuration values
        server_config_gunicorn.update_config({
            'workers': 8,
            'threads': 4,
            'timeout': 60
        })

        assert server_config_gunicorn.get_config('workers') == 8
        assert server_config_gunicorn.get_config('threads') == 4
        assert server_config_gunicorn.get_config('timeout') == 60

    @patch('pythonweb_installer.server.config.render_template')
    def test_generate_config(self, mock_render_template, server_config_gunicorn, temp_config_dir):
        """Test generating a server configuration."""
        # Mock the render_template function
        mock_render_template.return_value = 'rendered template'

        # Generate the configuration
        success, message, content = server_config_gunicorn.generate_config()

        assert success is True
        assert 'Generated gunicorn configuration' in message
        assert content == 'rendered template'

        # Check if the configuration file was created
        config_path = os.path.join(temp_config_dir, server_config_gunicorn.config_file)
        assert os.path.exists(config_path)

        # Check if the render_template function was called
        mock_render_template.assert_called_once_with(
            server_config_gunicorn.config_template,
            server_config_gunicorn.config_data
        )

    @patch('pythonweb_installer.server.config.render_template')
    def test_generate_config_error(self, mock_render_template, server_config_gunicorn):
        """Test generating a server configuration with an error."""
        # Mock the render_template function to raise an exception
        mock_render_template.side_effect = Exception('Test error')

        # Generate the configuration
        success, message, content = server_config_gunicorn.generate_config()

        assert success is False
        assert 'Failed to generate gunicorn configuration' in message
        assert content is None

    def test_validate_config_valid(self, server_config_gunicorn):
        """Test validating a valid server configuration."""
        # Validate the configuration
        valid, errors = server_config_gunicorn.validate_config()

        assert valid is True
        assert len(errors) == 0

    def test_validate_config_invalid(self, server_config_gunicorn):
        """Test validating an invalid server configuration."""
        # Set invalid configuration values
        server_config_gunicorn.set_config('port', 'invalid')
        server_config_gunicorn.set_config('workers', 'invalid')

        # Validate the configuration
        valid, errors = server_config_gunicorn.validate_config()

        assert valid is False
        assert len(errors) > 0
        assert any('Port must be an integer' in error for error in errors)
        assert any('Workers must be an integer' in error for error in errors)

    def test_validate_config_ssl_enabled_no_cert(self, server_config_gunicorn):
        """Test validating a server configuration with SSL enabled but no certificate."""
        # Set SSL enabled but no certificate
        server_config_gunicorn.set_config('ssl_enabled', True)

        # Validate the configuration
        valid, errors = server_config_gunicorn.validate_config()

        assert valid is False
        assert len(errors) > 0
        assert any('SSL certificate path is required' in error for error in errors)

    def test_validate_config_ssl_enabled_no_key(self, server_config_gunicorn):
        """Test validating a server configuration with SSL enabled but no key."""
        # Set SSL enabled and certificate but no key
        server_config_gunicorn.set_config('ssl_enabled', True)
        server_config_gunicorn.set_config('ssl_cert', 'cert.pem')

        # Validate the configuration
        valid, errors = server_config_gunicorn.validate_config()

        assert valid is False
        assert len(errors) > 0
        assert any('SSL key path is required' in error for error in errors)

    @patch('pythonweb_installer.server.config.render_template')
    def test_test_config_gunicorn(self, mock_render_template, server_config_gunicorn):
        """Test testing a Gunicorn server configuration."""
        # Mock the render_template function
        mock_render_template.return_value = """
bind = '0.0.0.0:8000'
workers = 4
worker_class = 'sync'
timeout = 30
"""

        # Test the configuration
        success, message = server_config_gunicorn.test_config()

        assert success is True
        assert 'Gunicorn configuration is valid' in message

    @patch('pythonweb_installer.server.config.render_template')
    def test_test_config_gunicorn_invalid(self, mock_render_template, server_config_gunicorn):
        """Test testing an invalid Gunicorn server configuration."""
        # Mock the render_template function
        mock_render_template.return_value = """
# Missing required attributes
"""

        # Test the configuration
        success, message = server_config_gunicorn.test_config()

        assert success is False
        assert 'Missing required attribute' in message

    @patch('pythonweb_installer.server.config.render_template')
    def test_test_config_uwsgi(self, mock_render_template, server_config_uwsgi):
        """Test testing a uWSGI server configuration."""
        # Mock the render_template function
        mock_render_template.return_value = """
[uwsgi]
socket = 0.0.0.0:8000
processes = 4
threads = 2
module = app:app
"""

        # Test the configuration
        success, message = server_config_uwsgi.test_config()

        assert success is True
        assert 'uWSGI configuration is valid' in message

    @patch('pythonweb_installer.server.config.render_template')
    def test_test_config_uwsgi_invalid(self, mock_render_template, server_config_uwsgi):
        """Test testing an invalid uWSGI server configuration."""
        # Mock the render_template function
        mock_render_template.return_value = """
[invalid]
# Missing required section
"""

        # Test the configuration
        success, message = server_config_uwsgi.test_config()

        assert success is False
        assert 'Missing required section' in message

    @patch('pythonweb_installer.server.config.render_template')
    def test_test_config_nginx(self, mock_render_template, server_config_nginx):
        """Test testing a Nginx server configuration."""
        # Mock the render_template function
        mock_render_template.return_value = """
server {
    listen 80;
    server_name localhost;
    location / {
        proxy_pass http://127.0.0.1:8000;
    }
}
"""

        # Test the configuration
        success, message = server_config_nginx.test_config()

        assert success is True
        assert 'Nginx configuration is valid' in message

    @patch('pythonweb_installer.server.config.render_template')
    def test_test_config_nginx_invalid(self, mock_render_template, server_config_nginx):
        """Test testing an invalid Nginx server configuration."""
        # Mock the render_template function
        mock_render_template.return_value = """
# Missing required directives
"""

        # Test the configuration
        success, message = server_config_nginx.test_config()

        assert success is False
        assert 'Missing required directive' in message

    @patch('pythonweb_installer.server.config.render_template')
    def test_test_config_apache(self, mock_render_template, server_config_apache):
        """Test testing an Apache server configuration."""
        # Mock the render_template function
        mock_render_template.return_value = """
<VirtualHost *:80>
    ServerName localhost
    DocumentRoot /var/www/html
    WSGIScriptAlias / /var/www/app/wsgi.py
</VirtualHost>
"""

        # Test the configuration
        success, message = server_config_apache.test_config()

        assert success is True
        assert 'Apache configuration is valid' in message

    @patch('pythonweb_installer.server.config.render_template')
    def test_test_config_apache_invalid(self, mock_render_template, server_config_apache):
        """Test testing an invalid Apache server configuration."""
        # Mock the render_template function
        mock_render_template.return_value = """
# Missing required directives
"""

        # Test the configuration
        success, message = server_config_apache.test_config()

        assert success is False
        assert 'Missing required directive' in message

    @patch('pythonweb_installer.server.config.create_server_config')
    def test_generate_server_config(self, mock_create_server_config, temp_config_dir):
        """Test generating a server configuration."""
        # Mock the create_server_config function
        mock_server_config = MagicMock()
        mock_server_config.generate_config.return_value = (True, 'Generated configuration', 'content')
        mock_create_server_config.return_value = mock_server_config

        # Generate the configuration
        success, message, content = generate_server_config('gunicorn', temp_config_dir, {'workers': 8})

        assert success is True
        assert 'Generated configuration' in message
        assert content == 'content'

        # Check if the create_server_config function was called
        mock_create_server_config.assert_called_once_with('gunicorn', temp_config_dir)

        # Check if the update_config method was called
        mock_server_config.update_config.assert_called_once_with({'workers': 8})

        # Check if the generate_config method was called
        mock_server_config.generate_config.assert_called_once()

    @patch('pythonweb_installer.server.config.create_server_config')
    def test_generate_server_config_error(self, mock_create_server_config, temp_config_dir):
        """Test generating a server configuration with an error."""
        # Mock the create_server_config function to raise an exception
        mock_create_server_config.side_effect = Exception('Test error')

        # Generate the configuration
        success, message, content = generate_server_config('gunicorn', temp_config_dir)

        assert success is False
        assert 'Failed to generate gunicorn configuration' in message
        assert content is None

    @patch('pythonweb_installer.server.config.create_server_config')
    def test_validate_server_config(self, mock_create_server_config):
        """Test validating a server configuration."""
        # Mock the create_server_config function
        mock_server_config = MagicMock()
        mock_server_config.validate_config.return_value = (True, [])
        mock_create_server_config.return_value = mock_server_config

        # Validate the configuration
        valid, errors = validate_server_config('gunicorn', {'workers': 8})

        assert valid is True
        assert len(errors) == 0

        # Check if the create_server_config function was called
        mock_create_server_config.assert_called_once_with('gunicorn', '')

        # Check if the update_config method was called
        mock_server_config.update_config.assert_called_once_with({'workers': 8})

        # Check if the validate_config method was called
        mock_server_config.validate_config.assert_called_once()

    @patch('pythonweb_installer.server.config.create_server_config')
    def test_validate_server_config_error(self, mock_create_server_config):
        """Test validating a server configuration with an error."""
        # Mock the create_server_config function to raise an exception
        mock_create_server_config.side_effect = Exception('Test error')

        # Validate the configuration
        valid, errors = validate_server_config('gunicorn', {})

        assert valid is False
        assert len(errors) > 0
        assert 'Failed to validate gunicorn configuration' in errors[0]
