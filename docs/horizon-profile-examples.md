# Horizon Profile Examples

## Local Window Angle System

All horizon points are defined from the window's point of view:

- `0` = far left visible sky edge
- `90` = straight out from the window
- `180` = far right visible sky edge

This keeps the profile independent from the global compass azimuth. The global sun position is transformed into this local `0..180` system before the profile is evaluated.

## Point Format

Each point uses:

- `angle`: local horizontal angle in degrees
- `lower_elevation`: lower visible sky limit in degrees
- `upper_elevation`: upper visible sky limit in degrees

The sun is considered geometrically visible only when:

`lower_elevation <= sun_elevation <= upper_elevation`

## Simple Example

Use this as a starting profile:

```json
[
  { "angle": 0, "lower_elevation": 18, "upper_elevation": 90 },
  { "angle": 45, "lower_elevation": 12, "upper_elevation": 90 },
  { "angle": 90, "lower_elevation": 8, "upper_elevation": 55 },
  { "angle": 135, "lower_elevation": 14, "upper_elevation": 90 },
  { "angle": 180, "lower_elevation": 20, "upper_elevation": 90 }
]
```

Interpretation:

- the middle view is relatively open near the lower horizon
- the left and right edges are more blocked by nearby buildings or walls
- above the center, the sky is cut off at `55°`, for example by a tree canopy or roof overhang

## Typical Patterns

### Open Sky

```json
[
  { "angle": 0, "lower_elevation": 0, "upper_elevation": 90 },
  { "angle": 180, "lower_elevation": 0, "upper_elevation": 90 }
]
```

### Neighbor Building In Front

```json
[
  { "angle": 0, "lower_elevation": 20, "upper_elevation": 90 },
  { "angle": 90, "lower_elevation": 12, "upper_elevation": 90 },
  { "angle": 180, "lower_elevation": 24, "upper_elevation": 90 }
]
```

### Tree Canopy Above

```json
[
  { "angle": 0, "lower_elevation": 8, "upper_elevation": 90 },
  { "angle": 90, "lower_elevation": 8, "upper_elevation": 50 },
  { "angle": 180, "lower_elevation": 8, "upper_elevation": 90 }
]
```

## Reveal Inputs

Reveal shading is modeled with:

- `window_width`
- `reveal_left_depth`
- `reveal_right_depth`
- `reveal_top_depth`

Example:

- `window_width = 1.4`
- `reveal_left_depth = 0.18`
- `reveal_right_depth = 0.12`
- `reveal_top_depth = 0.10`

Interpretation:

- left reveal shades more strongly for sun from the left
- right reveal shades more strongly for sun from the right
- top reveal shades more strongly for high sun

`window_width` is required as soon as any reveal depth is set, because the reveal shading is calculated as a fraction of the visible window area.
