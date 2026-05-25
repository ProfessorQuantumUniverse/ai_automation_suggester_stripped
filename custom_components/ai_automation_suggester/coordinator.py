
import logging
import json
import yaml
import os
import random
import anyio
from pathlib import Path

from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er, device_registry as dr, area_registry as ar
from .const import CONF_EXCLUDED_DOMAINS, CONF_EXCLUDED_ENTITIES, CONF_EXCLUDED_AREAS, CONF_CUSTOM_SYSTEM_PROMPT
from .language_utils import suggestion_language_instruction

_LOGGER = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are an expert Home Assistant Automation consultant.
Your task is to analyze the provided smart home environment setup (entities, devices, areas, and existing automations, scripts, and scenes)
and suggest new, unique, and highly useful automations that the user might not have thought of."""

STRUCTURED_OUTPUT_INSTRUCTIONS = """Please provide your output as standard Home Assistant YAML automations.
Include comments explaining why the automation is useful."""

class PromptBuilder:
    def __init__(self, hass: HomeAssistant, entry):
        self.hass = hass
        self.entry = entry

        self.excluded_domains = self._opt_list(CONF_EXCLUDED_DOMAINS)
        self.excluded_entities = self._opt_list(CONF_EXCLUDED_ENTITIES)
        self.excluded_areas = self._opt_list(CONF_EXCLUDED_AREAS)
        self.custom_system_prompt = self._opt(CONF_CUSTOM_SYSTEM_PROMPT, "")
        
        self.selected_domains = []
        self.entity_limit = 100
        self.yaml_limit = 15
        self.automation_read_file = True
        
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

    def _collect_entities(self) -> dict[str, dict]:
        current: dict[str, dict] = {}
        selected_domains = set(self.selected_domains)
        for entity_id in self.hass.states.async_entity_ids():
            domain = entity_id.split(".", 1)[0]
            if selected_domains and domain not in selected_domains:
                continue
            if self._is_entity_excluded(entity_id):
                continue
            state = self.hass.states.get(entity_id)
            if state:
                current[entity_id] = {
                    "state": state.state,
                    "attributes": state.attributes,
                    "last_changed": state.last_changed,
                    "last_updated": state.last_updated,
                    "friendly_name": state.attributes.get("friendly_name", entity_id),
                }
        return current

    def _is_entity_excluded(self, entity_id: str) -> bool:
        domain = entity_id.split(".", 1)[0]
        if domain in set(self.excluded_domains):
            return True
        if entity_id in set(self.excluded_entities):
            return True
        if not self.excluded_areas or not self.entity_registry:
            return False

        entity_entry = self.entity_registry.async_get(entity_id)
        device_entry = None
        if entity_entry and entity_entry.device_id and self.device_registry:
            device_entry = self.device_registry.async_get(entity_entry.device_id)
        area_id = entity_entry.area_id if entity_entry and entity_entry.area_id else None
        if not area_id and device_entry:
            area_id = device_entry.area_id
        area_names = {area_id.lower()} if area_id else set()
        if area_id and self.area_registry:
            area_entry = self.area_registry.async_get_area(area_id)
            if area_entry:
                area_names.add(area_entry.name.lower())
        excluded = {area.lower() for area in self.excluded_areas}
        return bool(area_names & excluded)

    async def _build_prompt(self, entities: dict) -> str:
        max_attr = 150
        max_yaml = self.yaml_limit
        ent_sections: list[str] = []
        for entity_id, meta in random.sample(list(entities.items()), min(len(entities), self.entity_limit)):
            attr_str = str(meta["attributes"])
            if len(attr_str) > max_attr:
                attr_str = f"{attr_str[:max_attr]}...(truncated)"

            entity_entry = self.entity_registry.async_get(entity_id) if self.entity_registry else None
            device_entry = (
                self.device_registry.async_get(entity_entry.device_id)
                if entity_entry and entity_entry.device_id and self.device_registry
                else None
            )
            area_id = entity_entry.area_id if entity_entry and entity_entry.area_id else None
            if not area_id and device_entry:
                area_id = device_entry.area_id
            area_name = "Unknown Area"
            if area_id and self.area_registry:
                area_entry = self.area_registry.async_get_area(area_id)
                if area_entry:
                    area_name = area_entry.name

            block = f"- {entity_id} ({meta['friendly_name']}): state={meta['state']} | Area: {area_name}\n"
            if attr_str and attr_str != "{}":
                block += f"  Attrs: {attr_str}\n"
            if device_entry:
                block += f"  Device: {device_entry.manufacturer} {device_entry.model} ({device_entry.name_by_user or device_entry.name})\n"
            ent_sections.append(block)

        overview_sections = []
        overview_sections.extend(self._read_entities_overview("automation", max_yaml, max_attr))
        overview_sections.extend(self._read_entities_overview("script", max_yaml, max_attr))
        overview_sections.extend(self._read_entities_overview("scene", max_yaml, max_attr))

        yaml_codes: list[str] = []
        if self.automation_read_file:
            yaml_codes.extend(await self._read_yaml_file("automations.yaml", max_yaml))
            yaml_codes.extend(await self._read_yaml_file("scripts.yaml", max_yaml))
            yaml_codes.extend(await self._read_yaml_file("scenes.yaml", max_yaml))

        language_instruction = suggestion_language_instruction(getattr(self.hass.config, "language", None))
        language_block = f"{language_instruction}\n\n" if language_instruction else ""

        base_prompt = self.custom_system_prompt or SYSTEM_PROMPT

        return (
            f"{base_prompt}\n\n"
            f"{STRUCTURED_OUTPUT_INSTRUCTIONS}\n\n"
            f"{language_block}"
            f"Entities in your Home Assistant (sampled):\n{''.join(ent_sections)}\n"
            "Existing Logic Overview (Automations, Scripts, Scenes):\n"
            f"{''.join(overview_sections) if overview_sections else 'None found.'}\n\n"
            "Logic YAML Code (for analysis and improvement):\n"
            f"{''.join(yaml_codes) if yaml_codes else 'No YAML code included.'}\n\n"
            "Analyze the entities, existing automations, scripts, and scenes. Propose useful new automations or improvements "
            "that reference only the entity_ids shown above."
        )

    def _read_entities_overview(self, domain: str, max_items: int, max_attr: int) -> list[str]:
        sections: list[str] = []
        for entity_id in self.hass.states.async_entity_ids(domain)[:max_items]:
            state = self.hass.states.get(entity_id)
            if state:
                attr = str(state.attributes)
                if len(attr) > max_attr:
                    attr = f"{attr[:max_attr]}...(truncated)"
                friendly_name = state.attributes.get('friendly_name', entity_id)
                sections.append(f"- {entity_id} ({friendly_name}): {state.state} | Attrs: {attr}\n")
        return sections

    async def _read_yaml_file(self, filename: str, max_items: int) -> list[str]:
        file_path = Path(self.hass.config.path()) / filename
        codes: list[str] = []
        try:
            async with await anyio.open_file(file_path, "r", encoding="utf-8") as file:
                content = await file.read()
            data = yaml.safe_load(content) or []
            
            items = []
            if isinstance(data, list):
                items = data
            elif isinstance(data, dict):
                items = list(data.values())

            for item in items[:max_items]:
                if not isinstance(item, dict):
                    continue
                label = filename.split('.')[0].capitalize()
                codes.append(
                    f"{label} YAML:\n```yaml\n"
                    f"{yaml.safe_dump([item], sort_keys=False)}"
                    "```\n---\n"
                )
        except FileNotFoundError:
            _LOGGER.warning("%s file was not found", filename)
        except yaml.YAMLError as err:
            _LOGGER.warning("Error parsing %s: %s", filename, err)
        return codes
