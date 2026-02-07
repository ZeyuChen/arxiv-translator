import logging
import logging.handlers
import os
import sys

# Define log directory from environment or default to local logs
LOG_DIR = os.getenv("ARXIV_TRANSLATOR_LOG_DIR", os.path.join(os.getcwd(), "logs"))
if not os.path.exists(LOG_DIR):
    try:
        os.makedirs(LOG_DIR)
    except OSError:
        # Fallback to tmp if permission denied or other issue
        LOG_DIR = "/tmp/arxiv_translator_logs"
        os.makedirs(LOG_DIR, exist_ok=True)

LOG_FILE = os.path.join(LOG_DIR, "translator.log")

def setup_logger(name: str) -> logging.Logger:
    """
    Sets up a logger with a rotating file handler and a console handler.
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    # Prevent adding handlers multiple times if logger is already set up
    if logger.hasHandlers():
        return logger

    # Formatter
    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # 1. Rotating File Handler (10MB per file, keep last 5)
    try:
        file_handler = logging.handlers.RotatingFileHandler(
            LOG_FILE, maxBytes=10*1024*1024, backupCount=5, encoding="utf-8"
        )
        file_handler.setFormatter(formatter)
        file_handler.setLevel(logging.INFO)
        logger.addHandler(file_handler)
    except Exception as e:
        sys.stderr.write(f"Failed to setup file logging to {LOG_FILE}: {e}\n")

    # 2. Console Handler (Standard Error for logs, keeping stdout clean for IPC)
    # Important: We write logs to STDERR so we don't pollute STDOUT which is used for IPC (PROGRESS:...)
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.INFO)
    logger.addHandler(console_handler)

    return logger

# Create a default logger
logger = setup_logger("arxiv_translator")

def log_ipc(message: str):
    """
    Logs an IPC message to STDOUT.
    This is used for communicating progress to the calling process (Backend).
    """
    print(message, flush=True)

