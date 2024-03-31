workers = 3  # Set the number of worker processes
worker_class = "gthread"  # Use threads for worker processes
threads = 3  # Set the number of threads per worker
worker_connections = 1000  # Set the maximum number of simultaneous clients

max_requests = 1000  # Maximum number of requests a worker will process before restarting
max_requests_jitter = 100  # The maximum jitter to add to the max_requests setting

timeout = 3000  # Set the maximum time (in seconds) that the worker can process a request

# Memory-related settings
max_requests = 0  # Disable automatic worker restarts based on the number of requests
max_requests_jitter = 0  # Disable jitter for max_requests

# Logging
accesslog = "-"  # Log to stdout
errorlog = "-"  # Log to stderr

# gunicorn -c gunicorn_config.py your_app:app