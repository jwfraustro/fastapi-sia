"""Main API router for the SIA service."""
from typing import Annotated

from fastapi import APIRouter, Query, Depends
from fastapi_restful.cbv import cbv

from fastapi_sia.models import DataProductType, SIASearchParams
from fastapi_sia.service import perform_sia_query
from fastapi_sia.dependencies import get_session

sia_router = APIRouter(tags=["SIA"])


@cbv(sia_router)
class SIARouter:
    """Router for SIA API endpoints."""

    @sia_router.get(
        "/sia",
        summary="Perform an SIA query",
        description="Perform an SIA query with specified parameters.",
    )
    def sia_request(
        self,
        POS: Annotated[
            list[str],
            Query(
                description="Position of the search area in the format of a DALI POS string.",
                example=["CIRCLE 10.684 -74.044 0.1"],
            ),
        ] = None,
        BAND: Annotated[
            list[str], Query(description="Wavelength band for the search, in meters.", example=["0.5 2.0"])
        ] = None,
        TIME: Annotated[
            list[str],
            Query(description="Time range for the search, in Modified Julian Date (MJD).", example=["59000 59010"]),
        ] = None,
        POL: Annotated[list[str], Query(description="Polarization labels for the search.", example=["LR"])] = None,
        FOV: Annotated[
            list[str], Query(description="Field of view for the search, in degrees.", example=["0.5 1.0"])
        ] = None,
        SPATRES: Annotated[
            list[str], Query(description="Spatial resolution for the search, in arcseconds.", example=["1.0 2.0"])
        ] = None,
        SPECRP: Annotated[
            list[str], Query(description="Spectral resolving power for the search.", example=["10 20"])
        ] = None,
        EXPTIME: Annotated[
            list[str], Query(description="Exposure time for the search, in seconds.", example=["30 60"])
        ] = None,
        TIMERES: Annotated[
            list[str], Query(description="Time resolution for the search, in seconds.", example=["1.0 2.0"])
        ] = None,
        ID: Annotated[
            list[str],
            Query(description="Identifier of the dataset(s)."),
        ] = None,
        COLLECTION: Annotated[
            list[str],
            Query(description="Name of the data collection."),
        ] = None,
        FACILITY: Annotated[
            list[str],
            Query(description="Name of the facility that collected the data."),
        ] = None,
        INSTRUMENT: Annotated[
            list[str],
            Query(description="Name of the instrument used for data collection."),
        ] = None,
        DPTYPE: Annotated[
            list[DataProductType],
            Query(description="Type of data product, e.g., 'image' or 'cube'.", example=["image"]),
        ] = None,
        CALIB: Annotated[
            list[int], Query(description="Calibration level of the data product, e.g., 1, 2, or 3.", example=[1, 2, 3])
        ] = None,
        TARGET: Annotated[list[str], Query(description="Target name for the search.", example=["M31"])] = None,
        FORMAT: Annotated[
            list[str],
            Query(
                description="Format of the data to be returned",
                example=["appplication/x-votable+xml"],
            ),
        ] = None,
        MAXREC: Annotated[int, Query(description="Maximum number of records to return.", ge=0)] = 100,
        session = Depends(get_session)
    ) -> dict:
        """
        Perform a Cone Search.

        Args:
            query_params (SIAQueryParams): Query parameters for the SIA request.

        Returns:
            JSON response with search results.
        """

        query_params = SIASearchParams(
            POS=POS,
            BAND=BAND,
            TIME=TIME,
            POL=POL,
            FOV=FOV,
            SPATRES=SPATRES,
            SPECRP=SPECRP,
            EXPTIME=EXPTIME,
            TIMERES=TIMERES,
            ID=ID,
            COLLECTION=COLLECTION,
            FACILITY=FACILITY,
            INSTRUMENT=INSTRUMENT,
            DPTYPE=DPTYPE,
            CALIB=CALIB,
            TARGET=TARGET,
            FORMAT=FORMAT,
            MAXREC=MAXREC,
        )

        # Placeholder for actual search logic
        return perform_sia_query(session, query_params)