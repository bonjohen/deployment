"""
Server startup script functionality.
"""
import os
import re
import stat
import logging
import platform
from typing import Dict, Any, List, Tuple, Optional, Union

from pythonweb_installer.utils.templates import render_template

logger = logging.getLogger(__name__)


class StartupScript:
    """
    Server startup script.
    """
    
    def __init__(self, server_type: str, app_dir: str, script_dir: str):
        """
        Initialize the startup script.
        
        Args:
            server_type: Server type (gunicorn, uwsgi, nginx, apache)
            app_dir: Application directory
            script_dir: Script directory
        """
        self.server_type = server_type.lower()
        self.app_dir = app_dir
        self.script_dir = script_dir
        self.script_file = None
        self.script_template = None
        self.script_data = {}
        
        # Set default script values
        self._set_defaults()
    
    def _set_defaults(self) -> None:
        """
        Set default script values.
        """
        # Common defaults
        self.script_data = {
            'app_dir': self.app_dir,
            'server_type': self.server_type,
            'python_path': os.path.join(self.app_dir, 'venv', 'bin', 'python'),
            'log_dir': os.path.join(self.app_dir, 'logs'),
            'config_dir': os.path.join(self.app_dir, 'config'),
            'user': os.environ.get('USER', 'www-data'),
            'group': os.environ.get('USER', 'www-data'),
            'description': f'PythonWeb {self.server_type.capitalize()} Server',
            'app_name': os.path.basename(self.app_dir),
            'environment': 'production'
        }
        
        # Adjust Python path for Windows
        if platform.system() == 'Windows':
            self.script_data['python_path'] = os.path.join(self.app_dir, 'venv', 'Scripts', 'python.exe')
        
        # Server-specific defaults
        if self.server_type == 'gunicorn':
            self.script_file = 'start_gunicorn.sh'
            self.script_template = 'start_gunicorn.sh.j2'
            self.script_data.update({
                'gunicorn_path': os.path.join(self.app_dir, 'venv', 'bin', 'gunicorn'),
                'config_file': os.path.join(self.app_dir, 'config', 'gunicorn.conf.py'),
                'app_module': 'app:app',
                'workers': 4,
                'bind': '0.0.0.0:8000',
                'daemon': False,
                'pid_file': os.path.join(self.app_dir, 'gunicorn.pid')
            })
            
            # Adjust Gunicorn path for Windows
            if platform.system() == 'Windows':
                self.script_data['gunicorn_path'] = os.path.join(self.app_dir, 'venv', 'Scripts', 'gunicorn.exe')
        
        elif self.server_type == 'uwsgi':
            self.script_file = 'start_uwsgi.sh'
            self.script_template = 'start_uwsgi.sh.j2'
            self.script_data.update({
                'uwsgi_path': os.path.join(self.app_dir, 'venv', 'bin', 'uwsgi'),
                'config_file': os.path.join(self.app_dir, 'config', 'uwsgi.ini'),
                'processes': 4,
                'threads': 2,
                'socket': '0.0.0.0:8000',
                'daemonize': os.path.join(self.app_dir, 'logs', 'uwsgi.log'),
                'pidfile': os.path.join(self.app_dir, 'uwsgi.pid')
            })
            
            # Adjust uWSGI path for Windows
            if platform.system() == 'Windows':
                self.script_data['uwsgi_path'] = os.path.join(self.app_dir, 'venv', 'Scripts', 'uwsgi.exe')
        
        elif self.server_type == 'nginx':
            self.script_file = 'start_nginx.sh'
            self.script_template = 'start_nginx.sh.j2'
            self.script_data.update({
                'nginx_path': '/usr/sbin/nginx',
                'config_file': os.path.join(self.app_dir, 'config', 'nginx.conf'),
                'pid_file': '/var/run/nginx.pid',
                'error_log': os.path.join(self.app_dir, 'logs', 'nginx_error.log'),
                'access_log': os.path.join(self.app_dir, 'logs', 'nginx_access.log')
            })
        
        elif self.server_type == 'apache':
            self.script_file = 'start_apache.sh'
            self.script_template = 'start_apache.sh.j2'
            self.script_data.update({
                'apache_path': '/usr/sbin/apache2',
                'config_file': os.path.join(self.app_dir, 'config', 'apache.conf'),
                'pid_file': '/var/run/apache2.pid',
                'error_log': os.path.join(self.app_dir, 'logs', 'apache_error.log'),
                'access_log': os.path.join(self.app_dir, 'logs', 'apache_access.log')
            })
        
        else:
            raise ValueError(f"Unsupported server type: {self.server_type}")
        
        # Add systemd service file
        self.service_file = f'pythonweb-{self.server_type}.service'
        self.service_template = 'systemd.service.j2'
    
    def set_script_data(self, key: str, value: Any) -> None:
        """
        Set a script data value.
        
        Args:
            key: Script data key
            value: Script data value
        """
        self.script_data[key] = value
    
    def get_script_data(self, key: str, default: Any = None) -> Any:
        """
        Get a script data value.
        
        Args:
            key: Script data key
            default: Default value
            
        Returns:
            Any: Script data value
        """
        return self.script_data.get(key, default)
    
    def update_script_data(self, script_data: Dict[str, Any]) -> None:
        """
        Update script data values.
        
        Args:
            script_data: Script data
        """
        self.script_data.update(script_data)
    
    def generate_startup_script(self) -> Tuple[bool, str, Optional[str]]:
        """
        Generate the startup script.
        
        Returns:
            Tuple[bool, str, Optional[str]]: Success status, message, and script content
        """
        try:
            # Create the script directory if it doesn't exist
            os.makedirs(self.script_dir, exist_ok=True)
            
            # Generate the script file path
            script_path = os.path.join(self.script_dir, self.script_file)
            
            # Render the script template
            script_content = render_template(
                self.script_template,
                self.script_data
            )
            
            # Write the script file
            with open(script_path, 'w') as f:
                f.write(script_content)
            
            # Make the script executable
            os.chmod(script_path, os.stat(script_path).st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
            
            logger.info(f"Generated {self.server_type} startup script: {script_path}")
            return True, f"Generated {self.server_type} startup script: {script_path}", script_content
        
        except Exception as e:
            logger.error(f"Failed to generate {self.server_type} startup script: {str(e)}")
            return False, f"Failed to generate {self.server_type} startup script: {str(e)}", None
    
    def generate_systemd_service(self, output_dir: Optional[str] = None) -> Tuple[bool, str, Optional[str]]:
        """
        Generate a systemd service file.
        
        Args:
            output_dir: Output directory
            
        Returns:
            Tuple[bool, str, Optional[str]]: Success status, message, and service content
        """
        try:
            # Skip if not on Linux
            if platform.system() != 'Linux':
                return False, "Systemd services are only supported on Linux", None
            
            # Set the output directory
            if output_dir is None:
                output_dir = self.script_dir
            
            # Create the output directory if it doesn't exist
            os.makedirs(output_dir, exist_ok=True)
            
            # Generate the service file path
            service_path = os.path.join(output_dir, self.service_file)
            
            # Render the service template
            service_content = render_template(
                self.service_template,
                self.script_data
            )
            
            # Write the service file
            with open(service_path, 'w') as f:
                f.write(service_content)
            
            logger.info(f"Generated {self.server_type} systemd service: {service_path}")
            return True, f"Generated {self.server_type} systemd service: {service_path}", service_content
        
        except Exception as e:
            logger.error(f"Failed to generate {self.server_type} systemd service: {str(e)}")
            return False, f"Failed to generate {self.server_type} systemd service: {str(e)}", None


def create_startup_script(server_type: str, app_dir: str, script_dir: str) -> StartupScript:
    """
    Create a startup script.
    
    Args:
        server_type: Server type (gunicorn, uwsgi, nginx, apache)
        app_dir: Application directory
        script_dir: Script directory
        
    Returns:
        StartupScript: Startup script
    """
    return StartupScript(server_type, app_dir, script_dir)


def generate_startup_script(server_type: str, app_dir: str, script_dir: str,
                           script_data: Optional[Dict[str, Any]] = None) -> Tuple[bool, str, Optional[str]]:
    """
    Generate a startup script.
    
    Args:
        server_type: Server type (gunicorn, uwsgi, nginx, apache)
        app_dir: Application directory
        script_dir: Script directory
        script_data: Script data
        
    Returns:
        Tuple[bool, str, Optional[str]]: Success status, message, and script content
    """
    try:
        # Create a startup script
        startup_script = create_startup_script(server_type, app_dir, script_dir)
        
        # Update the script data
        if script_data:
            startup_script.update_script_data(script_data)
        
        # Generate the startup script
        return startup_script.generate_startup_script()
    
    except Exception as e:
        logger.error(f"Failed to generate {server_type} startup script: {str(e)}")
        return False, f"Failed to generate {server_type} startup script: {str(e)}", None


def generate_systemd_service(server_type: str, app_dir: str, script_dir: str,
                            output_dir: Optional[str] = None,
                            script_data: Optional[Dict[str, Any]] = None) -> Tuple[bool, str, Optional[str]]:
    """
    Generate a systemd service file.
    
    Args:
        server_type: Server type (gunicorn, uwsgi, nginx, apache)
        app_dir: Application directory
        script_dir: Script directory
        output_dir: Output directory
        script_data: Script data
        
    Returns:
        Tuple[bool, str, Optional[str]]: Success status, message, and service content
    """
    try:
        # Create a startup script
        startup_script = create_startup_script(server_type, app_dir, script_dir)
        
        # Update the script data
        if script_data:
            startup_script.update_script_data(script_data)
        
        # Generate the systemd service
        return startup_script.generate_systemd_service(output_dir)
    
    except Exception as e:
        logger.error(f"Failed to generate {server_type} systemd service: {str(e)}")
        return False, f"Failed to generate {server_type} systemd service: {str(e)}", None
