"""Read-only status and overview helpers for Solar Shading windows."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from homeassistant.components.http import HomeAssistantView
from homeassistant.core import HomeAssistant

from .const import (
    CONF_ENTRY_TYPE,
    CONF_FACADE_NAME,
    CONF_FLOOR_NAME,
    CONF_HEIGHT_WIN,
    CONF_HORIZON_PROFILE,
    CONF_HOUSE_PROFILE_ENTRY_ID,
    CONF_ROOM_NAME,
    CONF_ROOM_TEMPERATURE_ENTITY,
    CONF_WINDOW_WIDTH,
    DOMAIN,
    ENTRY_TYPE_HOUSE,
)

OVERVIEW_API_URL = "/api/solar_shading/overview"
WINDOW_STATUS_OPTIONS = (
    "configuration_incomplete",
    "cover_unavailable",
    "control_disabled",
    "manual_override",
    "night_position",
    "cold_lockout",
    "no_direct_sun",
    "heat_protection_inactive",
    "binary_shading",
    "power_limited",
    "strong_shading",
    "partial_shading",
    "monitoring",
)


def estimate_power_with_cover(
    power_without_cover: float | None,
    open_position: float | None,
) -> float | None:
    """Estimate transmitted power with a linearly attenuating opaque cover."""
    if power_without_cover is None or open_position is None:
        return None
    fraction = max(0.0, min(100.0, float(open_position))) / 100.0
    return float(power_without_cover) * fraction


def derive_window_status(
    *,
    target_position: int,
    decision_reason: str | None,
    activation_reason: str | None,
    direct_sun_valid: bool,
    control_enabled: bool,
    manual_override: bool,
    cover_available: bool,
    configuration_warnings: list[str],
    full_close_position: int | None = None,
) -> str:
    """Return one stable, user-facing status for a window calculation."""
    blocking_warnings = {
        "no_cover_entities",
        "missing_window_dimensions",
        "missing_house_profile",
    }
    if blocking_warnings.intersection(configuration_warnings):
        return "configuration_incomplete"
    if not cover_available:
        return "cover_unavailable"
    if not control_enabled:
        return "control_disabled"
    if manual_override:
        return "manual_override"
    if decision_reason == "night_position":
        return "night_position"
    if activation_reason == "cold_lockout":
        return "cold_lockout"
    if not direct_sun_valid:
        return "no_direct_sun"
    if activation_reason == "inactive":
        return "heat_protection_inactive"
    if decision_reason == "binary_solar_threshold":
        return "binary_shading"
    if decision_reason == "transmitted_solar_power_limit":
        return "power_limited"
    if target_position >= 99:
        return "monitoring"
    if full_close_position is not None and target_position <= full_close_position:
        return "strong_shading"
    return "partial_shading"


def configuration_warnings(
    options: dict[str, Any],
    *,
    entities: list[str],
    current_positions: dict[str, float | None],
    solar_radiation_value: float | None,
) -> list[str]:
    """Return explicit configuration gaps without an opaque quality score."""
    warnings: list[str] = []
    if not entities:
        warnings.append("no_cover_entities")
    elif not any(position is not None for position in current_positions.values()):
        warnings.append("covers_unavailable")
    elif any(position is None for position in current_positions.values()):
        warnings.append("some_covers_unavailable")
    if not options.get(CONF_HOUSE_PROFILE_ENTRY_ID):
        warnings.append("missing_house_profile")
    if not options.get(CONF_FLOOR_NAME):
        warnings.append("missing_floor")
    if not options.get(CONF_ROOM_NAME):
        warnings.append("missing_room")
    if not options.get(CONF_FACADE_NAME):
        warnings.append("missing_facade")
    if not options.get(CONF_ROOM_TEMPERATURE_ENTITY):
        warnings.append("no_room_temperature_sensor")
    if not options.get(CONF_HORIZON_PROFILE):
        warnings.append("clear_horizon_assumed")
    if not options.get(CONF_HEIGHT_WIN) or not options.get(CONF_WINDOW_WIDTH):
        warnings.append("missing_window_dimensions")
    if solar_radiation_value is None:
        warnings.append("no_current_solar_radiation")
    return warnings


def _rounded(value: Any, digits: int = 2) -> float | None:
    if value is None:
        return None
    try:
        return round(float(value), digits)
    except (TypeError, ValueError):
        return None


def build_window_snapshot(entry, coordinator) -> dict[str, Any]:
    """Build one compact window record from an active coordinator."""
    data = coordinator.data
    states = data.states
    attributes = data.attributes
    positions = attributes.get("current_cover_positions") or {}
    covers = [
        {
            "entity_id": entity_id,
            "open_position": _rounded(position),
            "available": position is not None,
        }
        for entity_id, position in positions.items()
    ]
    return {
        "entry_id": entry.entry_id,
        "name": entry.data.get("name") or entry.title,
        "sensor_type": entry.data.get("sensor_type"),
        "house_profile": attributes.get("house_profile"),
        "floor": attributes.get("floor_name"),
        "room": attributes.get("room_name"),
        "facade": attributes.get("facade_name"),
        "target_open_position": states.get("state"),
        "actual_open_position": attributes.get("current_cover_position_average"),
        "status": states.get("window_status"),
        "decision_reason": attributes.get("decision_reason"),
        "activation_reason": attributes.get("heat_protection_activation_reason"),
        "control_enabled": attributes.get("control_enabled"),
        "manual_override": states.get("manual_override"),
        "solar_power_without_cover_w_per_window": attributes.get(
            "solar_power_without_cover_w_per_window"
        ),
        "solar_power_without_cover_w_total": attributes.get(
            "solar_power_without_cover_w_total"
        ),
        "solar_power_with_target_cover_w_per_window": attributes.get(
            "solar_power_with_target_cover_w_per_window"
        ),
        "solar_power_with_target_cover_w_total": attributes.get(
            "solar_power_with_target_cover_w_total"
        ),
        "solar_power_with_actual_cover_w_total": attributes.get(
            "solar_power_with_actual_cover_w_total"
        ),
        "transmitted_solar_power_w_m2": attributes.get(
            "transmitted_solar_power_w_m2"
        ),
        "solar_radiation_value_w_m2": attributes.get("solar_radiation_value_w_m2"),
        "room_temperature": attributes.get("room_temperature"),
        "room_temperature_threshold": attributes.get(
            "room_heat_protection_threshold"
        ),
        "warnings": attributes.get("configuration_warnings") or [],
        "covers": covers,
        "configuration_layers": attributes.get("configuration_layers") or [],
        "configuration_sources": attributes.get("configuration_sources") or {},
        "decision_trace": attributes.get("decision_trace") or [],
        "cover_attenuation_model": attributes.get("cover_attenuation_model"),
    }


def build_overview_payload(hass: HomeAssistant) -> dict[str, Any]:
    """Aggregate all loaded Solar Shading window coordinators."""
    windows = []
    for entry in hass.config_entries.async_entries(DOMAIN):
        if entry.data.get(CONF_ENTRY_TYPE) == ENTRY_TYPE_HOUSE:
            continue
        coordinator = hass.data.get(DOMAIN, {}).get(entry.entry_id)
        if coordinator is None or coordinator.data is None:
            continue
        windows.append(build_window_snapshot(entry, coordinator))

    def total(key: str, *, require_all: bool = False) -> float | None:
        values = [window.get(key) for window in windows]
        if require_all and any(value is None for value in values):
            return None
        return round(sum(float(value or 0.0) for value in values), 2)

    return {
        "generated_at": datetime.now(UTC).isoformat(),
        "summary": {
            "window_groups": len(windows),
            "covers": sum(len(window["covers"]) for window in windows),
            "warnings": sum(len(window["warnings"]) for window in windows),
            "solar_power_without_cover_w": total(
                "solar_power_without_cover_w_total"
            ),
            "solar_power_with_target_cover_w": total(
                "solar_power_with_target_cover_w_total"
            ),
            "solar_power_with_actual_cover_w": total(
                "solar_power_with_actual_cover_w_total", require_all=True
            ),
        },
        "windows": windows,
    }


class SolarShadingOverviewView(HomeAssistantView):
    """Serve the authenticated read-only window overview."""

    url = OVERVIEW_API_URL
    name = "api:solar_shading:overview"
    requires_auth = True

    async def get(self, request):
        """Return current status for all loaded windows."""
        hass: HomeAssistant = request.app["hass"]
        return self.json(build_overview_payload(hass))
