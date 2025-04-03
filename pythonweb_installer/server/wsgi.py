"""
WSGI/ASGI support functionality.
"""
import os
import re
import logging
from typing import Dict, Any, List, Tuple, Optional, Union

from pythonweb_installer.utils.templates import render_template

logger = logging.getLogger(__name__)


class WSGIConfig:
    """
    WSGI configuration.
    """
    
    def __init__(self, app_dir: str, app_module: str, app_variable: str = 'app'):
        """
        Initialize the WSGI configuration.
        
        Args:
            app_dir: Application directory
            app_module: Application module
            app_variable: Application variable
        """
        self.app_dir = app_dir
        self.app_module = app_module
        self.app_variable = app_variable
        self.config_data = {}
        
        # Set default configuration values
        self._set_defaults()
    
    def _set_defaults(self) -> None:
        """
        Set default configuration values.
        """
        self.config_data = {
            'app_dir': self.app_dir,
            'app_module': self.app_module,
            'app_variable': self.app_variable,
            'python_path': self.app_dir,
            'log_file': os.path.join(self.app_dir, 'logs', 'wsgi.log'),
            'error_log_file': os.path.join(self.app_dir, 'logs', 'wsgi_error.log'),
            'static_dir': os.path.join(self.app_dir, 'static'),
            'static_url': '/static/',
            'media_dir': os.path.join(self.app_dir, 'media'),
            'media_url': '/media/',
            'debug': False
        }
    
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
    
    def generate_wsgi_file(self, output_path: Optional[str] = None) -> Tuple[bool, str, Optional[str]]:
        """
        Generate a WSGI file.
        
        Args:
            output_path: Output path
            
        Returns:
            Tuple[bool, str, Optional[str]]: Success status, message, and file content
        """
        try:
            # Generate the WSGI file content
            wsgi_content = render_template(
                'wsgi.py.j2',
                self.config_data
            )
            
            # Write the WSGI file if an output path is provided
            if output_path:
                # Create the directory if it doesn't exist
                os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
                
                # Write the file
                with open(output_path, 'w') as f:
                    f.write(wsgi_content)
                
                logger.info(f"Generated WSGI file: {output_path}")
            
            return True, "Generated WSGI file", wsgi_content
        
        except Exception as e:
            logger.error(f"Failed to generate WSGI file: {str(e)}")
            return False, f"Failed to generate WSGI file: {str(e)}", None
    
    def generate_asgi_file(self, output_path: Optional[str] = None) -> Tuple[bool, str, Optional[str]]:
        """
        Generate an ASGI file.
        
        Args:
            output_path: Output path
            
        Returns:
            Tuple[bool, str, Optional[str]]: Success status, message, and file content
        """
        try:
            # Generate the ASGI file content
            asgi_content = render_template(
                'asgi.py.j2',
                self.config_data
            )
            
            # Write the ASGI file if an output path is provided
            if output_path:
                # Create the directory if it doesn't exist
                os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
                
                # Write the file
                with open(output_path, 'w') as f:
                    f.write(asgi_content)
                
                logger.info(f"Generated ASGI file: {output_path}")
            
            return True, "Generated ASGI file", asgi_content
        
        except Exception as e:
            logger.error(f"Failed to generate ASGI file: {str(e)}")
            return False, f"Failed to generate ASGI file: {str(e)}", None


class ASGIConfig(WSGIConfig):
    """
    ASGI configuration.
    """
    
    def _set_defaults(self) -> None:
        """
        Set default configuration values.
        """
        super()._set_defaults()
        
        # Add ASGI-specific defaults
        self.config_data.update({
            'asgi_framework': 'uvicorn',
            'asgi_lifespan': 'on',
            'asgi_http': 'auto',
            'asgi_websockets': 'auto',
            'asgi_workers': 4,
            'asgi_timeout': 30
        })


def create_wsgi_config(app_dir: str, app_module: str, app_variable: str = 'app') -> WSGIConfig:
    """
    Create a WSGI configuration.
    
    Args:
        app_dir: Application directory
        app_module: Application module
        app_variable: Application variable
        
    Returns:
        WSGIConfig: WSGI configuration
    """
    return WSGIConfig(app_dir, app_module, app_variable)


def create_asgi_config(app_dir: str, app_module: str, app_variable: str = 'app') -> ASGIConfig:
    """
    Create an ASGI configuration.
    
    Args:
        app_dir: Application directory
        app_module: Application module
        app_variable: Application variable
        
    Returns:
        ASGIConfig: ASGI configuration
    """
    return ASGIConfig(app_dir, app_module, app_variable)


def generate_wsgi_file(app_dir: str, app_module: str, app_variable: str = 'app',
                      output_path: Optional[str] = None,
                      config_data: Optional[Dict[str, Any]] = None) -> Tuple[bool, str, Optional[str]]:
    """
    Generate a WSGI file.
    
    Args:
        app_dir: Application directory
        app_module: Application module
        app_variable: Application variable
        output_path: Output path
        config_data: Configuration data
        
    Returns:
        Tuple[bool, str, Optional[str]]: Success status, message, and file content
    """
    try:
        # Create a WSGI configuration
        wsgi_config = create_wsgi_config(app_dir, app_module, app_variable)
        
        # Update the configuration data
        if config_data:
            wsgi_config.update_config(config_data)
        
        # Generate the WSGI file
        return wsgi_config.generate_wsgi_file(output_path)
    
    except Exception as e:
        logger.error(f"Failed to generate WSGI file: {str(e)}")
        return False, f"Failed to generate WSGI file: {str(e)}", None


def generate_asgi_file(app_dir: str, app_module: str, app_variable: str = 'app',
                      output_path: Optional[str] = None,
                      config_data: Optional[Dict[str, Any]] = None) -> Tuple[bool, str, Optional[str]]:
    """
    Generate an ASGI file.
    
    Args:
        app_dir: Application directory
        app_module: Application module
        app_variable: Application variable
        output_path: Output path
        config_data: Configuration data
        
    Returns:
        Tuple[bool, str, Optional[str]]: Success status, message, and file content
    """
    try:
        # Create an ASGI configuration
        asgi_config = create_asgi_config(app_dir, app_module, app_variable)
        
        # Update the configuration data
        if config_data:
            asgi_config.update_config(config_data)
        
        # Generate the ASGI file
        return asgi_config.generate_asgi_file(output_path)
    
    except Exception as e:
        logger.error(f"Failed to generate ASGI file: {str(e)}")
        return False, f"Failed to generate ASGI file: {str(e)}", None
