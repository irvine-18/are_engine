import json
import logging
from typing import TypeVar

import azure.functions as func
from pydantic import BaseModel, ValidationError

T = TypeVar("T", bound=BaseModel)
logger = logging.getLogger(__name__)


class ApiError(Exception):
    def __init__(
        self, status_code: int, code: str, message: str, details: dict | None = None
    ):
        self.status_code = status_code
        self.code = code
        self.message = message
        self.details = details
        super().__init__(message)


def parse_body(req: func.HttpRequest, model: type[T]) -> T:
    try:
        payload = req.get_json()
    except ValueError as exc:
        raise ApiError(400, "invalid_json", "Request body is not valid JSON") from exc
    try:
        return model.model_validate(payload)
    except ValidationError as exc:
        raise ApiError(
            422,
            "validation_error",
            "Request body failed validation",
            {"errors": exc.errors()},
        ) from exc


def json_response(
    payload: BaseModel | dict | list, status_code: int = 200
) -> func.HttpResponse:
    if isinstance(payload, BaseModel):
        body = payload.model_dump_json()
    else:
        body = json.dumps(payload, default=str)
    return func.HttpResponse(body, status_code=status_code, mimetype="application/json")


def error_response(error: ApiError) -> func.HttpResponse:
    body = {
        "error": {
            "code": error.code,
            "message": error.message,
            "details": error.details,
        }
    }
    return func.HttpResponse(
        json.dumps(body), status_code=error.status_code, mimetype="application/json"
    )


def handle(fn):
    """Decorator: run a blueprint handler, turning `ApiError`/validation failures into
    the standard `{error:{code,message,details}}` shape instead of a 500."""

    def wrapped(req: func.HttpRequest) -> func.HttpResponse:
        try:
            return fn(req)
        except ApiError as exc:
            return error_response(exc)
        except (
            Exception
        ) as exc:  
            logger.exception("Unhandled exception in %s", fn.__name__)
            return error_response(ApiError(500, "internal_error", str(exc)))

    wrapped.__name__ = fn.__name__
    return wrapped
