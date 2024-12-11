import os
from pathlib import Path
import json
import sys
from typing import Dict, Optional

class ConfigHandler:
    """Handles secure configuration loading for the Cumulocity IoT connection."""
    
    DEFAULT_CONFIG_PATH = "/etc/tedge/c8y_credentials.json"
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or self.DEFAULT_CONFIG_PATH
        self.config: Dict[str, str] = {}
        
    def load_config(self) -> Dict[str, str]:
        """Load configuration from environment variables or config file."""
        # Try environment variables first
        env_config = {
            'C8Y_BASEURL': os.getenv('C8Y_BASEURL'),
            'TENANT_ID': os.getenv('C8Y_TENANT'),
            'USERNAME': os.getenv('C8Y_USERNAME'),
            'PASSWORD': os.getenv('C8Y_PASSWORD')
        }
        
        # If all environment variables are set, use them
        if all(env_config.values()):
            self.config = env_config
            return self.config
            
        # Otherwise, try loading from config file
        try:
            with open(self.config_path, 'r') as f:
                self.config = json.load(f)
                return self.config
        except FileNotFoundError:
            raise Exception(f"Configuration file not found at {self.config_path}. "
                          "Please either set environment variables (C8Y_BASEURL, C8Y_TENANT, "
                          "C8Y_USERNAME, C8Y_PASSWORD) or create a config file.")
        except json.JSONDecodeError:
            raise Exception(f"Invalid JSON format in config file {self.config_path}")
            
    def create_default_config(self, config: Dict[str, str]) -> None:
        """Create a default configuration file with the provided credentials."""
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        
        # Set restrictive permissions before writing
        if os.path.exists(self.config_path):
            os.chmod(self.config_path, 0o600)
            
        with open(self.config_path, 'w') as f:
            json.dump(config, f, indent=4)
            
        # Ensure file has restrictive permissions
        os.chmod(self.config_path, 0o600)
