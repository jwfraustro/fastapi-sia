"""Main router for the Cone Search API."""

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException

from fastapi_sia.exceptions import general_exception_handler, http_exception_handler, validation_exception_handler
from fastapi_sia.middleware import UppercaseQueryParamsMiddleware
from fastapi_sia.router.sia_router import sia_router

app = FastAPI(
    title="Simple Image Access v2 API",
    description="An example API implementation of the IVOA Simple Image Access Version 2 standard.",
    version="1.0.0",
)

# Middleware to convert all query parameter names to uppercase
app.add_middleware(UppercaseQueryParamsMiddleware)

# Exception handlers
app.add_exception_handler(Exception, general_exception_handler)
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)

# Include the Cone Search router
app.include_router(sia_router)
