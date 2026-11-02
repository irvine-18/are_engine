import azure.functions as func

from api._common import handle, json_response
from storage import store

bp = func.Blueprint()
COLLECTION = "scenarios"


@bp.route(route="scenarios", methods=["GET"])
@handle
def list_scenarios(req: func.HttpRequest) -> func.HttpResponse:
    curve_set = req.params.get("curve_set")
    items = store.query_items(COLLECTION)
    if curve_set:
        items = [i for i in items if i.get("curve_set") == curve_set]
    return json_response(sorted(items, key=lambda i: (not i.get("is_builtin"), i.get("name", ""))))
