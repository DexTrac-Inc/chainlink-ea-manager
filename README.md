# Chainlink External Adapter Manager

Python-based management tool for deploying and managing Chainlink External Adapters using Docker.

## Features

- Deploy and manage multiple Chainlink External Adapters
- Setup Docker environment automatically
- Manage Redis cache container
- Configure adapters with proper API keys and subscription tiers
- Test adapters with simple commands
- Easy upgrade of adapters to newer versions

## Installation

```bash
# Clone the repository
git clone https://github.com/DexTrac-Inc/chainlink-ea-manager.git
cd chainlink-ea-manager

# Create a virtual environment
python3 -m venv venv
source venv/bin/activate

# Install the package
pip install -e .
```

## Prerequisites

- Python 3.7+
- Docker (will be installed automatically if not present)
- API keys for the External Adapters you want to use

## Configuration

Before using the manager, update these configuration files:

- `api_keys` - Add your API keys and subscription tiers for adapters
- `misc_vars` - Configure RPC URLs and blockchain settings

## Usage

### Initialize Environment

Set up Docker network and Redis container:

```bash
ea-manager -i
```

### List Supported Adapters

```bash
ea-manager -l
```

### Deploy New Adapter

```bash
ea-manager -d coingecko
```

### Upgrade Existing Adapter

```bash
ea-manager -u coingecko
```

### Test Adapter

```bash
ea-manager -t coingecko-redis LINK USD
```

### Show Version

```bash
ea-manager -v
```

## Advanced Features

- Operation logging for audit purposes
- Structured configuration management
- Docker environment management
- Customizable adapter configuration

## License

MIT
