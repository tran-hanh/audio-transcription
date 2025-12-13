#!/usr/bin/env python3
"""
Gunicorn configuration file to ensure gevent worker is used correctly.
This file can be referenced with: gunicorn -c gunicorn_config.py backend.app:app
"""

import os
import multiprocessing

# Server socket
bind = "0.0.0.0:{}".format(int(os.environ.get('PORT', 10000)))
backlog = 2048

# Worker processes
workers = 2
worker_class = 'gevent'
worker_connections = 1000
timeout = 7200  # 120 minutes - increased for very long audio files (up to 20 minutes transcription time)
keepalive = 5
graceful_timeout = 300  # Give workers 5 minutes to finish before force kill
max_requests = 1000  # Restart workers after this many requests to prevent memory leaks
max_requests_jitter = 50  # Add randomness to prevent all workers restarting at once

# Logging
loglevel = 'info'
accesslog = '-'
errorlog = '-'

# Process naming
proc_name = 'audio-transcription-api'

# Server mechanics
daemon = False
pidfile = None
umask = 0
user = None
group = None
tmp_upload_dir = None

