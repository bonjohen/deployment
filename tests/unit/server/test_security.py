"""
Unit tests for server security configuration functionality.
"""
from unittest.mock import patch, MagicMock

import pytest

from pythonweb_installer.server.security import (
    SecurityConfig,
    create_security_config,
    get_security_config,
    apply_security_config
)


class TestSecurityConfig:
    """Tests for security configuration functionality."""

    @pytest.fixture
    def security_config_nginx(self):
        """Create a Nginx security configuration."""
        return SecurityConfig('nginx')

    @pytest.fixture
    def security_config_apache(self):
        """Create an Apache security configuration."""
        return SecurityConfig('apache')

    def test_create_security_config(self):
        """Test creating a security configuration."""
        # Create a security configuration
        security_config = create_security_config('nginx')

        assert security_config is not None
        assert isinstance(security_config, SecurityConfig)
        assert security_config.server_type == 'nginx'

    def test_set_config(self, security_config_nginx):
        """Test setting a configuration value."""
        # Set a configuration value
        security_config_nginx.set_config('ssl_enabled', True)

        assert security_config_nginx.get_config('ssl_enabled') is True

    def test_get_config(self, security_config_nginx):
        """Test getting a configuration value."""
        # Get a configuration value
        ssl_enabled = security_config_nginx.get_config('ssl_enabled')

        assert ssl_enabled is False

    def test_get_config_default(self, security_config_nginx):
        """Test getting a configuration value with a default."""
        # Get a configuration value with a default
        value = security_config_nginx.get_config('nonexistent', 'default')

        assert value == 'default'

    def test_update_config(self, security_config_nginx):
        """Test updating configuration values."""
        # Update configuration values
        security_config_nginx.update_config({
            'ssl_enabled': True,
            'ssl_cert': 'cert.pem',
            'ssl_key': 'key.pem'
        })

        assert security_config_nginx.get_config('ssl_enabled') is True
        assert security_config_nginx.get_config('ssl_cert') == 'cert.pem'
        assert security_config_nginx.get_config('ssl_key') == 'key.pem'

    def test_get_security_config(self, security_config_nginx):
        """Test getting the security configuration."""
        # Get the security configuration
        config = security_config_nginx.get_security_config()

        assert config is not None
        assert isinstance(config, dict)
        assert 'ssl_enabled' in config
        assert 'security_headers' in config
        assert 'cors_enabled' in config

    def test_enable_ssl(self, security_config_nginx):
        """Test enabling SSL/TLS."""
        # Enable SSL/TLS
        security_config_nginx.enable_ssl('cert.pem', 'key.pem')

        assert security_config_nginx.get_config('ssl_enabled') is True
        assert security_config_nginx.get_config('ssl_cert') == 'cert.pem'
        assert security_config_nginx.get_config('ssl_key') == 'key.pem'

    def test_enable_cors(self, security_config_nginx):
        """Test enabling CORS."""
        # Enable CORS
        security_config_nginx.enable_cors(['example.com'])

        assert security_config_nginx.get_config('cors_enabled') is True
        assert security_config_nginx.get_config('cors_allow_origins') == ['example.com']

    def test_enable_cors_default(self, security_config_nginx):
        """Test enabling CORS with default origins."""
        # Enable CORS with default origins
        security_config_nginx.enable_cors()

        assert security_config_nginx.get_config('cors_enabled') is True
        assert security_config_nginx.get_config('cors_allow_origins') == ['*']

    def test_enable_rate_limiting(self, security_config_nginx):
        """Test enabling rate limiting."""
        # Enable rate limiting
        security_config_nginx.enable_rate_limiting(200, 120, 400)

        assert security_config_nginx.get_config('rate_limiting_enabled') is True
        assert security_config_nginx.get_config('rate_limit_requests') == 200
        assert security_config_nginx.get_config('rate_limit_period') == 120
        assert security_config_nginx.get_config('rate_limit_burst') == 400

    def test_enable_rate_limiting_default(self, security_config_nginx):
        """Test enabling rate limiting with default values."""
        # Enable rate limiting with default values
        security_config_nginx.enable_rate_limiting()

        assert security_config_nginx.get_config('rate_limiting_enabled') is True
        assert security_config_nginx.get_config('rate_limit_requests') == 100
        assert security_config_nginx.get_config('rate_limit_period') == 60
        assert security_config_nginx.get_config('rate_limit_burst') == 200

    def test_enable_ip_filtering(self, security_config_nginx):
        """Test enabling IP filtering."""
        # Enable IP filtering
        security_config_nginx.enable_ip_filtering(['192.168.1.1'], ['10.0.0.1'])

        assert security_config_nginx.get_config('ip_filtering_enabled') is True
        assert security_config_nginx.get_config('allowed_ips') == ['192.168.1.1']
        assert security_config_nginx.get_config('denied_ips') == ['10.0.0.1']

    def test_enable_ip_filtering_default(self, security_config_nginx):
        """Test enabling IP filtering with default values."""
        # Enable IP filtering with default values
        security_config_nginx.enable_ip_filtering()

        assert security_config_nginx.get_config('ip_filtering_enabled') is True
        assert security_config_nginx.get_config('allowed_ips') == []
        assert security_config_nginx.get_config('denied_ips') == []

    def test_enable_basic_auth(self, security_config_nginx):
        """Test enabling basic authentication."""
        # Enable basic authentication
        security_config_nginx.enable_basic_auth({'user': 'password'})

        assert security_config_nginx.get_config('basic_auth_enabled') is True
        assert security_config_nginx.get_config('basic_auth_users') == {'user': 'password'}

    def test_apply_security_headers_nginx(self, security_config_nginx):
        """Test applying security headers to a Nginx configuration."""
        # Enable SSL to include HSTS header
        security_config_nginx.enable_ssl('cert.pem', 'key.pem')

        # Apply security headers
        config_dict = {}
        result = security_config_nginx.apply_security_headers(config_dict)

        assert result is not None
        assert isinstance(result, dict)
        assert 'add_header' in result
        assert 'server_tokens' in result
        assert result['server_tokens'] == 'off'

        # Check the headers
        headers = result['add_header']
        assert 'X-Content-Type-Options' in headers
        assert 'X-Frame-Options' in headers
        assert 'X-XSS-Protection' in headers
        assert 'Content-Security-Policy' in headers
        assert 'Referrer-Policy' in headers
        assert 'Strict-Transport-Security' in headers
        assert 'Permissions-Policy' in headers

    def test_apply_security_headers_apache(self, security_config_apache):
        """Test applying security headers to an Apache configuration."""
        # Enable SSL to include HSTS header
        security_config_apache.enable_ssl('cert.pem', 'key.pem')

        # Apply security headers
        config_dict = {}
        result = security_config_apache.apply_security_headers(config_dict)

        assert result is not None
        assert isinstance(result, dict)
        assert 'headers' in result
        assert 'server_tokens' in result
        assert 'server_signature' in result
        assert 'trace_enable' in result
        assert result['server_tokens'] == 'Prod'
        assert result['server_signature'] == 'off'
        assert result['trace_enable'] == 'off'

        # Check the headers
        headers = result['headers']
        assert len(headers) > 0
        assert any('X-Content-Type-Options' in header for header in headers)
        assert any('X-Frame-Options' in header for header in headers)
        assert any('X-XSS-Protection' in header for header in headers)
        assert any('Content-Security-Policy' in header for header in headers)
        assert any('Referrer-Policy' in header for header in headers)
        assert any('Strict-Transport-Security' in header for header in headers)
        assert any('Permissions-Policy' in header for header in headers)

    def test_apply_security_headers_disabled(self, security_config_nginx):
        """Test applying security headers when disabled."""
        # Disable security headers
        security_config_nginx.set_config('security_headers', False)

        # Apply security headers
        config_dict = {}
        result = security_config_nginx.apply_security_headers(config_dict)

        assert result is not None
        assert isinstance(result, dict)
        assert 'add_header' not in result

    def test_apply_cors_config_nginx(self, security_config_nginx):
        """Test applying CORS configuration to a Nginx configuration."""
        # Enable CORS
        security_config_nginx.enable_cors(['example.com'])

        # Apply CORS configuration
        config_dict = {}
        result = security_config_nginx.apply_cors_config(config_dict)

        assert result is not None
        assert isinstance(result, dict)
        assert 'add_header' in result

        # Check the headers
        headers = result['add_header']
        assert 'Access-Control-Allow-Origin' in headers
        assert 'Access-Control-Allow-Methods' in headers
        assert 'Access-Control-Allow-Headers' in headers
        assert headers['Access-Control-Allow-Origin'] == 'example.com'

    def test_apply_cors_config_apache(self, security_config_apache):
        """Test applying CORS configuration to an Apache configuration."""
        # Enable CORS
        security_config_apache.enable_cors(['example.com'])

        # Apply CORS configuration
        config_dict = {}
        result = security_config_apache.apply_cors_config(config_dict)

        assert result is not None
        assert isinstance(result, dict)
        assert 'headers' in result

        # Check the headers
        headers = result['headers']
        assert len(headers) > 0
        assert any('Access-Control-Allow-Origin' in header for header in headers)
        assert any('Access-Control-Allow-Methods' in header for header in headers)
        assert any('Access-Control-Allow-Headers' in header for header in headers)

    def test_apply_cors_config_disabled(self, security_config_nginx):
        """Test applying CORS configuration when disabled."""
        # Apply CORS configuration (disabled by default)
        config_dict = {}
        result = security_config_nginx.apply_cors_config(config_dict)

        assert result is not None
        assert isinstance(result, dict)
        assert 'add_header' not in result

    def test_apply_rate_limiting_nginx(self, security_config_nginx):
        """Test applying rate limiting to a Nginx configuration."""
        # Enable rate limiting
        security_config_nginx.enable_rate_limiting()

        # Apply rate limiting
        config_dict = {}
        result = security_config_nginx.apply_rate_limiting(config_dict)

        assert result is not None
        assert isinstance(result, dict)
        assert 'limit_req_zone' in result
        assert 'limit_req' in result

    def test_apply_rate_limiting_apache(self, security_config_apache):
        """Test applying rate limiting to an Apache configuration."""
        # Enable rate limiting
        security_config_apache.enable_rate_limiting()

        # Apply rate limiting
        config_dict = {}
        result = security_config_apache.apply_rate_limiting(config_dict)

        assert result is not None
        assert isinstance(result, dict)
        assert 'mod_ratelimit_enabled' in result
        assert 'rate_limit' in result

    def test_apply_rate_limiting_disabled(self, security_config_nginx):
        """Test applying rate limiting when disabled."""
        # Apply rate limiting (disabled by default)
        config_dict = {}
        result = security_config_nginx.apply_rate_limiting(config_dict)

        assert result is not None
        assert isinstance(result, dict)
        assert 'limit_req_zone' not in result
        assert 'limit_req' not in result

    def test_apply_ip_filtering_nginx(self, security_config_nginx):
        """Test applying IP filtering to a Nginx configuration."""
        # Enable IP filtering with allowed IPs
        security_config_nginx.enable_ip_filtering(['192.168.1.1'])

        # Apply IP filtering
        config_dict = {}
        result = security_config_nginx.apply_ip_filtering(config_dict)

        assert result is not None
        assert isinstance(result, dict)
        assert 'allow_deny_rules' in result

        # Check the rules
        rules = result['allow_deny_rules']
        assert len(rules) > 0
        assert any('allow 192.168.1.1' in rule for rule in rules)
        assert any('deny all' in rule for rule in rules)

    def test_apply_ip_filtering_nginx_denied(self, security_config_nginx):
        """Test applying IP filtering to a Nginx configuration with denied IPs."""
        # Enable IP filtering with denied IPs
        security_config_nginx.enable_ip_filtering(None, ['10.0.0.1'])

        # Apply IP filtering
        config_dict = {}
        result = security_config_nginx.apply_ip_filtering(config_dict)

        assert result is not None
        assert isinstance(result, dict)
        assert 'allow_deny_rules' in result

        # Check the rules
        rules = result['allow_deny_rules']
        assert len(rules) > 0
        assert any('deny 10.0.0.1' in rule for rule in rules)
        assert any('allow all' in rule for rule in rules)

    def test_apply_ip_filtering_apache(self, security_config_apache):
        """Test applying IP filtering to an Apache configuration."""
        # Enable IP filtering with allowed IPs
        security_config_apache.enable_ip_filtering(['192.168.1.1'])

        # Apply IP filtering
        config_dict = {}
        result = security_config_apache.apply_ip_filtering(config_dict)

        assert result is not None
        assert isinstance(result, dict)
        assert 'ip_allow_deny_rules' in result

        # Check the rules
        rules = result['ip_allow_deny_rules']
        assert len(rules) > 0
        assert 'Order deny,allow' in rules
        assert 'Deny from all' in rules
        assert 'Allow from 192.168.1.1' in rules

    def test_apply_ip_filtering_apache_denied(self, security_config_apache):
        """Test applying IP filtering to an Apache configuration with denied IPs."""
        # Enable IP filtering with denied IPs
        security_config_apache.enable_ip_filtering(None, ['10.0.0.1'])

        # Apply IP filtering
        config_dict = {}
        result = security_config_apache.apply_ip_filtering(config_dict)

        assert result is not None
        assert isinstance(result, dict)
        assert 'ip_allow_deny_rules' in result

        # Check the rules
        rules = result['ip_allow_deny_rules']
        assert len(rules) > 0
        assert 'Order allow,deny' in rules
        assert 'Allow from all' in rules
        assert 'Deny from 10.0.0.1' in rules

    def test_apply_ip_filtering_disabled(self, security_config_nginx):
        """Test applying IP filtering when disabled."""
        # Apply IP filtering (disabled by default)
        config_dict = {}
        result = security_config_nginx.apply_ip_filtering(config_dict)

        assert result is not None
        assert isinstance(result, dict)
        assert 'allow_deny_rules' not in result

    def test_apply_basic_auth_nginx(self, security_config_nginx):
        """Test applying basic authentication to a Nginx configuration."""
        # Enable basic authentication
        security_config_nginx.enable_basic_auth({'user': 'password'})

        # Apply basic authentication
        config_dict = {}
        result = security_config_nginx.apply_basic_auth(config_dict)

        assert result is not None
        assert isinstance(result, dict)
        assert 'auth_basic' in result
        assert 'auth_basic_user_file' in result
        assert 'htpasswd_users' in result
        assert result['htpasswd_users'] == {'user': 'password'}

    def test_apply_basic_auth_apache(self, security_config_apache):
        """Test applying basic authentication to an Apache configuration."""
        # Enable basic authentication
        security_config_apache.enable_basic_auth({'user': 'password'})

        # Apply basic authentication
        config_dict = {}
        result = security_config_apache.apply_basic_auth(config_dict)

        assert result is not None
        assert isinstance(result, dict)
        assert 'auth_type' in result
        assert 'auth_name' in result
        assert 'auth_basic_provider' in result
        assert 'auth_user_file' in result
        assert 'require' in result
        assert 'htpasswd_users' in result
        assert result['htpasswd_users'] == {'user': 'password'}

    def test_apply_basic_auth_disabled(self, security_config_nginx):
        """Test applying basic authentication when disabled."""
        # Apply basic authentication (disabled by default)
        config_dict = {}
        result = security_config_nginx.apply_basic_auth(config_dict)

        assert result is not None
        assert isinstance(result, dict)
        assert 'auth_basic' not in result
        assert 'auth_basic_user_file' not in result

    def test_apply_ssl_config_nginx(self, security_config_nginx):
        """Test applying SSL/TLS configuration to a Nginx configuration."""
        # Enable SSL/TLS
        security_config_nginx.enable_ssl('cert.pem', 'key.pem')

        # Apply SSL/TLS configuration
        config_dict = {}
        result = security_config_nginx.apply_ssl_config(config_dict)

        assert result is not None
        assert isinstance(result, dict)
        assert 'ssl' in result
        assert 'ssl_certificate' in result
        assert 'ssl_certificate_key' in result
        assert 'ssl_protocols' in result
        assert 'ssl_ciphers' in result
        assert 'ssl_prefer_server_ciphers' in result
        assert 'ssl_session_timeout' in result
        assert 'ssl_session_cache' in result
        assert 'ssl_session_tickets' in result
        assert 'ssl_stapling' in result
        assert 'ssl_stapling_verify' in result
        assert result['ssl'] == 'on'
        assert result['ssl_certificate'] == 'cert.pem'
        assert result['ssl_certificate_key'] == 'key.pem'

    def test_apply_ssl_config_apache(self, security_config_apache):
        """Test applying SSL/TLS configuration to an Apache configuration."""
        # Enable SSL/TLS
        security_config_apache.enable_ssl('cert.pem', 'key.pem')

        # Apply SSL/TLS configuration
        config_dict = {}
        result = security_config_apache.apply_ssl_config(config_dict)

        assert result is not None
        assert isinstance(result, dict)
        assert 'ssl_engine' in result
        assert 'ssl_certificate_file' in result
        assert 'ssl_certificate_key_file' in result
        assert 'ssl_protocols' in result
        assert 'ssl_cipher_suite' in result
        assert 'ssl_honor_cipher_order' in result
        assert 'ssl_session_timeout' in result
        assert 'ssl_session_cache' in result
        assert 'ssl_use_stapling' in result
        assert 'ssl_stapling_verify' in result
        assert 'ssl_stapling_cache' in result
        assert result['ssl_engine'] == 'on'
        assert result['ssl_certificate_file'] == 'cert.pem'
        assert result['ssl_certificate_key_file'] == 'key.pem'

    def test_apply_ssl_config_disabled(self, security_config_nginx):
        """Test applying SSL/TLS configuration when disabled."""
        # Apply SSL/TLS configuration (disabled by default)
        config_dict = {}
        result = security_config_nginx.apply_ssl_config(config_dict)

        assert result is not None
        assert isinstance(result, dict)
        assert 'ssl' not in result
        assert 'ssl_certificate' not in result
        assert 'ssl_certificate_key' not in result

    def test_apply_ssl_config_no_cert(self, security_config_nginx):
        """Test applying SSL/TLS configuration with no certificate."""
        # Enable SSL/TLS with no certificate
        security_config_nginx.set_config('ssl_enabled', True)

        # Apply SSL/TLS configuration
        config_dict = {}
        result = security_config_nginx.apply_ssl_config(config_dict)

        assert result is not None
        assert isinstance(result, dict)
        assert 'ssl' not in result
        assert 'ssl_certificate' not in result
        assert 'ssl_certificate_key' not in result

    def test_apply_all_security_configs(self, security_config_nginx):
        """Test applying all security configurations."""
        # Enable various security features
        security_config_nginx.enable_ssl('cert.pem', 'key.pem')
        security_config_nginx.enable_cors(['example.com'])
        security_config_nginx.enable_rate_limiting()
        security_config_nginx.enable_ip_filtering(['192.168.1.1'])
        security_config_nginx.enable_basic_auth({'user': 'password'})

        # Apply all security configurations
        config_dict = {}
        result = security_config_nginx.apply_all_security_configs(config_dict)

        assert result is not None
        assert isinstance(result, dict)

        # Check for security headers
        assert 'add_header' in result

        # Check for CORS configuration
        headers = result['add_header']
        assert 'Access-Control-Allow-Origin' in headers

        # Check for rate limiting
        assert 'limit_req_zone' in result
        assert 'limit_req' in result

        # Check for IP filtering
        assert 'allow_deny_rules' in result

        # Check for basic authentication
        assert 'auth_basic' in result
        assert 'auth_basic_user_file' in result

        # Check for SSL/TLS configuration
        assert 'ssl' in result
        assert 'ssl_certificate' in result
        assert 'ssl_certificate_key' in result

    @patch('pythonweb_installer.server.security.create_security_config')
    def test_get_security_config_function(self, mock_create_security_config):
        """Test the get_security_config function."""
        # Mock the create_security_config function
        mock_security_config = MagicMock()
        mock_security_config.get_security_config.return_value = {'ssl_enabled': False}
        mock_create_security_config.return_value = mock_security_config

        # Get the security configuration
        config = get_security_config('nginx')

        assert config is not None
        assert isinstance(config, dict)
        assert 'ssl_enabled' in config
        assert config['ssl_enabled'] is False

        # Check if the create_security_config function was called
        mock_create_security_config.assert_called_once_with('nginx')

        # Check if the get_security_config method was called
        mock_security_config.get_security_config.assert_called_once()

    @patch('pythonweb_installer.server.security.create_security_config')
    def test_get_security_config_function_error(self, mock_create_security_config):
        """Test the get_security_config function with an error."""
        # Mock the create_security_config function to raise an exception
        mock_create_security_config.side_effect = Exception('Test error')

        # Get the security configuration
        config = get_security_config('nginx')

        assert config is not None
        assert isinstance(config, dict)
        assert len(config) == 0

    @patch('pythonweb_installer.server.security.create_security_config')
    def test_apply_security_config_function(self, mock_create_security_config):
        """Test the apply_security_config function."""
        # Mock the create_security_config function
        mock_security_config = MagicMock()
        mock_security_config.apply_all_security_configs.return_value = {'ssl': 'on'}
        mock_create_security_config.return_value = mock_security_config

        # Apply the security configuration
        config_dict = {}
        result = apply_security_config('nginx', config_dict)

        assert result is not None
        assert isinstance(result, dict)
        assert 'ssl' in result
        assert result['ssl'] == 'on'

        # Check if the create_security_config function was called
        mock_create_security_config.assert_called_once_with('nginx')

        # Check if the apply_all_security_configs method was called
        mock_security_config.apply_all_security_configs.assert_called_once_with(config_dict)

    @patch('pythonweb_installer.server.security.create_security_config')
    def test_apply_security_config_function_with_options(self, mock_create_security_config):
        """Test the apply_security_config function with security options."""
        # Mock the create_security_config function
        mock_security_config = MagicMock()
        mock_security_config.apply_all_security_configs.return_value = {'ssl': 'on'}
        mock_create_security_config.return_value = mock_security_config

        # Apply the security configuration with options
        config_dict = {}
        security_options = {'ssl_enabled': True}
        result = apply_security_config('nginx', config_dict, security_options)

        assert result is not None
        assert isinstance(result, dict)
        assert 'ssl' in result
        assert result['ssl'] == 'on'

        # Check if the update_config method was called
        mock_security_config.update_config.assert_called_once_with(security_options)

    @patch('pythonweb_installer.server.security.create_security_config')
    def test_apply_security_config_function_error(self, mock_create_security_config):
        """Test the apply_security_config function with an error."""
        # Mock the create_security_config function to raise an exception
        mock_create_security_config.side_effect = Exception('Test error')

        # Apply the security configuration
        config_dict = {'original': 'value'}
        result = apply_security_config('nginx', config_dict)

        assert result is not None
        assert isinstance(result, dict)
        assert 'original' in result
        assert result['original'] == 'value'
