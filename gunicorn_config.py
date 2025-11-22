# Gunicorn configuration for Render free tier (512MB RAM limit)

# Use only 1 worker to minimize memory usage
workers = 1

# Use threads instead of workers (more memory efficient)
threads = 2

# Limit worker lifetime to prevent memory leaks
max_requests = 100
max_requests_jitter = 10

# Timeout
timeout = 120

# Bind
bind = "0.0.0.0:8050"

# Logging
loglevel = "info"
accesslog = "-"
errorlog = "-"
