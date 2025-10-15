import os


def get_upload_dir() -> str:
    return os.getenv("UPLOAD_DIR", "./var/uploads")


HTTP_MAX_RETRIES = int(os.getenv("HTTP_MAX_RETRIES", "2"))
HTTP_BACKOFF_BASE = float(os.getenv("HTTP_BACKOFF_BASE", "0.2"))
HTTP_CONNECT_TIMEOUT = float(os.getenv("HTTP_CONNECT_TIMEOUT", "2.0"))
HTTP_READ_TIMEOUT = float(os.getenv("HTTP_READ_TIMEOUT", "5.0"))
