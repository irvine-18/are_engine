import type { Position, PositionResult } from "@/lib/api/types";

/** `PositionResult` (from `GET /runs/{id}/positions`) only carries what
 * `services/run_service.py`'s placeholder pricing produces -- market value and an
 * SCR breakdown, nothing from the position's own stored metadata. Joining against
 * `GET /portfolios/{id}/positions` (real Cosmos data) on `position_id`/`id` is how
 * every other tab (grouping, maturity buckets, the Positions grid) gets rating/CQS/
 * country/issuer/maturity without `run_service.py` needing to duplicate that data
 * into every run's result set. */
export interface EnrichedPositionResult {
  id: string;
  name: string;
  modellingClass: string;
  marketValue: number;
  scrInterestUp: number;
  scrInterestDown: number;
  scrSpread: number;
  scrEquity: number;
  scrTotal: number;
  currency: string;
  rating: string | null;
  cqs: number | null;
  country: string | null;
  issuer: string | null;
  maturityDate: string | null;
}

export function joinPositionResults(results: PositionResult[], positions: Position[]): EnrichedPositionResult[] {
  const byId = new Map(positions.map((p) => [p.id, p]));
  return results.map((r) => {
    const p = byId.get(r.position_id);
    return {
      id: r.position_id,
      name: r.name,
      modellingClass: r.modelling_class,
      marketValue: r.market_value,
      scrInterestUp: r.scr_interest_up,
      scrInterestDown: r.scr_interest_down,
      scrSpread: r.scr_spread,
      scrEquity: r.scr_equity,
      scrTotal: r.scr_total,
      currency: p?.currency ?? "EUR",
      rating: p?.rating ?? null,
      cqs: p?.cqs ?? null,
      country: p?.country ?? null,
      issuer: p?.issuer ?? null,
      maturityDate: p?.maturity_date ?? null,
    };
  });
}
