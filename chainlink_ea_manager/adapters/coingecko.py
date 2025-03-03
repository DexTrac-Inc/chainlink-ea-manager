#!/usr/bin/env python3
"""
CoinGecko adapter configuration
"""

from typing import Dict, Optional

class CoinGeckoAdapter:
    """
    Specific configuration for the CoinGecko adapter
    """
    
    @staticmethod
    def get_env_vars(api_key: Optional[str], sub_tier: Optional[str]) -> Dict[str, str]:
        """
        Get environment variables specific to CoinGecko
        
        Args:
            api_key: API key for CoinGecko
            sub_tier: Subscription tier for CoinGecko
            
        Returns:
            Dictionary of environment variables
        """
        env_vars = {
            'CACHE_KEY_GROUP': 'coingecko',
            'RATE_LIMIT_API_PROVIDER': 'coingecko',
            'METRICS_NAME': 'coingecko',
        }
        
        if api_key:
            env_vars['API_KEY'] = api_key
            
        if sub_tier:
            env_vars['RATE_LIMIT_API_TIER'] = sub_tier
            
        return env_vars
        
    @staticmethod
    def get_default_config() -> Dict[str, str]:
        """
        Get default configuration for CoinGecko
        
        Returns:
            Dictionary of default configuration
        """
        return {
            'ip': '192.168.1.113',
            'port': '1113',
            'api_key_var': 'COINGECKO_API_KEY',
            'sub_tier_var': 'COINGECKO_SUB_HTTP'
        }