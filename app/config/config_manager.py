import json
import logging
from pathlib import Path

from app.constants import SettingsCategory


USER_CONFIG = Path("user_config")

logger = logging.getLogger(__name__)


def load_config(category: SettingsCategory) -> dict | None:
    json_file = USER_CONFIG / f"{category.value}.json"

    logger.info("Loading %s config from %s", category.value, json_file)

    if not json_file.exists():
        logger.info(
            "%s config file not found at %s, using defaults", category.value, json_file
        )
        return None

    try:
        with open(json_file, "r", encoding="utf-8") as f:
            data = f.read()
        config = json.loads(data)
        logger.info("%s config loaded successfully", category.value)
        logger.debug("Loaded %s config: %s", category.value, config)
        return config
    except json.JSONDecodeError as e:
        logger.error(
            "Failed to parse %s config at %s: %s", category.value, json_file, e
        )
        return None
    except OSError as e:
        logger.error("Failed to read %s config at %s: %s", category.value, json_file, e)
        return None


def save_config(config: dict, category: SettingsCategory) -> None:
    json_file = USER_CONFIG / f"{category.value}.json"

    logger.info("Saving %s config to %s", category.value, json_file)

    try:
        USER_CONFIG.mkdir(exist_ok=True)
        with open(json_file, "w", encoding="utf-8") as f:
            f.write(json.dumps(config, indent=4))
        logger.info("%s saved successfully", category.value)
        logger.debug("Saved %s config: %s", category.value, config)
    except OSError as e:
        logger.error("Failed to save %s config to %s: %s", category.value, json_file, e)


def load_stt_config() -> dict | None:
    return load_config(SettingsCategory.STT)


def load_general_config() -> dict | None:
    return load_config(SettingsCategory.GENERAL)


def save_stt_config(config: dict) -> None:
    save_config(config, SettingsCategory.STT)


def save_general_config(config: dict) -> None:
    save_config(config, SettingsCategory.GENERAL)
