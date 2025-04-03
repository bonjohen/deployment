"""
Unit tests for WSGI/ASGI functionality.
"""
import os
import tempfile
from unittest.mock import patch, MagicMock

import pytest

from pythonweb_installer.server.wsgi import (
    WSGIConfig,
    ASGIConfig,
    create_wsgi_config,
    create_asgi_config,
    generate_wsgi_file,
    generate_asgi_file
)


class TestWSGIConfig:
    """Tests for WSGI configuration functionality."""

    @pytest.fixture
    def app_dir(self):
        """Create a temporary application directory."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir

        # Clean up
        import shutil
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def wsgi_config(self, app_dir):
        """Create a WSGI configuration."""
        return WSGIConfig(app_dir, 'app:app')

    @pytest.fixture
    def asgi_config(self, app_dir):
        """Create an ASGI configuration."""
        return ASGIConfig(app_dir, 'app:app')

    def test_create_wsgi_config(self, app_dir):
        """Test creating a WSGI configuration."""
        # Create a WSGI configuration
        wsgi_config = create_wsgi_config(app_dir, 'app:app')

        assert wsgi_config is not None
        assert isinstance(wsgi_config, WSGIConfig)
        assert wsgi_config.app_dir == app_dir
        assert wsgi_config.app_module == 'app:app'
        assert wsgi_config.app_variable == 'app'

    def test_create_asgi_config(self, app_dir):
        """Test creating an ASGI configuration."""
        # Create an ASGI configuration
        asgi_config = create_asgi_config(app_dir, 'app:app')

        assert asgi_config is not None
        assert isinstance(asgi_config, ASGIConfig)
        assert asgi_config.app_dir == app_dir
        assert asgi_config.app_module == 'app:app'
        assert asgi_config.app_variable == 'app'

    def test_set_config(self, wsgi_config):
        """Test setting a configuration value."""
        # Set a configuration value
        wsgi_config.set_config('debug', True)

        assert wsgi_config.get_config('debug') is True

    def test_get_config(self, wsgi_config):
        """Test getting a configuration value."""
        # Get a configuration value
        app_module = wsgi_config.get_config('app_module')

        assert app_module == 'app:app'

    def test_get_config_default(self, wsgi_config):
        """Test getting a configuration value with a default."""
        # Get a configuration value with a default
        value = wsgi_config.get_config('nonexistent', 'default')

        assert value == 'default'

    def test_update_config(self, wsgi_config):
        """Test updating configuration values."""
        # Update configuration values
        wsgi_config.update_config({
            'debug': True,
            'static_dir': '/static',
            'static_url': '/static/'
        })

        assert wsgi_config.get_config('debug') is True
        assert wsgi_config.get_config('static_dir') == '/static'
        assert wsgi_config.get_config('static_url') == '/static/'

    @patch('pythonweb_installer.server.wsgi.render_template')
    def test_generate_wsgi_file(self, mock_render_template, wsgi_config, app_dir):
        """Test generating a WSGI file."""
        # Mock the render_template function
        mock_render_template.return_value = 'rendered template'

        # Generate the WSGI file
        success, message, content = wsgi_config.generate_wsgi_file()

        assert success is True
        assert 'Generated WSGI file' in message
        assert content == 'rendered template'

        # Check if the render_template function was called
        mock_render_template.assert_called_once_with(
            'wsgi.py.j2',
            wsgi_config.config_data
        )

    @patch('pythonweb_installer.server.wsgi.render_template')
    def test_generate_wsgi_file_with_output(self, mock_render_template, wsgi_config, app_dir):
        """Test generating a WSGI file with an output path."""
        # Mock the render_template function
        mock_render_template.return_value = 'rendered template'

        # Generate the WSGI file with an output path
        output_path = os.path.join(app_dir, 'wsgi.py')
        success, message, content = wsgi_config.generate_wsgi_file(output_path)

        assert success is True
        assert 'Generated WSGI file' in message
        assert content == 'rendered template'

        # Check if the file was created
        assert os.path.exists(output_path)

        # Check the file content
        with open(output_path, 'r') as f:
            file_content = f.read()

        assert file_content == 'rendered template'

    @patch('pythonweb_installer.server.wsgi.render_template')
    def test_generate_wsgi_file_error(self, mock_render_template, wsgi_config):
        """Test generating a WSGI file with an error."""
        # Mock the render_template function to raise an exception
        mock_render_template.side_effect = Exception('Test error')

        # Generate the WSGI file
        success, message, content = wsgi_config.generate_wsgi_file()

        assert success is False
        assert 'Failed to generate WSGI file' in message
        assert content is None

    @patch('pythonweb_installer.server.wsgi.render_template')
    def test_generate_asgi_file(self, mock_render_template, asgi_config, app_dir):
        """Test generating an ASGI file."""
        # Mock the render_template function
        mock_render_template.return_value = 'rendered template'

        # Generate the ASGI file
        success, message, content = asgi_config.generate_asgi_file()

        assert success is True
        assert 'Generated ASGI file' in message
        assert content == 'rendered template'

        # Check if the render_template function was called
        mock_render_template.assert_called_once_with(
            'asgi.py.j2',
            asgi_config.config_data
        )

    @patch('pythonweb_installer.server.wsgi.render_template')
    def test_generate_asgi_file_with_output(self, mock_render_template, asgi_config, app_dir):
        """Test generating an ASGI file with an output path."""
        # Mock the render_template function
        mock_render_template.return_value = 'rendered template'

        # Generate the ASGI file with an output path
        output_path = os.path.join(app_dir, 'asgi.py')
        success, message, content = asgi_config.generate_asgi_file(output_path)

        assert success is True
        assert 'Generated ASGI file' in message
        assert content == 'rendered template'

        # Check if the file was created
        assert os.path.exists(output_path)

        # Check the file content
        with open(output_path, 'r') as f:
            file_content = f.read()

        assert file_content == 'rendered template'

    @patch('pythonweb_installer.server.wsgi.render_template')
    def test_generate_asgi_file_error(self, mock_render_template, asgi_config):
        """Test generating an ASGI file with an error."""
        # Mock the render_template function to raise an exception
        mock_render_template.side_effect = Exception('Test error')

        # Generate the ASGI file
        success, message, content = asgi_config.generate_asgi_file()

        assert success is False
        assert 'Failed to generate ASGI file' in message
        assert content is None

    @patch('pythonweb_installer.server.wsgi.create_wsgi_config')
    def test_generate_wsgi_file_function(self, mock_create_wsgi_config, app_dir):
        """Test the generate_wsgi_file function."""
        # Mock the create_wsgi_config function
        mock_wsgi_config = MagicMock()
        mock_wsgi_config.generate_wsgi_file.return_value = (True, 'Generated WSGI file', 'content')
        mock_create_wsgi_config.return_value = mock_wsgi_config

        # Generate the WSGI file
        success, message, content = generate_wsgi_file(app_dir, 'app:app', 'app')

        assert success is True
        assert 'Generated WSGI file' in message
        assert content == 'content'

        # Check if the create_wsgi_config function was called
        mock_create_wsgi_config.assert_called_once_with(app_dir, 'app:app', 'app')

        # Check if the generate_wsgi_file method was called
        mock_wsgi_config.generate_wsgi_file.assert_called_once_with(None)

    @patch('pythonweb_installer.server.wsgi.create_wsgi_config')
    def test_generate_wsgi_file_function_with_config(self, mock_create_wsgi_config, app_dir):
        """Test the generate_wsgi_file function with configuration data."""
        # Mock the create_wsgi_config function
        mock_wsgi_config = MagicMock()
        mock_wsgi_config.generate_wsgi_file.return_value = (True, 'Generated WSGI file', 'content')
        mock_create_wsgi_config.return_value = mock_wsgi_config

        # Generate the WSGI file with configuration data
        config_data = {'debug': True}
        success, message, content = generate_wsgi_file(app_dir, 'app:app', 'app', None, config_data)

        assert success is True
        assert 'Generated WSGI file' in message
        assert content == 'content'

        # Check if the update_config method was called
        mock_wsgi_config.update_config.assert_called_once_with(config_data)

    @patch('pythonweb_installer.server.wsgi.create_wsgi_config')
    def test_generate_wsgi_file_function_error(self, mock_create_wsgi_config, app_dir):
        """Test the generate_wsgi_file function with an error."""
        # Mock the create_wsgi_config function to raise an exception
        mock_create_wsgi_config.side_effect = Exception('Test error')

        # Generate the WSGI file
        success, message, content = generate_wsgi_file(app_dir, 'app:app')

        assert success is False
        assert 'Failed to generate WSGI file' in message
        assert content is None

    @patch('pythonweb_installer.server.wsgi.create_asgi_config')
    def test_generate_asgi_file_function(self, mock_create_asgi_config, app_dir):
        """Test the generate_asgi_file function."""
        # Mock the create_asgi_config function
        mock_asgi_config = MagicMock()
        mock_asgi_config.generate_asgi_file.return_value = (True, 'Generated ASGI file', 'content')
        mock_create_asgi_config.return_value = mock_asgi_config

        # Generate the ASGI file
        success, message, content = generate_asgi_file(app_dir, 'app:app', 'app')

        assert success is True
        assert 'Generated ASGI file' in message
        assert content == 'content'

        # Check if the create_asgi_config function was called
        mock_create_asgi_config.assert_called_once_with(app_dir, 'app:app', 'app')

        # Check if the generate_asgi_file method was called
        mock_asgi_config.generate_asgi_file.assert_called_once_with(None)

    @patch('pythonweb_installer.server.wsgi.create_asgi_config')
    def test_generate_asgi_file_function_with_config(self, mock_create_asgi_config, app_dir):
        """Test the generate_asgi_file function with configuration data."""
        # Mock the create_asgi_config function
        mock_asgi_config = MagicMock()
        mock_asgi_config.generate_asgi_file.return_value = (True, 'Generated ASGI file', 'content')
        mock_create_asgi_config.return_value = mock_asgi_config

        # Generate the ASGI file with configuration data
        config_data = {'debug': True}
        success, message, content = generate_asgi_file(app_dir, 'app:app', 'app', None, config_data)

        assert success is True
        assert 'Generated ASGI file' in message
        assert content == 'content'

        # Check if the update_config method was called
        mock_asgi_config.update_config.assert_called_once_with(config_data)

    @patch('pythonweb_installer.server.wsgi.create_asgi_config')
    def test_generate_asgi_file_function_error(self, mock_create_asgi_config, app_dir):
        """Test the generate_asgi_file function with an error."""
        # Mock the create_asgi_config function to raise an exception
        mock_create_asgi_config.side_effect = Exception('Test error')

        # Generate the ASGI file
        success, message, content = generate_asgi_file(app_dir, 'app:app')

        assert success is False
        assert 'Failed to generate ASGI file' in message
        assert content is None
