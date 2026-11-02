import azure.functions as func

from api._common import ApiError, handle, json_response, parse_body
from schemas.parameters import ParameterSet
from storage import store

bp = func.Blueprint()
COLLECTION = "parameters"


@bp.route(route="parameters/{valuation_date}", methods=["GET"])
@handle
def get_parameters(req: func.HttpRequest) -> func.HttpResponse:
    valuation_date = req.route_params["valuation_date"]
    doc = store.get_active(COLLECTION, valuation_date)
    if doc is None:
        # No saved parameter set yet -- return schema defaults so the frontend has
        # something sensible to render and edit.
        return json_response(ParameterSet(valuation_date=valuation_date).model_dump(mode="json"))
    return json_response(doc)


@bp.route(route="parameters/{valuation_date}", methods=["PUT"])
@handle
def put_parameters(req: func.HttpRequest) -> func.HttpResponse:
    valuation_date = req.route_params["valuation_date"]
    body = parse_body(req, ParameterSet)
    doc = store.append_version(COLLECTION, valuation_date, body.model_dump(mode="json"))
    doc["id"] = f"{valuation_date}-v{doc['version']}"
    return json_response(doc, 201)


@bp.route(route="parameters/{valuation_date}/versions", methods=["GET"])
@handle
def parameter_versions(req: func.HttpRequest) -> func.HttpResponse:
    valuation_date = req.route_params["valuation_date"]
    return json_response(store.list_versions(COLLECTION, valuation_date))
