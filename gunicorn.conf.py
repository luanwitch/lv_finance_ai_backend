import os

port = os.getenv("PORT", "8000")
bind = os.getenv("GUNICORN_BIND", f"0.0.0.0:{port}")
workers = int(os.getenv("GUNICORN_WORKERS", "3"))
worker_class = "gthread"
threads = int(os.getenv("GUNICORN_THREADS", "2"))
timeout = int(os.getenv("GUNICORN_TIMEOUT", "120"))
keepalive = 5
accesslog = "-"
errorlog = "-"
loglevel = os.getenv("LOG_LEVEL", "info")
