# Solar Shading

Private Home Assistant custom integration for daylight-aware heat protection of
covers, rollers, blinds and awnings.

This project is a private fork of
[Adaptive Cover](https://github.com/basbruss/adaptive-cover). The original
integration, entity model, manual override handling and sun-position control
backbone come from that project.

## Installation

Add `https://github.com/deffySams/solar-shading` as a custom HACS integration,
download Solar Shading, restart Home Assistant and add the integration.

For a manual installation, copy `custom_components/solar_shading` into the Home
Assistant configuration directory and restart Home Assistant.

## Configuration Model

Settings inherit from broad defaults to precise local overrides:

1. House profile: reference facade, facade orientations, floors, rooms, glazing,
   common heat-protection rules and forecast behaviour.
2. Room: floor and facade assignment plus room-wide overrides such as the room
   temperature sensor.
3. Room facade: geometry and horizon shared by windows on one room facade.
4. Window: cover entity and final geometry or policy overrides.

This lets a house with many similar windows use one consistent rule set while
still supporting a separate horizon or reveal geometry for an individual
window.

## Heat-Protection Activation

The active model has one temperature gate:

- A measured outside temperature below the cold-lockout threshold disables heat
  protection.
- Today's forecast maximum at or above the hot-day threshold enables
  pre-emptive protection after the configured start time.
- A measured room temperature at or above the house threshold enables immediate
  reactive protection.
- Tomorrow's forecast can strengthen already active protection but cannot
  activate protection today by itself.
- The very-hot threshold increases the scaling pressure; it does not select a
  separate fixed blind position.

Actual direct sun, facade orientation, horizon, reveals, glazing and incoming
solar irradiance still determine whether and how strongly a window shades.

## Physical Solar Inputs

- Open-Meteo solar irradiance is the default current and forecast heat signal.
- A local irradiance sensor can override the current Open-Meteo value.
- `solar_radiation_reference_w_m2` is the incoming direct irradiance before
  geometry and glazing that counts as strong sun.
- The continuous cap and binary mode use estimated transmitted solar power after
  orientation, horizon, reveals, incidence angle and glazing.

## Simulator

The integration installs the simulator and horizon preview into Home Assistant's
`/config/www` directory:

- `/local/solar_shading_simulator.html`
- `/local/solar_shading_horizon_preview.html`

The simulator calls the same Python calculation endpoint as the live integration
and exposes intermediate geometry, optical, irradiance, activation and target
values without moving a physical cover.

## Documentation

- [Settings catalog](docs/settings-catalog.md)
- [Calculation flow and formulas](docs/calculation-flow.md)
- [House profile model](docs/house-profile-model.md)

## Compatibility And Migration

Existing entries are migrated when their options are loaded or saved. Legacy
climate-mode inputs, old weather proxies and duplicate hot-day limits are not
part of the active calculation. Existing indoor-temperature and hot-day values
are mapped to the unified room-temperature and forecast settings where possible.

Wall and roof phase shift remains a future room-facade feature. It is
intentionally separate from the current window-optics calculation.

## Disclaimer

This is experimental private-home automation software, not a certified
building-physics or HVAC controller. Validate every window before enabling cover
control. Use the simulator and diagnostics to inspect each decision first.
