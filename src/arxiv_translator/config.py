import os
import json
from pathlib import Path
from typing import Optional, Dict, Any
from .logging_utils import logger

class ConfigManager:
    def __init__(self, config_dir: Optional[str] = None):
        if config_dir:
            self.config_dir = Path(config_dir)
        else:
            # Default to ~/.arxiv-translator/
            self.config_dir = Path.home() / ".arxiv-translator"
        
        self.config_file = self.config_dir / "config.json"
        
    def _ensure_dir(self):
        if not self.config_dir.exists():
            self.config_dir.mkdir(parents=True, exist_ok=True)

    def load_config(self) -> Dict[str, Any]:
        """Loads configuration from JSON file."""
        if not self.config_file.exists():
            return {}
        
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {}
        except Exception as e:
            logger.warning(f"Warning: Could not load config file: {e}")
            return {}

    def save_config(self, config: Dict[str, Any]):
        """Saves configuration to JSON file."""
        self._ensure_dir()
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4)
        except Exception as e:
            logger.error(f"Error saving config file: {e}")

    def get_api_key(self) -> Optional[str]:
        """Retrieves API key from config."""
        config = self.load_config()
        return config.get("GEMINI_API_KEY")

    def set_api_key(self, api_key: str):
        """Saves API key to config."""
        config = self.load_config()
        config["GEMINI_API_KEY"] = api_key
        self.save_config(config)
        logger.info(f"API key saved to {self.config_file}")
