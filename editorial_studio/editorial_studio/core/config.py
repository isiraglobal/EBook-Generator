from __future__ import annotations
import os
from pathlib import Path
from typing import Any
import yaml


class Config:
    _instance: Config | None = None
    _data: dict[str, Any] = {}

    def __new__(cls, config_path: str | None = None):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load(config_path)
        return cls._instance

    def _load(self, config_path: str | None = None):
        if config_path is None:
            config_path = os.environ.get(
                "EDITORIAL_STUDIO_CONFIG",
                str(Path(__file__).parent.parent.parent / "config.yaml"),
            )
        path = Path(config_path)
        if path.exists():
            with open(path) as f:
                self._data = yaml.safe_load(f) or {}
        else:
            self._data = {}

        # Override with environment variables
        self._apply_env_overrides()

    def _apply_env_overrides(self):
        env_mappings = {
            "EDITORIAL_STUDIO_DB_PATH": "storage.database_path",
            "EDITORIAL_STUDIO_PROJECTS_ROOT": "storage.projects_root",
            "EDITORIAL_STUDIO_ASSETS_ROOT": "storage.assets_root",
            "EDITORIAL_STUDIO_TEMP_ROOT": "storage.temp_root",
            "EDITORIAL_STUDIO_API_HOST": "api.host",
            "EDITORIAL_STUDIO_API_PORT": "api.port",
            "EDITORIAL_STUDIO_WEB_HOST": "web.host",
            "EDITORIAL_STUDIO_WEB_PORT": "web.port",
            "OPENAI_API_KEY": "providers.image_generation.openai.api_key",
            "ANTHROPIC_API_KEY": "providers.llm.anthropic.api_key",
            "REPLICATE_API_KEY": "providers.image_generation.replicate.api_key",
        }
        for env_var, config_key in env_mappings.items():
            value = os.environ.get(env_var)
            if value:
                self._set_nested(config_key, value)

    def _set_nested(self, key: str, value: Any):
        parts = key.split(".")
        d = self._data
        for part in parts[:-1]:
            if part not in d:
                d[part] = {}
            d = d[part]
        d[parts[-1]] = value

    def get(self, key: str, default: Any = None) -> Any:
        parts = key.split(".")
        d = self._data
        for part in parts:
            if isinstance(d, dict) and part in d:
                d = d[part]
            else:
                return default
        return d

    def __getitem__(self, key: str) -> Any:
        return self.get(key)

    def __contains__(self, key: str) -> bool:
        return self.get(key) is not None

    @property
    def data(self) -> dict[str, Any]:
        return self._data


def load_config(config_path: str | None = None) -> Config:
    return Config(config_path)