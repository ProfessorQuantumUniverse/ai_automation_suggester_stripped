"""The AI Automation Suggester integration."""
import logging
import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall, SupportsResponse
from homeassistant.exceptions import ConfigEntryNotReady, ServiceValidationError
from homeassistant.helpers.typing import ConfigType

from .const import (
    DOMAIN,
    PLATFORMS,
    CONFIG_VERSION,
    SERVICE_GET_PROMPT
)
from .coordinator import PromptBuilder

_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = vol.Schema({DOMAIN: vol.Schema({})}, extra=vol.ALLOW_EXTRA)

async def async_migrate_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Migrate old config entry if necessary."""
    if config_entry.version < CONFIG_VERSION:
        new_data = {**config_entry.data}
        hass.config_entries.async_update_entry(config_entry, data=new_data, version=CONFIG_VERSION)
        return True
    return True

async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the AI Automation Suggester component."""
    hass.data.setdefault(DOMAIN, {})

    async def handle_get_prompt(call: ServiceCall):
        """Handle the get_prompt service call and return the generated prompt."""
        try:
            # Find the configured prompt builder
            builder = None
            for entry_id, b in hass.data[DOMAIN].items():
                if isinstance(b, PromptBuilder):
                    builder = b
                    break

            if builder is None:
                raise ServiceValidationError("No AI Automation Suggester configured")

            prompt = await builder.async_get_prompt()
            return {"prompt": prompt}

        except Exception as err:
            raise ServiceValidationError(f"Failed to generate prompt: {err}")

    # Register the service
    hass.services.async_register(
        DOMAIN,
        SERVICE_GET_PROMPT,
        handle_get_prompt,
        supports_response=SupportsResponse.ONLY,
    )

    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up AI Automation Suggester from a config entry."""
    try:
        builder = PromptBuilder(hass, entry)
        hass.data[DOMAIN][entry.entry_id] = builder
        
        entry.async_on_unload(entry.add_update_listener(async_reload_entry))
        return True

    except Exception as err:
        _LOGGER.error("Failed to setup integration: %s", err)
        raise ConfigEntryNotReady from err

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if entry.entry_id in hass.data[DOMAIN]:
        hass.data[DOMAIN].pop(entry.entry_id)
    return True

async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry."""
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)

