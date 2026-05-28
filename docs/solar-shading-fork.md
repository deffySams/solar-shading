# Solar Shading Fork Notes

Solar Shading is a private, experimental fork of Adaptive Cover.

## Credits

The base integration is [Adaptive Cover](https://github.com/basbruss/adaptive-cover). The fork keeps Adaptive Cover's Home Assistant integration structure, cover entities, manual override behavior, sun-position backbone and much of the original setup flow.

## Experimental Layer

The fork adds a daylight-aware heat-gain layer:

- local polar horizon profile per window
- left/right/top reveal self-shading
- angle-aware glass transmission and reflection presets
- weather and forecast damping
- optional Open-Meteo open-data solar radiation in W/m2, plus an optional local irradiance sensor override
- estimated solar heat power in W/m2 and W per configured window
- optional outside-temperature gated maximum watt cap per window
- forecast hot-day gate
- separate hot-day and very-hot-day maximum open-position caps
- away-from-home stricter behavior
- `/local/solar_shading_simulator.html` for tuning and sanity checks

All position settings are expressed as `% open`: `100` means fully open, `0` means closed.

## Hot vs Very Hot

`Hot-Day-Schwelle` opens the heat-protection gate. `Very-Hot-Schwelle` is where the temperature pressure saturates.

The optional override caps make the difference visible:

- `Hot-day max position (% open)` applies once the hot-day override threshold is reached.
- `Very-hot-day max position (% open)` applies once the forecast also reaches the very-hot threshold.

For a visible difference, set the very-hot position lower than the hot-day position, for example:

- hot day: `35 % open`
- very hot day: `15 % open`

## Later Roadmap

- Link multiple windows in one room, so the controller can protect the hot facade while preserving daylight from cooler orientations.
- Add optional AC/cooling capacity as a room-level budget: if the predicted solar window load would overload the AC, shade earlier/harder.
- Add outside wall area and a simple room-envelope estimate for longer-term overheating risk.
- Keep this as a transparent optimizer, not a black-box learner, until the core physics and UI are stable.

## Disclaimer

This is not a certified building-physics model. It is intentionally transparent, adjustable and experimental. In plain terms: it is AI-assisted overengineering slop for a private smart-home project, written to be inspectable instead of magical. Test each window before relying on it.
