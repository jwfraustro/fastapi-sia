"""Models for FastAPI SIA requests."""


from enum import StrEnum
from typing import List, Literal, Optional, Union

from pydantic import BaseModel, Field, field_validator, model_validator

FloatOrInf = Union[float, Literal["Inf", "-Inf"]]


class MinMaxRange(BaseModel):
    min: FloatOrInf
    max: FloatOrInf

    @classmethod
    def from_string(cls, s: str):
        tokens = s.strip().split()
        if len(tokens) != 2:
            raise ValueError(f"Expected two values, got: {s}")
        min_val = cls._parse_token(tokens[0])
        max_val = cls._parse_token(tokens[1])
        return cls(min=min_val, max=max_val)

    @staticmethod
    def _parse_token(token: str) -> FloatOrInf:
        if token in ("Inf", "-Inf"):
            return token
        try:
            return float(token)
        except ValueError:
            raise ValueError(f"Invalid float or Inf value: {token}")


class Polygon(BaseModel):
    shape: Literal["POLYGON"] = "POLYGON"
    coordinates: List[float]  # flat list: lon1, lat1, lon2, lat2, ...

    @model_validator(mode="before")
    def validate_polygon(cls, values):
        coords = values.get("coordinates", [])
        if len(coords) < 6 or len(coords) % 2 != 0:
            raise ValueError("POLYGON must have at least 3 lon/lat pairs (6 values total)")
        return values


class Range(BaseModel):
    shape: Literal["RANGE"] = "RANGE"
    lon1: float
    lon2: float
    lat1: float
    lat2: float

    @model_validator(mode="before")
    def check_bounds(cls, values):
        for key in ["lon1", "lon2"]:
            if not 0 <= values[key] <= 360:
                raise ValueError(f"{key} must be in [0, 360]")
        for key in ["lat1", "lat2"]:
            if not -90 <= values[key] <= 90:
                raise ValueError(f"{key} must be in [-90, 90]")
        return values


class Circle(BaseModel):
    shape: Literal["CIRCLE"] = "CIRCLE"
    longitude: float
    latitude: float
    radius: float

    @model_validator(mode="before")
    def check_bounds(cls, values):
        lon, lat, _ = values["longitude"], values["latitude"], values["radius"]
        if not (0 <= lon <= 360):
            raise ValueError("Longitude must be in [0, 360]")
        if not (-90 <= lat <= 90):
            raise ValueError("Latitude must be in [-90, 90]")
        return values


class Time(BaseModel):
    """Time range request model."""

    start_time: float
    end_time: Optional[float] = None  # None means no end time specified

    @classmethod
    def from_string(cls, s: str):
        tokens = s.strip().split()
        if len(tokens) == 1:
            return cls(start_time=float(tokens[0]), end_time=None)
        elif len(tokens) == 2:
            return cls(start_time=float(tokens[0]), end_time=float(tokens[1]))
        else:
            raise ValueError(f"Expected one or two values, got: {s}")


class PolarizationLabels(StrEnum):
    """Enumeration for allowed polarization states."""

    I = "I"
    Q = "Q"
    U = "U"
    V = "V"
    RR = "RR"
    LL = "LL"
    RL = "RL"
    LR = "LR"
    XX = "XX"
    YY = "YY"
    XY = "XY"
    YX = "YX"
    POLI = "POLI"
    POLA = "POLA"


class DataProductType(StrEnum):
    """Enumeration for data product types.

    For SIA, only image and cube are allowed
    """

    IMAGE = "image"
    CUBE = "cube"


def parse_pos(pos_str: str) -> Union[Circle, Range, Polygon]:
    """Parse POS string into appropriate shape model."""
    shape = pos_str.split()[0].upper()
    parts = pos_str[len(shape) :].strip()
    if shape == "CIRCLE":
        lon, lat, radius = map(float, parts.split(" "))
        return Circle(longitude=lon, latitude=lat, radius=radius)
    elif shape == "RANGE":
        lon1, lon2, lat1, lat2 = map(float, parts.split(" "))
        return Range(lon1=lon1, lon2=lon2, lat1=lat1, lat2=lat2)
    elif shape == "POLYGON":
        coords = list(map(float, parts.split(" ")))
        return Polygon(shape="POLYGON", coordinates=coords)
    else:
        raise ValueError(f"Unknown POS shape: {shape}")


class SIASearchParams(BaseModel):
    """Query parameters for the SIA API."""

    POS: Optional[list[Union[Circle, Range, Polygon]]] = None
    BAND: Optional[list[MinMaxRange]] = None
    TIME: Optional[list[Time]] = None
    POL: Optional[list[PolarizationLabels]] = None
    FOV: Optional[list[MinMaxRange]] = None
    SPATRES: Optional[list[MinMaxRange]] = None
    SPECRP: Optional[list[MinMaxRange]] = None
    EXPTIME: Optional[list[MinMaxRange]] = None
    TIMERES: Optional[list[MinMaxRange]] = None
    ID: Optional[list[str]] = None
    COLLECTION: Optional[list[str]] = None
    FACILITY: Optional[list[str]] = None
    INSTRUMENT: Optional[list[str]] = None
    DPTYPE: Optional[list[DataProductType]] = None
    CALIB: Optional[list[Literal[1, 2, 3]]] = None
    TARGET: Optional[list[str]] = None
    FORMAT: Optional[list[str]] = None
    MAXREC: Optional[int] = Field(default=None, ge=0)

    @field_validator("POS", mode="before")
    @classmethod
    def parse_pos(cls, pos: list[str] | None) -> list[Union[Circle, Range, Polygon]]:
        """Parse POS string into appropriate shape model."""
        if pos is None:
            return None

        positions = []

        for p in pos:
            if isinstance(p, str):
                pos_shape = parse_pos(p)
                if isinstance(pos_shape, (Circle, Range, Polygon)):
                    positions.append(pos_shape)
                else:
                    raise ValueError(f"Invalid POS shape: {p}")
            else:
                raise ValueError(f"Invalid type for POS parameter: {type(p)}")

        return positions

    @field_validator("BAND", "FOV", "SPATRES", "SPECRP", "EXPTIME", "TIMERES", mode="before")
    @classmethod
    def parse_range_params(cls, values: list[str] | None) -> list[MinMaxRange]:
        """Parse band or other min-max range parameters from strings."""
        if values is None:
            return None
        range_params = []
        for val in values:
            if not isinstance(val, str):
                raise ValueError(f"Invalid type for range parameter: {type(val)}")
            if isinstance(val, str):
                range_params.append(MinMaxRange.from_string(val))
        return range_params

    @field_validator("TIME", mode="before")
    @classmethod
    def parse_time(cls, time_ranges: list[str] | None) -> list[Time]:
        """Parse time ranges from strings."""
        if time_ranges is None:
            return None
        ranges = []
        for time_val in time_ranges:
            if isinstance(time_val, str):
                ranges.append(Time.from_string(time_val))
        return ranges
