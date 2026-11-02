from typing import Literal

from pydantic import BaseModel

CurveSet = Literal["EIOPA_no_VA", "EIOPA_incl_VA", "Inflation", "Cost Inflation"]


class Scenario(BaseModel):

    id: str  # matches `scenario_id`, e.g. "EIOPA_incl_VA (IR50_Up)"
    curve_set: CurveSet
    name: str  # matches `scenario`, e.g. "IR50_Up"
    shock_bp: float = 0
    is_builtin: bool = False
    active: bool = True
    description: str | None = None
