import sys
import re

with open("custom_components/ai_automation_suggester/coordinator.py", "r", encoding="utf-8") as f:
    text = f.read()

# We need the imports and the core methods from the class AIAutomationCoordinator.
# Let us define a new class replacing AIAutomationCoordinator.

start_methods = text.find("    def _collect_entities(")
end_methods = text.find("    async def _dispatch(")

methods_text = text[start_methods:end_methods]

new_file = f"""import logging
import json
import yaml
import os
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er, device_registry as dr, area_registry as ar
from .const import CONF_EXCLUDED_DOMAINS, CONF_EXCLUDED_ENTITIES, CONF_EXCLUDED_AREAS, CONF_CUSTOM_SYSTEM_PROMPT

_LOGGER = logging.getLogger(__name__)

class PromptBuilder:
    def __init__(self, hass: HomeAssistant, entry):
        self.hass = hass
        self.entry = entry
        
        self.excluded_domains = self._opt_list(CONF_EXCLUDED_DOMAINS)
        self.excluded_entities = self._opt_list(CONF_EXCLUDED_ENTITIES)
        self.excluded_areas = self._opt_list(CONF_EXCLUDED_AREAS)
        self.custom_system_prompt = self._opt(CONF_CUSTOM_SYSTEM_PROMPT, "")
        
        # Some default empty lists if needed
        self.selected_domains = []
        self.entity_registry = er.async_get(self.hass)
        self.device_registry = dr.async_get(self.hass)
        self.area_registry = ar.async_get(self.hass)

    def _opt(self, key: str, default=None):
        return self.entry.options.get(key, self.entry.data.get(key, default))

    def _opt_list(self, key: str, default: list | None = None) -> list[str]:
        value = self._opt(key, default or [])
        if isinstance(value, str):
            return [v.strip() for v in value.split(",") if v.strip()]
        return value if isinstance(value, list) else []

    async def async_get_prompt(self):
        entities = self._collect_entities()
        return await self._build_prompt(entities)

{methods_text}
"""

with open("custom_components/ai_automation_suggester/coordinator.py", "w", encoding="utf-8") as f:
    f.write(new_file)
print("Done rewriting coordinator.py")

