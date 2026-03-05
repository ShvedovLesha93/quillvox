import json
import logging
from pathlib import Path

from app.constants import SettingsCategory


CONFIG_FILE = Path("user_config.json")

logger = logging.getLogger(__name__)


def _load_all() -> dict:
    if not CONFIG_FILE.exists():
        return {}
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.loads(f.read())
    except json.JSONDecodeError as e:
        logger.error("Failed to parse config at %s: %s", CONFIG_FILE, e)
        return {}
    except OSError as e:
        logger.error("Failed to read config at %s: %s", CONFIG_FILE, e)
        return {}


def _save_all(data: dict) -> None:
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            f.write(json.dumps(data, indent=2))
    except OSError as e:
        logger.error("Failed to save config to %s: %s", CONFIG_FILE, e)


def load_config(category: SettingsCategory) -> dict | None:
    logger.info("Loading %s config", category.value)
    data = _load_all()
    config = data.get(category.value)
    if config is None:
        logger.info("%s config not found, using defaults", category.value)
        return None
    logger.info("%s config loaded successfully", category.value)
    logger.debug("Loaded %s config: %s", category.value, config)
    return config


def save_config(config: dict, category: SettingsCategory) -> None:
    logger.info("Saving %s config", category.value)
    data = _load_all()
    data[category.value] = config
    _save_all(data)
    logger.info("%s config saved successfully", category.value)
    logger.debug("Saved %s config: %s", category.value, config)


def load_stt_config() -> dict | None:
    return load_config(SettingsCategory.STT)


def load_general_config() -> dict | None:
    return load_config(SettingsCategory.GENERAL)


def save_stt_config(config: dict) -> None:
    save_config(config, SettingsCategory.STT)


def save_general_config(config: dict) -> None:
    save_config(config, SettingsCategory.GENERAL)
