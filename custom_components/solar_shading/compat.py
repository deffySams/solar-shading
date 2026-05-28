"""Compatibility helpers for Home Assistant API changes."""

from __future__ import annotations

from typing import Any

from homeassistant.core import HomeAssistant


def state_attr(hass: HomeAssistant, entity_id: str | None, attr_name: str) -> Any:
    """Return a state attribute without relying on deprecated HA helpers."""
    if not entity_id:
        return None

    state = hass.states.get(entity_id)
    if state is None:
        return None

    return state.attributes.get(attr_name)
