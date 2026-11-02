import type { EconomicDataTemplate } from "@/lib/economicTemplates";
import type { ScenarioCurve } from "@/lib/api/types";

const REGULATORY_SCENARIO_IDS = ["base", "scr-ir-up", "scr-ir-down"];

export function selectBaseScenario(scenarios: ScenarioCurve[] | undefined): ScenarioCurve | undefined {
  return scenarios?.find((s) => s.scenario === "Base" && s.shock === "base");
}

export function selectUpScenario(scenarios: ScenarioCurve[] | undefined): ScenarioCurve | undefined {
  return scenarios?.find((s) => s.shock === "scr_interest_up");
}

export function selectDownScenario(scenarios: ScenarioCurve[] | undefined): ScenarioCurve | undefined {
  return scenarios?.find((s) => s.shock === "scr_interest_down");
}

/** Custom, active interest-rate overlays in the template — excludes the built-in Base/SCR
 * Up/SCR Down scenarios, which are already plotted from the run result directly. */
export function selectCustomInterestScenarios(template: EconomicDataTemplate | undefined) {
  if (!template) return [];
  return template.scenarios.filter(
    (s) => s.active && !REGULATORY_SCENARIO_IDS.includes(s.id) && s.interestShock.type !== "none" && s.interestShock.type !== "regulatory",
  );
}
