#!/usr/bin/env python3
"""Unified logging configuration for Trading KB."""

import logging
import sys
from pathlib import Path
from datetime import datetime


class TradingKBLogger:
    """Unified logger for Trading KB with console and file outputs."""
    
    def __init__(self, name: str = "trading_kb", log_dir: str = None):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)
        
        # Prevent duplicate handlers
        if self.logger.handlers:
            return
        
        # Log directory
        log_dir = log_dir or Path(__file__).parent.parent.parent / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # Log filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = log_dir / f"trading_kb_{timestamp}.log"
        
        # Log format
        log_format = logging.Formatter(
            "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(log_format)
        self.logger.addHandler(console_handler)
        
        # File handler
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(log_format)
        self.logger.addHandler(file_handler)
    
    def get_logger(self) -> logging.Logger:
        """Return the configured logger instance."""
        return self.logger
    
    def info(self, message: str):
        """Log info message."""
        self.logger.info(message)
    
    def warning(self, message: str):
        """Log warning message."""
        self.logger.warning(message)
    
    def error(self, message: str):
        """Log error message."""
        self.logger.error(message)
    
    def debug(self, message: str):
        """Log debug message."""
        self.logger.debug(message)


# Global logger instance
_logger_instance = None


def get_logger(name: str = "trading_kb"):
    """Get or create the global logger instance."""
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = TradingKBLogger(name)
    return _logger_instance.get_logger()


def log_info(message: str):
    """Convenience function to log info."""
    get_logger().info(message)


def log_warning(message: str):
    """Convenience function to log warning."""
    get_logger().warning(message)


def log_error(message: str):
    """Convenience function to log error."""
    get_logger().error(message)


def log_debug(message: str):
    """Convenience function to log debug."""
    get_logger().debug(message)
