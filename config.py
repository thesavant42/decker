# Configuration for T-Deck LLM Chat Application

import json
import os

class Config:
    def __init__(self):
        self.lm_studio_base_url = None
        self.api_key = None
        self.last_used_model = None
        self.logging_enabled = False
        self.sd_card_path = "/sd"
        self.tts_base_url = None
        self.tts_model_name = None
        self.tts_voice = None
        self.tts_exaggeration = None
        self.tts_cfg_weight = None
        self.tts_temperature = None
        self.tts_device = None
        self.tts_dtype = None
        self.tts_seed = None
        self.tts_chunked = None

    def load_config(self):
        config_path = "config.json"
        defaults = {
            "last_used_model": None,
            "logging_enabled": False,
            "sd_card_path": "/sd"
        }
        # Check if config file exists (CircuitPython compatible - no os.path)
        config_exists = False
        try:
            with open(config_path, "r") as f:
                f.read(1)  # Minimal read to test existence
                config_exists = True
        except OSError:
            config_exists = False
        
        if config_exists:
            try:
                with open(config_path, "r") as f:
                    data = json.load(f)
                for key, default_value in defaults.items():
                    setattr(self, key, data.get(key, default_value))
                
                # Load sensitive configs directly from JSON if present
                if "lm_studio_base_url" in data:
                    self.lm_studio_base_url = data["lm_studio_base_url"]
                if "api_key" in data:
                    self.api_key = data["api_key"]

                # Load TTS configs from JSON if present
                if "tts_base_url" in data:
                    self.tts_base_url = data["tts_base_url"]
                if "tts_model_name" in data:
                    self.tts_model_name = data["tts_model_name"]
                if "tts_voice" in data:
                    self.tts_voice = data["tts_voice"]
                if "tts_exaggeration" in data:
                    self.tts_exaggeration = data["tts_exaggeration"]
                if "tts_cfg_weight" in data:
                    self.tts_cfg_weight = data["tts_cfg_weight"]
                if "tts_temperature" in data:
                    self.tts_temperature = data["tts_temperature"]
                if "tts_device" in data:
                    self.tts_device = data["tts_device"]
                if "tts_dtype" in data:
                    self.tts_dtype = data["tts_dtype"]
                if "tts_seed" in data:
                    self.tts_seed = data["tts_seed"]
                if "tts_chunked" in data:
                    self.tts_chunked = data["tts_chunked"]
                
                
                
                # Validate required sensitive configs (after loading)
                if self.lm_studio_base_url is None or self.api_key is None:
                    raise ValueError("Missing required configuration in config.json: 'lm_studio_base_url' and/or 'api_key'. Please add them to the file.")
                
                print(f"Loaded config: base_url={self.lm_studio_base_url}, api_key={self.api_key[:5]}..., model={self.last_used_model}, logging={self.logging_enabled}, sd_path={self.sd_card_path}")
            except Exception as e:
                raise ValueError(f"Error loading config.json: {e}. Please ensure the file is valid JSON with required fields.")
        else:
            raise ValueError("config.json not found. Please create it with required fields: 'lm_studio_base_url' and 'api_key'.")

    def save_config(self):
        config_path = "config.json"
        data = {
            "lm_studio_base_url": self.lm_studio_base_url,
            "api_key": self.api_key,
            "last_used_model": self.last_used_model,
            "logging_enabled": self.logging_enabled,
            "sd_card_path": self.sd_card_path,
            "tts_base_url": self.tts_base_url,
            "tts_model_name": self.tts_model_name,
            "tts_voice": self.tts_voice,
            "tts_exaggeration": self.tts_exaggeration,
            "tts_cfg_weight": self.tts_cfg_weight,
            "tts_temperature": self.tts_temperature,
            "tts_device": self.tts_device,
            "tts_dtype": self.tts_dtype,
            "tts_seed": self.tts_seed,
            "tts_chunked": self.tts_chunked,
        }
        try:
            with open(config_path, "w") as f:
                json.dump(data, f, indent=2)
            print("Config saved to config.json")
        except Exception as e:
            print(f"Error saving config: {e}")