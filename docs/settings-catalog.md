# Solar Shading Settings Catalog

Current settings, short meaning, and proposed ownership for the profile model.

Ownership legend:

```text
House        Shared defaults/rules for the whole house.
Room         Applies to all windows in one room.
Room facade  Applies to all windows on one room wall/facade.
Window       Physical endpoint or real local exception.
Expert       Keep, but hide from normal setup.
Legacy       Keep only for compatibility until retired.
Retire       Remove or migrate away.
```

## Setup And Identity

| Setting | Meaning | Target |
| --- | --- | --- |
| `name` | Name of this Solar Shading config entry. | Window |
| `mode` / `sensor_type` | Cover calculation type: blind, awning, tilt. | House default, Window override |
| `template_entry` | Copies options from an existing entry during setup. | Retire after real profiles |
| `group` | Cover entities controlled by this entry. | Window |
| `facade_name` | Free text label for the facade. | Retire into facade_id / facade dropdown |
| `floor_name` | Free text label for the floor. | Retire into HA floor dropdown |
| `room_name` | Free text label for the room. | Retire into HA area/room dropdown |

## House Axis, Facades, And Geometry

| Setting | Meaning | Target |
| --- | --- | --- |
| `use_facade_azimuth` | Derive window azimuth from reference facade plus offset. | Retire into profile merge |
| `facade_reference_azimuth` | Compass azimuth of the house reference facade. | House |
| `facade_offset` | Angle offset from reference facade to this facade/window. | Facade / Room facade |
| `set_azimuth` | Final compass azimuth of the window normal. | Derived, Window override |
| `fov_left` | How far left the sun can be and still hit the window. | House default, Room facade override |
| `fov_right` | How far right the sun can be and still hit the window. | House default, Room facade override |
| `min_elevation` | Minimum solar elevation to consider. | Expert / Room facade |
| `max_elevation` | Maximum solar elevation to consider. | Expert / Room facade |
| `horizon_profile` | Local lower/upper horizon profile across the window view. | Room facade, Window override |
| `window_width` | Physical glass/window width in m. | Window |
| `window_height` | Physical glass/window height in m. | Window |
| `distance_shaded_area` | Vertical blind projection depth / shaded target distance. | Window, rename |
| `reveal_left_depth` | Left reveal self-shading depth in m. | House default, Room facade override |
| `reveal_right_depth` | Right reveal self-shading depth in m. | House default, Room facade override |
| `reveal_top_depth` | Top reveal self-shading depth in m. | House default, Room facade override |
| `glass_type` | Glass optical preset. | House default, Window override |
| `length_awning` | Awning extension length. | Window, awning only |
| `angle` | Awning angle. | Window, awning only |
| `height_awning` | Defined but not used by active code. | Retire |
| `slat_depth` | Venetian blind slat depth. | House default, Window override |
| `slat_distance` | Venetian blind slat spacing. | House default, Window override |
| `tilt_mode` | Tilt calculation mode. | House default, Window override |

## Base Position And Output Limits

| Setting | Meaning | Target |
| --- | --- | --- |
| `default_percentage` | Normal open position / fallback target. | House default, Room/Window override |
| `sunset_position` | Position after sunset / night fallback. | House, rename to Ruhe-/Nachtposition |
| `sunset_offset` | Offset around sunset. | Expert, replace normal UI with time-guided setting |
| `sunrise_offset` | Offset around sunrise. | Expert, replace normal UI with time-guided setting |
| `enable_max_position` | Enable upper output clamp. | Expert / Window |
| `max_position` | Maximum allowed open position. | Expert / Window |
| `enable_min_position` | Enable lower output clamp. | Expert / Window |
| `min_position` | Minimum allowed open position. | Expert / Window |
| `inverse_state` | Invert final output. | Expert / Window compatibility |
| `interp` | Enable output remapping. | Expert / Window compatibility |
| `interp_start` | New start value for simple remap. | Expert |
| `interp_end` | New end value for simple remap. | Expert |
| `interp_list` | Input list for custom remap. | Expert |
| `interp_list_new` | Output list for custom remap. | Expert |

## Automation Timing And Manual Override

| Setting | Meaning | Target |
| --- | --- | --- |
| `delta_position` | Minimum position delta before sending a command. | House default, Window override |
| `delta_time` | Minimum time between repeated commands. | House default, Window override |
| `start_time` | Static automation start time. | House / Room |
| `start_entity` | Entity-based automation start time. | House / Room |
| `end_time` | Static automation end time. | House / Room |
| `end_entity` | Entity-based automation end time. | House / Room |
| `return_sunset` | Schedule refresh/return around sunset. | House |
| `manual_override_duration` | How long manual changes pause automation. | House |
| `manual_override_reset` | Whether new manual changes reset the timer. | House |
| `manual_threshold` | Difference threshold for detecting manual override. | Expert / Window |
| `manual_ignore_intermediate` | Ignore opening/closing intermediate states. | Expert |

## Blind Spot

| Setting | Meaning | Target |
| --- | --- | --- |
| `blind_spot` / `enable_blind_spot` | Enables a sun-angle exclusion band. | Expert / Room facade |
| `blind_spot_left` | Left edge of excluded sun angle. | Expert / Room facade |
| `blind_spot_right` | Right edge of excluded sun angle. | Expert / Room facade |
| `blind_spot_elevation` | Optional elevation for the blind spot rule. | Expert / Room facade |

## Weather, Solar Radiation, And Forecast

| Setting | Meaning | Target |
| --- | --- | --- |
| `weather_entity` | Weather entity, mainly for temperature forecast. | House |
| `weather_state` | Legacy list of sunny/weather states. | Legacy / Retire from heat policy |
| `use_open_data_solar_radiation` | Fetch Open-Meteo/OpenSolar radiation. | House |
| `solar_radiation_entity` | Local irradiance sensor override. | House / Window override |
| `solar_radiation_reference_w_m2` | Incoming radiation threshold where sun counts as strong. | House, rename to Schwelle fuer starke Sonneneinstrahlung |
| `use_forecast_max_temp_today` | Use today's max temperature forecast. | House |
| `use_forecast_max_temp_tomorrow` | Use tomorrow's max temperature forecast. | House |
| `forecast_hot_day_threshold` | Temperature where heat protection starts to care. | House |
| `forecast_very_hot_day_threshold` | Temperature where very-hot pressure saturates. | House |
| `forecast_preemptive_start_time` | Earliest time forecast can act preemptively. | House |
| `forecast_influence_strength` | Forecast pressure multiplier. | House preset, Expert numeric |
| `use_forecast_cloud_coverage` | Legacy forecast cloud toggle, currently not active. | Retire |
| `use_forecast_precipitation_probability` | Legacy rain-probability toggle, currently not active. | Retire |
| `use_forecast_precipitation_amount` | Legacy rain amount toggle, currently not active. | Retire |
| `use_forecast_uv_index` | Legacy UV toggle, currently not active. | Retire |

## Heat Protection Policy

| Setting | Meaning | Target |
| --- | --- | --- |
| `enable_heat_gain_policy` | Enables the current heat-gain policy. | House |
| `policy_preset` | Bias profile: daylight/balanced/cooling. | House |
| `has_additional_daylight_windows` | Room has other daylight, so shading may be stricter. | Room |
| `partial_close_threshold` | Internal score where partial shading starts. | Expert / House preset |
| `full_close_threshold` | Internal score where strong shading starts. | Expert / House preset |
| `partial_close_position` | Open position target for partial shading. | House preset |
| `full_close_position` | Open position target for strong shading. | House preset |
| `show_expert_weights` | Expose raw component weights. | Expert |
| `weight_direct_exposure` | Weight of direct solar exposure. | Expert / House |
| `weight_incidence` | Weight of incidence angle. | Expert / House |
| `weight_glazing` | Weight of glass transmission. | Expert / House |
| `weight_weather` | Weight of old weather proxy. | Retire |
| `weight_solar_radiation` | Weight of measured/open solar radiation. | Expert / House |
| `weight_forecast_temperature` | Weight of temperature forecast pressure. | Expert / House |
| `weight_forecast_uv` | Legacy UV weight, currently not active. | Retire |
| `weight_forecast_clouds` | Legacy cloud weight, currently not active. | Retire |
| `weight_forecast_precipitation_probability` | Legacy rain probability weight. | Retire |
| `weight_forecast_precipitation_amount` | Legacy rain amount weight. | Retire |
| `enable_legacy_basic_shading` | Legacy flag currently hardcoded inactive. | Retire |

## Heat Cap And Away Mode

| Setting | Meaning | Target |
| --- | --- | --- |
| `heat_power_limit_enabled` | Enables hard cap by transmitted solar heat. | House |
| `heat_power_max_watts` | Actually max transmitted heat in W/m2. | House, rename |
| `heat_power_outside_temp_threshold` | Outside temperature gate for hard heat cap. | House |
| `heat_protection_min_outside_temp` | Minimum outside temperature for heat protection. | House |
| `hot_day_close_enabled` | Separate hot-day position cap. | Merge into heat preset |
| `hot_day_close_threshold` | Temperature where hot-day cap starts. | Merge into heat preset |
| `hot_day_close_position` | Open position on hot days. | Merge into heat preset |
| `very_hot_day_close_position` | Open position on very hot days. | Merge into heat preset |
| `enable_away_mode` | Enables stricter behaviour when away. | House |
| `away_entity` | Entity that indicates away/absence. | House |
| `away_score_multiplier` | Makes policy score stronger when away. | Expert / House |
| `away_threshold_reduction` | Lowers thresholds when away. | Expert / House |
| `away_position_offset` | Closes further when away. | Expert / House |

## Legacy Climate Mode

| Setting | Meaning | Target |
| --- | --- | --- |
| `climate_mode` | Enables old comfort/climate layer. | Legacy / optional mode |
| `temp_entity` | Indoor/climate temperature source. | Legacy |
| `temp_low` | Winter/low temperature threshold. | Legacy |
| `temp_high` | Summer/high temperature threshold. | Legacy |
| `outside_temp` | Outside temperature sensor. | Legacy / House if kept |
| `outside_threshold` | Outside temperature threshold for summer mode. | Legacy |
| `presence_entity` | Presence source for old comfort logic. | Legacy |
| `lux_entity` | Brightness sensor for old logic. | Legacy / Retire |
| `lux_threshold` | Brightness threshold for old logic. | Legacy / Retire |
| `irradiance_entity` | Irradiance sensor for old logic. | Legacy |
| `irradiance_threshold` | Irradiance threshold for old logic. | Legacy |
| `transparent_blind` | Old binary transparent-cover summer close rule. | Replace with cover effect + binary/scaling mode |

## Other Constants

| Setting | Meaning | Target |
| --- | --- | --- |
| `blueprint` | Old blueprint path/text, not exposed in current flow. | Retire |
