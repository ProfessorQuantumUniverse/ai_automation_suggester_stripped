"""Config flow for AI Automation Suggester import."""
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
import homeassistant.helpers.config_validation as cv

from .const import (
    DOMAIN,
    CONF_CUSTOM_SYSTEM_PROMPT,
    CONF_EXCLUDED_DOMAINS,
    CONF_EXCLUDED_ENTITIES,
    CONF_EXCLUDED_AREAS,
)

class AIAutomationSuggesterConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for AI Automation Suggester."""

    VERSION = 4

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")

        if user_input is not None:
            return self.async_create_entry(title="AI Automation Suggester", data=user_input)

        schema = vol.Schema({
            vol.Optional(CONF_CUSTOM_SYSTEM_PROMPT, default=""): cv.string,
            vol.Optional(CONF_EXCLUDED_DOMAINS, default=[]): cv.multi_select(["light", "switch", "sensor", "media_player", "climate", "vacuum", "person", "device_tracker"]),
            vol.Optional(CONF_EXCLUDED_ENTITIES, default=""): cv.string,
            vol.Optional(CONF_EXCLUDED_AREAS, default=""): cv.string,
        })
        return self.async_show_form(step_id="user", data_schema=schema)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get the options flow for this handler."""
        return OptionsFlowHandler(config_entry)

class OptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options flow."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        schema = vol.Schema({
            vol.Optional(CONF_CUSTOM_SYSTEM_PROMPT, default=self.config_entry.options.get(CONF_CUSTOM_SYSTEM_PROMPT, self.config_entry.data.get(CONF_CUSTOM_SYSTEM_PROMPT, ""))): cv.string,
            vol.Optional(CONF_EXCLUDED_DOMAINS, default=self.config_entry.options.get(CONF_EXCLUDED_DOMAINS, self.config_entry.data.get(CONF_EXCLUDED_DOMAINS, []))): cv.multi_select(["light", "switch", "sensor", "media_player", "climate", "vacuum", "person", "device_tracker"]),
            vol.Optional(CONF_EXCLUDED_ENTITIES, default=self.config_entry.options.get(CONF_EXCLUDED_ENTITIES, self.config_entry.data.get(CONF_EXCLUDED_ENTITIES, ""))): cv.string,
            vol.Optional(CONF_EXCLUDED_AREAS, default=self.config_entry.options.get(CONF_EXCLUDED_AREAS, self.config_entry.data.get(CONF_EXCLUDED_AREAS, ""))): cv.string,
        })
        return self.async_show_form(step_id="init", data_schema=schema)

