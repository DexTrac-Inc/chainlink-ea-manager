#!/usr/bin/env python3
"""
Docker utilities for the Chainlink EA Manager
"""

import os
import subprocess
import platform
import logging
from typing import Tuple, List, Dict

logger = logging.getLogger(__name__)

def ensure_docker_running() -> bool:
    """
    Ensure Docker is installed and running
    If not installed, attempt to install it
    
    Returns:
        bool: True if Docker is running, False otherwise
    """
    logger.info("Checking if Docker is installed and running...")
    
    # Check if Docker is installed
    if not is_docker_installed():
        logger.warning("Docker is not installed")
        
        # Check if user has sudo privileges
        if not has_sudo_privileges():
            logger.error("Cannot install Docker: insufficient privileges")
            logger.error("Please install Docker manually and run the command again")
            return False
            
        # Try to install Docker
        if not install_docker():
            logger.error("Failed to install Docker")
            return False
            
    # Check if Docker is running
    if not is_docker_running():
        logger.warning("Docker is not running")
        
        # Try to start Docker
        if not start_docker():
            logger.error("Failed to start Docker")
            return False
            
    logger.info("Docker is installed and running")
    return True
    
def is_docker_installed() -> bool:
    """
    Check if Docker is installed
    
    Returns:
        bool: True if Docker is installed, False otherwise
    """
    try:
        subprocess.run(
            ["docker", "--version"], 
            capture_output=True, 
            check=True
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False
        
def is_docker_running() -> bool:
    """
    Check if Docker daemon is running
    
    Returns:
        bool: True if Docker is running, False otherwise
    """
    try:
        subprocess.run(
            ["docker", "info"], 
            capture_output=True, 
            check=True
        )
        return True
    except subprocess.CalledProcessError:
        return False
        
def has_sudo_privileges() -> bool:
    """
    Check if the user has sudo privileges
    
    Returns:
        bool: True if the user has sudo privileges, False otherwise
    """
    try:
        subprocess.run(
            ["sudo", "-n", "true"],
            capture_output=True,
            check=True
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False
        
def install_docker() -> bool:
    """
    Install Docker
    
    Returns:
        bool: True if Docker was installed successfully, False otherwise
    """
    system = platform.system()
    
    if system == "Linux":
        return install_docker_linux()
    elif system == "Darwin":  # macOS
        logger.error("Docker installation on macOS is not supported")
        logger.error("Please install Docker Desktop manually: https://docs.docker.com/desktop/install/mac-install/")
        return False
    elif system == "Windows":
        logger.error("Docker installation on Windows is not supported")
        logger.error("Please install Docker Desktop manually: https://docs.docker.com/desktop/install/windows-install/")
        return False
    else:
        logger.error(f"Unsupported operating system: {system}")
        return False
        
def install_docker_linux() -> bool:
    """
    Install Docker on Linux
    
    Returns:
        bool: True if Docker was installed successfully, False otherwise
    """
    try:
        # Detect the Linux distribution
        if os.path.exists("/etc/debian_version"):
            # Debian, Ubuntu, etc.
            return install_docker_debian()
        elif os.path.exists("/etc/redhat-release"):
            # RHEL, CentOS, Fedora, etc.
            return install_docker_redhat()
        else:
            logger.error("Unsupported Linux distribution")
            logger.error("Please install Docker manually: https://docs.docker.com/engine/install/")
            return False
    except Exception as e:
        logger.error(f"Failed to install Docker: {str(e)}")
        return False
        
def install_docker_debian() -> bool:
    """
    Install Docker on Debian-based systems
    
    Returns:
        bool: True if Docker was installed successfully, False otherwise
    """
    try:
        logger.info("Installing Docker on Debian-based system...")
        
        # Update package index
        subprocess.run(
            ["sudo", "apt-get", "update"],
            check=True
        )
        
        # Install prerequisites
        subprocess.run(
            ["sudo", "apt-get", "install", "-y",
             "apt-transport-https", "ca-certificates", 
             "curl", "gnupg", "lsb-release"],
            check=True
        )
        
        # Add Docker's official GPG key
        subprocess.run(
            ["curl", "-fsSL", "https://download.docker.com/linux/debian/gpg", 
             "|", "sudo", "gpg", "--dearmor", "-o", 
             "/usr/share/keyrings/docker-archive-keyring.gpg"],
            shell=True,
            check=True
        )
        
        # Set up the stable repository
        subprocess.run(
            ["echo", 
             "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] " +
             "https://download.docker.com/linux/debian " +
             "$(lsb_release -cs) stable", 
             "|", "sudo", "tee", "/etc/apt/sources.list.d/docker.list", ">", "/dev/null"],
            shell=True,
            check=True
        )
        
        # Update the package index again
        subprocess.run(
            ["sudo", "apt-get", "update"],
            check=True
        )
        
        # Install Docker Engine
        subprocess.run(
            ["sudo", "apt-get", "install", "-y", "docker-ce", "docker-ce-cli", "containerd.io"],
            check=True
        )
        
        # Add current user to the docker group
        username = os.environ.get("SUDO_USER") or os.environ.get("USER")
        subprocess.run(
            ["sudo", "usermod", "-aG", "docker", username],
            check=True
        )
        
        logger.info("Docker installed successfully")
        return True
        
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to install Docker: {str(e)}")
        return False
        
def install_docker_redhat() -> bool:
    """
    Install Docker on Red Hat-based systems
    
    Returns:
        bool: True if Docker was installed successfully, False otherwise
    """
    try:
        logger.info("Installing Docker on Red Hat-based system...")
        
        # Remove old versions if any
        subprocess.run(
            ["sudo", "yum", "remove", "-y", "docker", "docker-client", 
             "docker-client-latest", "docker-common", "docker-latest", 
             "docker-latest-logrotate", "docker-logrotate", "docker-engine"],
            check=True
        )
        
        # Install prerequisites
        subprocess.run(
            ["sudo", "yum", "install", "-y", "yum-utils"],
            check=True
        )
        
        # Add Docker repository
        subprocess.run(
            ["sudo", "yum-config-manager", "--add-repo", 
             "https://download.docker.com/linux/centos/docker-ce.repo"],
            check=True
        )
        
        # Install Docker Engine
        subprocess.run(
            ["sudo", "yum", "install", "-y", "docker-ce", "docker-ce-cli", "containerd.io"],
            check=True
        )
        
        # Start Docker
        subprocess.run(
            ["sudo", "systemctl", "start", "docker"],
            check=True
        )
        
        # Enable Docker to start on boot
        subprocess.run(
            ["sudo", "systemctl", "enable", "docker"],
            check=True
        )
        
        # Add current user to the docker group
        username = os.environ.get("SUDO_USER") or os.environ.get("USER")
        subprocess.run(
            ["sudo", "usermod", "-aG", "docker", username],
            check=True
        )
        
        logger.info("Docker installed successfully")
        return True
        
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to install Docker: {str(e)}")
        return False
        
def start_docker() -> bool:
    """
    Start Docker daemon
    
    Returns:
        bool: True if Docker was started successfully, False otherwise
    """
    try:
        system = platform.system()
        
        if system == "Linux":
            subprocess.run(
                ["sudo", "systemctl", "start", "docker"],
                check=True
            )
            logger.info("Docker started successfully")
            return True
        else:
            logger.error(f"Starting Docker daemon on {system} is not supported")
            logger.error("Please start Docker manually")
            return False
            
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to start Docker: {str(e)}")
        return False