#!/usr/bin/env python3
"""
Configuration manager for the Chainlink EA Manager
"""

import os
import re
import json
import yaml
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Union

logger = logging.getLogger(__name__)

class ConfigManager:
    """
    Manages configuration for the Chainlink EA Manager
    """
    
    def __init__(self, config_path: str = None):
        """
        Initialize the configuration manager
        
        Args:
            config_path: Path to the configuration file. If None, uses default location.
        """
        self.logger = logging.getLogger(__name__)
        
        # Set default configuration path
        if not config_path:
            self.config_dir = os.path.expanduser("~/.chainlink_ea_manager")
            self.config_path = os.path.join(self.config_dir, "config.yaml")
        else:
            self.config_path = config_path
            self.config_dir = os.path.dirname(config_path)
            
        # Create directory if it doesn't exist
        if not os.path.exists(self.config_dir):
            os.makedirs(self.config_dir)
            
        # Load or create configuration
        self.config = self._load_or_create_config()
        
        # Load API keys and chain variables from original config files
        self.api_keys = self._load_api_keys()
        self.chain_vars = self._load_chain_vars()
        
        # Create adapter configurations
        self.adapter_configs = self._create_adapter_configs()
        
    def _load_or_create_config(self) -> Dict:
        """
        Load the existing configuration or create a new one
        
        Returns:
            The configuration dictionary
        """
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r') as f:
                    config = yaml.safe_load(f)
                    if not config:
                        config = {}
                    return config
            except Exception as e:
                self.logger.error(f"Failed to load configuration: {str(e)}")
                return {}
        else:
            # Create default configuration
            default_config = {
                "redis": {
                    "host": "192.168.1.1",
                    "port": 6379,
                    "maxclients": 2500
                },
                "docker": {
                    "network_name": "eas-net",
                    "subnet": "192.168.0.0/16",
                    "gateway": "192.168.0.1"
                },
                "adapters": {}
            }
            
            try:
                with open(self.config_path, 'w') as f:
                    yaml.dump(default_config, f)
                return default_config
            except Exception as e:
                self.logger.error(f"Failed to create configuration: {str(e)}")
                return default_config
                
    def _load_api_keys(self) -> Dict:
        """
        Load API keys from the api_keys file
        
        Returns:
            Dictionary of API keys
        """
        api_keys_path = os.path.join(os.getcwd(), "api_keys")
        api_keys = {}
        
        if os.path.exists(api_keys_path):
            try:
                with open(api_keys_path, 'r') as f:
                    content = f.read()
                    
                # Extract export statements
                export_pattern = re.compile(r'export\s+(\w+)=([^\n]*)')
                matches = export_pattern.findall(content)
                
                for name, value in matches:
                    # Clean up the value (remove quotes, etc.)
                    value = value.strip()
                    if value.startswith('"') and value.endswith('"'):
                        value = value[1:-1]
                    elif value.startswith("'") and value.endswith("'"):
                        value = value[1:-1]
                        
                    api_keys[name] = value
                    
                return api_keys
                
            except Exception as e:
                self.logger.error(f"Failed to load API keys: {str(e)}")
                return {}
        else:
            self.logger.warning(f"API keys file not found: {api_keys_path}")
            return {}
            
    def _load_chain_vars(self) -> Dict:
        """
        Load chain variables from the misc_vars file
        
        Returns:
            Dictionary of chain variables
        """
        misc_vars_path = os.path.join(os.getcwd(), "misc_vars")
        chain_vars = {}
        
        if os.path.exists(misc_vars_path):
            try:
                with open(misc_vars_path, 'r') as f:
                    content = f.read()
                    
                # Extract RPC URLs and chain IDs
                rpc_pattern = re.compile(r'([A-Za-z0-9_]+)_RPC_URL=([^\n]*)')
                chain_id_pattern = re.compile(r'([A-Za-z0-9_]+)_CHAIN_ID=([^\n]*)')
                
                rpc_matches = rpc_pattern.findall(content)
                chain_id_matches = chain_id_pattern.findall(content)
                
                # Process RPC URLs
                for chain, url in rpc_matches:
                    url = url.strip()
                    if url:
                        if chain not in chain_vars:
                            chain_vars[chain] = {}
                        chain_vars[chain]['rpc_url'] = url
                        
                # Process chain IDs
                for chain, chain_id in chain_id_matches:
                    chain_id = chain_id.strip()
                    if chain_id:
                        if chain not in chain_vars:
                            chain_vars[chain] = {}
                        try:
                            chain_vars[chain]['chain_id'] = int(chain_id)
                        except ValueError:
                            self.logger.warning(f"Invalid chain ID for {chain}: {chain_id}")
                            
                return chain_vars
                
            except Exception as e:
                self.logger.error(f"Failed to load chain variables: {str(e)}")
                return {}
        else:
            self.logger.warning(f"Misc vars file not found: {misc_vars_path}")
            return {}
            
    def _create_adapter_configs(self) -> Dict:
        """
        Create adapter configurations based on the files in the externalAdapters directory
        
        Returns:
            Dictionary of adapter configurations
        """
        adapters_dir = os.path.join(os.getcwd(), "externalAdapters")
        adapter_configs = {}
        
        if os.path.exists(adapters_dir):
            try:
                for adapter_file in os.listdir(adapters_dir):
                    adapter_path = os.path.join(adapters_dir, adapter_file)
                    
                    # Skip directories and non-executable files
                    if os.path.isdir(adapter_path) or not os.access(adapter_path, os.X_OK):
                        continue
                        
                    adapter_name = adapter_file
                    
                    # Extract configuration from the adapter script
                    with open(adapter_path, 'r') as f:
                        content = f.read()
                        
                    # Extract IP address
                    ip_match = re.search(r'--ip\s+(\d+\.\d+\.\d+\.\d+)', content)
                    ip = ip_match.group(1) if ip_match else None
                    
                    # Extract port
                    port_match = re.search(r'-p\s+(\d+):(\d+)', content)
                    port = port_match.group(1) if port_match else None
                    
                    # Extract API key variable name
                    api_key_match = re.search(r'-e\s+API_KEY=\$([A-Za-z0-9_]+)', content)
                    api_key_var = api_key_match.group(1) if api_key_match else None
                    
                    # Extract subscription tier variable name
                    sub_tier_match = re.search(r'-e\s+RATE_LIMIT_API_TIER=\$([A-Za-z0-9_]+)', content)
                    sub_tier_var = sub_tier_match.group(1) if sub_tier_match else None
                    
                    # Create adapter configuration
                    adapter_configs[adapter_name] = {
                        'ip': ip,
                        'port': port,
                        'api_key_var': api_key_var,
                        'sub_tier_var': sub_tier_var
                    }
                    
                return adapter_configs
                
            except Exception as e:
                self.logger.error(f"Failed to create adapter configurations: {str(e)}")
                return {}
        else:
            self.logger.warning(f"External adapters directory not found: {adapters_dir}")
            return {}
            
    def get_adapter_config(self, adapter_name: str) -> Optional[Dict]:
        """
        Get the configuration for a specific adapter
        
        Args:
            adapter_name: Name of the adapter
            
        Returns:
            The adapter configuration, or None if not found
        """
        return self.adapter_configs.get(adapter_name)
        
    def get_api_key(self, adapter_name: str) -> Optional[str]:
        """
        Get the API key for a specific adapter
        
        Args:
            adapter_name: Name of the adapter
            
        Returns:
            The API key, or None if not found
        """
        adapter_config = self.get_adapter_config(adapter_name)
        if not adapter_config:
            return None
            
        api_key_var = adapter_config.get('api_key_var')
        if not api_key_var:
            return None
            
        return self.api_keys.get(api_key_var)
        
    def get_subscription_tier(self, adapter_name: str) -> Optional[str]:
        """
        Get the subscription tier for a specific adapter
        
        Args:
            adapter_name: Name of the adapter
            
        Returns:
            The subscription tier, or None if not found
        """
        adapter_config = self.get_adapter_config(adapter_name)
        if not adapter_config:
            return None
            
        sub_tier_var = adapter_config.get('sub_tier_var')
        if not sub_tier_var:
            return None
            
        return self.api_keys.get(sub_tier_var)
        
    def get_supported_adapters(self) -> List[str]:
        """
        Get a list of all supported adapters
        
        Returns:
            List of adapter names
        """
        return list(self.adapter_configs.keys())
        
    def save_config(self) -> bool:
        """
        Save the current configuration to the configuration file
        
        Returns:
            True if successful, False otherwise
        """
        try:
            with open(self.config_path, 'w') as f:
                yaml.dump(self.config, f)
            return True
        except Exception as e:
            self.logger.error(f"Failed to save configuration: {str(e)}")
            return False