"""Types for the minimal example ObsCore implementation."""

from enum import Enum, auto

class DataProductType(Enum):
    """Enumeration for data product types."""

    image = "image"
    cube = "cube"
    spectrum = "spectrum"
    sed = "sed"
    time_series = "timeseries"
    visibility = "visibility"
    event = "event"
    measurements = "measurements"