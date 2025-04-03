"""
Web server security configuration functionality.
"""
import os
import logging
from typing import Dict, Any, List, Tuple, Optional, Union

logger = logging.getLogger(__name__)


class SecurityConfig:
    """
    Web server security configuration.
    """
    
    def __init__(self, server_type: str):
        """
        Initialize the security configuration.
        
        Args:
            server_type: Server type (gunicorn, uwsgi, nginx, apache)
        """
        self.server_type = server_type.lower()
        self.config_data = {}
        
        # Set default configuration values
        self._set_defaults()
    
    def _set_defaults(self) -> None:
        """
        Set default configuration values.
        """
        # Common security defaults
        self.config_data = {
            # SSL/TLS Configuration
            'ssl_enabled': False,
            'ssl_cert': None,
            'ssl_key': None,
            'ssl_protocols': ['TLSv1.2', 'TLSv1.3'],
            'ssl_ciphers': 'ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305:DHE-RSA-AES128-GCM-SHA256:DHE-RSA-AES256-GCM-SHA384',
            'ssl_prefer_server_ciphers': True,
            'ssl_session_timeout': '1d',
            'ssl_session_cache': 'shared:SSL:50m',
            'ssl_session_tickets': False,
            'ssl_stapling': True,
            'ssl_stapling_verify': True,
            
            # HTTP Security Headers
            'security_headers': True,
            'x_content_type_options': 'nosniff',
            'x_frame_options': 'SAMEORIGIN',
            'x_xss_protection': '1; mode=block',
            'content_security_policy': "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self'; connect-src 'self'",
            'referrer_policy': 'strict-origin-when-cross-origin',
            'strict_transport_security': 'max-age=31536000; includeSubDomains',
            'permissions_policy': 'camera=(), microphone=(), geolocation=()',
            
            # CORS Configuration
            'cors_enabled': False,
            'cors_allow_origins': ['*'],
            'cors_allow_methods': ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
            'cors_allow_headers': ['Content-Type', 'Authorization'],
            'cors_allow_credentials': False,
            'cors_expose_headers': [],
            'cors_max_age': 86400,
            
            # Rate Limiting
            'rate_limiting_enabled': False,
            'rate_limit_requests': 100,
            'rate_limit_period': 60,
            'rate_limit_burst': 200,
            
            # IP Filtering
            'ip_filtering_enabled': False,
            'allowed_ips': [],
            'denied_ips': [],
            
            # Authentication
            'basic_auth_enabled': False,
            'basic_auth_users': {},
            
            # CSRF Protection
            'csrf_protection': True,
            
            # Cookie Security
            'secure_cookies': True,
            'http_only_cookies': True,
            'same_site_cookies': 'Lax'
        }
        
        # Server-specific defaults
        if self.server_type == 'nginx':
            self.config_data.update({
                'server_tokens': 'off',
                'add_header': {
                    'X-Content-Type-Options': 'nosniff',
                    'X-Frame-Options': 'SAMEORIGIN',
                    'X-XSS-Protection': '1; mode=block',
                    'Content-Security-Policy': "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self'; connect-src 'self'",
                    'Referrer-Policy': 'strict-origin-when-cross-origin',
                    'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
                    'Permissions-Policy': 'camera=(), microphone=(), geolocation=()'
                },
                'limit_conn_zone': '$binary_remote_addr zone=addr:10m',
                'limit_conn': 'addr 10',
                'limit_req_zone': '$binary_remote_addr zone=req_limit:10m rate=10r/s',
                'limit_req': 'zone=req_limit burst=20 nodelay'
            })
        
        elif self.server_type == 'apache':
            self.config_data.update({
                'server_tokens': 'Prod',
                'trace_enable': 'off',
                'server_signature': 'off',
                'headers': [
                    'always set X-Content-Type-Options "nosniff"',
                    'always set X-Frame-Options "SAMEORIGIN"',
                    'always set X-XSS-Protection "1; mode=block"',
                    'always set Content-Security-Policy "default-src \'self\'; script-src \'self\' \'unsafe-inline\' \'unsafe-eval\'; style-src \'self\' \'unsafe-inline\'; img-src \'self\' data:; font-src \'self\'; connect-src \'self\'"',
                    'always set Referrer-Policy "strict-origin-when-cross-origin"',
                    'always set Strict-Transport-Security "max-age=31536000; includeSubDomains"',
                    'always set Permissions-Policy "camera=(), microphone=(), geolocation=()"'
                ],
                'mod_security_enabled': False,
                'mod_evasive_enabled': False
            })
    
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
    
    def get_security_config(self) -> Dict[str, Any]:
        """
        Get the security configuration.
        
        Returns:
            Dict[str, Any]: Security configuration
        """
        return self.config_data
    
    def enable_ssl(self, cert_path: str, key_path: str) -> None:
        """
        Enable SSL/TLS.
        
        Args:
            cert_path: SSL certificate path
            key_path: SSL key path
        """
        self.config_data.update({
            'ssl_enabled': True,
            'ssl_cert': cert_path,
            'ssl_key': key_path
        })
    
    def enable_cors(self, origins: Optional[List[str]] = None) -> None:
        """
        Enable CORS.
        
        Args:
            origins: Allowed origins
        """
        self.config_data.update({
            'cors_enabled': True,
            'cors_allow_origins': origins or ['*']
        })
    
    def enable_rate_limiting(self, requests: int = 100, period: int = 60, burst: int = 200) -> None:
        """
        Enable rate limiting.
        
        Args:
            requests: Number of requests
            period: Time period in seconds
            burst: Burst size
        """
        self.config_data.update({
            'rate_limiting_enabled': True,
            'rate_limit_requests': requests,
            'rate_limit_period': period,
            'rate_limit_burst': burst
        })
    
    def enable_ip_filtering(self, allowed_ips: Optional[List[str]] = None, 
                           denied_ips: Optional[List[str]] = None) -> None:
        """
        Enable IP filtering.
        
        Args:
            allowed_ips: Allowed IP addresses
            denied_ips: Denied IP addresses
        """
        self.config_data.update({
            'ip_filtering_enabled': True,
            'allowed_ips': allowed_ips or [],
            'denied_ips': denied_ips or []
        })
    
    def enable_basic_auth(self, users: Dict[str, str]) -> None:
        """
        Enable basic authentication.
        
        Args:
            users: Dictionary of username to password
        """
        self.config_data.update({
            'basic_auth_enabled': True,
            'basic_auth_users': users
        })
    
    def apply_security_headers(self, config_dict: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply security headers to a configuration dictionary.
        
        Args:
            config_dict: Configuration dictionary
            
        Returns:
            Dict[str, Any]: Updated configuration dictionary
        """
        if not self.config_data.get('security_headers', True):
            return config_dict
        
        # Apply security headers based on server type
        if self.server_type == 'nginx':
            headers = {}
            
            if self.config_data.get('x_content_type_options'):
                headers['X-Content-Type-Options'] = self.config_data['x_content_type_options']
            
            if self.config_data.get('x_frame_options'):
                headers['X-Frame-Options'] = self.config_data['x_frame_options']
            
            if self.config_data.get('x_xss_protection'):
                headers['X-XSS-Protection'] = self.config_data['x_xss_protection']
            
            if self.config_data.get('content_security_policy'):
                headers['Content-Security-Policy'] = self.config_data['content_security_policy']
            
            if self.config_data.get('referrer_policy'):
                headers['Referrer-Policy'] = self.config_data['referrer_policy']
            
            if self.config_data.get('strict_transport_security') and self.config_data.get('ssl_enabled'):
                headers['Strict-Transport-Security'] = self.config_data['strict_transport_security']
            
            if self.config_data.get('permissions_policy'):
                headers['Permissions-Policy'] = self.config_data['permissions_policy']
            
            config_dict['add_header'] = headers
            config_dict['server_tokens'] = 'off'
        
        elif self.server_type == 'apache':
            headers = []
            
            if self.config_data.get('x_content_type_options'):
                headers.append(f'always set X-Content-Type-Options "{self.config_data["x_content_type_options"]}"')
            
            if self.config_data.get('x_frame_options'):
                headers.append(f'always set X-Frame-Options "{self.config_data["x_frame_options"]}"')
            
            if self.config_data.get('x_xss_protection'):
                headers.append(f'always set X-XSS-Protection "{self.config_data["x_xss_protection"]}"')
            
            if self.config_data.get('content_security_policy'):
                headers.append(f'always set Content-Security-Policy "{self.config_data["content_security_policy"]}"')
            
            if self.config_data.get('referrer_policy'):
                headers.append(f'always set Referrer-Policy "{self.config_data["referrer_policy"]}"')
            
            if self.config_data.get('strict_transport_security') and self.config_data.get('ssl_enabled'):
                headers.append(f'always set Strict-Transport-Security "{self.config_data["strict_transport_security"]}"')
            
            if self.config_data.get('permissions_policy'):
                headers.append(f'always set Permissions-Policy "{self.config_data["permissions_policy"]}"')
            
            config_dict['headers'] = headers
            config_dict['server_tokens'] = 'Prod'
            config_dict['server_signature'] = 'off'
            config_dict['trace_enable'] = 'off'
        
        return config_dict
    
    def apply_cors_config(self, config_dict: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply CORS configuration to a configuration dictionary.
        
        Args:
            config_dict: Configuration dictionary
            
        Returns:
            Dict[str, Any]: Updated configuration dictionary
        """
        if not self.config_data.get('cors_enabled', False):
            return config_dict
        
        # Apply CORS configuration based on server type
        if self.server_type == 'nginx':
            if 'add_header' not in config_dict:
                config_dict['add_header'] = {}
            
            origins = ','.join(self.config_data.get('cors_allow_origins', ['*']))
            methods = ','.join(self.config_data.get('cors_allow_methods', ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS']))
            headers = ','.join(self.config_data.get('cors_allow_headers', ['Content-Type', 'Authorization']))
            expose_headers = ','.join(self.config_data.get('cors_expose_headers', []))
            
            config_dict['add_header']['Access-Control-Allow-Origin'] = origins
            config_dict['add_header']['Access-Control-Allow-Methods'] = methods
            config_dict['add_header']['Access-Control-Allow-Headers'] = headers
            
            if expose_headers:
                config_dict['add_header']['Access-Control-Expose-Headers'] = expose_headers
            
            if self.config_data.get('cors_allow_credentials', False):
                config_dict['add_header']['Access-Control-Allow-Credentials'] = 'true'
            
            if self.config_data.get('cors_max_age'):
                config_dict['add_header']['Access-Control-Max-Age'] = str(self.config_data['cors_max_age'])
        
        elif self.server_type == 'apache':
            if 'headers' not in config_dict:
                config_dict['headers'] = []
            
            origins = ' '.join(self.config_data.get('cors_allow_origins', ['*']))
            methods = ' '.join(self.config_data.get('cors_allow_methods', ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS']))
            headers = ' '.join(self.config_data.get('cors_allow_headers', ['Content-Type', 'Authorization']))
            expose_headers = ' '.join(self.config_data.get('cors_expose_headers', []))
            
            config_dict['headers'].append(f'always set Access-Control-Allow-Origin "{origins}"')
            config_dict['headers'].append(f'always set Access-Control-Allow-Methods "{methods}"')
            config_dict['headers'].append(f'always set Access-Control-Allow-Headers "{headers}"')
            
            if expose_headers:
                config_dict['headers'].append(f'always set Access-Control-Expose-Headers "{expose_headers}"')
            
            if self.config_data.get('cors_allow_credentials', False):
                config_dict['headers'].append('always set Access-Control-Allow-Credentials "true"')
            
            if self.config_data.get('cors_max_age'):
                config_dict['headers'].append(f'always set Access-Control-Max-Age "{self.config_data["cors_max_age"]}"')
        
        return config_dict
    
    def apply_rate_limiting(self, config_dict: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply rate limiting configuration to a configuration dictionary.
        
        Args:
            config_dict: Configuration dictionary
            
        Returns:
            Dict[str, Any]: Updated configuration dictionary
        """
        if not self.config_data.get('rate_limiting_enabled', False):
            return config_dict
        
        # Apply rate limiting configuration based on server type
        if self.server_type == 'nginx':
            requests = self.config_data.get('rate_limit_requests', 100)
            period = self.config_data.get('rate_limit_period', 60)
            burst = self.config_data.get('rate_limit_burst', 200)
            
            rate = f"{requests}r/{period}s"
            
            config_dict['limit_req_zone'] = f'$binary_remote_addr zone=req_limit:10m rate={rate}'
            config_dict['limit_req'] = f'zone=req_limit burst={burst} nodelay'
        
        elif self.server_type == 'apache':
            # For Apache, we need mod_ratelimit or mod_qos
            config_dict['mod_ratelimit_enabled'] = True
            
            requests = self.config_data.get('rate_limit_requests', 100)
            period = self.config_data.get('rate_limit_period', 60)
            
            # Convert to requests per second
            rate = requests / period
            
            config_dict['rate_limit'] = f'{rate}/s'
        
        return config_dict
    
    def apply_ip_filtering(self, config_dict: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply IP filtering configuration to a configuration dictionary.
        
        Args:
            config_dict: Configuration dictionary
            
        Returns:
            Dict[str, Any]: Updated configuration dictionary
        """
        if not self.config_data.get('ip_filtering_enabled', False):
            return config_dict
        
        allowed_ips = self.config_data.get('allowed_ips', [])
        denied_ips = self.config_data.get('denied_ips', [])
        
        # Apply IP filtering configuration based on server type
        if self.server_type == 'nginx':
            if allowed_ips:
                allow_rules = []
                for ip in allowed_ips:
                    allow_rules.append(f'allow {ip};')
                
                # Deny all other IPs
                allow_rules.append('deny all;')
                
                config_dict['allow_deny_rules'] = allow_rules
            
            elif denied_ips:
                deny_rules = []
                for ip in denied_ips:
                    deny_rules.append(f'deny {ip};')
                
                # Allow all other IPs
                deny_rules.append('allow all;')
                
                config_dict['allow_deny_rules'] = deny_rules
        
        elif self.server_type == 'apache':
            if allowed_ips:
                allow_rules = ['Order deny,allow', 'Deny from all']
                for ip in allowed_ips:
                    allow_rules.append(f'Allow from {ip}')
                
                config_dict['ip_allow_deny_rules'] = allow_rules
            
            elif denied_ips:
                deny_rules = ['Order allow,deny', 'Allow from all']
                for ip in denied_ips:
                    deny_rules.append(f'Deny from {ip}')
                
                config_dict['ip_allow_deny_rules'] = deny_rules
        
        return config_dict
    
    def apply_basic_auth(self, config_dict: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply basic authentication configuration to a configuration dictionary.
        
        Args:
            config_dict: Configuration dictionary
            
        Returns:
            Dict[str, Any]: Updated configuration dictionary
        """
        if not self.config_data.get('basic_auth_enabled', False):
            return config_dict
        
        users = self.config_data.get('basic_auth_users', {})
        
        if not users:
            return config_dict
        
        # Apply basic authentication configuration based on server type
        if self.server_type == 'nginx':
            config_dict['auth_basic'] = '"Restricted Area"'
            config_dict['auth_basic_user_file'] = '/etc/nginx/.htpasswd'
            config_dict['htpasswd_users'] = users
        
        elif self.server_type == 'apache':
            config_dict['auth_type'] = 'Basic'
            config_dict['auth_name'] = '"Restricted Area"'
            config_dict['auth_basic_provider'] = 'file'
            config_dict['auth_user_file'] = '/etc/apache2/.htpasswd'
            config_dict['require'] = 'valid-user'
            config_dict['htpasswd_users'] = users
        
        return config_dict
    
    def apply_ssl_config(self, config_dict: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply SSL/TLS configuration to a configuration dictionary.
        
        Args:
            config_dict: Configuration dictionary
            
        Returns:
            Dict[str, Any]: Updated configuration dictionary
        """
        if not self.config_data.get('ssl_enabled', False):
            return config_dict
        
        cert_path = self.config_data.get('ssl_cert')
        key_path = self.config_data.get('ssl_key')
        
        if not cert_path or not key_path:
            return config_dict
        
        # Apply SSL/TLS configuration based on server type
        if self.server_type == 'nginx':
            config_dict['ssl'] = 'on'
            config_dict['ssl_certificate'] = cert_path
            config_dict['ssl_certificate_key'] = key_path
            config_dict['ssl_protocols'] = ' '.join(self.config_data.get('ssl_protocols', ['TLSv1.2', 'TLSv1.3']))
            config_dict['ssl_ciphers'] = self.config_data.get('ssl_ciphers', 'HIGH:!aNULL:!MD5')
            config_dict['ssl_prefer_server_ciphers'] = 'on' if self.config_data.get('ssl_prefer_server_ciphers', True) else 'off'
            config_dict['ssl_session_timeout'] = self.config_data.get('ssl_session_timeout', '1d')
            config_dict['ssl_session_cache'] = self.config_data.get('ssl_session_cache', 'shared:SSL:50m')
            config_dict['ssl_session_tickets'] = 'on' if self.config_data.get('ssl_session_tickets', False) else 'off'
            
            if self.config_data.get('ssl_stapling', True):
                config_dict['ssl_stapling'] = 'on'
                config_dict['ssl_stapling_verify'] = 'on' if self.config_data.get('ssl_stapling_verify', True) else 'off'
        
        elif self.server_type == 'apache':
            config_dict['ssl_engine'] = 'on'
            config_dict['ssl_certificate_file'] = cert_path
            config_dict['ssl_certificate_key_file'] = key_path
            config_dict['ssl_protocols'] = ' '.join(self.config_data.get('ssl_protocols', ['TLSv1.2', 'TLSv1.3']))
            config_dict['ssl_cipher_suite'] = self.config_data.get('ssl_ciphers', 'HIGH:!aNULL:!MD5')
            config_dict['ssl_honor_cipher_order'] = 'on' if self.config_data.get('ssl_prefer_server_ciphers', True) else 'off'
            config_dict['ssl_session_timeout'] = self.config_data.get('ssl_session_timeout', '300')
            config_dict['ssl_session_cache'] = 'shmcb:/var/run/apache2/ssl_scache(512000)'
            
            # Enable OCSP Stapling
            if self.config_data.get('ssl_stapling', True):
                config_dict['ssl_use_stapling'] = 'on'
                config_dict['ssl_stapling_verify'] = 'on' if self.config_data.get('ssl_stapling_verify', True) else 'off'
                config_dict['ssl_stapling_cache'] = 'shmcb:/var/run/apache2/ssl_stapling(32768)'
        
        return config_dict
    
    def apply_all_security_configs(self, config_dict: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply all security configurations to a configuration dictionary.
        
        Args:
            config_dict: Configuration dictionary
            
        Returns:
            Dict[str, Any]: Updated configuration dictionary
        """
        # Apply security headers
        config_dict = self.apply_security_headers(config_dict)
        
        # Apply CORS configuration
        config_dict = self.apply_cors_config(config_dict)
        
        # Apply rate limiting
        config_dict = self.apply_rate_limiting(config_dict)
        
        # Apply IP filtering
        config_dict = self.apply_ip_filtering(config_dict)
        
        # Apply basic authentication
        config_dict = self.apply_basic_auth(config_dict)
        
        # Apply SSL/TLS configuration
        config_dict = self.apply_ssl_config(config_dict)
        
        return config_dict


def create_security_config(server_type: str) -> SecurityConfig:
    """
    Create a security configuration.
    
    Args:
        server_type: Server type (gunicorn, uwsgi, nginx, apache)
        
    Returns:
        SecurityConfig: Security configuration
    """
    return SecurityConfig(server_type)


def get_security_config(server_type: str) -> Dict[str, Any]:
    """
    Get the security configuration for a server type.
    
    Args:
        server_type: Server type (gunicorn, uwsgi, nginx, apache)
        
    Returns:
        Dict[str, Any]: Security configuration
    """
    try:
        # Create a security configuration
        security_config = create_security_config(server_type)
        
        # Get the security configuration
        return security_config.get_security_config()
    
    except Exception as e:
        logger.error(f"Failed to get security configuration for {server_type}: {str(e)}")
        return {}


def apply_security_config(server_type: str, config_dict: Dict[str, Any],
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
    try:
        # Create a security configuration
        security_config = create_security_config(server_type)
        
        # Update the security configuration
        if security_options:
            security_config.update_config(security_options)
        
        # Apply all security configurations
        return security_config.apply_all_security_configs(config_dict)
    
    except Exception as e:
        logger.error(f"Failed to apply security configuration for {server_type}: {str(e)}")
        return config_dict
