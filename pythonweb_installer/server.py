"""
Web server configuration for PythonWeb Installer.

This module provides high-level functions for web server configuration,
WSGI/ASGI setup, and server startup.
"""
import os
import logging
from typing import Dict, Any, List, Tuple, Optional, Union

from pythonweb_installer.server.config import (
    ServerConfig,
    create_server_config,
    generate_server_config,
    validate_server_config
)
from pythonweb_installer.server.wsgi import (
    WSGIConfig,
    ASGIConfig,
    create_wsgi_config,
    create_asgi_config,
    generate_wsgi_file,
    generate_asgi_file
)
from pythonweb_installer.server.startup import (
    StartupScript,
    create_startup_script,
    generate_startup_script,
    generate_systemd_service
)
from pythonweb_installer.server.performance import (
    PerformanceConfig,
    create_performance_config,
    get_performance_config,
    optimize_performance
)
from pythonweb_installer.server.security import (
    SecurityConfig,
    create_security_config,
    get_security_config,
    apply_security_config
)

logger = logging.getLogger(__name__)


def generate_server_configuration(server_type: str, config_dir: str,
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
    return generate_server_config(server_type, config_dir, config_data)


def generate_wsgi_configuration(app_dir: str, app_module: str, app_variable: str = 'app',
                              output_path: Optional[str] = None,
                              config_data: Optional[Dict[str, Any]] = None) -> Tuple[bool, str, Optional[str]]:
    """
    Generate a WSGI configuration.
    
    Args:
        app_dir: Application directory
        app_module: Application module
        app_variable: Application variable
        output_path: Output path
        config_data: Configuration data
        
    Returns:
        Tuple[bool, str, Optional[str]]: Success status, message, and configuration content
    """
    return generate_wsgi_file(app_dir, app_module, app_variable, output_path, config_data)


def generate_asgi_configuration(app_dir: str, app_module: str, app_variable: str = 'app',
                              output_path: Optional[str] = None,
                              config_data: Optional[Dict[str, Any]] = None) -> Tuple[bool, str, Optional[str]]:
    """
    Generate an ASGI configuration.
    
    Args:
        app_dir: Application directory
        app_module: Application module
        app_variable: Application variable
        output_path: Output path
        config_data: Configuration data
        
    Returns:
        Tuple[bool, str, Optional[str]]: Success status, message, and configuration content
    """
    return generate_asgi_file(app_dir, app_module, app_variable, output_path, config_data)


def generate_startup_configuration(server_type: str, app_dir: str, script_dir: str,
                                 script_data: Optional[Dict[str, Any]] = None) -> Tuple[bool, str, Optional[str]]:
    """
    Generate a startup configuration.
    
    Args:
        server_type: Server type (gunicorn, uwsgi, nginx, apache)
        app_dir: Application directory
        script_dir: Script directory
        script_data: Script data
        
    Returns:
        Tuple[bool, str, Optional[str]]: Success status, message, and configuration content
    """
    return generate_startup_script(server_type, app_dir, script_dir, script_data)


def generate_systemd_configuration(server_type: str, app_dir: str, script_dir: str,
                                 output_dir: Optional[str] = None,
                                 script_data: Optional[Dict[str, Any]] = None) -> Tuple[bool, str, Optional[str]]:
    """
    Generate a systemd configuration.
    
    Args:
        server_type: Server type (gunicorn, uwsgi, nginx, apache)
        app_dir: Application directory
        script_dir: Script directory
        output_dir: Output directory
        script_data: Script data
        
    Returns:
        Tuple[bool, str, Optional[str]]: Success status, message, and configuration content
    """
    return generate_systemd_service(server_type, app_dir, script_dir, output_dir, script_data)


def get_server_performance_config(server_type: str) -> Dict[str, Any]:
    """
    Get the performance configuration for a server type.
    
    Args:
        server_type: Server type (gunicorn, uwsgi, nginx, apache)
        
    Returns:
        Dict[str, Any]: Performance configuration
    """
    return get_performance_config(server_type)


def optimize_server_performance(server_type: str, optimization_type: str) -> Dict[str, Any]:
    """
    Optimize the performance configuration for a server type.
    
    Args:
        server_type: Server type (gunicorn, uwsgi, nginx, apache)
        optimization_type: Optimization type (cpu, io, memory, traffic)
        
    Returns:
        Dict[str, Any]: Optimized performance configuration
    """
    return optimize_performance(server_type, optimization_type)


def get_server_security_config(server_type: str) -> Dict[str, Any]:
    """
    Get the security configuration for a server type.
    
    Args:
        server_type: Server type (gunicorn, uwsgi, nginx, apache)
        
    Returns:
        Dict[str, Any]: Security configuration
    """
    return get_security_config(server_type)


def apply_server_security_config(server_type: str, config_dict: Dict[str, Any],
                               security_options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Apply security configuration to a configuration dictionary.
    
    Args:
        server_type: Server type (gunicorn, uwsgi, nginx, apache)
        config_dict: Configuration dictionary
        security_options: Security options
        
    Returns:
        Dict[str, Any]: Updated configuration dictionary
    """
    return apply_security_config(server_type, config_dict, security_options)


def validate_server_configuration(server_type: str, config_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate a server configuration.
    
    Args:
        server_type: Server type (gunicorn, uwsgi, nginx, apache)
        config_data: Configuration data
        
    Returns:
        Tuple[bool, List[str]]: Validation status and list of errors
    """
    return validate_server_config(server_type, config_data)


def generate_complete_server_config(server_type: str, app_dir: str, config_dir: str, script_dir: str,
                                  app_module: str, app_variable: str = 'app',
                                  performance_type: Optional[str] = None,
                                  security_options: Optional[Dict[str, Any]] = None,
                                  additional_config: Optional[Dict[str, Any]] = None) -> Tuple[bool, str, Dict[str, str]]:
    """
    Generate a complete server configuration.
    
    Args:
        server_type: Server type (gunicorn, uwsgi, nginx, apache)
        app_dir: Application directory
        config_dir: Configuration directory
        script_dir: Script directory
        app_module: Application module
        app_variable: Application variable
        performance_type: Performance optimization type (cpu, io, memory, traffic)
        security_options: Security options
        additional_config: Additional configuration data
        
    Returns:
        Tuple[bool, str, Dict[str, str]]: Success status, message, and dictionary of generated files
    """
    try:
        generated_files = {}
        
        # Get the base configuration
        config_data = {}
        
        # Add performance configuration
        if performance_type:
            performance_config = optimize_server_performance(server_type, performance_type)
            config_data.update(performance_config)
        
        # Add additional configuration
        if additional_config:
            config_data.update(additional_config)
        
        # Apply security configuration
        config_data = apply_server_security_config(server_type, config_data, security_options)
        
        # Generate server configuration
        success, message, server_config = generate_server_config(server_type, config_dir, config_data)
        
        if not success:
            return False, message, generated_files
        
        generated_files['server_config'] = os.path.join(config_dir, f"{server_type}.conf")
        
        # Generate WSGI/ASGI configuration
        if server_type in ['gunicorn', 'uwsgi']:
            # Generate WSGI file
            wsgi_path = os.path.join(app_dir, 'wsgi.py')
            success, message, wsgi_config = generate_wsgi_file(app_dir, app_module, app_variable, wsgi_path)
            
            if not success:
                return False, message, generated_files
            
            generated_files['wsgi_config'] = wsgi_path
            
            # Generate ASGI file
            asgi_path = os.path.join(app_dir, 'asgi.py')
            success, message, asgi_config = generate_asgi_file(app_dir, app_module, app_variable, asgi_path)
            
            if success:
                generated_files['asgi_config'] = asgi_path
        
        # Generate startup script
        success, message, startup_script = generate_startup_script(server_type, app_dir, script_dir)
        
        if not success:
            return False, message, generated_files
        
        generated_files['startup_script'] = os.path.join(script_dir, f"start_{server_type}.sh")
        
        # Generate systemd service
        success, message, systemd_service = generate_systemd_service(server_type, app_dir, script_dir)
        
        if success:
            generated_files['systemd_service'] = os.path.join(script_dir, f"pythonweb-{server_type}.service")
        
        return True, "Generated complete server configuration", generated_files
    
    except Exception as e:
        logger.error(f"Failed to generate complete server configuration: {str(e)}")
        return False, f"Failed to generate complete server configuration: {str(e)}", {}
