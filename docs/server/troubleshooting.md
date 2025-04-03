# Web Server Configuration: Troubleshooting Guide

This guide provides solutions for common issues encountered when configuring and running web servers for Python web applications.

## Table of Contents

- [Common Issues](#common-issues)
- [Gunicorn Troubleshooting](#gunicorn-troubleshooting)
- [uWSGI Troubleshooting](#uwsgi-troubleshooting)
- [Nginx Troubleshooting](#nginx-troubleshooting)
- [Apache Troubleshooting](#apache-troubleshooting)
- [SSL/TLS Troubleshooting](#ssltls-troubleshooting)
- [Performance Troubleshooting](#performance-troubleshooting)
- [Security Troubleshooting](#security-troubleshooting)
- [Diagnostic Procedures](#diagnostic-procedures)

## Common Issues

### Application Not Starting

**Symptoms:**
- Web server returns 502 Bad Gateway or 503 Service Unavailable
- No application logs are being generated

**Possible Causes:**
- Python application has syntax errors
- Required dependencies are missing
- Incorrect file permissions
- Incorrect path to the Python executable
- Incorrect WSGI/ASGI module path

**Solutions:**
1. Check application logs for errors:
   ```bash
   tail -f /path/to/app/logs/error.log
   ```

2. Verify file permissions:
   ```bash
   ls -la /path/to/app/
   ```

3. Test the application directly:
   ```bash
   cd /path/to/app/
   /path/to/venv/bin/python app.py
   ```

4. Check for missing dependencies:
   ```bash
   /path/to/venv/bin/pip freeze > installed.txt
   diff -u requirements.txt installed.txt
   ```

5. Verify the WSGI/ASGI module path:
   ```bash
   /path/to/venv/bin/python -c "import myapp.wsgi"
   ```

### Connection Refused

**Symptoms:**
- Web browser shows "Connection refused"
- `curl` returns "Connection refused"

**Possible Causes:**
- Web server is not running
- Web server is listening on a different address or port
- Firewall is blocking the connection

**Solutions:**
1. Check if the web server is running:
   ```bash
   ps aux | grep nginx
   ps aux | grep gunicorn
   ```

2. Verify the listening address and port:
   ```bash
   netstat -tuln | grep 80
   ```

3. Check firewall rules:
   ```bash
   sudo iptables -L
   ```

4. Restart the web server:
   ```bash
   sudo systemctl restart nginx
   sudo systemctl restart gunicorn
   ```

### Static Files Not Found

**Symptoms:**
- CSS, JavaScript, or images are not loading
- Browser console shows 404 errors for static files

**Possible Causes:**
- Incorrect static file path configuration
- Incorrect file permissions
- Web server not configured to serve static files

**Solutions:**
1. Check static file path configuration:
   ```bash
   grep -r "static" /etc/nginx/
   ```

2. Verify file permissions:
   ```bash
   ls -la /path/to/app/static/
   ```

3. Test static file access directly:
   ```bash
   curl -I http://localhost/static/css/style.css
   ```

4. Update static file configuration:
   ```python
   # Nginx configuration
   config_data = {
       'static_dir': '/path/to/app/static',
       'static_url': '/static/'
   }
   ```

## Gunicorn Troubleshooting

### Worker Timeout

**Symptoms:**
- Requests take a long time to process
- Gunicorn logs show worker timeout errors

**Possible Causes:**
- Long-running database queries
- External API calls taking too long
- Insufficient worker timeout

**Solutions:**
1. Increase worker timeout:
   ```python
   # Gunicorn configuration
   config_data = {
       'timeout': 60  # Increase to 60 seconds
   }
   ```

2. Optimize database queries:
   ```python
   # Add database indexes
   # Use query caching
   ```

3. Add timeouts to external API calls:
   ```python
   import requests
   
   response = requests.get('https://api.example.com', timeout=5)
   ```

### Worker Restart Loop

**Symptoms:**
- Gunicorn workers keep restarting
- Gunicorn logs show "Worker restarting" messages

**Possible Causes:**
- Application errors causing workers to crash
- Memory leaks
- Resource exhaustion

**Solutions:**
1. Check application logs for errors:
   ```bash
   tail -f /path/to/app/logs/error.log
   ```

2. Monitor memory usage:
   ```bash
   ps -o pid,user,%mem,command ax | grep gunicorn
   ```

3. Increase max requests before worker restart:
   ```python
   # Gunicorn configuration
   config_data = {
       'max_requests': 10000,
       'max_requests_jitter': 1000
   }
   ```

4. Add memory profiling to identify leaks:
   ```python
   from memory_profiler import profile
   
   @profile
   def memory_intensive_function():
       # Function code
   ```

### Connection Reset

**Symptoms:**
- Clients receive "Connection reset by peer" errors
- Gunicorn logs show "SIGPIPE" errors

**Possible Causes:**
- Client disconnects before response is complete
- Network issues
- Keepalive timeout too short

**Solutions:**
1. Increase keepalive timeout:
   ```python
   # Gunicorn configuration
   config_data = {
       'keepalive': 5  # Increase to 5 seconds
   }
   ```

2. Handle client disconnects gracefully:
   ```python
   try:
       # Send response
   except BrokenPipeError:
       # Client disconnected
       pass
   ```

3. Check network stability:
   ```bash
   ping -c 100 client_ip
   ```

## uWSGI Troubleshooting

### uWSGI Crashes

**Symptoms:**
- uWSGI process terminates unexpectedly
- System logs show segmentation fault

**Possible Causes:**
- C extension compatibility issues
- Memory corruption
- Resource exhaustion

**Solutions:**
1. Check system logs for segmentation faults:
   ```bash
   dmesg | grep uwsgi
   ```

2. Enable core dumps:
   ```bash
   ulimit -c unlimited
   ```

3. Run uWSGI with memory debugging:
   ```bash
   uwsgi --memory-report --master --processes 4 --socket 0.0.0.0:8000 --module app:app
   ```

4. Disable threads if using problematic C extensions:
   ```python
   # uWSGI configuration
   config_data = {
       'threads': 1  # Disable threading
   }
   ```

### Harakiri Timeout

**Symptoms:**
- uWSGI logs show "HARAKIRI" messages
- Requests are terminated after a certain time

**Possible Causes:**
- Long-running database queries
- External API calls taking too long
- Insufficient harakiri timeout

**Solutions:**
1. Increase harakiri timeout:
   ```python
   # uWSGI configuration
   config_data = {
       'harakiri': 60  # Increase to 60 seconds
   }
   ```

2. Optimize database queries:
   ```python
   # Add database indexes
   # Use query caching
   ```

3. Add timeouts to external API calls:
   ```python
   import requests
   
   response = requests.get('https://api.example.com', timeout=5)
   ```

### Socket Queue Full

**Symptoms:**
- uWSGI logs show "socket queue is full" messages
- Clients receive 502 Bad Gateway errors

**Possible Causes:**
- Too many concurrent requests
- Workers processing requests too slowly
- Insufficient listen queue size

**Solutions:**
1. Increase listen queue size:
   ```python
   # uWSGI configuration
   config_data = {
       'listen': 4096  # Increase to 4096
   }
   ```

2. Increase number of workers:
   ```python
   # uWSGI configuration
   config_data = {
       'processes': 8  # Increase to 8
   }
   ```

3. Enable async mode:
   ```python
   # uWSGI configuration
   config_data = {
       'async': 100,
       'ugreen': True
   }
   ```

## Nginx Troubleshooting

### 502 Bad Gateway

**Symptoms:**
- Nginx returns 502 Bad Gateway errors
- Nginx error logs show "upstream prematurely closed connection"

**Possible Causes:**
- Application server (Gunicorn/uWSGI) is not running
- Application server is crashing
- Incorrect proxy configuration

**Solutions:**
1. Check if the application server is running:
   ```bash
   ps aux | grep gunicorn
   ps aux | grep uwsgi
   ```

2. Check Nginx error logs:
   ```bash
   tail -f /var/log/nginx/error.log
   ```

3. Check application server logs:
   ```bash
   tail -f /path/to/app/logs/error.log
   ```

4. Verify proxy configuration:
   ```bash
   grep -r "proxy_pass" /etc/nginx/
   ```

5. Increase proxy timeouts:
   ```python
   # Nginx configuration
   config_data = {
       'proxy_connect_timeout': 60,
       'proxy_read_timeout': 60,
       'proxy_send_timeout': 60
   }
   ```

### 504 Gateway Timeout

**Symptoms:**
- Nginx returns 504 Gateway Timeout errors
- Nginx error logs show "upstream timed out"

**Possible Causes:**
- Application server taking too long to respond
- Proxy timeout too short
- Long-running database queries

**Solutions:**
1. Increase proxy timeout:
   ```python
   # Nginx configuration
   config_data = {
       'proxy_read_timeout': 120  # Increase to 120 seconds
   }
   ```

2. Optimize application code:
   ```python
   # Use asynchronous processing for long-running tasks
   # Optimize database queries
   ```

3. Implement request queuing:
   ```python
   # Use a task queue like Celery for long-running tasks
   ```

### Client Request Body Too Large

**Symptoms:**
- Nginx returns 413 Request Entity Too Large errors
- Nginx error logs show "client intended to send too large body"

**Possible Causes:**
- File upload size exceeds limit
- Large form submission
- Insufficient client_max_body_size

**Solutions:**
1. Increase client_max_body_size:
   ```python
   # Nginx configuration
   config_data = {
       'client_max_body_size': '100m'  # Increase to 100 MB
   }
   ```

2. Implement chunked file uploads:
   ```javascript
   // Use a JavaScript library for chunked file uploads
   ```

3. Compress large request bodies:
   ```python
   # Enable gzip compression
   config_data = {
       'gzip_enabled': True
   }
   ```

## Apache Troubleshooting

### mod_wsgi Issues

**Symptoms:**
- Apache returns 500 Internal Server Error
- Apache error logs show mod_wsgi errors

**Possible Causes:**
- Incompatible mod_wsgi version
- Python version mismatch
- Incorrect WSGI script path

**Solutions:**
1. Check Apache error logs:
   ```bash
   tail -f /var/log/apache2/error.log
   ```

2. Verify mod_wsgi installation:
   ```bash
   apache2ctl -M | grep wsgi
   ```

3. Check Python version compatibility:
   ```bash
   python --version
   ldd /usr/lib/apache2/modules/mod_wsgi.so
   ```

4. Reinstall mod_wsgi with the correct Python version:
   ```bash
   pip install mod_wsgi-standalone
   mod_wsgi-express install-module > /etc/apache2/mods-available/wsgi.load
   ```

### Permission Denied

**Symptoms:**
- Apache returns 403 Forbidden errors
- Apache error logs show "Permission denied"

**Possible Causes:**
- Incorrect file permissions
- SELinux restrictions
- Apache user cannot access files

**Solutions:**
1. Check file permissions:
   ```bash
   ls -la /path/to/app/
   ```

2. Update file permissions:
   ```bash
   chmod -R 755 /path/to/app/
   chown -R www-data:www-data /path/to/app/
   ```

3. Check SELinux context:
   ```bash
   ls -Z /path/to/app/
   ```

4. Update SELinux context:
   ```bash
   semanage fcontext -a -t httpd_sys_content_t "/path/to/app(/.*)?"
   restorecon -Rv /path/to/app/
   ```

### MPM Worker Configuration

**Symptoms:**
- Apache performance is poor
- High memory usage
- Connections are queued

**Possible Causes:**
- Incorrect MPM worker configuration
- Too few worker threads
- Too many worker threads

**Solutions:**
1. Check current MPM configuration:
   ```bash
   apache2ctl -V | grep MPM
   ```

2. Switch to event MPM:
   ```bash
   a2dismod mpm_prefork
   a2enmod mpm_event
   ```

3. Optimize MPM event configuration:
   ```python
   # Apache configuration
   config_data = {
       'mpm_module': 'event',
       'start_servers': 2,
       'min_spare_threads': 25,
       'max_spare_threads': 75,
       'thread_limit': 64,
       'threads_per_child': 25,
       'max_request_workers': 150
   }
   ```

## SSL/TLS Troubleshooting

### SSL Certificate Issues

**Symptoms:**
- Browser shows "Your connection is not private"
- SSL Labs test shows certificate errors

**Possible Causes:**
- Self-signed certificate
- Expired certificate
- Missing intermediate certificates
- Certificate name mismatch

**Solutions:**
1. Check certificate information:
   ```bash
   openssl x509 -in /path/to/cert.pem -text -noout
   ```

2. Verify certificate chain:
   ```bash
   openssl verify -CAfile /path/to/chain.pem /path/to/cert.pem
   ```

3. Check certificate expiration:
   ```bash
   openssl x509 -in /path/to/cert.pem -noout -enddate
   ```

4. Renew certificate with Let's Encrypt:
   ```bash
   certbot renew
   ```

5. Update SSL configuration:
   ```python
   # Nginx configuration
   config_data = {
       'ssl_enabled': True,
       'ssl_cert': '/path/to/fullchain.pem',  # Include intermediate certificates
       'ssl_key': '/path/to/privkey.pem'
   }
   ```

### SSL Protocol/Cipher Issues

**Symptoms:**
- Older clients cannot connect
- SSL Labs test shows protocol or cipher issues

**Possible Causes:**
- Disabled older protocols (TLSv1.0, TLSv1.1)
- Restricted cipher suites
- Missing modern cipher suites

**Solutions:**
1. Check supported protocols and ciphers:
   ```bash
   nmap --script ssl-enum-ciphers -p 443 example.com
   ```

2. Update SSL protocol configuration:
   ```python
   # Nginx configuration
   config_data = {
       'ssl_protocols': ['TLSv1.2', 'TLSv1.3']  # Modern protocols only
   }
   ```

3. Update SSL cipher configuration:
   ```python
   # Nginx configuration
   config_data = {
       'ssl_ciphers': 'ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305:DHE-RSA-AES128-GCM-SHA256:DHE-RSA-AES256-GCM-SHA384'
   }
   ```

4. Enable backward compatibility (if needed):
   ```python
   # Nginx configuration
   config_data = {
       'ssl_protocols': ['TLSv1', 'TLSv1.1', 'TLSv1.2', 'TLSv1.3']  # Include older protocols
   }
   ```

### OCSP Stapling Issues

**Symptoms:**
- SSL Labs test shows OCSP stapling is not working
- Slow SSL handshakes

**Possible Causes:**
- OCSP stapling not enabled
- OCSP responder unreachable
- Missing CA certificate

**Solutions:**
1. Enable OCSP stapling:
   ```python
   # Nginx configuration
   config_data = {
       'ssl_stapling': True,
       'ssl_stapling_verify': True
   }
   ```

2. Verify OCSP responder:
   ```bash
   openssl x509 -in /path/to/cert.pem -noout -ocsp_uri
   ```

3. Test OCSP responder:
   ```bash
   openssl ocsp -issuer /path/to/chain.pem -cert /path/to/cert.pem -text -url $(openssl x509 -in /path/to/cert.pem -noout -ocsp_uri)
   ```

4. Add resolver for OCSP stapling:
   ```python
   # Nginx configuration
   config_data = {
       'resolver': '8.8.8.8 8.8.4.4 valid=300s',
       'resolver_timeout': '5s'
   }
   ```

## Performance Troubleshooting

### High CPU Usage

**Symptoms:**
- Server CPU usage is consistently high
- Response times are slow
- Load average is high

**Possible Causes:**
- Inefficient application code
- Too many worker processes
- CPU-intensive operations

**Solutions:**
1. Monitor CPU usage:
   ```bash
   top -c
   ```

2. Profile application code:
   ```python
   import cProfile
   
   cProfile.run('expensive_function()')
   ```

3. Optimize worker configuration:
   ```python
   # Gunicorn configuration
   config_data = {
       'workers': 4,  # Adjust based on CPU cores
       'worker_class': 'sync'  # Use 'sync' for CPU-bound applications
   }
   ```

4. Implement caching:
   ```python
   # Use Redis for caching
   from flask_caching import Cache
   
   cache = Cache(app, config={'CACHE_TYPE': 'redis'})
   
   @cache.cached(timeout=60)
   def expensive_function():
       # Function code
   ```

### High Memory Usage

**Symptoms:**
- Server memory usage is consistently high
- Swap usage is high
- Out of memory errors

**Possible Causes:**
- Memory leaks
- Too many worker processes
- Large in-memory caches

**Solutions:**
1. Monitor memory usage:
   ```bash
   free -m
   ps -o pid,user,%mem,command ax | sort -b -k3 -r
   ```

2. Identify memory leaks:
   ```python
   from memory_profiler import profile
   
   @profile
   def memory_intensive_function():
       # Function code
   ```

3. Optimize worker configuration:
   ```python
   # Gunicorn configuration
   config_data = {
       'workers': 2,  # Reduce number of workers
       'max_requests': 1000,  # Restart workers periodically
       'max_requests_jitter': 50
   }
   ```

4. Implement memory limits:
   ```python
   # uWSGI configuration
   config_data = {
       'limit-as': 256,  # Limit to 256 MB per worker
   }
   ```

### Slow Response Times

**Symptoms:**
- Requests take a long time to complete
- Time to first byte (TTFB) is high
- Browser shows slow loading times

**Possible Causes:**
- Slow database queries
- External API calls
- Inefficient application code
- Network latency

**Solutions:**
1. Measure response times:
   ```bash
   curl -w "%{time_total}\n" -o /dev/null -s http://example.com/
   ```

2. Enable request timing logging:
   ```python
   # Nginx configuration
   config_data = {
       'log_format': 'main \'$remote_addr - $remote_user [$time_local] "$request" $status $body_bytes_sent "$http_referer" "$http_user_agent" $request_time\'',
   }
   ```

3. Optimize database queries:
   ```python
   # Add database indexes
   # Use query caching
   # Implement database connection pooling
   ```

4. Implement content caching:
   ```python
   # Nginx configuration
   config_data = {
       'proxy_cache_path': '/var/cache/nginx levels=1:2 keys_zone=cache:10m max_size=1g inactive=60m',
       'proxy_cache': 'cache',
       'proxy_cache_valid': {'200': '60m', '301': '1h', '404': '1m'}
   }
   ```

## Security Troubleshooting

### CORS Issues

**Symptoms:**
- Browser console shows CORS errors
- API requests from frontend fail
- "No 'Access-Control-Allow-Origin' header" errors

**Possible Causes:**
- Missing CORS headers
- Incorrect CORS configuration
- Preflight requests not handled

**Solutions:**
1. Enable CORS:
   ```python
   from pythonweb_installer.server.security import create_security_config
   
   security_config = create_security_config('nginx')
   security_config.enable_cors(['https://example.com'])
   ```

2. Configure CORS headers:
   ```python
   # Nginx configuration
   config_data = {
       'cors_enabled': True,
       'cors_allow_origins': ['https://example.com'],
       'cors_allow_methods': ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
       'cors_allow_headers': ['Content-Type', 'Authorization'],
       'cors_allow_credentials': True
   }
   ```

3. Handle preflight requests:
   ```python
   # Flask application
   @app.route('/api', methods=['OPTIONS'])
   def options():
       response = make_response()
       response.headers.add('Access-Control-Allow-Origin', 'https://example.com')
       response.headers.add('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
       response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization')
       return response
   ```

### Rate Limiting Issues

**Symptoms:**
- Legitimate requests are blocked
- Too many 429 Too Many Requests errors
- Rate limiting is not effective

**Possible Causes:**
- Rate limit too low
- Rate limit too high
- Incorrect rate limiting configuration

**Solutions:**
1. Adjust rate limiting:
   ```python
   from pythonweb_installer.server.security import create_security_config
   
   security_config = create_security_config('nginx')
   security_config.enable_rate_limiting(200, 60, 400)  # 200 requests per minute, burst of 400
   ```

2. Implement IP-based rate limiting:
   ```python
   # Nginx configuration
   config_data = {
       'rate_limiting_enabled': True,
       'rate_limit_requests': 200,
       'rate_limit_period': 60,
       'rate_limit_burst': 400
   }
   ```

3. Implement API key-based rate limiting:
   ```python
   # Flask application
   from flask_limiter import Limiter
   
   limiter = Limiter(app, key_func=lambda: request.headers.get('X-API-Key', ''))
   
   @app.route('/api')
   @limiter.limit('200 per minute')
   def api():
       # API code
   ```

### SSL/TLS Security Issues

**Symptoms:**
- SSL Labs test shows poor grade
- Security scanners report vulnerabilities
- Weak cipher suites or protocols

**Possible Causes:**
- Outdated SSL/TLS configuration
- Weak cipher suites enabled
- Vulnerable protocols enabled

**Solutions:**
1. Implement strong SSL/TLS configuration:
   ```python
   from pythonweb_installer.server.security import create_security_config
   
   security_config = create_security_config('nginx')
   security_config.enable_ssl('/path/to/cert.pem', '/path/to/key.pem')
   ```

2. Disable weak protocols:
   ```python
   # Nginx configuration
   config_data = {
       'ssl_protocols': ['TLSv1.2', 'TLSv1.3']  # Only modern protocols
   }
   ```

3. Use strong cipher suites:
   ```python
   # Nginx configuration
   config_data = {
       'ssl_ciphers': 'ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305:DHE-RSA-AES128-GCM-SHA256:DHE-RSA-AES256-GCM-SHA384'
   }
   ```

4. Enable HTTP Strict Transport Security (HSTS):
   ```python
   # Nginx configuration
   config_data = {
       'strict_transport_security': 'max-age=31536000; includeSubDomains; preload'
   }
   ```

## Diagnostic Procedures

### Server Status Check

Check the status of all server components:

```bash
# Check Nginx status
systemctl status nginx

# Check Gunicorn status
systemctl status gunicorn

# Check uWSGI status
systemctl status uwsgi

# Check Apache status
systemctl status apache2
```

### Log Analysis

Analyze server logs for errors:

```bash
# Check Nginx error logs
tail -f /var/log/nginx/error.log

# Check Gunicorn logs
tail -f /path/to/app/logs/gunicorn.log

# Check uWSGI logs
tail -f /path/to/app/logs/uwsgi.log

# Check Apache error logs
tail -f /var/log/apache2/error.log

# Check application logs
tail -f /path/to/app/logs/app.log
```

### Network Diagnostics

Diagnose network issues:

```bash
# Check listening ports
netstat -tuln

# Check connections to a specific port
netstat -an | grep :80

# Test connectivity to a server
telnet example.com 80

# Trace network route
traceroute example.com

# Check DNS resolution
dig example.com
```

### Performance Monitoring

Monitor server performance:

```bash
# Monitor CPU and memory usage
top -c

# Monitor disk I/O
iostat -x 1

# Monitor network I/O
iftop

# Monitor system load
uptime

# Monitor all system resources
htop
```

### Configuration Validation

Validate server configurations:

```bash
# Validate Nginx configuration
nginx -t

# Validate Apache configuration
apache2ctl configtest

# Validate uWSGI configuration
uwsgi --check-config --ini /path/to/uwsgi.ini

# Validate SSL certificate
openssl x509 -in /path/to/cert.pem -text -noout
```

### Application Debugging

Debug the Python application:

```bash
# Run the application in debug mode
/path/to/venv/bin/python app.py --debug

# Check for syntax errors
/path/to/venv/bin/python -m py_compile app.py

# Test WSGI application
/path/to/venv/bin/python -c "from app import app; print(app)"

# Test database connection
/path/to/venv/bin/python -c "from app import db; print(db.engine.connect())"
```
