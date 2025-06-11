"""Utilities for ObsCore."""


from fastapi_sia.obscore.types import DataProductType
from fastapi_sia.obscore.db_models import ObsCore
from fastapi_sia.models import PolarizationLabels
import random, uuid
from fastapi_sia.dependencies import engine as db_engine
from sqlalchemy.orm import Session

FAKE_COLLECTIONS = [
    "SurveyA",
    "SurveyB",
    "DeepSky",
    "GalacticCenter",
    "ExoplanetSurvey",
    "CosmicMicrowaveBackground",
    "QuickLook",
    "TransientEvents",
    "HighEnergyAstrophysics",
]

FAKE_FORMATS = [
    "image/fits",
    "image/jpeg",
    "application/fits",
    "application/x+votable+xml",
    "text/csv",
    "image/x-fits-gzip",
]

FAKE_FACILITIES = [
    "HST",
    "JWST",
    "Chandra",
    "Spitzer",
    "VLA",
    "ALMA",
    "Fermi",
    "LSST",
    "Euclid",
    "SKA",
]

FAKE_INSTRUMENTS = [
    "WFC3",
    "MIRI",
    "ACIS",
    "IRAC",
    "ACS",
    "SPITZER-IRAC",
    "VLA-CASA",
    "ALMA-ACA",
    "Fermi-LAT",
    "LSST-Camera",
]

def generate_fake_obscore_data():
    """Generate a fake ObsCore data entry."""

    dataproduct_type = random.choice(list(DataProductType))
    calib_level = random.choice([1, 2, 3])

    facility = random.choice(FAKE_FACILITIES)
    instrument = random.choice(FAKE_INSTRUMENTS)
    obs_collection = f"{facility}/{instrument}"

    obs_id = uuid.uuid4()
    obs_publisher_did = f"ivo://{facility.lower()}/{obs_id}"

    access_url = f"https://data.{facility.lower()}.org/{obs_id}"
    access_format = random.choice(FAKE_FORMATS)
    access_estsize = random.randint(1000, 100000)  # in kbytes

    target_name = f"Target-{random.randint(1, 1000)}"

    s_ra = random.uniform(0, 360)  # Right Ascension in degrees
    s_dec = random.uniform(-90, 90)  # Declination in degrees
    s_fov = round(random.uniform(0.1, 5.0), 3)  # Field of View in degrees
    s_region = f"CIRCLE {s_ra} {s_dec} {s_fov / 2}"  # STC-S string format

    s_resolution = round(random.uniform(0.1, 10.0), 3)  # Resolution in arcseconds
    s_xel1 = 1
    s_xel2 = 1

    t_min = random.uniform(50000, 60000)  # Start time in MJD
    t_max = t_min + random.uniform(0, 100)  # End time in MJD
    t_exptime = round(random.uniform(1, 3600), 2)  # Exposure time in seconds
    t_resolution = round(random.uniform(0.1, 10.0), 2)  # Time resolution in seconds
    t_xel = 1

    em_min = round(random.uniform(0.1, 500.0), 3)  # Wavelength minimum in meters
    em_max = em_min + round(random.uniform(0.1, 100.0), 3)  # Wavelength maximum in meters
    em_res_power = random.randint(1, 1000)  # Spectral resolving power
    em_xel = 1
    o_ucd = "phot.mag;em.opt"

    pol_states = random.sample(
        list(PolarizationLabels),
        k=random.randint(1, min(5, len(PolarizationLabels)))
    )
    pol_states = f"/{'/'.join(pol_states)}/" if pol_states else None
    pol_xel = len(pol_states)

    return ObsCore(
        dataproduct_type=dataproduct_type,
        calib_level=calib_level,
        obs_collection=obs_collection,
        obs_id=str(obs_id),
        obs_publisher_did=obs_publisher_did,
        access_url=access_url,
        access_format=access_format,
        access_estsize=access_estsize,
        target_name=target_name,
        s_ra=s_ra,
        s_dec=s_dec,
        s_fov=s_fov,
        s_region=s_region,
        s_resolution=s_resolution,
        s_xel1=s_xel1,
        s_xel2=s_xel2,
        t_min=t_min,
        t_max=t_max,
        t_exptime=t_exptime,
        t_resolution=t_resolution,
        t_xel=t_xel,
        em_min=em_min,
        em_max=em_max,
        em_res_power=em_res_power,
        em_xel=em_xel,
        o_ucd=o_ucd,
        pol_states=pol_states,
        pol_xel=pol_xel,
        facility_name=facility,
        instrument_name=instrument
    )

if __name__ == "__main__":
    random.seed(42)  # For reproducibility
    with Session(db_engine) as session:
        for _ in range(100):
            fake_record = generate_fake_obscore_data()
            session.add(fake_record)
        session.commit()
    print("Inserted 100 fake ObsCore records.")