import logging
import yaml
import os
from pathlib import Path

DEFAULT_CONFIG= {
    "models": {
        "default": "microsoft/CodeGPT-small-py",
        "large": "microsoft/CodeBERT-base"
    },
    "max_file_size_mb": 5,
    "logging": {
        "level": "INFO",
        "file": "ai_debugger.log"
    },
    "static_analysis": {
        "enabled_checkers": ["unused", "complexity", "naming"]
    }
}

class Config:
    def __init__(self, config_path=None):
        self.config = self._load_config(config_path)
        self._setup_logging()

    def _load_config(self, config_path=None):
        if not config_path:
            config_path = Path.home() / ".ai_debugger.yml"

        config = DEFAULT_CONFIG.copy()

        if os.path.exists(config_path):
            try:
                with open(config_path, "r") as f:
                    user_config = yaml.safe_load(f)
                    if user_config:
                        for key, value in user_config.items():
                            if isinstance(value, dict) and key in config:
                                config[key].update(value)
                            else:
                                config[key] = value
            except yaml.YAMLError as e:
                print(f"Error loading config file: {e}")

        return config


    def _setup_logging(self):
        root_logger = logging.getLogger()
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)

        level_setting = self.config["logging"]["level"]
        if isinstance(level_setting, list) and level_setting:
            level_name = level_setting[0]
        else:
            level_name = level_setting

        log_level = getattr(logging, level_name, logging.INFO)
        log_file = self.config["logging"].get("file")

        if isinstance(log_file, list) and log_file:
            log_file = log_file[0]

        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)

        if log_file:
            try:
                file_handler = logging.FileHandler(log_file, mode='a')
                file_handler.setFormatter(formatter)
                root_logger.addHandler(file_handler)
            except Exception as e:
                print(f"Error setting up log file: {e}")

        root_logger.setLevel(log_level)


    def get(self, key, default=None):
        keys = key.split(".")
        value = self.config

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value


    def set(self, key, value):
        keys = key.split(".")
        config = self.config

        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]

        config[keys[-1]] = value


    def save(self, config_path=None):
        if not config_path:
            config_path = Path.home() / ".ai_debugger.yml"

        try:
            with open(config_path, "w") as f:
                yaml.safe_dump(self.config, f, default_flow_style=False)
            return True
        except Exception as e:
            logging.error(f"Failed to save config: {e}")
            return False