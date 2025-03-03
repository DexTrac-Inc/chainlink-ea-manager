#!/usr/bin/env python3
"""
Logging utilities for the Chainlink EA Manager
"""

import os
import logging
from datetime import datetime
from typing import Optional

class EALogger:
    """
    Logger class for the Chainlink EA Manager
    """
    
    def __init__(self, log_dir: Optional[str] = None):
        """
        Initialize the logger
        
        Args:
            log_dir: Directory to store log files. If None, logs to ~/.chainlink_ea_manager/logs
        """
        # Set up log directory
        if not log_dir:
            log_dir = os.path.expanduser("~/.chainlink_ea_manager/logs")
            
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
            
        # Create a log file with timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d")
        log_file = os.path.join(log_dir, f"ea_manager_{timestamp}.log")
        
        # Configure logging
        self.logger = logging.getLogger("ea_manager")
        self.logger.setLevel(logging.INFO)
        
        # Create file handler
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.INFO)
        
        # Create formatter
        formatter = logging.Formatter(
            "%(asctime)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        file_handler.setFormatter(formatter)
        
        # Add handlers
        self.logger.addHandler(file_handler)
        
    def log_operation(self, operation: str, adapter: Optional[str] = None, success: bool = True, details: Optional[str] = None):
        """
        Log an operation
        
        Args:
            operation: Type of operation (initialize, deploy, upgrade, test)
            adapter: Name of the adapter (if applicable)
            success: Whether the operation was successful
            details: Additional details
        """
        status = "SUCCESS" if success else "FAILURE"
        
        message = f"{operation} - {status}"
        if adapter:
            message += f" - Adapter: {adapter}"
        if details:
            message += f" - Details: {details}"
            
        if success:
            self.logger.info(message)
        else:
            self.logger.error(message)
            
    def log_initialize(self, success: bool, details: Optional[str] = None):
        """
        Log an initialization operation
        
        Args:
            success: Whether the operation was successful
            details: Additional details
        """
        self.log_operation("INITIALIZE", None, success, details)
        
    def log_deploy(self, adapter: str, tag: str, success: bool, details: Optional[str] = None):
        """
        Log a deploy operation
        
        Args:
            adapter: Name of the adapter
            tag: Tag of the deployed version
            success: Whether the operation was successful
            details: Additional details
        """
        details_with_tag = f"Tag: {tag}"
        if details:
            details_with_tag += f", {details}"
            
        self.log_operation("DEPLOY", adapter, success, details_with_tag)
        
    def log_upgrade(self, adapter: str, tag: str, success: bool, details: Optional[str] = None):
        """
        Log an upgrade operation
        
        Args:
            adapter: Name of the adapter
            tag: Tag of the upgraded version
            success: Whether the operation was successful
            details: Additional details
        """
        details_with_tag = f"Tag: {tag}"
        if details:
            details_with_tag += f", {details}"
            
        self.log_operation("UPGRADE", adapter, success, details_with_tag)
        
    def log_test(self, container: str, from_param: str, to_param: str, success: bool, result: Optional[str] = None):
        """
        Log a test operation
        
        Args:
            container: Name of the container
            from_param: FROM parameter
            to_param: TO parameter
            success: Whether the operation was successful
            result: Result of the test
        """
        details = f"FROM: {from_param}, TO: {to_param}"
        if result:
            details += f", Result: {result}"
            
        self.log_operation("TEST", container, success, details)
        
def get_logger(log_dir: Optional[str] = None) -> EALogger:
    """
    Get a logger instance
    
    Args:
        log_dir: Directory to store log files
        
    Returns:
        Logger instance
    """
    return EALogger(log_dir)