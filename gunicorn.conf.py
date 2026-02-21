"""
Gunicorn configuration for the Phonix platform.

Usage:
    gunicorn -c gunicorn.conf.py config.wsgi:application
"""
import multiprocessing
import os

# ─── Server Socket ────────────────────────────────────────────────────────────
bind = os.environ.get('GUNICORN_BIND', '0.0.0.0:8000')
backlog = 2048

# ─── Workers ──────────────────────────────────────────────────────────────────
workers = int(os.environ.get('GUNICORN_WORKERS', multiprocessing.cpu_count() * 2 + 1))
worker_class = 'sync'
worker_connections = 1000
max_requests = 1000           # Restart workers after this many requests (prevents memory leaks)
max_requests_jitter = 50      # Random jitter to prevent all workers restarting at once

# ─── Timeouts ─────────────────────────────────────────────────────────────────
timeout = 120                  # Worker silent for more than this many seconds is killed
graceful_timeout = 30          # After receiving QUIT, workers get this long to finish
keepalive = 5                  # Seconds to wait for requests on keep-alive connections

# ─── Logging ──────────────────────────────────────────────────────────────────
accesslog = os.environ.get('GUNICORN_ACCESS_LOG', '-')   # '-' = stdout
errorlog = os.environ.get('GUNICORN_ERROR_LOG', '-')     # '-' = stderr
loglevel = os.environ.get('GUNICORN_LOG_LEVEL', 'info')
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# ─── Process Naming ───────────────────────────────────────────────────────────
proc_name = 'phonix'

# ─── Security ─────────────────────────────────────────────────────────────────
limit_request_line = 8190
limit_request_fields = 100
limit_request_field_size = 8190

# ─── Server Mechanics ────────────────────────────────────────────────────────
preload_app = True             # Load app code before forking workers (saves memory)
daemon = False                 # Managed by systemd, so don't daemonize
tmp_upload_dir = None
