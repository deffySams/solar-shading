# Solar Shading

Private Home Assistant custom integration for daylight-aware heat protection of covers, rollers, blinds and awnings.

## Simulation oeffnen

Nach der Installation ist der Simulator direkt ueber Home Assistant erreichbar:

- Lokaler Home-Assistant-Link: `http://homeassistant.local:8123/local/solar_shading_simulator.html`
- Direkter Link in diesem Setup: `http://192.168.178.20:8123/local/solar_shading_simulator.html`
- Horizon-Preview: `http://homeassistant.local:8123/local/solar_shading_horizon_preview.html`

Falls der Hostname nicht aufloest, ersetze `homeassistant.local:8123` durch die IP-Adresse deiner Home-Assistant-Instanz. Die Dateien werden beim Setup der Integration automatisch nach `/config/www` kopiert und sind deshalb unter `/local/...` erreichbar.

This project is a private fork of [Adaptive Cover](https://github.com/basbruss/adaptive-cover). Huge credit to Bas Bruss and the Adaptive Cover contributors: the original integration, entity model, manual override handling and sun-position control backbone come from that project. This fork layers an experimental thermal/daylight policy on top.

## What This Fork Adds

- Local horizon model from 0..180 degrees relative to the window view.
- Side/top reveal shading model for partial self-shading by window geometry.
- Angle-aware glazing transmission/reflection presets, including double/triple glazing and low-e glass.
- Weather and forecast damping from clouds, rain, UV, daily max temperature and optional Open-Meteo solar radiation in W/m2.
- Estimated solar heat power in `W/m2` and `W per window`, plus an optional outside-temperature gated watt cap per window.
- Daylight-first heat-gain policy with presets, expert weights and `% open` targets.
- Separate hot-day and very-hot-day open limits, so "hot" and "very hot" can produce visibly different maximum closing behavior.
- Away-from-home stricter mode.
- Bundled browser simulator at `/local/solar_shading_simulator.html` for importing an existing Solar Shading window and tuning the inputs before committing settings.
- Bundled horizon preview at `/local/solar_shading_horizon_preview.html`.

## Simulator

Solar Shading ships with a browser simulator. It is installed with the integration and copied automatically to Home Assistant's `/config/www` folder on setup.

- Main simulator: `/local/solar_shading_simulator.html`
- Horizon preview: `/local/solar_shading_horizon_preview.html`
- In Home Assistant, open `http://homeassistant.local:8123/local/solar_shading_simulator.html`.
- The simulator can import current Solar Shading sensor attributes, show the visible horizon in the window preview, plot the current sun position, and compare the selected day with the shortest and longest day.

## Important Disclaimer

This is intentionally experimental private-home automation software. It is also, with love and full transparency, AI-assisted overengineering slop from someone who decided that "close the blinds when hot" deserved horizon interpolation, glazing spectra-ish approximations and a policy simulator. Treat it as a transparent tuning tool, not as safety-critical HVAC logic.

The goal is understandable and adjustable behavior, not a certified building-physics model. Validate every window manually before letting it control real covers.

## Quick Links In Home Assistant

- Simulator: `/local/solar_shading_simulator.html`
- Horizon preview: `/local/solar_shading_horizon_preview.html`
- Settings: Home Assistant -> Settings -> Devices & services -> Solar Shading -> Configure

## TODO / Later

- Change the hard heat-power cap from `W per window` to `W/m2 glass` for per-cover shading decisions. Keep `W per window` as a diagnostic value and later use it for room-level heat budgets.
- Keep the next product pass sensor-light: no new indoor/window/ventilation sensor workflow yet; focus first on simpler heat-gain decisions and clearer settings.
- Product settings cleanup: do not remove useful control. Hide only obsolete proxy settings and inactive dependent settings, so the UI stays precise but shows only inputs that can currently affect the decision.
- Keep threshold/gate consolidation for later; first retire obsolete proxy inputs without changing the meaning of the remaining controls.
- Room-level heat balance across multiple windows, so one darkened facade can be offset by daylight from other orientations.
- Optional air-conditioner capacity input, to avoid allowing more solar heat gain than the AC can realistically remove.
- Wall/room envelope estimate using total outside wall area, window area and simplified thermal inertia. Prefer importing user-entered results from the Ubakus U-value calculator (`https://www.ubakus.de/u-wert-rechner/`) instead of rebuilding wall physics ourselves.
- Wall and roof heat delay / phase-shift model as a simple correction factor from Ubakus-style inputs such as U-value, phase shift in hours, and temperature amplitude damping, not a full building-physics simulation.
- Group-level optimizer that balances `do not overload cooling` against `keep enough daylight`.
- Retire older proxy features from the heat-gain policy: UV, forecast cloud coverage, rain probability and rain amount. Use absolute solar radiation in `W/m2` as the current/forecast heat signal, keep rain only as a top-level no-solar/safety gate, and keep glazing/reflection plus solar radiation as core physics.

## Original Adaptive Cover Documentation

- [Adaptive Cover](#adaptive-cover)
  - [Features](#features)
  - [Installation](#installation)
    - [HACS (Recommended)](#hacs-recommended)
    - [Manual](#manual)
  - [Setup](#setup)
  - [Cover Types](#cover-types)
  - [Modes](#modes)
    - [Basic mode](#basic-mode)
    - [Climate mode](#climate-mode)
      - [Climate strategies](#climate-strategies)
  - [Variables](#variables)
    - [Common](#common)
    - [Vertical](#vertical)
    - [Horizontal](#horizontal)
    - [Tilt](#tilt)
    - [Automation](#automation)
    - [Climate](#climate)
    - [Blindspot](#blindspot)
  - [Entities](#entities)
  - [Blueprint (deprecated since v1.0.0)](#blueprint-deprecated-since-v100)

## Features

- Individual service devices for `vertical`, `horizontal` and `tilted` covers
- Two mode approach with multiple strategies [Modes(`basic`,`climate`)](https://github.com/basbruss/adaptive-cover?tab=readme-ov-file#modes)
- Binary Sensor to track when the sun is in front of the window
- Sensors for `start` and `end` time
- Auto manual override detection

- **Climate Mode**

  - Weather condition based operation
  - Presence based operation
  - Switch to toggle climate mode
  - Sensor for displaying the operation modus (`winter`,`intermediate`,`summer`)

- **Adaptive Control**

  - Turn control on/off
  - Control multiple covers
  - Set start time to prevent opening blinds while you are asleep
  - Set minimum interval time between position changes
  - set minimum percentage change

## Installation

### HACS (Recommended)

Add <https://github.com/deffySams/solar-shading> as custom repository to HACS.
Search and download Solar Shading within HACS.

Restart Home Assistant and add the integration. The simulator is bundled and copied to `/config/www` automatically during setup.

### Manual

Download the `solar_shading` folder from this GitHub repository.
Add the folder to `config/custom_components/`.

Restart Home-Assistant and add the integration.

## Setup

Adaptive Cover supports (for now) three types of covers/blinds; `Vertical` and `Horizontal` and `Venetian (Tilted)` blinds.
Each type has its own specific parameters to setup a sensor. To setup the sensor you first need to find out the azimuth of the window(s). This can be done by finding your location on [Open Street Map Compass](https://osmcompass.com/).

## Cover Types

|              | Vertical                      | Horizontal                      | Tilted                          |
| ------------ | ----------------------------- | ------------------------------- | ------------------------------- |
|              | ![alt text](images/image.png) | ![alt text](images/image-2.png) | ![alt text](images/image-1.png) |
| **Movement** | Up/Down                       | In/Out                          | Tilting                         |
|              | [variables](#vertical)        | [variables](#horizontal)        | [variables](#tilt)              |

## Modes

This component supports two strategy modes: A `basic` mode and a `climate comfort/energy saving` mode that works with presence and temperature detection.

```mermaid
  graph TD

  A[("fa:fa-sun Sundata")]
  A --> B["Basic Mode"]
  A --> C["Climate Mode"]

  subgraph "Basic Mode"
      B --> BA("Sun within field of view")

      BA --> |No| BC{{Default}}
      BC --> BE("Time between sunset and sunrise?")
      BE --> |Yes| BF["Return default"]
      BE --> |No| BG["Return Sunset default"]

      BA --> |Yes| BD("Elevation above 0?")
      BD --> |Yes| BH{{"Calculated Position"}}
      BD --> |No| BC
  end

  subgraph "Climate Mode"
      C --> CA("Check Presence")
  end

  subgraph "Occupants"
      CA --> |True| CB("Temperature above maximum comfort (summer)?")

      CB --> |Yes| CD("Transparent blind?")
      CB --> |No| CE("Lux/Irradiance below threshold or Weather is not sunny?")

      CD --> |Yes| CF["Return fully closed (0%)"]
      CD --> |No| B

      CE --> |Yes| CG("Temperature below minimum comfort (winter) and sun infront of window and elevation > 0?")
      CE --> |No| B

      CG --> |Yes| CH["Return fully open (100%)"]
      CG --> |No| BC
  end

  subgraph "No Occupants"
      CA --> |False| CC("Sun infront of window and elevation > 0?")
      CC --> |No| BC
      CC --> |Yes| CI("Temperature above maximum comfort (summer)?")
      CI --> |Yes| CF
      CI --> |No| CJ("Temperature below minimum comfort (winter)")
      CJ --> |Yes| CH
      CJ --> |No| BC
  end
```

### Basic mode

This mode uses the calculated position when the sun is within the specified azimuth range of the window. Else it defaults to the default value or after sunset value depending on the time of day.

### Climate mode

This mode calculates the position based on extra parameters for presence, indoor temperature, minimal comfort temperature, maximum comfort temperature and weather (optional).
This mode is split up in two types of strategies; [Presence](https://github.com/basbruss/adaptive-cover?tab=readme-ov-file#presence) and [No Presence](https://github.com/basbruss/adaptive-cover?tab=readme-ov-file#no-presence).

#### Climate strategies

- **No Presence**:
  Providing daylight to the room is no objective if there is no presence.

  - **Below minimal comfort temperature**:
    If the sun is above the horizon and the indoor temperature is below the minimal comfort temperature it opens the blind fully or tilt the slats to be parallel with the sun rays to allow for maximum solar radiation to heat up the room.

  - **Above maximum comfort temperature**:
    The objective is to not heat up the room any further by blocking out all possible radiation. All blinds close fully to block out light. <br> <br>
    If the indoor temperature is between both thresholds the position defaults to the set default value based on the time of day.

- **Presence** (or no Presence Entity set):
  The objective is to reduce glare while providing daylight to the room. All calculation is done by the basic model for Horizontal and Vertical blinds. <br> <br>
  If you added a weather entity, it will only use the above calculations if the weather state corresponds with the existence of direct sun rays. These states are `sunny`,`windy`, `partlycloudy`, and `cloudy` by default, but you can change the list of states in the weather options. If not equal to these states the position will default to the default value to allow more sunlight entering the room with minimizing the glare due to the weather condition. <br><br>
  Tilted blinds will only deviate from the above approach if the inside temperature is above the maximum comfort temperature. In that case, the slats will be positioned at 45 degrees as this is [found optimal](https://www.mdpi.com/1996-1073/13/7/1731).

## Variables

### Common

| Variables                     | Default | Range | Description                                                                                              |
| ----------------------------- | ------- | ----- | -------------------------------------------------------------------------------------------------------- |
| Entities                      | []      |       | Denotes entities controllable by the integration                                                         |
| Window Azimuth                | 180     | 0-359 | The compass direction of the window, discoverable via [Open Street Map Compass](https://osmcompass.com/) |
| Default Position              | 60      | 0-100 | Initial position of the cover in the absence of sunlight glare detection                                 |
| Minimal Position              | 100     | 0-99  | Minimal opening position for the cover, suitable for partially closing certain cover types               |
| Maximum Position              | 100     | 1-100 | Maximum opening position for the cover, suitable for partially opening certain cover types               |
| Field of view Left            | 90      | 1-90  | Unobstructed viewing angle from window center to the left, in degrees                                    |
| Field of view Right           | 90      | 1-90  | Unobstructed viewing angle from window center to the right, in degrees                                   |
| Minimal Elevation             | None    | 0-90  | Minimal elevation degree of the sun to be considered                                                     |
| Maximum Elevation             | None    | 1-90  | Maximum elevation degree of the sun to be considered                                                     |
| Default position after Sunset | 0       | 0-100 | Cover's default position from sunset to sunrise                                                          |
| Offset Sunset time            | 0       |       | Additional minutes before/after sunset                                                                   |
| Offset Sunrise time           | 0       |       | Additional minutes before/after sunrise                                                                  |
| Inverse State                 | False   |       | Calculates inverse state for covers fully closed at 100%                                                 |

### Vertical

| Variables         | Default | Range | Description                                                                                 |
| ----------------- | ------- | ----- | ------------------------------------------------------------------------------------------- |
| Window Height     | 2.1     | 0.1-6 | Length of fully extended cover/window                                                       |
| Glare Zone        | 0.5     | 0.1-2 | Objects within this distance of the cover recieve direct sunlight. Measured horizontally from the bottom of the cover when fully extended |

### Horizontal

| Variables                  | Default | Range | Description                                    |
| -------------------------- | ------- | ----- | ---------------------------------------------- |
| Awning Height              | 2       | 0.1-6 | Height from work area to awning mounting point |
| Awning Length (horizontal) | 2.1     | 0.3-6 | Length of the awning when fully extended       |
| Awning Angle               | 0       | 0-45  | Angle of the awning from the wall              |
| Glare Zone                 | 0.5     | 0.1-2 | Objects within this distance of the cover recieve direct sunlight |

### Tilt

| Variables     | Default        | Range  | Description                                                |
| ------------- | -------------- | ------ | ---------------------------------------------------------- |
| Slat Depth    | 3              | 0.1-15 | Width of each slat                                         |
| Slat Distance | 2              | 0.1-15 | Vertical distance between two slats in horizontal position |
| Tilt Mode     | Bi-directional |        |                                                            |

### Automation

| Variables                                  | Default      | Range | Description                                                                                    |
| ------------------------------------------ | ------------ | ----- | ---------------------------------------------------------------------------------------------- |
| Minimum Delta Position                     | 1            | 1-90  | Minimum position change required before another change can occur                               |
| Minimum Delta Time                         | 2            |       | Minimum time gap between position change                                                       |
| Start Time                                 | `"00:00:00"` |       | Earliest time a cover can be adjusted after midnight                                           |
| Start Time Entity                          | None         |       | The earliest moment a cover may be changed after midnight. _Overrides the `start_time` value_  |
| Manual Override Duration                   | `15 min`     |       | Minimum duration for manual control status to remain active                                    |
| Manual Override reset Timer                | False        |       | Resets duration timer each time the position changes while the manual control status is active |
| Manual Override Threshold                  | None         | 1-99  | Minimal position change to be recognized as manual change                                      |
| Manual Override ignore intermediate states | False        |       | Ignore StateChangedEvents that have state `opening` or `closing`                               |
| End Time                                   | `"00:00:00"` |       | Latest time a cover can be adjusted each day                                                   |
| End Time Entity                            | None         |       | The latest moment a cover may be changed . _Overrides the `end_time` value_                    |
| Adjust at end time                         | `False`      |       | Make sure to always update the position to the default setting at the end time.                |

### Climate

| Variables                     | Default | Range | Example                                       | Description                                                                                                                                          |
| ----------------------------- | ------- | ----- | --------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------- |
| Indoor Temperature Entity     | `None`  |       | `climate.living_room` \| `sensor.indoor_temp` |                                                                                                                                                      |
| Minimum Comfort Temperature   | 21      | 0-86  |                                               |                                                                                                                                                      |
| Maximum Comfort Temperature   | 25      | 0-86  |                                               |                                                                                                                                                      |
| Outdoor Temperature Entity    | `None`  |       | `sensor.outdoor_temp`                         |                                                                                                                                                      |
| Outdoor Temperature Threshold | `None`  |       |                                               | If the minimum outside temperature for summer mode is set and the outside temperature falls below this threshold, summer mode will not be activated. |
| Presence Entity               | `None`  |       |                                               |                                                                                                                                                      |
| Weather Entity                | `None`  |       | `weather.home`                                | Can also serve as outdoor temperature sensor                                                                                                         |
| Lux Entity                    | `None`  |       | `sensor.lux`                                  | Returns measured lux                                                                                                                                 |
| Lux Threshold                 | `1000`  |       |                                               | "In non-summer, above threshold, use optimal position. Otherwise, default position or fully open in winter."                                         |
| Irradiance Entity             | `None`  |       | `sensor.irradiance`                           | Returns measured irradiance                                                                                                                          |
| Irradiance Threshold          | `300`   |       |                                               | "In non-summer, above threshold, use optimal position. Otherwise, default position or fully open in winter."                                         |

### Blindspot

| Variables            | Default | Range                 | Example | Description                                                                                                          |
| -------------------- | ------- | --------------------- | ------- | -------------------------------------------------------------------------------------------------------------------- |
| Blind Spot Left      | None    | 0-max(fov_right, 180) |         | Start point of the blind spot on the predefined field of view, where 0 is equal to the window azimuth - fov left.    |
| Blind Spot Right     | None    | 1-max(fov_right, 180) |         | End point of the blind spot on the predefined field of view, where 1 is equal to the window azimuth - fov left + 1 . |
| Blind Spot Elevation | None    | 0-90                  |         | Minimal elevation of the sun for the blindspot area.                                                                 |

## Entities

The integration dynamically adds multiple entities based on the used features.

These entities are always available:
| Entities | Default | Description |
| --------------------------------------------- | -------------- | ---------------------------------------------------------------------------------------------------------------------- |
| `sensor.{type}_cover_position_{name}` | | Reflects the current state determined by predefined settings and factors such as sun position, weather, and temperature |
| `sensor.{type}_control_method_{name}` | `intermediate` | Indicates the active control strategy based on weather conditions. Options include `winter`, `summer`, and `intermediate` |
| `sensor.{type}_start_sun_{name}` | | Shows the starting time when the sun enters the window's view, with an interval of every 5 minutes. |
| `sensor.{type}_end_sun_{name}` | | Indicates the ending time when the sun exits the window's view, with an interval of every 5 minutes. |
| `binary_sensor.{type}_manual_override_{name}` | `off` | Indicates if manual override is engaged for any blinds. |
| `binary_sensor.{type}_sun_infront_{name}` | `off` | Indicates whether the sun is in front of the window within the designated field of view. |
| `switch.{type}_toggle_control_{name}` | `on` | Activates the adaptive control feature. When enabled, blinds adjust based on calculated position, unless manually overridden. |
| `switch.{type}_manual_override_{name}` | `on` | Enables detection of manual overrides. A cover is marked if its position differs from the calculated one, resetting to adaptive control after a set duration. |
| `button.{type}_reset_manual_override_{name}` | `on` | Resets manual override tags for all covers; if `switch.{type}_toggle_control_{name}` is on, it also restores blinds to their correct positions. |

When climate mode is setup you will also get these entities:

| Entities                                   | Default | Description                                                                                                 |
| ------------------------------------------ | ------- | ----------------------------------------------------------------------------------------------------------- |
| `switch.{type}_climate_mode_{name}`        | `on`    | Enables climate mode strategy; otherwise, defaults to the standard strategy.                                |
| `switch.{type}_outside_temperature_{name}` | `on`    | Switches between inside and outside temperatures as the basis for determining the climate control strategy. |

![entities](https://github.com/basbruss/adaptive-cover/blob/main/images/entities.png)

### Blueprint (deprecated since v1.0.0)

This integration provides the option to download a blueprint to control the covers automatically by the provide sensor.
By selecting the option the blueprints will be added to your local blueprints folder.
