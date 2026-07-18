# Thermal Control TODO

Scope for the next larger coding session around maximum indoor temperature and cleaner solar heat limits.

Near-term constraint: keep the next product pass simple and sensor-light. Do not add new indoor temperature, window-contact, ventilation, humidity, dew-point, or room sensor workflows yet. Keep those ideas documented for later, but focus the next coding session on simplifying the existing heat-gain logic and settings.

Also keep the next pass conservative: retire obsolete inputs, but do not merge existing threshold/gate concepts yet. Consolidating hot-day thresholds, outside-temperature gates, forecast influence, or solar-source selection can wait until the obsolete proxy logic is removed and the behavior is easier to observe.

## Heat-Power Limit

- Change the per-cover hard cap from `W per window` to `W/m2 glass`.
- Use `estimated_solar_heat_power_w_m2` for the active cap calculation.
- Keep `estimated_solar_heat_power_w` as a diagnostic value.
- Reserve total `W per window` for future room-level heat budgets and cooling-capacity checks.
- Rename UI text from "Maximum heat gain per window" to a clearer `Maximum heat gain per m2 glass`.
- Revisit defaults:
  - strict: `100-150 W/m2`
  - normal: `150-250 W/m2`
  - tolerant: `250-350 W/m2`

## Indoor Temperature Protection

- Deferred for later; do not include in the next simplification pass.
- Add optional indoor temperature sensor per room/zone.
- Add configurable maximum indoor temperature.
- Add hysteresis so covers do not oscillate around the threshold.
- Add temperature trend detection: rising fast, stable, falling.
- Add pre-shading when indoor temperature is below the limit but rising and solar heat gain is high.
- Add handling for unavailable/stale sensors.
- Add attributes for diagnostics: current indoor temperature, maximum indoor temperature, margin, trend, active reason, and target position.

## Ventilation Cooling

- Deferred for later; do not include in the next simplification pass.
- Add an optional ventilation cooling sensor/decision layer that compares indoor temperature with current outside temperature.
- Prefer ventilation when the room is too warm or trending too warm and outside air is meaningfully cooler.
- Keep shading active when direct solar heat gain remains high; ventilation can reduce stored/air heat, but it does not stop solar input through glass.
- Treat rain primarily as a "no heat-shading needed" signal when it means there is no meaningful direct solar gain. Rain remains a safety blocker for ventilation/open-window automation.
- Estimate ventilation cooling power with a simple formula:
  - `ventilation_cooling_w = 0.33 * airflow_m3_h * max(indoor_temp - outside_temp, 0)`
  - If airflow is unknown, offer presets such as tilted window, one open window, cross ventilation, or mechanical ventilation.
- Compare ventilation cooling against estimated solar heat gain:
  - if `ventilation_cooling_w` is higher than solar gain plus a margin, ventilation can be the primary cooling action.
  - if solar gain is high, shade first and ventilate as an additional action when safe.
- Add hysteresis and minimum run time:
  - start ventilation cooling when `indoor_temp > max_indoor_temp - pre_margin` and `indoor_temp - outside_temp >= 2 K`.
  - stop when indoor temperature falls below target margin, outside temperature rises, or safety/weather locks trigger.
- Optional safety inputs:
  - rain sensor / precipitation forecast
  - wind speed
  - window contact sensor
  - presence/security mode
  - indoor and outdoor humidity / dew point
  - pollen or air-quality lockout
- Add attributes for diagnostics: cooling delta, estimated ventilation cooling watts, suggested action, blocker reason, and whether shading or ventilation currently wins.

## Product Settings Cleanup

Goal: keep the control accurate and configurable, but make the settings conditional and understandable. Do not castrate useful tuning. Remove only obsolete inputs and hide settings that cannot affect the current configuration.

- This is the next main product track. Prefer one clean, understandable options flow over adding more automation features.
- First simplify what the user sees; only then add new behavior.
- Keep precise controls when they belong to the active model.
- Use progressive disclosure:
  - if no forecast source is selected, do not show forecast-derived settings.
  - do not show cloud/rain proxy controls for heat-gain policy; they are retired.
  - if weather fallback is active, show only minimal fallback source settings, not tunable cloud/rain weights.
  - if away mode is disabled, hide away multiplier/threshold/position details.
  - if expert mode is disabled, keep advanced weights hidden but still driven by presets.
  - if hot-day override is disabled, hide hot/very-hot position limits.
  - if heat-power cap is disabled, hide its threshold and limit fields.
- Retire these because they are obsolete with the current direction:
  - forecast UV weight
  - forecast cloud weight
  - forecast precipitation probability weight
  - forecast precipitation amount weight
- Remove cloud/rain proxy inputs from the heat-gain score instead of keeping them as expert tuning.
- Collapse duplicate heat thresholds:
  - deferred; do not merge thresholds in the next cleanup pass.
  - use one comfort/max indoor temperature once indoor sensor support exists.
  - keep forecast hot/very-hot thresholds as derived defaults or expert options.
  - keep outside cold lockout as a simple safety setting.
- Make rain and bad weather a top-level gating/safety decision instead of several tunable weights.
- Make absolute solar radiation the primary current heat signal whenever available.
- Keep glazing/reflection and solar radiation weights because they belong to the physical heat-gain model.
- Keep direct exposure and incidence controls because they describe real geometry and sun angle.
- Keep only a minimal weather fallback mode when no absolute radiation source is available; avoid exposing cloud/rain proxy weights.
- Keep partial/full score thresholds and away-mode multiplier/threshold/position settings for now.
- Remove legacy Adaptive Cover basic shading from normal heat protection.

## Near-Term Useful Features

- Convert heat-power cap to `W/m2 glass`.
- Add a simple `decision_reason` / `active_strategy` diagnostic that says why the cover moved:
  - no direct sun
  - raining / no solar gain
  - below heat-protection temperature
  - morning pre-shading
  - watt-per-m2 cap
  - manual override
- Grow that into an inspectable `decision_trace` once the simple reason field is stable:
  - ordered list of checked gates and policies
  - winning reason
  - skipped/rejected reasons
  - final target position in `% open`
- Add automatic sane defaults so a user can tune one or two controls before opening expert mode.
- Make settings conditional so inactive feature settings are not shown.
- Add lightweight operational diagnostics:
  - last requested cover action
  - last skipped action and reason
  - last calculated target position
  - whether a delta/time/manual gate blocked movement
- Do not merge existing hot-day, outside-temperature, forecast-influence, or solar-source settings yet.
- Defer indoor-temperature, window-contact, and ventilation logic entirely.

## Differentiation From Adaptive Cover Pro

Use Adaptive Cover Pro as a reference for maturity, but not as a feature checklist.
Solar Shading should win by being simpler to tune for solar heat, daylight and room comfort.

Already on the Solar Shading list:

- Product settings cleanup and conditional UI.
- `decision_reason` / `active_strategy`.
- Rain and bad weather as top-level gates instead of heat-score weights.
- Optional window contact sensors, but deferred.
- Room/zone heat budgets across multiple windows.
- Indoor temperature protection and ventilation cooling, but deferred.
- Kälteschutz in its own TODO.

Things to avoid so Solar Shading stays distinct:

- Do not become a broad general-purpose cover automation suite.
- Do not clone 10+ runtime services before the settings model is clean.
- Do not build a full handler-priority editor as a first-class feature.
- Do not add many custom position slots with priorities unless a thermal/daylight use case proves it.
- Do not make motion/presence automation the main product story.
- Do not clone a generic Lovelace card; a future card should visualize Solar Shading's heat, horizon, glass and exposure model.
- Do not chase every cover type. Add only the cover behavior that improves the real target installation.

## Venetian And KNX Exploration

Venetian blinds are interesting if they become part of the heat/daylight model rather than generic cover parity.
KNX is interesting because it is common in serious building automation and may expose position and slat angle as separate channels.

- Research the Home Assistant cover capabilities commonly exposed by KNX venetian actuators:
  - position entity support
  - tilt/slat entity support
  - separate move/stop commands
  - state feedback reliability
  - travel-time and slat-time calibration
- Model venetian behavior as two outputs:
  - cover position for solar heat reduction
  - slat angle for daylight/glare control
- Keep the first scope diagnostic/simulator-first:
  - calculate recommended position
  - calculate recommended slat angle
  - expose both as attributes before controlling real hardware
- Later, add sequencing only if needed:
  - move cover first
  - wait for carriage settle
  - set slat angle
  - avoid repeated tilt chatter with minimum delta and hold time
- Avoid bus-specific code in the core model. Prefer Home Assistant cover capabilities and optional KNX notes/examples.

## Cheap Sensor Direction

- Deferred. Do not implement for the next simple product pass.
- Prefer Home Assistant entity inputs over vendor-specific logic.
- Cheap Zigbee/Tuya-style window contacts are useful for open/closed state, especially to avoid trying to cool/heat against an open window.
- Cheap Zigbee temperature/humidity sensors are useful as room sensors, but update interval and calibration quality vary by model.
- Avoid requiring a specific Tuya cloud integration; local Zigbee via ZHA or Zigbee2MQTT is usually the cleaner Home Assistant path.
- For the product, assume optional entities:
  - indoor temperature sensor
  - outdoor temperature sensor or weather entity
  - window contact sensor
  - rain sensor or weather precipitation state
  - solar radiation sensor in `W/m2`

## Room / Zone Model

- Allow multiple covers/windows to belong to one room or zone.
- Sum total solar heat power in `W` across all windows in the room.
- Balance closing one facade against daylight from other orientations.
- Later: optional AC/cooling capacity input as a room heat budget.

## Wall And Phase-Shift Model

- Refer users to the Ubakus U-value calculator (`https://www.ubakus.de/u-wert-rechner/`) for wall/roof construction values instead of trying to rebuild detailed building physics in Solar Shading.
- Ask for the relevant values that Ubakus calculates:
  - U-value in `W/m2K`
  - phase shift in hours
  - temperature amplitude damping / `1/TAV`
  - optional heat storage capacity if available
- Ask for the local room values that Ubakus does not know:
  - outside wall or roof area
  - orientation
  - room/zone assignment
  - whether the surface is shaded by trees, neighboring buildings, balcony, or roof overhang
- Add a simple wall/roof heat gain estimate using outside wall area, window area, outdoor temperature, and the imported Ubakus-style construction values.
- Model phase shift as a delayed heat pressure factor, especially for west walls, roof rooms, and heavy construction.
- Keep this intentionally coarse: presets and correction factors are enough for automation.

## Features To Retire Or Demote With Absolute Radiation

When reliable absolute solar radiation in `W/m2` is available, these should no longer drive current physical heat power:

- Cloud coverage damping for current heat-power estimation.
- Forecast cloud coverage as a heat-gain score input.
- UV as a proxy for current heat-power estimation.
- Rain probability / rain amount as current heat-power damping.
- Forecast precipitation probability / amount as heat-gain score inputs.
- Weather-derived reference radiation as the primary source.

Keep those signals as fallback or forecast signals:

- Use absolute current and forecast solar radiation for heat-gain decisions.
- Keep weather fallback minimal when no absolute radiation source is available.
- Keep forecast max temperature as a heat-protection gate and risk amplifier.
- Keep rain as a top-level no-solar/safety gate, not as a weighted heat-gain factor.
- Retire UV completely unless a later use case proves it adds real value.
