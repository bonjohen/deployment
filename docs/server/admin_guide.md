# Web Server Configuration: Administrator Guide

This guide provides detailed information for system administrators on configuring, optimizing, securing, and maintaining web servers for Python web applications.

## Table of Contents

- [Server Architecture](#server-architecture)
- [Performance Tuning](#performance-tuning)
- [Security Configuration](#security-configuration)
- [Monitoring and Maintenance](#monitoring-and-maintenance)
- [High Availability Setup](#high-availability-setup)
- [Load Balancing](#load-balancing)
- [Backup and Recovery](#backup-and-recovery)

## Server Architecture

### Recommended Architecture

The recommended architecture for a Python web application consists of:

1. **Web Server** (Nginx/Apache): Handles static files, SSL termination, and proxies requests to the application server
2. **Application Server** (Gunicorn/uWSGI): Runs the Python application and processes dynamic requests
3. **Database Server**: Stores application data
4. **Cache Server** (Redis/Memcached): Caches frequently accessed data

```
                   ┌─────────────┐
                   │   Client    │
                   └──────┬──────┘
                          │
                          ▼
                   ┌─────────────┐
                   │  Web Server │
                   │(Nginx/Apache)│
                   └──────┬──────┘
                          │
                          ▼
                   ┌─────────────┐
                   │    WSGI     │
                   │(Gunicorn/uWSGI)│
                   └──────┬──────┘
                          │
                          ▼
                   ┌─────────────┐
                   │   Python    │
                   │ Application │
                   └──────┬──────┘
                          │
              ┌───────────┴───────────┐
              ▼                       ▼
      ┌─────────────┐         ┌─────────────┐
      │  Database   │         │    Cache    │
      │   Server    │         │    Server   │
      └─────────────┘         └─────────────┘
```

### Component Roles

- **Web Server**:
  - Serves static files (CSS, JavaScript, images)
  - Handles SSL/TLS encryption
  - Performs load balancing
  - Implements caching
  - Provides security features (rate limiting, IP filtering)

- **Application Server**:
  - Executes Python code
  - Processes dynamic requests
  - Manages worker processes
  - Handles request queuing

- **Database Server**:
  - Stores application data
  - Processes queries
  - Manages transactions
  - Handles data integrity

- **Cache Server**:
  - Caches database queries
  - Stores session data
  - Reduces database load
  - Improves response times

## Performance Tuning

### Gunicorn Performance Tuning

The PythonWeb Installer provides performance optimization for different workloads:

```python
from pythonweb_installer.server.performance import optimize_server_performance

# Optimize for CPU-bound applications
cpu_config = optimize_server_performance('gunicorn', 'cpu')

# Optimize for I/O-bound applications
io_config = optimize_server_performance('gunicorn', 'io')

# Optimize for memory-constrained environments
memory_config = optimize_server_performance('gunicorn', 'memory')

# Optimize for high-traffic environments
traffic_config = optimize_server_performance('gunicorn', 'traffic')
```

#### Worker Processes

The number of worker processes depends on the workload:

- **CPU-bound applications**: `(2 × CPU cores) + 1`
- **I/O-bound applications**: `(CPU cores) × 2` to `(CPU cores) × 4`
- **Memory-constrained environments**: `(CPU cores) / 2` to `(CPU cores)`
- **High-traffic environments**: `(CPU cores) × 2` to `(CPU cores) × 4`

#### Worker Types

- **sync**: Synchronous workers, good for CPU-bound applications
- **gevent**: Greenlet-based workers, good for I/O-bound applications
- **eventlet**: Greenlet-based workers, alternative to gevent
- **tornado**: Tornado-based workers
- **gthread**: Threaded workers, good for I/O-bound applications

#### Example: CPU-Bound Configuration

```python
{
    'workers': 9,  # (2 × 4 cores) + 1
    'threads': 1,
    'worker_class': 'sync',
    'max_requests': 1000,
    'max_requests_jitter': 50
}
```

#### Example: I/O-Bound Configuration

```python
{
    'workers': 4,  # 4 cores
    'threads': 4,
    'worker_class': 'gevent',
    'worker_connections': 1000,
    'max_requests': 1000,
    'max_requests_jitter': 50
}
```

### uWSGI Performance Tuning

#### Process and Thread Management

- **processes**: Number of worker processes
- **threads**: Number of threads per worker
- **cheaper**: Minimum number of workers
- **cheaper-algo**: Algorithm for scaling workers ('busyness', 'spare', 'backlog')

#### Example: CPU-Bound Configuration

```python
{
    'processes': 9,  # (2 × 4 cores) + 1
    'threads': 1,
    'master': True,
    'cheaper': 2,
    'cheaper-algo': 'busyness',
    'cheaper-initial': 2,
    'cheaper-step': 1
}
```

#### Example: I/O-Bound Configuration

```python
{
    'processes': 4,  # 4 cores
    'threads': 4,
    'master': True,
    'async': 100,
    'ugreen': True,
    'cheaper': 2,
    'cheaper-algo': 'busyness',
    'cheaper-initial': 2,
    'cheaper-step': 1
}
```

### Nginx Performance Tuning

#### Worker Processes and Connections

- **worker_processes**: Number of worker processes ('auto' or a number)
- **worker_connections**: Maximum number of connections per worker
- **multi_accept**: Accept multiple connections at once
- **use**: Event processing method ('epoll', 'kqueue', 'select')

#### File Handling

- **sendfile**: Enable sendfile for static files
- **tcp_nopush**: Optimize packet sending
- **tcp_nodelay**: Disable Nagle's algorithm
- **open_file_cache**: Cache file descriptors

#### Example: High-Traffic Configuration

```python
{
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
    'open_file_cache': 'max=1000 inactive=20s',
    'open_file_cache_valid': '30s',
    'open_file_cache_min_uses': 2,
    'open_file_cache_errors': 'on'
}
```

### Apache Performance Tuning

#### MPM Configuration

- **mpm_module**: Multi-Processing Module ('event', 'worker', 'prefork')
- **start_servers**: Number of server processes to start
- **min_spare_threads**: Minimum number of spare threads
- **max_spare_threads**: Maximum number of spare threads
- **thread_limit**: Maximum number of threads per process
- **threads_per_child**: Number of threads per process
- **max_request_workers**: Maximum number of worker threads

#### Example: High-Traffic Configuration

```python
{
    'mpm_module': 'event',
    'start_servers': 4,
    'min_spare_threads': 50,
    'max_spare_threads': 150,
    'thread_limit': 128,
    'threads_per_child': 50,
    'max_request_workers': 400,
    'max_connections_per_child': 0,
    'server_limit': 32,
    'timeout': 30,
    'keep_alive': 'On',
    'max_keep_alive_requests': 1000,
    'keep_alive_timeout': 5
}
```

## Security Configuration

The PythonWeb Installer provides comprehensive security configuration options:

```python
from pythonweb_installer.server.security import (
    create_security_config,
    apply_security_config
)

# Create a security configuration
security_config = create_security_config('nginx')

# Enable SSL/TLS
security_config.enable_ssl('/path/to/cert.pem', '/path/to/key.pem')

# Enable CORS
security_config.enable_cors(['https://example.com'])

# Enable rate limiting
security_config.enable_rate_limiting(100, 60, 200)

# Enable IP filtering
security_config.enable_ip_filtering(['192.168.1.1'], ['10.0.0.1'])

# Enable basic authentication
security_config.enable_basic_auth({'user': 'password'})

# Apply security configuration to a server configuration
server_config = {}
secured_config = apply_security_config('nginx', server_config, security_config.get_security_config())
```

### SSL/TLS Configuration

#### Enabling SSL/TLS

```python
security_config.enable_ssl('/path/to/cert.pem', '/path/to/key.pem')
```

#### SSL/TLS Options

- **ssl_protocols**: SSL/TLS protocols to enable
- **ssl_ciphers**: SSL/TLS ciphers to enable
- **ssl_prefer_server_ciphers**: Prefer server ciphers over client ciphers
- **ssl_session_timeout**: SSL session timeout
- **ssl_session_cache**: SSL session cache
- **ssl_session_tickets**: Enable SSL session tickets
- **ssl_stapling**: Enable OCSP stapling
- **ssl_stapling_verify**: Verify OCSP stapling

#### Example: Strong SSL/TLS Configuration

```python
{
    'ssl_enabled': True,
    'ssl_cert': '/path/to/cert.pem',
    'ssl_key': '/path/to/key.pem',
    'ssl_protocols': ['TLSv1.2', 'TLSv1.3'],
    'ssl_ciphers': 'ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305:DHE-RSA-AES128-GCM-SHA256:DHE-RSA-AES256-GCM-SHA384',
    'ssl_prefer_server_ciphers': True,
    'ssl_session_timeout': '1d',
    'ssl_session_cache': 'shared:SSL:50m',
    'ssl_session_tickets': False,
    'ssl_stapling': True,
    'ssl_stapling_verify': True
}
```

### HTTP Security Headers

#### Security Headers Options

- **x_content_type_options**: Prevent MIME type sniffing
- **x_frame_options**: Prevent clickjacking
- **x_xss_protection**: Enable XSS filtering
- **content_security_policy**: Content Security Policy
- **referrer_policy**: Referrer Policy
- **strict_transport_security**: HTTP Strict Transport Security
- **permissions_policy**: Permissions Policy

#### Example: Comprehensive Security Headers

```python
{
    'security_headers': True,
    'x_content_type_options': 'nosniff',
    'x_frame_options': 'SAMEORIGIN',
    'x_xss_protection': '1; mode=block',
    'content_security_policy': "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self'; connect-src 'self'",
    'referrer_policy': 'strict-origin-when-cross-origin',
    'strict_transport_security': 'max-age=31536000; includeSubDomains',
    'permissions_policy': 'camera=(), microphone=(), geolocation=()'
}
```

### CORS Configuration

#### Enabling CORS

```python
security_config.enable_cors(['https://example.com'])
```

#### CORS Options

- **cors_allow_origins**: Allowed origins
- **cors_allow_methods**: Allowed methods
- **cors_allow_headers**: Allowed headers
- **cors_allow_credentials**: Allow credentials
- **cors_expose_headers**: Exposed headers
- **cors_max_age**: Maximum age

#### Example: Restrictive CORS Configuration

```python
{
    'cors_enabled': True,
    'cors_allow_origins': ['https://example.com'],
    'cors_allow_methods': ['GET', 'POST', 'PUT', 'DELETE'],
    'cors_allow_headers': ['Content-Type', 'Authorization'],
    'cors_allow_credentials': False,
    'cors_expose_headers': [],
    'cors_max_age': 86400
}
```

### Rate Limiting

#### Enabling Rate Limiting

```python
security_config.enable_rate_limiting(100, 60, 200)
```

#### Rate Limiting Options

- **rate_limit_requests**: Number of requests
- **rate_limit_period**: Time period in seconds
- **rate_limit_burst**: Burst size

#### Example: Rate Limiting Configuration

```python
{
    'rate_limiting_enabled': True,
    'rate_limit_requests': 100,
    'rate_limit_period': 60,
    'rate_limit_burst': 200
}
```

### IP Filtering

#### Enabling IP Filtering

```python
security_config.enable_ip_filtering(['192.168.1.1'], ['10.0.0.1'])
```

#### IP Filtering Options

- **allowed_ips**: Allowed IP addresses
- **denied_ips**: Denied IP addresses

#### Example: IP Filtering Configuration

```python
{
    'ip_filtering_enabled': True,
    'allowed_ips': ['192.168.1.1', '192.168.1.2'],
    'denied_ips': ['10.0.0.1', '10.0.0.2']
}
```

### Basic Authentication

#### Enabling Basic Authentication

```python
security_config.enable_basic_auth({'user': 'password'})
```

#### Basic Authentication Options

- **basic_auth_users**: Dictionary of username to password

#### Example: Basic Authentication Configuration

```python
{
    'basic_auth_enabled': True,
    'basic_auth_users': {
        'admin': 'password',
        'user': 'password'
    }
}
```

## Monitoring and Maintenance

### Log Management

#### Log Rotation

Configure log rotation to prevent logs from consuming too much disk space:

```bash
# /etc/logrotate.d/pythonweb
/var/log/pythonweb/*.log {
    daily
    missingok
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 www-data www-data
    sharedscripts
    postrotate
        systemctl reload pythonweb-gunicorn.service
    endscript
}
```

#### Log Analysis

Use tools like `goaccess` or `awstats` to analyze web server logs:

```bash
# Install goaccess
sudo apt-get install goaccess

# Analyze Nginx access logs
goaccess /var/log/nginx/access.log -c
```

### Health Checks

Implement health checks to monitor the application:

```python
# app.py
@app.route('/health')
def health_check():
    return jsonify({
        'status': 'ok',
        'version': '1.0.0',
        'database': check_database_connection(),
        'cache': check_cache_connection()
    })
```

Configure Nginx to proxy health checks:

```nginx
location /health {
    proxy_pass http://127.0.0.1:8000/health;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}
```

### Process Monitoring

Use tools like `supervisord` or `systemd` to monitor and restart processes:

```ini
# /etc/supervisor/conf.d/pythonweb.conf
[program:pythonweb]
command=/path/to/app/scripts/start_gunicorn.sh
directory=/path/to/app
user=www-data
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/supervisor/pythonweb.log
```

### Resource Monitoring

Use tools like `htop`, `iotop`, and `netstat` to monitor system resources:

```bash
# Monitor CPU and memory usage
htop

# Monitor disk I/O
iotop

# Monitor network connections
netstat -tunapl

# Monitor disk usage
df -h
```

## High Availability Setup

### Load Balancing with Nginx

Configure Nginx as a load balancer:

```nginx
upstream app_servers {
    server 192.168.1.1:8000;
    server 192.168.1.2:8000;
    server 192.168.1.3:8000;
}

server {
    listen 80;
    server_name example.com;

    location / {
        proxy_pass http://app_servers;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### Session Management

Use Redis for session management:

```python
# app.py
from flask import Flask
from flask_session import Session

app = Flask(__name__)
app.config['SESSION_TYPE'] = 'redis'
app.config['SESSION_REDIS'] = redis.from_url('redis://localhost:6379/0')
Session(app)
```

### Database Replication

Configure database replication for high availability:

```ini
# postgresql.conf (primary)
wal_level = replica
max_wal_senders = 10
wal_keep_segments = 64

# postgresql.conf (replica)
hot_standby = on
```

## Backup and Recovery

### Configuration Backup

Backup server configurations regularly:

```bash
# Backup Nginx configuration
tar -czf nginx_config_backup_$(date +%Y%m%d).tar.gz /etc/nginx/

# Backup Gunicorn configuration
tar -czf gunicorn_config_backup_$(date +%Y%m%d).tar.gz /path/to/config/gunicorn.conf.py
```

### Application Backup

Backup the application code and data:

```bash
# Backup application code
tar -czf app_backup_$(date +%Y%m%d).tar.gz /path/to/app/

# Backup database
pg_dump -U username -d database_name > database_backup_$(date +%Y%m%d).sql
```

### Automated Backups

Set up automated backups using cron:

```bash
# /etc/cron.d/pythonweb-backup
0 2 * * * www-data /path/to/app/scripts/backup.sh
```

### Disaster Recovery

Create a disaster recovery plan:

1. **Backup Verification**: Regularly verify backups
2. **Recovery Testing**: Test recovery procedures
3. **Documentation**: Document recovery steps
4. **Automation**: Automate recovery where possible
