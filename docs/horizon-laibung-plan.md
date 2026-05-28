# Horizon And Laibung Plan

## What Adaptive Cover Already Provides

Adaptive Cover already has a useful geometric baseline:

- window azimuth
- field of view left/right
- minimum and maximum sun elevation
- a simple blind spot segment
- vertical cover geometry through `window_height` and `distance_shaded_area`
- stable Home Assistant integration behavior such as manual override, minimum delta time, and minimum delta position

This makes it a good base, but it does not yet model:

- a polar horizon profile with multiple azimuth/elevation support points
- interpolation across the horizon curve
- reveal geometry on the left, right, and top
- percentage-based reveal shading over the visible glass area
- a reusable solar exposure factor for later heat-gain logic

## Proposed Approach

Keep Adaptive Cover Basic Mode as the control backbone and add a new geometry layer for:

1. horizon visibility
2. reveal shading percentage
3. combined direct solar exposure factor

The new logic should be additive and observable before it becomes control-critical.

The implementation should stay window-agnostic:

- no hardcoded room names
- no entity-specific geometry in code
- all geometry comes from config data per Adaptive Cover instance
- the same logic must work for any facade or window once the inputs are provided

## Suggested Delivery Steps

### Phase 1: Data Model

Add config fields for each window/facade instance:

- `horizon_profile`
- `reveal_left_depth`
- `reveal_right_depth`
- `reveal_top_depth`
- `window_width`
- `window_height`

The `horizon_profile` should be a polar list of support points, for example:

```json
[
  {"azimuth": 70, "elevation": 12},
  {"azimuth": 85, "elevation": 9},
  {"azimuth": 100, "elevation": 7}
]
```

### Phase 2: Horizon Engine

Implement a small geometry helper that:

- normalizes azimuth points
- interpolates the effective horizon elevation at the current solar azimuth
- returns whether the sun is above that local horizon

Planned outputs:

- `effective_horizon_elevation`
- `horizon_clearance`
- `sun_above_horizon_profile`

### Phase 3: Reveal Engine

Implement a reveal shading helper that estimates how much of the glass is shadowed by:

- left reveal
- right reveal
- top reveal

Planned outputs:

- `left_reveal_shadow_pct`
- `right_reveal_shadow_pct`
- `top_reveal_shadow_pct`
- `total_reveal_shadow_pct`

### Phase 4: Exposure Layer

Combine the two geometry blocks into one reusable output:

- `direct_solar_exposure_factor`

Initial idea:

- horizon block acts like a hard gate
- reveal block acts like a percentage reduction

### Phase 5: Diagnostics First

Before changing cover movement logic, expose the new values as debug-friendly sensors/attributes so we can validate:

- current effective horizon
- current reveal shading
- current exposure factor
- current reasoning for "sun effective on window"

### Phase 6: Control Integration

Only after validation:

- feed the new exposure factor into the cover position logic
- let the new logic tighten shading relative to the AC base state
- keep manual override and motion hysteresis unchanged

## Recommended First Implementation Scope

Build the feature in a reusable way first:

- generic config schema
- generic horizon helper
- generic reveal helper
- generic diagnostic outputs

First coding slice:

1. create internal data model
2. add horizon interpolation helper
3. expose diagnostics
4. stop before changing control behavior

Only after that, test the generic implementation on a first real window in Home Assistant.

This keeps the first merge small, reusable, and debuggable.
