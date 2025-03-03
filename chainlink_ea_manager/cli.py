#!/usr/bin/env python3
"""
Command-line interface for the Chainlink EA Manager
"""

import os
import sys
import argparse
import logging
import colorama
from typing import List, Optional, Tuple

from chainlink_ea_manager.core.manager import EAManager

# Initialize colorama
colorama.init()

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s"
)

# ANSI escape codes for formatting
BOLD = colorama.Style.BRIGHT
RESET = colorama.Style.RESET_ALL
UNDERLINE = "\033[4m"
NO_UNDERLINE = "\033[24m"

def setup_parser() -> argparse.ArgumentParser:
    """
    Set up the argument parser for the CLI
    
    Returns:
        The configured argument parser
    """
    parser = argparse.ArgumentParser(
        description="Chainlink External Adapter Manager",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Initialize the environment
  ea-manager -i
  
  # Deploy a new adapter
  ea-manager -d coingecko
  
  # Upgrade an existing adapter
  ea-manager -u coingecko
  
  # Test an adapter
  ea-manager -t coingecko-redis LINK USD
  
  # List all supported adapters
  ea-manager -l
"""
    )
    
    # Add arguments
    parser.add_argument(
        "-i", "--initialize",
        action="store_true",
        help="Initialize a generic EA environment"
    )
    
    parser.add_argument(
        "-d", "--deploy",
        metavar="ADAPTER",
        help="Deploy a new external adapter"
    )
    
    parser.add_argument(
        "-u", "--upgrade",
        metavar="ADAPTER",
        help="Upgrade an existing external adapter"
    )
    
    parser.add_argument(
        "-t", "--test",
        metavar="CONTAINER",
        help="Send a test request to the specified adapter container"
    )
    
    parser.add_argument(
        "-l", "--list",
        action="store_true",
        help="List all supported external adapters"
    )
    
    parser.add_argument(
        "-v", "--version",
        action="store_true",
        help="Print the version and exit"
    )
    
    parser.add_argument(
        "params",
        nargs="*",
        help="Additional parameters for test request (FROM and TO)"
    )
    
    parser.add_argument(
        "--tag",
        help="Specify a specific tag to deploy or upgrade"
    )
    
    return parser
    
def print_version():
    """Print the version information"""
    version = "0.1.0"
    print(f"Chainlink EA Manager version: {BOLD}{version}{RESET}")
    
def initialize_environment(manager: EAManager):
    """
    Initialize the environment
    
    Args:
        manager: The EA Manager instance
    """
    print(f"{BOLD}Initializing new Docker environment...{RESET}")
    
    if manager.initialize_environment():
        print(f"\n{BOLD}Redis container info:{RESET}")
        print("containerName: redis-cache")
        print("IPaddress: 192.168.1.1")
        print("listnPort: 6379")
    else:
        print(f"{BOLD}Failed to initialize environment{RESET}")
        sys.exit(1)
        
def deploy_adapter(manager: EAManager, adapter_name: str, tag: Optional[str]):
    """
    Deploy a new adapter
    
    Args:
        manager: The EA Manager instance
        adapter_name: Name of the adapter to deploy
        tag: Specific tag to deploy (optional)
    """
    # If a tag was not specified, get available tags and prompt the user
    if not tag:
        tags = manager.get_available_tags(adapter_name)
        if not tags:
            print(f"{BOLD}No tags found for {adapter_name}{RESET}")
            sys.exit(1)
            
        print(f"Available tags for {adapter_name}:")
        for i, tag_name in enumerate(tags):
            print(f"{i}) {tag_name}")
            
        while True:
            try:
                selection = input(f"Select a tag (0-{len(tags)-1}): ")
                index = int(selection)
                if 0 <= index < len(tags):
                    tag = tags[index]
                    break
                else:
                    print(f"Invalid selection. Please enter a number between 0 and {len(tags)-1}.")
            except ValueError:
                print("Invalid input. Please enter a number.")
                
    print(f"{BOLD}Deploying {adapter_name} at version {tag}{RESET}")
    
    if manager.deploy_adapter(adapter_name, tag):
        print(f"{BOLD}Successfully deployed {adapter_name} adapter{RESET}")
    else:
        print(f"{BOLD}Failed to deploy {adapter_name} adapter{RESET}")
        sys.exit(1)
        
def upgrade_adapter(manager: EAManager, adapter_name: str, tag: Optional[str]):
    """
    Upgrade an existing adapter
    
    Args:
        manager: The EA Manager instance
        adapter_name: Name of the adapter to upgrade
        tag: Specific tag to upgrade to (optional)
    """
    # If a tag was not specified, get available tags and prompt the user
    if not tag:
        tags = manager.get_available_tags(adapter_name)
        if not tags:
            print(f"{BOLD}No tags found for {adapter_name}{RESET}")
            sys.exit(1)
            
        print(f"Available tags for {adapter_name}:")
        for i, tag_name in enumerate(tags):
            print(f"{i}) {tag_name}")
            
        while True:
            try:
                selection = input(f"Select a tag (0-{len(tags)-1}): ")
                index = int(selection)
                if 0 <= index < len(tags):
                    tag = tags[index]
                    break
                else:
                    print(f"Invalid selection. Please enter a number between 0 and {len(tags)-1}.")
            except ValueError:
                print("Invalid input. Please enter a number.")
                
    print(f"{BOLD}Stopping, removing, and redeploying {adapter_name} at version {tag}{RESET}")
    
    if manager.upgrade_adapter(adapter_name, tag):
        print(f"{BOLD}Successfully upgraded {adapter_name} adapter{RESET}")
    else:
        print(f"{BOLD}Failed to upgrade {adapter_name} adapter{RESET}")
        sys.exit(1)
        
def test_adapter(manager: EAManager, container_name: str, params: List[str]):
    """
    Test an adapter by sending a request
    
    Args:
        manager: The EA Manager instance
        container_name: Name of the container to test
        params: List of parameters (FROM and TO)
    """
    if len(params) < 2:
        print(f"{BOLD}Error: Missing parameters for test{RESET}")
        print("Usage: ea-manager -t CONTAINER FROM TO")
        sys.exit(1)
        
    from_param = params[0]
    to_param = params[1]
    
    print(f"{BOLD}Container:{RESET} {container_name}")
    print(f"{BOLD}FROM:{RESET}      {from_param}")
    print(f"{BOLD}TO:{RESET}        {to_param}")
    
    result = manager.test_adapter(container_name, from_param, to_param)
    
    if result is not None:
        print(f"{BOLD}{from_param} / {to_param} --> {RESET}{result}")
    else:
        print(f"{BOLD}Failed to test adapter{RESET}")
        sys.exit(1)
        
def list_adapters(manager: EAManager):
    """
    List all supported adapters
    
    Args:
        manager: The EA Manager instance
    """
    print(f"{BOLD}Listing Supported EAs:{RESET}")
    print("")
    
    adapters = manager.get_supported_adapters()
    if adapters:
        for adapter in sorted(adapters):
            print(f"  {adapter}")
    else:
        print("  No supported adapters found")
        
def main():
    """Main entry point for the CLI"""
    parser = setup_parser()
    args = parser.parse_args()
    
    # Create the EA Manager
    manager = EAManager()
    
    # Process the commands
    if args.version:
        print_version()
    elif args.initialize:
        initialize_environment(manager)
    elif args.deploy:
        deploy_adapter(manager, args.deploy, args.tag)
    elif args.upgrade:
        upgrade_adapter(manager, args.upgrade, args.tag)
    elif args.test:
        test_adapter(manager, args.test, args.params)
    elif args.list:
        list_adapters(manager)
    else:
        parser.print_help()
        
if __name__ == "__main__":
    main()