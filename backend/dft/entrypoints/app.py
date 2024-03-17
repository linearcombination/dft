"""This module provides the FastAPI API definition."""

import os
import pathlib
from typing import Any, Iterable, Sequence

import celery.states
from celery.result import AsyncResult
from document.config import settings
from fastapi import FastAPI, HTTPException, Query, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pydantic import AnyHttpUrl

from dft.domain import dft_checker, model

app = FastAPI()


logger = settings.logger(__name__)

# CORS configuration to allow frontend to talk to backend
origins = settings.BACKEND_CORS_ORIGINS

logger.debug("CORS origins: %s", origins)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


@app.get("/language_codes_and_names")
async def lang_codes_and_names() -> Sequence[tuple[str, str, bool]]:
    """
    Return list of all available language code, name tuples.
    """
    return await dft_checker.lang_codes_and_names()  # When using data API


@app.post("/documents")
async def generate_document(
    document_request: model.DocumentRequest,
) -> JSONResponse:
    """
    Return file paths to PDF and Docx for God the Father terms table
    and Son of God terms table.
    """
    try:
        task = dft_checker.generate_document.apply_async(
            args=(document_request.json(),)
        )
    except HTTPException as exc:
        raise exc
    except Exception as exc:  # catch any exceptions we weren't expecting, handlers handle the ones we do expect.
        logger.exception(
            "There was an error while attempting to fulfill the document "
            "request. Likely reason is the following exception:"
        )
        # Handle exceptions that aren't handled otherwise
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)
        )
    else:
        logger.debug("task_id: %s", task.id)
        return JSONResponse({"task_id": task.id})


@app.post("/documents_docx")
async def generate_docx_document(
    document_request: model.DocumentRequest,
) -> JSONResponse:
    """
    Return file paths to PDF and Docx for God the Father terms table
    and Son of God terms table.
    """
    try:
        task = dft_checker.generate_docx_document.apply_async(
            args=(document_request.json(),)
        )
    except HTTPException as exc:
        raise exc
    except Exception as exc:  # catch any exceptions we weren't expecting, handlers handle the ones we do expect.
        logger.exception(
            "There was an error while attempting to fulfill the document "
            "request. Likely reason is the following exception:"
        )
        # Handle exceptions that aren't handled otherwise
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)
        )
    else:
        logger.debug("task_id: %s", task.id)
        return JSONResponse({"task_id": task.id})


@app.get("/task_status/{task_id}")
async def task_status(task_id: str) -> JSONResponse:
    res: AsyncResult[dict[str, str]] = AsyncResult(task_id)
    if res.state == celery.states.SUCCESS:
        return JSONResponse({"state": celery.states.SUCCESS, "result": res.result})
    return JSONResponse(
        {
            "state": res.state,
        }
    )


@app.get("/health/status")
async def health_status() -> tuple[dict[str, str], int]:
    """Ping-able server endpoint."""
    return {"status": "ok"}, 200


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    exc_str = f"{exc}".replace("\n", " ").replace("   ", " ")
    logger.error(f"{request}: {exc_str}")
    content = {"status_code": 10422, "message": exc_str, "data": None}
    return JSONResponse(
        content=content, status_code=status.HTTP_422_UNPROCESSABLE_ENTITY
    )


# @app.exception_handler(exceptions.InvalidDocumentRequestException)
# def invalid_document_request_exception_handler(
#     request: Request, exc: exceptions.InvalidDocumentRequestException
# ) -> JSONResponse:
#     logger.error(f"{request}: {exc}")
#     return JSONResponse(
#         status_code=status.HTTP_400_BAD_REQUEST,
#         content={
#             "message": f"{exc.message}",
#         },
#     )


# @app.post("/documents")
# async def generate_document(
#     document_request: model.DocumentRequest,
#     success_message: str = settings.SUCCESS_MESSAGE,
# ) -> JSONResponse:
#     """
#     Get the document request and hand it off to the document_generator
#     module for processing.
#     """
#     # Top level exception handler
#     try:
#         task = document_generator.generate_document.apply_async(
#             args=(document_request.json(),)
#         )
#     except HTTPException as exc:
#         raise exc
#     except Exception as exc:  # catch any exceptions we weren't expecting, handlers handle the ones we do expect.
#         logger.exception(
#             "There was an error while attempting to fulfill the document "
#             "request. Likely reason is the following exception:"
#         )
#         # Handle exceptions that aren't handled otherwise
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)
#         )
#     else:
#         logger.debug("task_id: %s", task.id)
#         return JSONResponse({"task_id": task.id})


# @app.post("/documents_docx")
# async def generate_docx_document(
#     document_request: model.DocumentRequest,
#     success_message: str = settings.SUCCESS_MESSAGE,
# ) -> JSONResponse:
#     """
#     Get the document request and hand it off to the document_generator
#     module for processing.
#     """
#     # Top level exception handler
#     try:
#         task = document_generator.generate_docx_document.apply_async(
#             args=(document_request.json(),)
#         )
#     except HTTPException as exc:
#         raise exc
#     except Exception as exc:  # catch any exceptions we weren't expecting, handlers handle the ones we do expect.
#         logger.exception(
#             "There was an error while attempting to fulfill the document "
#             "request. Likely reason is the following exception:"
#         )
#         # Handle exceptions that aren't handled otherwise
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)
#         )
#     else:
#         logger.debug("task_id: %s", task.id)
#         return JSONResponse({"task_id": task.id})
