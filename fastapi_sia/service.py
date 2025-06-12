"""Service module for Simple Image Access in FastAPI.

Implementors should extend this module to define their own service logic.
"""

import io

from astropy.io.votable import from_table, writeto
from astropy.table import Table as AstroTable
from fastapi.responses import Response
from sqlalchemy import and_, or_, text
from sqlalchemy.orm import Session

from fastapi_sia.models import Circle, MinMaxRange, Polygon, Range, SIASearchParams, Time
from fastapi_sia.obscore.db_models import ObsCore
from fastapi_sia.responses import XMLResponse

VOTABLE_METADATA = {
    "dataproduct_type": {"ucd": "meta.id", "datatype": "char", "utype": "obscore:ObsDataSet.dataProductType"},
    "calib_level": {"ucd": "meta.code;obs.calib", "datatype": "int", "utype": "obscore:ObsDataSet.calibLevel"},
    "obs_collection": {"ucd": "meta.id", "datatype": "char", "utype": "obscore:DataID.Collection"},
    "obs_id": {"ucd": "meta.id", "utype": "obscore:DataID.observationID"},
    "obs_publisher_did": {
        "ucd": "meta.ref.url;meta.curation",
        "datatype": "char",
        "utype": "obscore:Curation.PublisherDID",
    },
    "access_url": {"ucd": "meta.ref.url", "utype": "obscore:Access.Reference"},
    "access_format": {"ucd": "meta.code.mime", "utype": "obscore:Access.Format"},
    "access_estsize": {
        "ucd": "phys.size;meta.file",
        "utype": "obscore:Access.Size",
    },
    "target_name": {"ucd": "meta.id;src", "utype": "obscore:Target.Name"},
    "s_ra": {
        "ucd": "pos.eq.ra",
        "utype": "obscore:Char.SpatialAxis.Coverage.Location.Coord.Position2D.Value2.C1",
        "unit": "deg",
    },
    "s_dec": {
        "ucd": "pos.eq.dec",
        "utype": "obscore:Char.SpatialAxis.Coverage.Location.Coord.Position2D.Value2.C2",
        "unit": "deg",
    },
    "s_region": {
        "ucd": "phys.angArea;obs",
        "utype": "obscore:Char.SpatialAxis.Coverage.Support.Area",
        "unit": "deg",
    },
    "s_resolution": {
        "ucd": "pos.angResolution",
        "utype": "obscore:Char.SpatialAxis.Resolution.refval.value",
        "datatype": "double",
    },
    "t_min": {
        "datatype": "double",
        "ucd": "time.start;obs.exposure",
        "utype": "obscore:Char.TimeAxis.Coverage.Bounds.Limits.StartTime",
        "unit": "s",
    },
    "t_max": {
        "datatype": "double",
        "ucd": "time.end;obs.exposure",
        "utype": "obscore:Char.TimeAxis.Coverage.Bounds.Limits.StopTime",
        "unit": "s",
    },
    "t_exptime": {
        "datatype": "double",
        "ucd": "time.duration;obs.exposure",
        "utype": "obscore:Char.TimeAxis.Coverage.Support.Extent",
        "unit": "s",
    },
    "t_resolution": {
        "datatype": "double",
        "ucd": "time.resolution",
        "utype": "obscore:Char.TimeAxis.Resolution.refval.value",
        "unit": "s",
    },
    "em_min": {
        "datatype": "double",
        "ucd": "em.wl;stat.min",
        "utype": "obscore:Char.SpectralAxis.Coverage.Bounds.Limits.LoLimit",
        "unit": "m",
    },
    "em_max": {
        "datatype": "double",
        "ucd": "em.wl;stat.max",
        "utype": "obscore:Char.SpectralAxis.Coverage.Bounds.Limits.HiLimit",
        "unit": "m",
    },
    "em_res_power": {
        "datatype": "double",
        "ucd": "spect.resolution",
        "utype": "obscore:Char.SpectralAxis.Coverage.Resolution.ResolPower.refval",
    },
    "o_ucd": {
        "ucd": "meta.ucd",
        "utype" : "obscore:Char.ObservableAxis.ucd",
    },
    "pol_states": {
        "ucd": "meta.code;phys.polarization",
        "utype": "obscore:Char.PolarizationAxis.stateList",
    },
    "facility_name": {
        "ucd": "meta.id;instr.tel",
        "utype": "obscore:Provenance.ObsConfig.facility.name"
    },
    "instrument_name": {
        "ucd": "meta.id;instr",
        "utype": "obscore:Provenance.ObsConfig.instrument.name"
    }
}

def generate_votable(rows: list[dict]) -> Response:
    """Generate a basic VOTable for the conesearch results."""

    if not rows:
        return XMLResponse(content="<VOTABLE><INFO>Empty result set</INFO></VOTABLE>")

    # Convert rows to an Astropy Table
    table = AstroTable(rows)
    # Add metadata to the table
    for col_name, metadata in VOTABLE_METADATA.items():
        if col_name in table.columns:
            table[col_name].meta.update(metadata)

    # Convert the Astropy Table to a VOTable
    votable = from_table(table)

    buffer = io.BytesIO()
    writeto(votable, buffer)
    buffer.seek(0)

    return XMLResponse(content=buffer.read())


def perform_sia_query(session: Session, sia_search_params: SIASearchParams):
    """
    Search the database for matching records based on the provided SIA search parameters.
    """
    query = session.query(ObsCore)

    def apply_minmax_filter(field, ranges: list[MinMaxRange]):
        clauses = []
        for r in ranges:
            low = float("-inf") if r.min == "-Inf" else float(r.min)
            high = float("inf") if r.max == "Inf" else float(r.max)
            clauses.append(and_(field >= low, field <= high))
        return or_(*clauses)

    def apply_enum_filter(field, values):
        return or_(*[field == val for val in values])

    def apply_pos_filter(pos_list):
        clauses = []

        for pos in pos_list:
            if isinstance(pos, Circle):
                clauses.append(text(f"q3c_radial_query(s_ra, s_dec, {pos.longitude}, {pos.latitude}, {pos.radius})"))
            elif isinstance(pos, Range):
                # q3c_box_query uses center + width
                center_ra = (pos.lon1 + pos.lon2) / 2
                center_dec = (pos.lat1 + pos.lat2) / 2
                width_ra = abs(pos.lon2 - pos.lon1)
                width_dec = abs(pos.lat2 - pos.lat1)
                clauses.append(
                    text(f"q3c_box_query(s_ra, s_dec, {center_ra}, {center_dec}, {width_ra/2}, {width_dec/2})")
                )
            elif isinstance(pos, Polygon):
                lon_lat_pairs = list(zip(pos.coordinates[::2], pos.coordinates[1::2]))
                poly_str = ", ".join(f"{lon} {lat}" for lon, lat in lon_lat_pairs)
                clauses.append(text(f"q3c_poly_query(s_ra, s_dec, '{poly_str}')"))

        return or_(*clauses)

    def apply_time_filter(times: list[Time]):
        clauses = []
        for t in times:
            if t.end_time is not None:
                clauses.append(and_(ObsCore.t_max >= t.start_time, ObsCore.t_min <= t.end_time))
            else:
                clauses.append(ObsCore.t_max >= t.start_time)
        return or_(*clauses)

    # Apply filters
    if sia_search_params.POS:
        query = query.filter(apply_pos_filter(sia_search_params.POS))
    if sia_search_params.BAND:
        query = query.filter(apply_minmax_filter(ObsCore.em_min, sia_search_params.BAND))
    if sia_search_params.TIME:
        query = query.filter(apply_time_filter(sia_search_params.TIME))
    if sia_search_params.FOV:
        query = query.filter(apply_minmax_filter(ObsCore.s_fov, sia_search_params.FOV))
    if sia_search_params.SPATRES:
        query = query.filter(apply_minmax_filter(ObsCore.s_resolution, sia_search_params.SPATRES))
    if sia_search_params.SPECRP:
        query = query.filter(apply_minmax_filter(ObsCore.em_res_power, sia_search_params.SPECRP))
    if sia_search_params.EXPTIME:
        query = query.filter(apply_minmax_filter(ObsCore.t_exptime, sia_search_params.EXPTIME))
    if sia_search_params.TIMERES:
        query = query.filter(apply_minmax_filter(ObsCore.t_resolution, sia_search_params.TIMERES))
    if sia_search_params.POL:
        query = query.filter(apply_enum_filter(ObsCore.pol_states, sia_search_params.POL))
    if sia_search_params.ID:
        query = query.filter(apply_enum_filter(ObsCore.obs_id, sia_search_params.ID))
    if sia_search_params.COLLECTION:
        query = query.filter(apply_enum_filter(ObsCore.obs_collection, sia_search_params.COLLECTION))
    if sia_search_params.FACILITY:
        query = query.filter(apply_enum_filter(ObsCore.facility_name, sia_search_params.FACILITY))
    if sia_search_params.INSTRUMENT:
        query = query.filter(apply_enum_filter(ObsCore.instrument_name, sia_search_params.INSTRUMENT))
    if sia_search_params.DPTYPE:
        query = query.filter(apply_enum_filter(ObsCore.dataproduct_type, sia_search_params.DPTYPE))
    if sia_search_params.CALIB:
        query = query.filter(apply_enum_filter(ObsCore.calib_level, sia_search_params.CALIB))
    if sia_search_params.TARGET:
        query = query.filter(apply_enum_filter(ObsCore.target_name, sia_search_params.TARGET))
    if sia_search_params.FORMAT:
        query = query.filter(apply_enum_filter(ObsCore.access_format, sia_search_params.FORMAT))
    if sia_search_params.MAXREC:
        query = query.limit(sia_search_params.MAXREC)

    rows = [row.__dict__ for row in query.all()]
    # Remove SQLAlchemy internal state if present
    for row in rows:
        row.pop("_sa_i nstance_state", None)
    votable_response = generate_votable(rows)
    return votable_response
 