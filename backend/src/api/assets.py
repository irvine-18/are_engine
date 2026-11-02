import azure.functions as func

from api._common import handle, json_response, parse_body
from api.curves import load_asset_rates_table, load_equity_symmetric_adjustment
from config import get_model_settings
from schemas.assets import SingleAssetRequest
from schemas.parameters import ParameterSet
from storage import store
import services.asset_service as asset_service

bp = func.Blueprint()


@bp.route(route="assets/samples", methods=["GET"])
@handle
def list_sample_assets(req: func.HttpRequest) -> func.HttpResponse:
    items = store.query_items("sampleAssets")
    return json_response(sorted(items, key=lambda i: i.get("modelling_class", "")))


@bp.route(route="assets/calculate", methods=["POST"])
@handle
def calculate_asset(req: func.HttpRequest) -> func.HttpResponse:
    body = parse_body(req, SingleAssetRequest)
    df_rates = load_asset_rates_table(body.curve_run_id)
    settings = get_model_settings()

    active_parameters = store.get_active("parameters", body.valuation_date.isoformat())
    parameters = (
        ParameterSet.model_validate(active_parameters)
        if active_parameters
        else ParameterSet(valuation_date=body.valuation_date)
    )
    equity_symmetric_adjustment = load_equity_symmetric_adjustment(body.curve_run_id)

    result = asset_service.calculate_single_asset(
        valuation_date=body.valuation_date,
        asset=body.asset,
        df_rates=df_rates,
        df_modelling_properties=settings.parameters["modelling_properties"],
        df_cqs_rating_mapping=asset_service.build_cqs_mapping_df(
            parameters, settings.parameters["cqs_rating_mapping"]
        ),
        df_spread_risk_coefficients=asset_service.build_spread_coefficients_df(
            parameters, settings.parameters["spread_risk_coefficients"]
        ),
        df_eiopa_equity_adjustment=asset_service.build_equity_adjustment_df(
            parameters, equity_symmetric_adjustment
        ),
        scenarios=body.scenarios,
    )
    return json_response(result)
