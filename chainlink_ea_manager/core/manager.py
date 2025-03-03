#!/usr/bin/env python3
"""
Chainlink External Adapter Manager
Main module for managing Chainlink External Adapters
"""

import os
import json
import yaml
import logging
import subprocess
import docker
from typing import Dict, List, Optional, Union

from chainlink_ea_manager.utils.docker_utils import ensure_docker_running
from chainlink_ea_manager.config.config_manager import ConfigManager
from chainlink_ea_manager.utils.logger import get_logger


class EAManager:
    """Manager for Chainlink External Adapters"""
    
    def __init__(self, config_path: str = None, log_dir: str = None):
        """
        Initialize the External Adapter Manager
        
        Args:
            config_path: Path to the configuration file. If None, uses default location.
            log_dir: Directory to store log files. If None, uses default location.
        """
        self.logger = logging.getLogger(__name__)
        self.config = ConfigManager(config_path)
        self.docker_client = docker.from_env()
        
        # Initialize operation logger
        self.op_logger = get_logger(log_dir)
        
    def initialize_environment(self) -> bool:
        """
        Initialize a new Docker environment for External Adapters
        - Install Docker if not installed
        - Create Docker network
        - Deploy Redis container
        
        Returns:
            bool: True if successful, False otherwise
        """
        self.logger.info("Initializing new Docker environment...")
        
        # Ensure Docker is installed and running
        if not ensure_docker_running():
            return False
            
        # Create Docker network if it doesn't exist
        try:
            networks = self.docker_client.networks.list(names=['eas-net'])
            if not networks:
                self.logger.info("Creating Docker network...")
                self.docker_client.networks.create(
                    name='eas-net',
                    driver='bridge',
                    ipam=docker.types.IPAMConfig(
                        pool_configs=[docker.types.IPAMPool(
                            subnet='192.168.0.0/16',
                            gateway='192.168.0.1'
                        )]
                    )
                )
                self.logger.info("Docker network created successfully")
            else:
                self.logger.info("Docker network already exists")
                
            # Create Redis directory for volume if it doesn't exist
            redis_dir = os.path.expanduser('~/.redis')
            if not os.path.exists(redis_dir):
                self.logger.info("Creating Redis volume directory...")
                os.makedirs(redis_dir)
                
            # Check if Redis container already exists
            existing_containers = self.docker_client.containers.list(
                all=True, 
                filters={"name": "redis-cache"}
            )
            
            if existing_containers:
                self.logger.info("Redis container already exists")
            else:
                # Deploy Redis container
                self.logger.info("Deploying Redis container...")
                self.docker_client.containers.run(
                    image='redis',
                    name='redis-cache',
                    detach=True,
                    restart_policy={"Name": "unless-stopped"},
                    network_mode=None,  # We'll connect it to the network separately
                    ports={'6379/tcp': 6379},
                    volumes={redis_dir: {'bind': '/data', 'mode': 'rw'}},
                    command='redis-server --maxclients 2500'
                )
                
                # Connect container to the network with specific IP
                try:
                    container = self.docker_client.containers.get('redis-cache')
                    network = self.docker_client.networks.get('eas-net')
                    network.connect(container, ipv4_address='192.168.1.1')
                except Exception as e:
                    self.logger.warning(f"Failed to set static IP for Redis: {str(e)}")
                    # If setting IP fails, just connect to the network without a static IP
                    try:
                        network.connect(container)
                    except Exception as inner_e:
                        self.logger.error(f"Failed to connect Redis to network: {str(inner_e)}")
                self.logger.info("Redis container deployed successfully")
                
            self.logger.info("Environment initialization completed successfully")
            self.op_logger.log_initialize(True)
            return True
            
        except Exception as e:
            error_msg = f"Failed to initialize environment: {str(e)}"
            self.logger.error(error_msg)
            self.op_logger.log_initialize(False, error_msg)
            return False
            
    def get_available_tags(self, adapter_name: str) -> List[str]:
        """
        Get available tags for a specific adapter
        
        Args:
            adapter_name: Name of the adapter
            
        Returns:
            List of available tags
        """
        repo = f"public.ecr.aws/chainlink/adapters/{adapter_name}-adapter"
        
        try:
            # Use skopeo to list available tags
            result = subprocess.run(
                ["skopeo", "list-tags", f"docker://{repo}"],
                capture_output=True,
                text=True,
                check=True
            )
            
            # Parse the output
            tags_data = json.loads(result.stdout)
            tags = sorted(tags_data.get('Tags', []), reverse=True)
            
            # Return top 10 tags
            return tags[:10]
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Failed to get tags for {adapter_name}: {e}")
            return []
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse tags for {adapter_name}: {e}")
            return []
            
    def deploy_adapter(self, adapter_name: str, tag: str = None) -> bool:
        """
        Deploy a new External Adapter
        
        Args:
            adapter_name: Name of the adapter to deploy
            tag: Specific tag to deploy. If None, user will be prompted to select
            
        Returns:
            bool: True if successful, False otherwise
        """
        # Get available tags if not specified
        if not tag:
            tags = self.get_available_tags(adapter_name)
            if not tags:
                self.logger.error(f"No tags found for {adapter_name}")
                return False
                
            # In a CLI tool, we would prompt the user here
            # For now, just use the latest tag
            tag = tags[0]
            
        # Load adapter configuration
        adapter_config = self.config.get_adapter_config(adapter_name)
        if not adapter_config:
            self.logger.error(f"No configuration found for adapter {adapter_name}")
            return False
            
        # Check if the Docker network exists
        try:
            networks = self.docker_client.networks.list(names=['eas-net'])
            if not networks:
                self.logger.error("Docker network 'eas-net' does not exist. Please run 'ea-manager -i' first.")
                return False
        except Exception as e:
            self.logger.error(f"Failed to check Docker networks: {str(e)}")
            return False
            
        try:
            # Create environment variables dictionary
            env_vars = {
                'EA_PORT': adapter_config.get('port', '1113'),
                'CACHE_ENABLED': 'true',
                'CACHE_TYPE': 'redis',
                'CACHE_KEY_GROUP': adapter_name,
                'CACHE_REDIS_HOST': '192.168.1.1',
                'CACHE_REDIS_PORT': '6379',
                'CACHE_REDIS_TIMEOUT': '10000',
                'RATE_LIMIT_ENABLED': 'true',
                'WARMUP_ENABLED': 'true',
                'RATE_LIMIT_API_PROVIDER': adapter_name,
                'REQUEST_COALESCING_ENABLED': 'true',
                'REQUEST_COALESCING_INTERVAL': '100',
                'REQUEST_COALESCING_INTERVAL_MAX': '1000', 
                'REQUEST_COALESCING_INTERVAL_COEFFICIENT': '2',
                'REQUEST_COALESCING_ENTROPY_MAX': '0',
                'LOG_LEVEL': 'info',
                'DEBUG': 'false',
                'API_VERBOSE': 'false',
                'EXPERIMENTAL_METRICS_ENABLED': 'true',
                'METRICS_NAME': adapter_name,
                'RETRY': '1',
                'TIMEOUT': '30000'
            }
            
            # Add API key if available
            api_key = self.config.get_api_key(adapter_name)
            if api_key:
                env_vars['API_KEY'] = api_key
                
            # Add subscription tier if available
            sub_tier = self.config.get_subscription_tier(adapter_name)
            if sub_tier:
                env_vars['RATE_LIMIT_API_TIER'] = sub_tier
                
            # Deploy container
            container_name = f"{adapter_name}-redis"
            image_name = f"public.ecr.aws/chainlink/adapters/{adapter_name}-adapter:{tag}"
            
            # Check if container already exists
            existing_containers = self.docker_client.containers.list(
                all=True, 
                filters={"name": container_name}
            )
            
            if existing_containers:
                self.logger.warning(f"Container {container_name} already exists. Removing...")
                for container in existing_containers:
                    container.remove(force=True)
                    
            # Deploy new container
            self.logger.info(f"Deploying {adapter_name} adapter with tag {tag}")
            
            ip_address = adapter_config.get('ip', '192.168.1.113')
            port = adapter_config.get('port', '1113')
            
            # Create network config to include the IP address
            network_config = {
                'eas-net': {
                    'ipv4_address': ip_address
                }
            }
            
            self.docker_client.containers.run(
                image=image_name,
                name=container_name,
                detach=True,
                restart_policy={"Name": "unless-stopped"},
                network_mode=None,  # We'll connect it to the network separately
                ports={f"{port}/tcp": int(port)},
                environment=env_vars,
                labels={
                    'prometheus-scrape.enabled': 'true',
                    'prometheus-scrape.job_name': container_name,
                    'prometheus-scrape.port': '9080',
                    'prometheus-scrape.metrics_path': '/metrics'
                }
            )
            
            # Connect container to the network with specific IP
            try:
                container = self.docker_client.containers.get(container_name)
                network = self.docker_client.networks.get('eas-net')
                network.connect(container, ipv4_address=ip_address)
            except Exception as e:
                self.logger.warning(f"Failed to set static IP: {str(e)}")
                # If setting IP fails, just connect to the network without a static IP
                try:
                    network.connect(container)
                except Exception as inner_e:
                    self.logger.error(f"Failed to connect to network: {str(inner_e)}")
            
            self.logger.info(f"Successfully deployed {adapter_name} adapter")
            self.op_logger.log_deploy(adapter_name, tag, True)
            return True
            
        except Exception as e:
            error_msg = f"Failed to deploy {adapter_name} adapter: {str(e)}"
            self.logger.error(error_msg)
            self.op_logger.log_deploy(adapter_name, tag, False, error_msg)
            return False
            
    def upgrade_adapter(self, adapter_name: str, tag: str = None) -> bool:
        """
        Upgrade an existing External Adapter
        
        Args:
            adapter_name: Name of the adapter to upgrade
            tag: Specific tag to upgrade to. If None, user will be prompted to select
            
        Returns:
            bool: True if successful, False otherwise
        """
        container_name = f"{adapter_name}-redis"
        
        # Check if container exists
        existing_containers = self.docker_client.containers.list(
            all=True, 
            filters={"name": container_name}
        )
        
        if not existing_containers:
            self.logger.error(f"Container {container_name} does not exist")
            return False
            
        # Stop and remove the existing container
        try:
            for container in existing_containers:
                self.logger.info(f"Stopping and removing container {container_name}")
                container.stop()
                container.remove()
                
            # Deploy the new version
            result = self.deploy_adapter(adapter_name, tag)
            if result:
                self.op_logger.log_upgrade(adapter_name, tag, True)
            return result
            
        except Exception as e:
            error_msg = f"Failed to upgrade {adapter_name} adapter: {str(e)}"
            self.logger.error(error_msg)
            self.op_logger.log_upgrade(adapter_name, tag, False, error_msg)
            return False
            
    def test_adapter(self, container_name: str, from_param: str, to_param: str) -> Optional[str]:
        """
        Test an External Adapter by sending a request
        
        Args:
            container_name: Name of the container to test
            from_param: FROM parameter for the test request
            to_param: TO parameter for the test request
            
        Returns:
            Result string if successful, None otherwise
        """
        try:
            # Get container IP or use container name
            try:
                container = self.docker_client.containers.get(container_name)
                container_ip = container.attrs['NetworkSettings']['Networks']['eas-net']['IPAddress']
            except:
                # If container doesn't exist or not in eas-net, use the container name
                container_ip = container_name
                
            # Prepare curl command with verbose flag and timeout
            curl_cmd = [
                "curl", "-v", "--connect-timeout", "5",
                "--header", "Content-Type: application/json",
                "--request", "POST",
                "--data", f'{{"data":{{"from":"{from_param}", "to":"{to_param}"}}}}',
                f"http://{container_ip}:1113"
            ]
            
            self.logger.info(f"Running command: {' '.join(curl_cmd)}")
            
            # Execute the curl command
            result = subprocess.run(curl_cmd, capture_output=True, text=True, check=True)
            
            # Parse the JSON response
            response = json.loads(result.stdout)
            adapter_result = response.get("result")
            
            self.logger.info(f"Test result for {container_name}: {from_param} / {to_param} --> {adapter_result}")
            self.op_logger.log_test(container_name, from_param, to_param, True, adapter_result)
            return adapter_result
            
        except subprocess.CalledProcessError as e:
            error_msg = f"Failed to test adapter: {e}"
            self.logger.error(error_msg)
            self.op_logger.log_test(container_name, from_param, to_param, False, error_msg)
            return None
        except json.JSONDecodeError as e:
            error_msg = f"Failed to parse adapter response: {e}"
            self.logger.error(error_msg)
            self.op_logger.log_test(container_name, from_param, to_param, False, error_msg)
            return None
        except Exception as e:
            error_msg = f"Error testing adapter: {str(e)}"
            self.logger.error(error_msg)
            self.op_logger.log_test(container_name, from_param, to_param, False, error_msg)
            return None
            
    def get_supported_adapters(self) -> List[str]:
        """
        Get a list of all supported External Adapters
        
        Returns:
            List of adapter names
        """
        return self.config.get_supported_adapters()