from __future__ import annotations

import io
import uuid
from datetime import date
from typing import Any

import pandas as pd

from schemas.assets import AssetPropertiesInput
from schemas.portfolios import Position, PositionCreate, ValidationIssue

RATING_TO_CQS: dict[str, int] = {
    "AAA": 0,
    "AA": 1,
    "A": 2,
    "BBB": 3,
    "BB": 4,
    "B": 5,
    "CCC": 6,
}
RATINGS = list(RATING_TO_CQS)

_COLUMN_ALIASES: dict[str, list[str]] = {
    "name": ["instrument name", "name", "17. instrument name", "internal_class"],
    "market_value": [
        "market value (portfolio ccy)",
        "market value",
        "market_value",
        "24. market valuation in portfolio currency (b)",
    ],
    "nominal": ["nominal amount", "nominal", "nominal_amount", "19. nominal amount"],
    "rating": ["credit quality step / rating", "rating", "112. credit rating"],
    "modelling_class": ["modelling class", "modelling_class"],
    "asset_category": ["underlying asset category", "131. underlying asset category"],
    "maturity_date": ["maturity date", "maturity_date", "39. maturity date"],
    "issuer": ["issuer name", "issuer", "46. issuer name", "counterparty"],
    "country": ["issuer country", "country", "52. issuer country", "country_of_issuer"],
    "currency": [
        "quotation currency",
        "currency",
        "21. quotation currency (a)",
        "portfolio_currency",
        "quotation_currency",
    ],
    "cic": ["cic code", "cic", "12. cic code of the instrument"],
}

_MODELLING_CLASS_BY_ASSET_CATEGORY: dict[str, str] = {
    "government bonds": "gvt_bond_fixed_coupon",
    "corporate bonds": "corp_bond_fixed_coupon",
    "inflation derivatives": "ils_fixed",
    "interest rate derivatives": "irs_fixed",
    "fx derivatives": "fx_forward",
    "private equity / alternatives": "equity",
    "cash and deposits": "cash",
}

_MODELLING_CLASS_BY_CIC_PREFIX: dict[str, str] = {
    "11": "gvt_bond_fixed_coupon",
    "22": "corp_bond_fixed_coupon",
    "7D": "irs_fixed",
    "35": "equity",
    "81": "cash",
}


def cic_for_modelling_class(modelling_class: str) -> str:

    if modelling_class.startswith("gvt"):
        return "11XX"
    if modelling_class.startswith("corp"):
        return "22XX"
    if modelling_class in ("irs_fixed", "irs_floating"):
        return "7DXX"
    if modelling_class == "equity":
        return "35XX"
    if modelling_class == "cash":
        return "81XX"
    return "00XX"


def _modelling_class_from_asset_category(asset_category: str) -> str | None:
    return _MODELLING_CLASS_BY_ASSET_CATEGORY.get(asset_category.strip().lower())


def _modelling_class_from_cic(cic: str) -> str | None:
    return _MODELLING_CLASS_BY_CIC_PREFIX.get(cic[:2].upper())


def new_position_id() -> str:
    return f"POS-{uuid.uuid4().hex[:8].upper()}"


def position_from_create(portfolio_id: str, payload: PositionCreate) -> Position:
    cqs = RATING_TO_CQS.get((payload.rating or "").upper())
    return Position(
        id=new_position_id(),
        portfolio_id=portfolio_id,
        name=payload.name,
        modelling_class=payload.modelling_class,
        cic=cic_for_modelling_class(payload.modelling_class),
        currency=payload.currency,
        nominal=payload.nominal,
        market_value=payload.market_value,
        rating=payload.rating,
        cqs=cqs,
        maturity_date=payload.maturity_date,
        issuer="Manual entry",
        country="NL",
        included=True,
        status="ok",
        asset_detail=payload.asset_detail,
    )


def _find_column(columns: list[str], field: str) -> str | None:
    aliases = _COLUMN_ALIASES.get(field, [])
    lowered = {c.lower().strip(): c for c in columns}
    for alias in aliases:
        if alias in lowered:
            return lowered[alias]
    return None


_ASSET_DETAIL_STRING_FIELDS = (
    "storage_class",
    "internal_class",
    "fixed_or_floating",
    "counterparty",
    "management_style",
    "inflation_index",
)
_ASSET_DETAIL_DATE_FIELDS = ("issue_date", "first_call_date", "next_coupon_date")
_ASSET_DETAIL_INT_FIELDS = (
    "coupon_frequency",
    "swap_term",
    "inflation_index_lag",
    "equity_type",
)
_ASSET_DETAIL_FLOAT_FIELDS = (
    "modified_duration",
    "annual_fixed_coupon_rate",
    "annual_nominal_coupon_rate",
    "annual_floating_coupon_rate",
    "annual_coupon_spread",
    "annual_fixed_interest_rate",
    "annual_floating_interest_rate",
    "annual_interest_rate",
    "inflation_index_start",
    "current_indexation_coefficient",
    "nominal_quotation_currency",
    "nominal_portfolio_currency",
)


def _has_asset_detail_columns(columns: list[str]) -> bool:
    lowered = {c.lower().strip() for c in columns}
    all_detail_fields = (
        _ASSET_DETAIL_STRING_FIELDS
        + _ASSET_DETAIL_DATE_FIELDS
        + _ASSET_DETAIL_INT_FIELDS
        + _ASSET_DETAIL_FLOAT_FIELDS
    )
    return any(name in lowered for name in all_detail_fields)


def _asset_detail_from_row(
    columns: list[str],
    row: pd.Series,
    *,
    has_detail_columns: bool,
    position_id: str,
    portfolio_id: str,
    modelling_class: str,
    market_value: float,
    nominal: float | None,
    rating: str | None,
    country: str | None,
    currency: str,
    maturity_date: date | None,
) -> AssetPropertiesInput | None:
    if not has_detail_columns:
        return None

    lowered = {c.lower().strip(): c for c in columns}

    fields: dict[str, Any] = {}
    for name in _ASSET_DETAIL_STRING_FIELDS:
        source = lowered.get(name)
        if source and pd.notna(row.get(source)):
            fields[name] = str(row[source])
    for name in _ASSET_DETAIL_DATE_FIELDS:
        source = lowered.get(name)
        if source and pd.notna(row.get(source)):
            try:
                fields[name] = pd.to_datetime(row[source]).date()
            except (
                Exception
            ):  # noqa: BLE001 -- unparseable date, leave this one field unset
                pass
    for name in _ASSET_DETAIL_INT_FIELDS:
        source = lowered.get(name)
        if source and pd.notna(row.get(source)):
            try:
                fields[name] = int(row[source])
            except (TypeError, ValueError):
                pass
    for name in _ASSET_DETAIL_FLOAT_FIELDS:
        source = lowered.get(name)
        if source and pd.notna(row.get(source)):
            try:
                fields[name] = float(row[source])
            except (TypeError, ValueError):
                pass

    exchange_rate = 1.0
    exchange_rate_col = lowered.get("exchange_rate")
    if exchange_rate_col and pd.notna(row.get(exchange_rate_col)):
        try:
            exchange_rate = float(row[exchange_rate_col])
        except (TypeError, ValueError):
            pass

    try:
        return AssetPropertiesInput(
            position_id=position_id,
            portfolio=portfolio_id,
            asset_id=position_id,
            modelling_class=modelling_class,
            market_value=market_value,
            nominal=nominal,
            rating=rating,
            country_of_issuer=country,
            quotation_currency=currency,
            exchange_rate=exchange_rate,
            maturity_date=maturity_date,
            **fields,
        )
    except Exception:
        return None


def _read_rows(data: bytes, filename: str) -> pd.DataFrame:
    if filename.lower().endswith(".csv"):
        return pd.read_csv(io.BytesIO(data))
    return pd.read_excel(io.BytesIO(data))


_REQUIRED_COLUMNS = ("name", "market_value")


def parse_positions_file(
    data: bytes, filename: str, portfolio_id: str
) -> tuple[list[Position], list[ValidationIssue]]:

    issues: list[ValidationIssue] = []

    try:
        df = _read_rows(data, filename)
    except Exception:
        issues.append(
            ValidationIssue(
                severity="error",
                position="(file)",
                field="file",
                message=f"Could not read '{filename}' as an Excel (.xlsx) or CSV file.",
            )
        )
        return [], issues

    if df.empty:
        issues.append(
            ValidationIssue(
                severity="error",
                position="(file)",
                field="file",
                message="The uploaded file has no rows.",
            )
        )
        return [], issues

    columns = list(df.columns.astype(str))
    col = {field: _find_column(columns, field) for field in _COLUMN_ALIASES}
    has_detail_columns = _has_asset_detail_columns(columns)

    for required in _REQUIRED_COLUMNS:
        if not col[required]:
            issues.append(
                ValidationIssue(
                    severity="error",
                    position="(file)",
                    field=required,
                    message=f"Required column '{required}' was not found. Download the sample portfolio to see the expected column names.",
                )
            )
    if any(i.severity == "error" for i in issues):
        return [], issues

    positions: list[Position] = []
    rows = df.reset_index(drop=True)
    for i, row in rows.iterrows():
        position_label = f"Row {i + 2}"  # +1 for the header row, +1 for 1-indexing
        row_has_error = False

        if col["name"] and pd.notna(row.get(col["name"])):
            name = str(row[col["name"]])
        else:
            name = f"Imported position {i + 1}"
            issues.append(
                ValidationIssue(
                    severity="warning",
                    position=position_label,
                    field="name",
                    message=f"Name missing — defaulted to '{name}'.",
                )
            )

        try:
            market_value = (
                float(row[col["market_value"]])
                if col["market_value"] and pd.notna(row.get(col["market_value"]))
                else None
            )
        except (TypeError, ValueError):
            market_value = None
        if market_value is None:
            issues.append(
                ValidationIssue(
                    severity="error",
                    position=position_label,
                    field="market_value",
                    message="Market value is missing or not numeric — row skipped.",
                )
            )
            row_has_error = True

        # Notched ratings (e.g. "AA-", "BBB+") map to their base letter grade's CQS --
        # `rstrip` keeps the full notched rating for display while only the base grade
        # needs to exist in RATING_TO_CQS. Genuinely unrated/unrecognised values (e.g.
        # "NR") fall back to a rotating placeholder, same as a missing cell.
        raw_rating = (
            str(row[col["rating"]]).strip().upper()
            if col["rating"] and pd.notna(row.get(col["rating"]))
            else None
        )
        base_rating = raw_rating.rstrip("+-") if raw_rating else None
        if base_rating in RATING_TO_CQS:
            rating = raw_rating
        else:
            rating = RATINGS[i % len(RATINGS)]
            base_rating = rating
            if raw_rating:
                issues.append(
                    ValidationIssue(
                        severity="warning",
                        position=position_label,
                        field="rating",
                        message=f"Rating '{raw_rating}' not recognised — defaulted to {rating}.",
                    )
                )
            elif col["rating"]:
                issues.append(
                    ValidationIssue(
                        severity="warning",
                        position=position_label,
                        field="rating",
                        message=f"Rating missing — defaulted to {rating}.",
                    )
                )

        nominal = market_value if market_value is not None else 0.0
        if col["nominal"] and pd.notna(row.get(col["nominal"])):
            try:
                nominal = float(row[col["nominal"]])
            except (TypeError, ValueError):
                issues.append(
                    ValidationIssue(
                        severity="warning",
                        position=position_label,
                        field="nominal",
                        message="Nominal is not numeric — defaulted to market value.",
                    )
                )

        cic = (
            str(row[col["cic"]])
            if col["cic"] and pd.notna(row.get(col["cic"]))
            else None
        )

        modelling_class = None
        if col["modelling_class"] and pd.notna(row.get(col["modelling_class"])):
            modelling_class = str(row[col["modelling_class"]])
        elif col["asset_category"] and pd.notna(row.get(col["asset_category"])):
            modelling_class = _modelling_class_from_asset_category(
                str(row[col["asset_category"]])
            )
        elif cic:
            modelling_class = _modelling_class_from_cic(cic)
        if not modelling_class:
            modelling_class = "corp_bond_fixed_coupon"
            issues.append(
                ValidationIssue(
                    severity="warning",
                    position=position_label,
                    field="modelling_class",
                    message="Modelling class could not be determined — defaulted to Corporate bond (fixed coupon).",
                )
            )

        cic = cic or cic_for_modelling_class(modelling_class)

        maturity_date: date | None = None
        if col["maturity_date"] and pd.notna(row.get(col["maturity_date"])):
            try:
                maturity_date = pd.to_datetime(row[col["maturity_date"]]).date()
            except Exception:
                issues.append(
                    ValidationIssue(
                        severity="warning",
                        position=position_label,
                        field="maturity_date",
                        message="Maturity date could not be parsed — left blank.",
                    )
                )
        issuer = (
            str(row[col["issuer"]])
            if col["issuer"] and pd.notna(row.get(col["issuer"]))
            else "Imported"
        )
        country = (
            str(row[col["country"]])
            if col["country"] and pd.notna(row.get(col["country"]))
            else "NL"
        )
        currency = (
            str(row[col["currency"]])
            if col["currency"] and pd.notna(row.get(col["currency"]))
            else "EUR"
        )

        if row_has_error:
            continue

        position_id = new_position_id()
        asset_detail = _asset_detail_from_row(
            columns,
            row,
            has_detail_columns=has_detail_columns,
            position_id=position_id,
            portfolio_id=portfolio_id,
            modelling_class=modelling_class,
            market_value=market_value,
            nominal=nominal,
            rating=rating,
            country=country,
            currency=currency,
            maturity_date=maturity_date,
        )

        positions.append(
            Position(
                id=position_id,
                portfolio_id=portfolio_id,
                name=name,
                modelling_class=modelling_class,
                cic=cic,
                currency=currency,
                nominal=nominal,
                market_value=market_value,
                rating=rating,
                cqs=RATING_TO_CQS.get(base_rating),
                maturity_date=maturity_date,
                issuer=issuer,
                country=country,
                included=True,
                status="ok",
                asset_detail=asset_detail,
            )
        )

    if any(i.severity == "error" for i in issues):
        return [], issues
    return positions, issues


def totals(positions: list[dict[str, Any]]) -> tuple[int, float]:
    return len(positions), sum(p.get("market_value") or 0 for p in positions)
