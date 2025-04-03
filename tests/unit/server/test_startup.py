"""
Unit tests for server startup script functionality.
"""
import os
import stat
import tempfile
import platform
from unittest.mock import patch, MagicMock

import pytest

from pythonweb_installer.server.startup import (
    StartupScript,
    create_startup_script,
    generate_startup_script,
    generate_systemd_service
)


class TestStartupScript:
    """Tests for startup script functionality."""

    @pytest.fixture
    def app_dir(self):
        """Create a temporary application directory."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir

        # Clean up
        import shutil
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def script_dir(self):
        """Create a temporary script directory."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir

        # Clean up
        import shutil
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def startup_script_gunicorn(self, app_dir, script_dir):
        """Create a Gunicorn startup script."""
        return StartupScript('gunicorn', app_dir, script_dir)

    @pytest.fixture
    def startup_script_uwsgi(self, app_dir, script_dir):
        """Create a uWSGI startup script."""
        return StartupScript('uwsgi', app_dir, script_dir)

    @pytest.fixture
    def startup_script_nginx(self, app_dir, script_dir):
        """Create a Nginx startup script."""
        return StartupScript('nginx', app_dir, script_dir)

    @pytest.fixture
    def startup_script_apache(self, app_dir, script_dir):
        """Create an Apache startup script."""
        return StartupScript('apache', app_dir, script_dir)

    def test_create_startup_script(self, app_dir, script_dir):
        """Test creating a startup script."""
        # Create a startup script
        startup_script = create_startup_script('gunicorn', app_dir, script_dir)

        assert startup_script is not None
        assert isinstance(startup_script, StartupScript)
        assert startup_script.server_type == 'gunicorn'
        assert startup_script.app_dir == app_dir
        assert startup_script.script_dir == script_dir

    def test_create_startup_script_invalid_type(self, app_dir, script_dir):
        """Test creating a startup script with an invalid type."""
        # Create a startup script with an invalid type
        with pytest.raises(ValueError):
            create_startup_script('invalid', app_dir, script_dir)

    def test_set_script_data(self, startup_script_gunicorn):
        """Test setting a script data value."""
        # Set a script data value
        startup_script_gunicorn.set_script_data('workers', 8)

        assert startup_script_gunicorn.get_script_data('workers') == 8

    def test_get_script_data(self, startup_script_gunicorn):
        """Test getting a script data value."""
        # Get a script data value
        app_dir = startup_script_gunicorn.get_script_data('app_dir')

        assert app_dir is not None
        assert isinstance(app_dir, str)

    def test_get_script_data_default(self, startup_script_gunicorn):
        """Test getting a script data value with a default."""
        # Get a script data value with a default
        value = startup_script_gunicorn.get_script_data('nonexistent', 'default')

        assert value == 'default'

    def test_update_script_data(self, startup_script_gunicorn):
        """Test updating script data values."""
        # Update script data values
        startup_script_gunicorn.update_script_data({
            'workers': 8,
            'threads': 4,
            'timeout': 60
        })

        assert startup_script_gunicorn.get_script_data('workers') == 8
        assert startup_script_gunicorn.get_script_data('threads') == 4
        assert startup_script_gunicorn.get_script_data('timeout') == 60

    @patch('pythonweb_installer.server.startup.render_template')
    def test_generate_startup_script(self, mock_render_template, startup_script_gunicorn, script_dir):
        """Test generating a startup script."""
        # Mock the render_template function
        mock_render_template.return_value = 'rendered template'

        # Generate the startup script
        success, message, content = startup_script_gunicorn.generate_startup_script()

        assert success is True
        assert 'Generated gunicorn startup script' in message
        assert content == 'rendered template'

        # Check if the script file was created
        script_path = os.path.join(script_dir, startup_script_gunicorn.script_file)
        assert os.path.exists(script_path)

        # Check if the script is executable
        assert os.access(script_path, os.X_OK)

        # Check if the render_template function was called
        mock_render_template.assert_called_once_with(
            startup_script_gunicorn.script_template,
            startup_script_gunicorn.script_data
        )

    @patch('pythonweb_installer.server.startup.render_template')
    def test_generate_startup_script_error(self, mock_render_template, startup_script_gunicorn):
        """Test generating a startup script with an error."""
        # Mock the render_template function to raise an exception
        mock_render_template.side_effect = Exception('Test error')

        # Generate the startup script
        success, message, content = startup_script_gunicorn.generate_startup_script()

        assert success is False
        assert 'Failed to generate gunicorn startup script' in message
        assert content is None

    @patch('platform.system')
    @patch('pythonweb_installer.server.startup.render_template')
    def test_generate_systemd_service_linux(self, mock_render_template, mock_system, startup_script_gunicorn, script_dir):
        """Test generating a systemd service file on Linux."""
        # Mock the platform.system function
        mock_system.return_value = 'Linux'

        # Mock the render_template function
        mock_render_template.return_value = 'rendered template'

        # Generate the systemd service file
        success, message, content = startup_script_gunicorn.generate_systemd_service()

        assert success is True
        assert 'Generated gunicorn systemd service' in message
        assert content == 'rendered template'

        # Check if the service file was created
        service_path = os.path.join(script_dir, startup_script_gunicorn.service_file)
        assert os.path.exists(service_path)

        # Check if the render_template function was called
        mock_render_template.assert_called_once_with(
            startup_script_gunicorn.service_template,
            startup_script_gunicorn.script_data
        )

    @patch('platform.system')
    def test_generate_systemd_service_non_linux(self, mock_system, startup_script_gunicorn):
        """Test generating a systemd service file on a non-Linux platform."""
        # Mock the platform.system function
        mock_system.return_value = 'Windows'

        # Generate the systemd service file
        success, message, content = startup_script_gunicorn.generate_systemd_service()

        assert success is False
        assert 'Systemd services are only supported on Linux' in message
        assert content is None

    @patch('platform.system')
    @patch('pythonweb_installer.server.startup.render_template')
    def test_generate_systemd_service_with_output_dir(self, mock_render_template, mock_system, startup_script_gunicorn, script_dir):
        """Test generating a systemd service file with an output directory."""
        # Mock the platform.system function
        mock_system.return_value = 'Linux'

        # Mock the render_template function
        mock_render_template.return_value = 'rendered template'

        # Create a temporary output directory
        output_dir = tempfile.mkdtemp()

        try:
            # Generate the systemd service file with an output directory
            success, message, content = startup_script_gunicorn.generate_systemd_service(output_dir)

            assert success is True
            assert 'Generated gunicorn systemd service' in message
            assert content == 'rendered template'

            # Check if the service file was created in the output directory
            service_path = os.path.join(output_dir, startup_script_gunicorn.service_file)
            assert os.path.exists(service_path)

        finally:
            # Clean up
            import shutil
            shutil.rmtree(output_dir)

    @patch('platform.system')
    @patch('pythonweb_installer.server.startup.render_template')
    def test_generate_systemd_service_error(self, mock_render_template, mock_system, startup_script_gunicorn):
        """Test generating a systemd service file with an error."""
        # Mock the platform.system function
        mock_system.return_value = 'Linux'

        # Mock the render_template function to raise an exception
        mock_render_template.side_effect = Exception('Test error')

        # Generate the systemd service file
        success, message, content = startup_script_gunicorn.generate_systemd_service()

        assert success is False
        assert 'Failed to generate gunicorn systemd service' in message
        assert content is None

    @patch('pythonweb_installer.server.startup.create_startup_script')
    def test_generate_startup_script_function(self, mock_create_startup_script, app_dir, script_dir):
        """Test the generate_startup_script function."""
        # Mock the create_startup_script function
        mock_startup_script = MagicMock()
        mock_startup_script.generate_startup_script.return_value = (True, 'Generated startup script', 'content')
        mock_create_startup_script.return_value = mock_startup_script

        # Generate the startup script
        success, message, content = generate_startup_script('gunicorn', app_dir, script_dir)

        assert success is True
        assert 'Generated startup script' in message
        assert content == 'content'

        # Check if the create_startup_script function was called
        mock_create_startup_script.assert_called_once_with('gunicorn', app_dir, script_dir)

        # Check if the generate_startup_script method was called
        mock_startup_script.generate_startup_script.assert_called_once()

    @patch('pythonweb_installer.server.startup.create_startup_script')
    def test_generate_startup_script_function_with_script_data(self, mock_create_startup_script, app_dir, script_dir):
        """Test the generate_startup_script function with script data."""
        # Mock the create_startup_script function
        mock_startup_script = MagicMock()
        mock_startup_script.generate_startup_script.return_value = (True, 'Generated startup script', 'content')
        mock_create_startup_script.return_value = mock_startup_script

        # Generate the startup script with script data
        script_data = {'workers': 8}
        success, message, content = generate_startup_script('gunicorn', app_dir, script_dir, script_data)

        assert success is True
        assert 'Generated startup script' in message
        assert content == 'content'

        # Check if the update_script_data method was called
        mock_startup_script.update_script_data.assert_called_once_with(script_data)

    @patch('pythonweb_installer.server.startup.create_startup_script')
    def test_generate_startup_script_function_error(self, mock_create_startup_script, app_dir, script_dir):
        """Test the generate_startup_script function with an error."""
        # Mock the create_startup_script function to raise an exception
        mock_create_startup_script.side_effect = Exception('Test error')

        # Generate the startup script
        success, message, content = generate_startup_script('gunicorn', app_dir, script_dir)

        assert success is False
        assert 'Failed to generate gunicorn startup script' in message
        assert content is None

    @patch('pythonweb_installer.server.startup.create_startup_script')
    @patch('platform.system')
    def test_generate_systemd_service_function(self, mock_system, mock_create_startup_script, app_dir, script_dir):
        """Test the generate_systemd_service function."""
        # Mock the platform.system function
        mock_system.return_value = 'Linux'

        # Mock the create_startup_script function
        mock_startup_script = MagicMock()
        mock_startup_script.generate_systemd_service.return_value = (True, 'Generated systemd service', 'content')
        mock_create_startup_script.return_value = mock_startup_script

        # Generate the systemd service file
        success, message, content = generate_systemd_service('gunicorn', app_dir, script_dir)

        assert success is True
        assert 'Generated systemd service' in message
        assert content == 'content'

        # Check if the create_startup_script function was called
        mock_create_startup_script.assert_called_once_with('gunicorn', app_dir, script_dir)

        # Check if the generate_systemd_service method was called
        mock_startup_script.generate_systemd_service.assert_called_once_with(None)

    @patch('pythonweb_installer.server.startup.create_startup_script')
    @patch('platform.system')
    def test_generate_systemd_service_function_with_output_dir(self, mock_system, mock_create_startup_script, app_dir, script_dir):
        """Test the generate_systemd_service function with an output directory."""
        # Mock the platform.system function
        mock_system.return_value = 'Linux'

        # Mock the create_startup_script function
        mock_startup_script = MagicMock()
        mock_startup_script.generate_systemd_service.return_value = (True, 'Generated systemd service', 'content')
        mock_create_startup_script.return_value = mock_startup_script

        # Create a temporary output directory
        output_dir = tempfile.mkdtemp()

        try:
            # Generate the systemd service file with an output directory
            success, message, content = generate_systemd_service('gunicorn', app_dir, script_dir, output_dir)

            assert success is True
            assert 'Generated systemd service' in message
            assert content == 'content'

            # Check if the generate_systemd_service method was called with the output directory
            mock_startup_script.generate_systemd_service.assert_called_once_with(output_dir)

        finally:
            # Clean up
            import shutil
            shutil.rmtree(output_dir)

    @patch('pythonweb_installer.server.startup.create_startup_script')
    @patch('platform.system')
    def test_generate_systemd_service_function_with_script_data(self, mock_system, mock_create_startup_script, app_dir, script_dir):
        """Test the generate_systemd_service function with script data."""
        # Mock the platform.system function
        mock_system.return_value = 'Linux'

        # Mock the create_startup_script function
        mock_startup_script = MagicMock()
        mock_startup_script.generate_systemd_service.return_value = (True, 'Generated systemd service', 'content')
        mock_create_startup_script.return_value = mock_startup_script

        # Generate the systemd service file with script data
        script_data = {'workers': 8}
        success, message, content = generate_systemd_service('gunicorn', app_dir, script_dir, None, script_data)

        assert success is True
        assert 'Generated systemd service' in message
        assert content == 'content'

        # Check if the update_script_data method was called
        mock_startup_script.update_script_data.assert_called_once_with(script_data)

    @patch('pythonweb_installer.server.startup.create_startup_script')
    def test_generate_systemd_service_function_error(self, mock_create_startup_script, app_dir, script_dir):
        """Test the generate_systemd_service function with an error."""
        # Mock the create_startup_script function to raise an exception
        mock_create_startup_script.side_effect = Exception('Test error')

        # Generate the systemd service file
        success, message, content = generate_systemd_service('gunicorn', app_dir, script_dir)

        assert success is False
        assert 'Failed to generate gunicorn systemd service' in message
        assert content is None
