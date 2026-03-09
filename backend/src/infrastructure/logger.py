import sys
import os
from loguru import logger

def setup_logger():
    """
    Configures the application logger.
    Removes the default handler and sets up routing to the console and log files.
    """
    # Remove the default logger to prevent duplicate prints
    logger.remove()

    # Add console logger - colorful and readable, logs INFO level and above
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level="INFO",
        colorize=True
    )

    # Create logs directory if it doesn't exist
    os.makedirs("logs", exist_ok=True)

    # Add file logger - saves everything including DEBUG for investigation
    # Rotation creates a new file every midnight, retention keeps logs for 30 days
    logger.add(
        "logs/stockup_{time:YYYY-MM-DD}.log",
        rotation="00:00",
        retention="30 days",
        level="DEBUG",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        encoding="utf-8"
    )

    return logger

# the configured logger instance for the rest of the project to use
app_logger = setup_logger()