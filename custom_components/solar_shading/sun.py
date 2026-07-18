"""Fetch sun data."""

from datetime import UTC, date, datetime, timedelta

import pandas as pd
from astral import Observer
from astral.sun import azimuth, elevation, sunrise, sunset
from homeassistant.core import HomeAssistant

try:
    from homeassistant.helpers.sun import get_astral_observer
except ImportError:  # Older supported Home Assistant releases

    def get_astral_observer(hass: HomeAssistant) -> Observer:
        """Build an Astral observer for older supported HA releases."""
        return Observer(
            latitude=hass.config.latitude,
            longitude=hass.config.longitude,
            elevation=hass.config.elevation,
        )


class SunData:
    """Access local sun data."""

    def __init__(self, timezone, hass: HomeAssistant) -> None:  # noqa: D107
        self.hass = hass
        self.observer = get_astral_observer(self.hass)
        self.timezone = timezone

    @property
    def times(self) -> pd.DatetimeIndex:
        """Define time interval."""
        start_date = date.today()
        end_date = start_date + timedelta(days=1)

        times = pd.date_range(
            start=start_date, end=end_date, freq="5min", tz=self.timezone, name="time"
        )
        return times

    @property
    def solar_azimuth(self) -> list:
        """Create list with solar azimuth data per 5 minutes."""
        return [azimuth(self.observer, point_in_time) for point_in_time in self.times]

    @property
    def solar_elevation(self) -> list:
        """Create list with solar elevation data per 5 minutes."""
        return [elevation(self.observer, point_in_time) for point_in_time in self.times]

    def sunset(self) -> datetime:
        """Fetch sunset time."""
        return sunset(self.observer, date.today(), tzinfo=UTC)

    def sunrise(self) -> datetime:
        """Fetch sunrise time."""
        return sunrise(self.observer, date.today(), tzinfo=UTC)
