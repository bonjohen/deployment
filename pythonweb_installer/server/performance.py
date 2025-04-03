"""
Web server performance tuning functionality.
"""
import os
import re
import logging
import platform
from typing import Dict, Any, List, Tuple, Optional, Union

logger = logging.getLogger(__name__)


class PerformanceConfig:
    """
    Web server performance configuration.
    """
    
    def __init__(self, server_type: str):
        """
        Initialize the performance configuration.
        
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
        # Common defaults
        self.config_data = {
            'workers': self._calculate_workers(),
            'threads': 2,
            'timeout': 30,
            'max_requests': 1000,
            'max_requests_jitter': 50,
            'keepalive': 5,
            'backlog': 2048,
            'connection_timeout': 30,
            'worker_connections': 1000,
            'buffer_size': 32768,
            'gzip_enabled': True,
            'gzip_comp_level': 6,
            'gzip_min_length': 1024,
            'gzip_types': [
                'text/plain',
                'text/css',
                'application/json',
                'application/javascript',
                'text/xml',
                'application/xml',
                'application/xml+rss',
                'text/javascript'
            ],
            'cache_enabled': True,
            'cache_time': 3600,
            'cache_dir': 'cache',
            'cache_size': '1g',
            'cache_inactive': '60m',
            'cache_valid': {
                '200': '60m',
                '301': '1h',
                '404': '1m'
            },
            'tcp_nodelay': True,
            'tcp_nopush': True,
            'sendfile': True,
            'keepalive_timeout': 65,
            'client_max_body_size': '10m',
            'client_body_buffer_size': '128k',
            'client_header_buffer_size': '1k',
            'large_client_header_buffers': '4 8k',
            'proxy_buffers': '8 16k',
            'proxy_buffer_size': '32k',
            'proxy_busy_buffers_size': '64k',
            'proxy_temp_file_write_size': '64k',
            'proxy_connect_timeout': 60,
            'proxy_read_timeout': 60,
            'proxy_send_timeout': 60
        }
        
        # Server-specific defaults
        if self.server_type == 'gunicorn':
            self.config_data.update({
                'worker_class': 'sync',
                'threads': 2,
                'max_requests': 1000,
                'max_requests_jitter': 50,
                'keepalive': 5,
                'backlog': 2048,
                'timeout': 30,
                'graceful_timeout': 30,
                'preload_app': True,
                'worker_connections': 1000,
                'limit_request_line': 4094,
                'limit_request_fields': 100,
                'limit_request_field_size': 8190
            })
        
        elif self.server_type == 'uwsgi':
            self.config_data.update({
                'processes': self._calculate_workers(),
                'threads': 2,
                'master': True,
                'vacuum': True,
                'die-on-term': True,
                'harakiri': 30,
                'max-requests': 1000,
                'buffer-size': 32768,
                'post-buffering': 8192,
                'socket-timeout': 30,
                'so-keepalive': True,
                'listen': 100,
                'thunder-lock': True,
                'lazy-apps': True,
                'cheaper': 2,
                'cheaper-algo': 'busyness',
                'cheaper-initial': 2,
                'cheaper-step': 1,
                'cheaper-overload': 5,
                'cheaper-idle': 20,
                'cheaper-busyness-multiplier': 30,
                'cheaper-busyness-min': 20,
                'cheaper-busyness-max': 70,
                'cheaper-busyness-backlog-alert': 16,
                'cheaper-busyness-backlog-step': 2
            })
        
        elif self.server_type == 'nginx':
            self.config_data.update({
                'worker_processes': 'auto',
                'worker_connections': 1024,
                'multi_accept': 'on',
                'use': 'epoll',
                'sendfile': 'on',
                'tcp_nopush': 'on',
                'tcp_nodelay': 'on',
                'keepalive_timeout': 65,
                'keepalive_requests': 100,
                'reset_timedout_connection': 'on',
                'client_body_timeout': 10,
                'client_header_timeout': 10,
                'send_timeout': 10,
                'limit_conn_zone': '$binary_remote_addr zone=addr:10m',
                'limit_conn': 'addr 100',
                'limit_req_zone': '$binary_remote_addr zone=req_limit:10m rate=10r/s',
                'limit_req': 'zone=req_limit burst=20 nodelay',
                'open_file_cache': 'max=1000 inactive=20s',
                'open_file_cache_valid': '30s',
                'open_file_cache_min_uses': 2,
                'open_file_cache_errors': 'on',
                'gzip': 'on',
                'gzip_comp_level': 6,
                'gzip_min_length': 1024,
                'gzip_types': 'text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript',
                'gzip_vary': 'on',
                'gzip_proxied': 'any',
                'gzip_disable': 'msie6',
                'proxy_cache_path': '/var/cache/nginx levels=1:2 keys_zone=cache:10m max_size=1g inactive=60m',
                'proxy_cache': 'cache',
                'proxy_cache_valid': '200 301 302 60m',
                'proxy_cache_valid_404': '1m',
                'proxy_cache_use_stale': 'error timeout invalid_header updating http_500 http_502 http_503 http_504',
                'proxy_cache_lock': 'on',
                'proxy_cache_lock_timeout': '5s',
                'proxy_cache_bypass': '$http_pragma $http_authorization',
                'proxy_cache_methods': 'GET HEAD',
                'proxy_cache_key': '$scheme$proxy_host$request_uri',
                'proxy_cache_min_uses': 1,
                'proxy_cache_revalidate': 'on',
                'proxy_cache_background_update': 'on'
            })
        
        elif self.server_type == 'apache':
            self.config_data.update({
                'mpm_module': 'event',
                'start_servers': 2,
                'min_spare_threads': 25,
                'max_spare_threads': 75,
                'thread_limit': 64,
                'threads_per_child': 25,
                'max_request_workers': 150,
                'max_connections_per_child': 0,
                'server_limit': 16,
                'timeout': 60,
                'keep_alive': 'On',
                'max_keep_alive_requests': 100,
                'keep_alive_timeout': 5,
                'hostname_lookups': 'Off',
                'access_log': 'combined',
                'buffer_size': 8192,
                'enable_mmap': 'On',
                'enable_sendfile': 'On',
                'file_etag': 'MTime Size',
                'expires_active': 'On',
                'expires_default': 'access plus 1 month',
                'compression': 'On',
                'compression_level': 6,
                'compression_min_size': 1000,
                'compression_types': 'text/html text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript',
                'browser_match': '^Mozilla/4 gzip-only-text/html',
                'browser_match': '^Mozilla/4\\.0[678] no-gzip',
                'browser_match': '\\bMSIE !no-gzip !gzip-only-text/html',
                'header': 'append Vary Accept-Encoding',
                'cache_enabled': 'On',
                'cache_lock': 'On',
                'cache_lock_max_wait': 5,
                'cache_disk_min_file_size': 1,
                'cache_disk_max_file_size': 1000000,
                'cache_socache_max_size': 102400,
                'cache_max_file_size': 1000000,
                'cache_min_file_size': 1,
                'cache_timeout': 3600
            })
        
        else:
            raise ValueError(f"Unsupported server type: {self.server_type}")
    
    def _calculate_workers(self) -> int:
        """
        Calculate the number of workers based on CPU cores.
        
        Returns:
            int: Number of workers
        """
        import multiprocessing
        
        # Get the number of CPU cores
        cores = multiprocessing.cpu_count()
        
        # Calculate the number of workers (2-4 workers per core)
        workers = cores * 2 + 1
        
        return workers
    
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
    
    def get_performance_config(self) -> Dict[str, Any]:
        """
        Get the performance configuration.
        
        Returns:
            Dict[str, Any]: Performance configuration
        """
        return self.config_data
    
    def optimize_for_cpu_bound(self) -> None:
        """
        Optimize the configuration for CPU-bound applications.
        """
        # Calculate the number of workers
        workers = self._calculate_workers()
        
        # Update the configuration
        if self.server_type == 'gunicorn':
            self.config_data.update({
                'workers': workers,
                'threads': 1,
                'worker_class': 'sync',
                'max_requests': 1000,
                'max_requests_jitter': 50
            })
        
        elif self.server_type == 'uwsgi':
            self.config_data.update({
                'processes': workers,
                'threads': 1,
                'master': True,
                'cheaper': 2,
                'cheaper-algo': 'busyness',
                'cheaper-initial': 2,
                'cheaper-step': 1
            })
        
        elif self.server_type == 'nginx':
            self.config_data.update({
                'worker_processes': 'auto',
                'worker_connections': 1024,
                'multi_accept': 'on',
                'use': 'epoll'
            })
        
        elif self.server_type == 'apache':
            self.config_data.update({
                'mpm_module': 'worker',
                'start_servers': 2,
                'min_spare_threads': 25,
                'max_spare_threads': 75,
                'thread_limit': 64,
                'threads_per_child': 25,
                'max_request_workers': workers * 25
            })
    
    def optimize_for_io_bound(self) -> None:
        """
        Optimize the configuration for I/O-bound applications.
        """
        # Calculate the number of workers
        workers = max(2, self._calculate_workers() // 2)
        
        # Update the configuration
        if self.server_type == 'gunicorn':
            self.config_data.update({
                'workers': workers,
                'threads': 4,
                'worker_class': 'gevent',
                'max_requests': 1000,
                'max_requests_jitter': 50,
                'worker_connections': 1000
            })
        
        elif self.server_type == 'uwsgi':
            self.config_data.update({
                'processes': workers,
                'threads': 4,
                'master': True,
                'async': 100,
                'ugreen': True,
                'cheaper': 2,
                'cheaper-algo': 'busyness',
                'cheaper-initial': 2,
                'cheaper-step': 1
            })
        
        elif self.server_type == 'nginx':
            self.config_data.update({
                'worker_processes': 'auto',
                'worker_connections': 2048,
                'multi_accept': 'on',
                'use': 'epoll',
                'keepalive_timeout': 65,
                'keepalive_requests': 100
            })
        
        elif self.server_type == 'apache':
            self.config_data.update({
                'mpm_module': 'event',
                'start_servers': 2,
                'min_spare_threads': 25,
                'max_spare_threads': 75,
                'thread_limit': 64,
                'threads_per_child': 25,
                'max_request_workers': workers * 25,
                'max_connections_per_child': 0
            })
    
    def optimize_for_memory(self) -> None:
        """
        Optimize the configuration for memory-constrained environments.
        """
        # Calculate the number of workers
        workers = max(2, self._calculate_workers() // 4)
        
        # Update the configuration
        if self.server_type == 'gunicorn':
            self.config_data.update({
                'workers': workers,
                'threads': 2,
                'worker_class': 'sync',
                'max_requests': 1000,
                'max_requests_jitter': 50,
                'preload_app': False
            })
        
        elif self.server_type == 'uwsgi':
            self.config_data.update({
                'processes': workers,
                'threads': 2,
                'master': True,
                'lazy-apps': False,
                'cheaper': 1,
                'cheaper-algo': 'busyness',
                'cheaper-initial': 1,
                'cheaper-step': 1
            })
        
        elif self.server_type == 'nginx':
            self.config_data.update({
                'worker_processes': workers,
                'worker_connections': 512,
                'multi_accept': 'off',
                'open_file_cache': 'max=500 inactive=20s',
                'open_file_cache_valid': '30s',
                'open_file_cache_min_uses': 2,
                'open_file_cache_errors': 'on',
                'proxy_cache_path': '/var/cache/nginx levels=1:2 keys_zone=cache:5m max_size=100m inactive=60m'
            })
        
        elif self.server_type == 'apache':
            self.config_data.update({
                'mpm_module': 'prefork',
                'start_servers': 2,
                'min_spare_servers': 1,
                'max_spare_servers': 3,
                'max_request_workers': workers * 10,
                'max_connections_per_child': 1000
            })
    
    def optimize_for_high_traffic(self) -> None:
        """
        Optimize the configuration for high-traffic environments.
        """
        # Calculate the number of workers
        workers = self._calculate_workers() * 2
        
        # Update the configuration
        if self.server_type == 'gunicorn':
            self.config_data.update({
                'workers': workers,
                'threads': 4,
                'worker_class': 'gevent',
                'max_requests': 10000,
                'max_requests_jitter': 1000,
                'worker_connections': 2000,
                'backlog': 4096,
                'keepalive': 5
            })
        
        elif self.server_type == 'uwsgi':
            self.config_data.update({
                'processes': workers,
                'threads': 4,
                'master': True,
                'async': 100,
                'ugreen': True,
                'listen': 4096,
                'max-requests': 10000,
                'cheaper': workers // 4,
                'cheaper-algo': 'busyness',
                'cheaper-initial': workers // 4,
                'cheaper-step': 2,
                'cheaper-overload': 5
            })
        
        elif self.server_type == 'nginx':
            self.config_data.update({
                'worker_processes': 'auto',
                'worker_connections': 4096,
                'multi_accept': 'on',
                'use': 'epoll',
                'keepalive_timeout': 30,
                'keepalive_requests': 1000,
                'reset_timedout_connection': 'on',
                'client_body_timeout': 10,
                'client_header_timeout': 10,
                'send_timeout': 10,
                'limit_conn_zone': '$binary_remote_addr zone=addr:10m',
                'limit_conn': 'addr 100',
                'limit_req_zone': '$binary_remote_addr zone=req_limit:10m rate=100r/s',
                'limit_req': 'zone=req_limit burst=200 nodelay',
                'proxy_cache_path': '/var/cache/nginx levels=1:2 keys_zone=cache:100m max_size=10g inactive=60m'
            })
        
        elif self.server_type == 'apache':
            self.config_data.update({
                'mpm_module': 'event',
                'start_servers': 4,
                'min_spare_threads': 50,
                'max_spare_threads': 150,
                'thread_limit': 128,
                'threads_per_child': 50,
                'max_request_workers': workers * 50,
                'max_connections_per_child': 0,
                'server_limit': 32,
                'timeout': 30,
                'keep_alive': 'On',
                'max_keep_alive_requests': 1000,
                'keep_alive_timeout': 5
            })


def create_performance_config(server_type: str) -> PerformanceConfig:
    """
    Create a performance configuration.
    
    Args:
        server_type: Server type (gunicorn, uwsgi, nginx, apache)
        
    Returns:
        PerformanceConfig: Performance configuration
    """
    return PerformanceConfig(server_type)


def get_performance_config(server_type: str) -> Dict[str, Any]:
    """
    Get the performance configuration for a server type.
    
    Args:
        server_type: Server type (gunicorn, uwsgi, nginx, apache)
        
    Returns:
        Dict[str, Any]: Performance configuration
    """
    try:
        # Create a performance configuration
        performance_config = create_performance_config(server_type)
        
        # Get the performance configuration
        return performance_config.get_performance_config()
    
    except Exception as e:
        logger.error(f"Failed to get performance configuration for {server_type}: {str(e)}")
        return {}


def optimize_performance(server_type: str, optimization_type: str) -> Dict[str, Any]:
    """
    Optimize the performance configuration for a server type.
    
    Args:
        server_type: Server type (gunicorn, uwsgi, nginx, apache)
        optimization_type: Optimization type (cpu, io, memory, traffic)
        
    Returns:
        Dict[str, Any]: Optimized performance configuration
    """
    try:
        # Create a performance configuration
        performance_config = create_performance_config(server_type)
        
        # Optimize the configuration
        if optimization_type == 'cpu':
            performance_config.optimize_for_cpu_bound()
        elif optimization_type == 'io':
            performance_config.optimize_for_io_bound()
        elif optimization_type == 'memory':
            performance_config.optimize_for_memory()
        elif optimization_type == 'traffic':
            performance_config.optimize_for_high_traffic()
        else:
            raise ValueError(f"Unsupported optimization type: {optimization_type}")
        
        # Get the optimized performance configuration
        return performance_config.get_performance_config()
    
    except Exception as e:
        logger.error(f"Failed to optimize performance for {server_type}: {str(e)}")
        return {}
