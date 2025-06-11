"""This module contains the database SQLAlchemy models for the mock ObsCore table in the database."""

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, BigInteger, Double
from sqlalchemy.orm import DeclarativeBase, relationship

from fastapi_sia.dependencies import engine as db_engine
from fastapi_sia.obscore.types import DataProductType
from sqlalchemy import Enum


class Base(DeclarativeBase):
    """The base class for all models."""

    __abstract__ = True

    def to_dict(self, as_str=True) -> dict:
        """Convert the model to a dictionary."""
        inner_func = str if as_str else lambda x: x
        return {
            column.name: inner_func(getattr(self, column.name)) for column in self.__table__.columns
        }

class ObsCore(Base):
    """The ObsCore SQLAlchemy model.

    See: https://www.ivoa.net/documents/ObsCore/20170509/REC-ObsCore-v1.1-20170509.pdf for details.
    """

    __tablename__ = "ObsCore"

    id = Column(Integer, primary_key=True, autoincrement=True)

    dataproduct_type = Column("value", Enum(DataProductType)) # Type of data product, e.g., 'image', 'cube', etc.
    calib_level = Column(Integer, nullable=False) # Calibration level of the data product, e.g., 1, 2, or 3.

    obs_collection = Column(String, nullable=False) # Name of the data collection
    obs_id = Column(String, nullable=False) # Unique identifier for the observation
    obs_publisher_did = Column(String, nullable=False) # IVOA dataset identifier

    access_url = Column(String) # URL to access the data product
    access_format = Column(String) # Format of the data product, e.g., 'image/fits', 'cube/fits', etc.
    access_estsize = Column(BigInteger) # in kbytes

    target_name = Column(String)

    s_ra = Column(Double) # Right Ascension in degrees
    s_dec = Column(Double) # Declination in degrees
    s_fov = Column(Double) # Field of View in degrees
    s_region = Column(String) # Spatial region in STC-S string format
    s_resolution = Column(Double) # Resolution in arcseconds
    s_xel1 = Column(BigInteger) # Number of Elements in the spatial dimension 1
    s_xel2 = Column(BigInteger) # Number of Elements in the spatial dimension 2

    t_min = Column(Double) # Start time in MJD
    t_max = Column(Double) # End time in MJD
    t_exptime = Column(Double) # Exposure time in seconds
    t_resolution = Column(Double) # Time resolution in seconds
    t_xel = Column(BigInteger) # Number of Elements in the time dimension

    em_min = Column(Double) # Wavelength minimum in meters
    em_max = Column(Double) # Wavelength maximum in meters
    em_res_power = Column(Double) # Spectral resolving power
    em_xel = Column(BigInteger) # Number of Elements in the spectral dimension

    o_ucd = Column(String) # UCD for the observation

    pol_states = Column(String) # Polarization states, e.g., "LR", "RR", "LL", etc.
    pol_xel = Column(BigInteger) # Number of Elements in the polarization dimension

    facility_name = Column(String)
    instrument_name = Column(String)

Base.metadata.create_all(db_engine)