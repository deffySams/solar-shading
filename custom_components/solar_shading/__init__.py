"""The Solar Shading integration."""

from __future__ import annotations

from pathlib import Path
from shutil import copy2

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.event import (
    async_track_state_change_event,
)

from .const import (
    CONF_AWAY_ENTITY,
    CONF_ENTRY_TYPE,
    CONF_END_ENTITY,
    CONF_ENTITIES,
    CONF_HOUSE_PROFILE_ENTRY_ID,
    CONF_ROOM_TEMPERATURE_ENTITY,
    CONF_SOLAR_RADIATION_ENTITY,
    CONF_WEATHER_ENTITY,
    DOMAIN,
    ENTRY_TYPE_HOUSE,
    _LOGGER,
)
from .coordinator import AdaptiveDataUpdateCoordinator
from .migration import migrate_retired_options
from .profiles import resolve_effective_options
from .simulator import SolarShadingSimulationView

PLATFORMS = [Platform.SENSOR, Platform.SWITCH, Platform.BINARY_SENSOR, Platform.BUTTON]
CONF_SUN = ["sun.sun"]
WWW_ASSETS = ("solar_shading_simulator.html", "solar_shading_horizon_preview.html")


async def async_initialize_integration(
    hass: HomeAssistant,
    config_entry: ConfigEntry | None = None,
) -> bool:
    """Initialize the integration."""

    return True


async def async_migrate_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Migrate stored entries to the unified heat-protection settings."""
    hass.config_entries.async_update_entry(
        entry,
        data=migrate_retired_options(dict(entry.data)),
        options=migrate_retired_options(dict(entry.options)),
        version=2,
    )
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Solar Shading from a config entry."""

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN].setdefault("house_profiles", {})
    _async_register_simulator_api(hass)
    await _async_install_www_assets(hass)

    if entry.data.get(CONF_ENTRY_TYPE) == ENTRY_TYPE_HOUSE:
        hass.data[DOMAIN]["house_profiles"][entry.entry_id] = entry
        entry.async_on_unload(entry.add_update_listener(_async_update_listener))
        return True

    coordinator = AdaptiveDataUpdateCoordinator(hass)
    options = resolve_effective_options(hass, entry).options
    _room_temperature_entity = options.get(CONF_ROOM_TEMPERATURE_ENTITY)
    _away_entity = options.get(CONF_AWAY_ENTITY)
    _weather_entity = options.get(CONF_WEATHER_ENTITY)
    _solar_radiation_entity = options.get(CONF_SOLAR_RADIATION_ENTITY)
    _cover_entities = options.get(CONF_ENTITIES, [])
    _end_time_entity = options.get(CONF_END_ENTITY)
    _entities = ["sun.sun"]
    for entity in [
        _room_temperature_entity,
        _away_entity,
        _weather_entity,
        _solar_radiation_entity,
        _end_time_entity,
    ]:
        if entity is not None:
            _entities.append(entity)

    _LOGGER.debug("Setting up entry %s", entry.data.get("name"))

    entry.async_on_unload(
        async_track_state_change_event(
            hass,
            _entities,
            coordinator.async_check_entity_state_change,
        )
    )

    entry.async_on_unload(
        async_track_state_change_event(
            hass,
            _cover_entities,
            coordinator.async_check_cover_state_change,
        )
    )

    await coordinator.async_config_entry_first_refresh()
    hass.data[DOMAIN][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    entry.async_on_unload(entry.add_update_listener(_async_update_listener))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if entry.data.get(CONF_ENTRY_TYPE) == ENTRY_TYPE_HOUSE:
        hass.data[DOMAIN].get("house_profiles", {}).pop(entry.entry_id, None)
        return True
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle options update."""
    if entry.data.get(CONF_ENTRY_TYPE) == ENTRY_TYPE_HOUSE:
        hass.data[DOMAIN].setdefault("house_profiles", {})[entry.entry_id] = entry
        linked_entries = [
            candidate
            for candidate in hass.config_entries.async_entries(DOMAIN)
            if candidate.options.get(CONF_HOUSE_PROFILE_ENTRY_ID) == entry.entry_id
        ]
        for linked_entry in linked_entries:
            await hass.config_entries.async_reload(linked_entry.entry_id)
        return
    await hass.config_entries.async_reload(entry.entry_id)


async def _async_install_www_assets(hass: HomeAssistant) -> None:
    """Install bundled simulator assets into Home Assistant's /local path."""
    await hass.async_add_executor_job(_install_www_assets, hass.config.path("www"))


def _install_www_assets(www_path: str) -> None:
    """Copy bundled simulator assets when missing or changed."""
    source_dir = Path(__file__).with_name("www")
    if not source_dir.exists():
        return

    target_dir = Path(www_path)
    target_dir.mkdir(parents=True, exist_ok=True)

    for filename in WWW_ASSETS:
        source = source_dir / filename
        if not source.exists():
            continue
        target = target_dir / filename
        if target.exists() and target.read_bytes() == source.read_bytes():
            continue
        copy2(source, target)


def _async_register_simulator_api(hass: HomeAssistant) -> None:
    """Register the simulator API once."""
    if hass.data[DOMAIN].get("simulator_api_registered"):
        return
    hass.http.register_view(SolarShadingSimulationView)
    hass.data[DOMAIN]["simulator_api_registered"] = True
