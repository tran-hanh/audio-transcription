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
timeout = 1800  # 30 minutes
keepalive = 5

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

