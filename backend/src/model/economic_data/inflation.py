import numpy as np
import pandas as pd
import requests
import json

from scipy.interpolate import CubicSpline
from economic_data.extrapolation import SmithWilson, MonthlyConversion
from utilities.general import add_months_to_date, left_join, months_between_dates

class Inflation:

    def __init__(
        self,
        valuation_date,
        df_inflation_swap_rates,
        df_inflation_scenarios,
        df_hicp       
    ):
        # Valuation Date
        self.valuation_date = valuation_date
        
        # Inflation Swap Rates
        self.df_inflation_swap_rates = df_inflation_swap_rates
        
        # HICP Rates
        self.df_hicp = df_hicp

        # Inflation Scenarios              
        self.df_inflation_scenarios = df_inflation_scenarios

        # Cost inflation Liquid Tenors
        self.cost_inflation_liquid_tenors = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 12, 15, 18, 20, 25, 30]
        self.projection_years = 120

        # Output
        self.inflation_data = {}

    def get_inflation(
        self,
        df_inflation_swap_rates,
        scenario,
        scenario_id,
        shock,
        instrument,
        shock_type,
        shock_bp
    ):

        df_liquid_rates = self.df_inflation_swap_rates.copy()
        df_liquid_rates['liquid_tenor_rate'] = df_liquid_rates['cmpl_pricing']/100

        # Shock inflation swap rate
        df_liquid_rates['liquid_tenor_rate'] = df_liquid_rates['liquid_tenor_rate'] + (shock_bp / 10000.0)
        df_liquid_rates = df_liquid_rates[['tenor', 'liquid_tenor_rate']]
        df_liquid_rates = df_liquid_rates.set_index(['tenor'])

        ## 1. Interpolation

        cs = CubicSpline(df_liquid_rates.index, df_liquid_rates['liquid_tenor_rate'])

        # Zero Inflation 
        last_tenor = df_liquid_rates.index[-1]
        interpolated_tenors = range(1, last_tenor + 1)
        df_interpolated_inflation_rates=pd.DataFrame({
            'year': interpolated_tenors,
            'spot_inflation': cs(interpolated_tenors)    
        })

        df_interpolated_inflation_rates.loc[1.5] = {'year': 0, 'spot_inflation': 0}
        
        # Discount Factor
        df_interpolated_inflation_rates["discount_factor"] = (
            (1 + df_interpolated_inflation_rates["spot_inflation"]) 
            ** (-df_interpolated_inflation_rates["year"])
        )

        # Forward Rate
        df_interpolated_inflation_rates = df_interpolated_inflation_rates.set_index(['year']).sort_index()
        df_interpolated_inflation_rates["forward_rate"] = np.where(
            df_interpolated_inflation_rates.index == 1,
            df_interpolated_inflation_rates['spot_inflation'],
            (df_interpolated_inflation_rates["discount_factor"].shift(1) / df_interpolated_inflation_rates["discount_factor"]) - 1
        )

        # Calculate constant projected forward rate using last 2 tenors' inflation swap rates
        prev_tenor = df_liquid_rates.index[-2]
        delta_tenor = last_tenor - prev_tenor
        prev_tenor_disc_factor = df_interpolated_inflation_rates["discount_factor"].loc[prev_tenor]
        last_tenor_disc_factor = df_interpolated_inflation_rates["discount_factor"].loc[last_tenor] 
        constant_forward_rate = (1+(prev_tenor_disc_factor/last_tenor_disc_factor-1))**(1/delta_tenor)-1

        ## 2. Extrapolation
 
        # Forward Rate
        # Assume constant forward rates after last inflation swap rate tenor        
        extrapolated_tenors = range(last_tenor + 1, self.projection_years + 1)
        df_extrapolated_inflation_rates=pd.DataFrame({
            'year': extrapolated_tenors,
            'forward_rate': constant_forward_rate 
        })

        # Discount Factor
        df_extrapolated_inflation_rates['discount_factor'] = (
            last_tenor_disc_factor
            * (1 + constant_forward_rate) ** -(df_extrapolated_inflation_rates['year'] - last_tenor)
        )

        # Inflation Rate
        df_extrapolated_inflation_rates['spot_inflation'] = (
            df_extrapolated_inflation_rates['discount_factor'] ** (-1/df_extrapolated_inflation_rates['year']) - 1
        )
   
        ## 3. Combine
        df_interpolated_inflation_rates.reset_index(inplace=True)
        df_extrapolated_inflation_rates.reset_index(inplace=True)
        df_inflation_curve = pd.concat([df_interpolated_inflation_rates, df_extrapolated_inflation_rates])

        ## 4. Output
        df_inflation_curve['scenario'] = scenario
        df_inflation_curve['shock'] = shock
        df_inflation_curve['rates'] = 'Inflation'

        # Parameters
        scenario_parameters = {
            'scenario': scenario,
            'instrument': instrument,
            'scenario_id': scenario_id,
            'shock_type': shock_type,
            'shock_bp': shock_bp
        }

        # Add scenario parameters to output
        df_inflation_curve = left_join(
            left_df=df_inflation_curve,
            right_df=pd.DataFrame(scenario_parameters, index=['scenario']),
            left_on=['scenario'],
            right_on=['scenario']
        )
   
        # Add liquid tenor rates used to output too
        df_inflation_curve = left_join(
            left_df=df_inflation_curve.reset_index(),
            right_df=df_liquid_rates.reset_index(),
            left_on=['year'],
            right_on=['tenor']
        )

        # Select relevant columns
        df_inflation_curve = df_inflation_curve[[
            'scenario',
            'scenario_id',
            'shock',
            'rates',
            'shock_type',
            'instrument',
            'shock_bp',
            'year',
            'liquid_tenor_rate',
            'discount_factor',
            'forward_rate',
            'spot_inflation'
        ]]

        return df_inflation_curve

    def get_cost_inflation(
        self, 
        df_inflation_swap_rates,
        scenario,
        scenario_id,
        shock,
        shock_type,
        instrument,
        cra_bp,
        ufr_bp,
        coupon_frequency,
        convergence_years,
        shock_bp
    ):
        df_inflation_swap_rates = df_inflation_swap_rates.copy()
        
        # Cost Inflation Swap Rate
        df_inflation_swap_rates['cost_inflation_swap_rate'] = df_inflation_swap_rates["bgn_pricing"]/100
        df_inflation_swap_rates['cost_inflation_swap_rate'] = df_inflation_swap_rates['cost_inflation_swap_rate'] + (shock_bp / 10000.0)
        df_inflation_swap_rates.set_index(['tenor'], inplace=True)
        df_inflation_swap_rates['tenor'] = df_inflation_swap_rates.index
        df_inflation_swap_rates['liquid_tenor_rate'] = df_inflation_swap_rates['cost_inflation_swap_rate']
        df_liquid_rates = df_inflation_swap_rates.loc[self.cost_inflation_liquid_tenors]
        df_liquid_rates = pd.DataFrame(df_liquid_rates['liquid_tenor_rate'])

        sw = SmithWilson(
            instrument=instrument,
            inputLiquidRates=df_liquid_rates,
            CRA_bp=cra_bp,
            UFR_bp=ufr_bp,
            nCoup=coupon_frequency,
            Tconv=convergence_years,
        )

        Q = sw.calcQ()
        sw.calcOptimalAlpha(Q, 1)
        sw.calcSW()

        # Output
        df_cost_inflation_curve = sw.resultsAll['results']
        df_cost_inflation_curve['year'] = df_cost_inflation_curve.index
        df_cost_inflation_curve = df_cost_inflation_curve.rename(columns={
            'discount': 'discount_factor',
            'forwardac': 'forward_rate',
            'zeroac': 'spot_inflation',
        })    

        # Add scenario parameters to output
        df_cost_inflation_curve["scenario_id"] = scenario_id
        df_cost_inflation_curve["shock"] = shock
        df_cost_inflation_curve["rates"] = 'Cost Inflation'

        # Parameters
        scenario_parameters = {
            'scenario': scenario,
            'scenario_id': scenario_id,
            'shock': shock,
            'shock_type': shock_type,
            'instrument': instrument,
            'coupon_frequency': coupon_frequency,
            'convergence_years': convergence_years,
            'cra_bp': cra_bp,
            'ufr_bp': ufr_bp,
            'shock_bp': shock_bp
        }

        df_cost_inflation_curve = left_join(
            left_df=df_cost_inflation_curve,
            right_df=pd.DataFrame(scenario_parameters, index=['scenario_id']),
            left_on=['scenario_id'],
            right_on=['scenario_id']
        )
   
        # Add liquid tenor rates used to output too
        df_cost_inflation_curve = left_join(
            left_df=df_cost_inflation_curve.reset_index(),
            right_df=df_liquid_rates.reset_index(),
            left_on=['year'],
            right_on=['tenor']
        )

        # Select relevant columns
        df_cost_inflation_curve = df_cost_inflation_curve[[
            'rates',
            'scenario',
            'shock',
            'scenario_id',
            'shock_type',
            'instrument',
            'coupon_frequency',
            'convergence_years',
            'cra_bp',
            'ufr_bp',
            'shock_bp',
            'year',
            'liquid_tenor_rate',
            'discount_factor',
            'forward_rate',
            'spot_inflation'
        ]]

        self.df_cost_inflation_curve = df_cost_inflation_curve

        return df_cost_inflation_curve

    def get_scenario_inflation_rates(
        self,
        scenario_parameters,
        df_inflation_swap_rates
    ):

        scenario = scenario_parameters['scenario']
        rates = scenario_parameters['rates']
        scenario_id = scenario_parameters['scenario_id']
        shock_type = scenario_parameters['shock_type']    
        instrument = scenario_parameters['instrument']
        coupon_frequency = scenario_parameters['coupon_frequency']
        convergence_years = scenario_parameters['convergence_years']
        cra_bp = scenario_parameters['cra_bp']
        ufr_bp = scenario_parameters['ufr_bp']
        shock_bp = scenario_parameters['shock_bp']

        df_scenario_inflation = None

        if rates == 'Cost Inflation':     
            df_scenario_rates = self.get_cost_inflation(
                df_inflation_swap_rates=df_inflation_swap_rates,
                scenario=scenario,
                scenario_id=scenario_id,
                shock='base',
                shock_type=shock_type,
                instrument=instrument,
                cra_bp=cra_bp,
                ufr_bp=ufr_bp,
                coupon_frequency=coupon_frequency,
                convergence_years=convergence_years,
                shock_bp=shock_bp
            )

            df_scenario_rates01 = self.get_cost_inflation(
                df_inflation_swap_rates=df_inflation_swap_rates,
                scenario=scenario,
                scenario_id=scenario_id,
                shock='inf01',
                shock_type=shock_type,
                instrument=instrument,
                cra_bp=cra_bp,
                ufr_bp=ufr_bp,
                coupon_frequency=coupon_frequency,
                convergence_years=convergence_years,
                shock_bp = shock_bp + 1
            )

            df_scenario_rates = pd.concat([df_scenario_rates, df_scenario_rates01])

        elif rates == 'Inflation':

            df_scenario_rates = self.get_inflation(
                df_inflation_swap_rates=df_inflation_swap_rates,
                scenario=scenario,
                scenario_id=scenario_id,
                instrument=instrument,
                shock='base',
                shock_type=shock_type,
                shock_bp=shock_bp
            )

            df_scenario_rates01 = self.get_inflation(
                df_inflation_swap_rates=df_inflation_swap_rates,
                scenario=scenario,
                scenario_id=scenario_id,
                instrument=instrument,
                shock='inf01',
                shock_type=shock_type,
                shock_bp=shock_bp + 1
            )

            df_scenario_rates = pd.concat([df_scenario_rates, df_scenario_rates01])   

        df_scenario_rates['scenario'] = scenario

        return df_scenario_rates
 
    def get_annual_rates(
        self,
        valuation_date,
        df_inflation_scenarios,
        df_inflation_swap_rates
    ):

        df_exante_inflation_scenarios = df_inflation_scenarios[df_inflation_scenarios['shock_type']=='exante']
        scenarios = df_exante_inflation_scenarios['scenario_id'].unique() 
        
        ## Get annual rates
        results = []

        for scenario_id in scenarios:
            print(f'Calculating {scenario_id}...')

            scenario_parameters = (
                df_exante_inflation_scenarios
                .copy()
                .set_index(['scenario_id'])
                .loc[[scenario_id]]
                .reset_index()
                .to_dict(orient='index')
            )[0]

            df_scenario_inflation_rates = self.get_scenario_inflation_rates(
                scenario_parameters=scenario_parameters,
                df_inflation_swap_rates=df_inflation_swap_rates
            )

            results.append(df_scenario_inflation_rates)

        ## Combine
        df_inflation_rates_annual = pd.concat(results)

        ## Add dates
        df_inflation_rates_annual['valuation_date'] = valuation_date
        df_inflation_rates_annual["valuation_date_month"] = df_inflation_rates_annual['valuation_date'].dt.to_period('M').dt.to_timestamp()
        df_inflation_rates_annual['date_month'] = add_months_to_date(
            date_column=df_inflation_rates_annual['valuation_date_month'], 
            months_column=df_inflation_rates_annual['year'] * 12
        ) 

        # Output
        df_inflation_rates_annual = df_inflation_rates_annual[[
            'valuation_date',
            'scenario',  
            'scenario_id',	  
            'shock',
            'rates',
            'shock_type',
            'instrument',
            'coupon_frequency',
            'convergence_years',
            'cra_bp',
            'ufr_bp',
            'shock_bp',
            'valuation_date_month',
            'date_month',
            'year',
            'liquid_tenor_rate',
            'discount_factor',        
            'forward_rate',
            'spot_inflation'
        ]]

        self.inflation_data['inflation_rates_annual'] = df_inflation_rates_annual

        return df_inflation_rates_annual
    
    def get_monthly_inflation_curves(
        self,
        df_inflation_rates_annual
    ):
        df_inflation_rates_annual = df_inflation_rates_annual.copy().set_index(['scenario_id', 'shock'])

        monthly_scenario_rates = []

        for scenario_id in df_inflation_rates_annual.index.unique():

            df_scenario_annual_rates = df_inflation_rates_annual.copy().loc[scenario_id].reset_index()
 
            mc = MonthlyConversion()

            df_monthly_scenario_rates = mc.convert_to_monthly(
                df_scenario_annual_rates=df_scenario_annual_rates,
                annual_rate_columns = ["spot_inflation"]
            )

            # Discount Factor
            df_monthly_scenario_rates["discount_factor"] = (
                (1 + df_monthly_scenario_rates["spot_inflation"]) 
                ** (-df_monthly_scenario_rates['month']/12)
            )

            df_monthly_scenario_rates = df_monthly_scenario_rates.set_index(['month']).sort_index()
            df_monthly_scenario_rates["discount_factor_lagged"] = df_monthly_scenario_rates["discount_factor"].shift(1)
            df_monthly_scenario_rates = df_monthly_scenario_rates.reset_index()

            # Forward Rate
            df_monthly_scenario_rates["forward_rate"] = np.where(
                df_monthly_scenario_rates['month'] == 0,
                df_monthly_scenario_rates['spot_inflation'],
                (df_monthly_scenario_rates["discount_factor_lagged"] / df_monthly_scenario_rates["discount_factor"]) - 1
            )

            monthly_scenario_rates.append(df_monthly_scenario_rates)

        df_inflation_rates_monthly = pd.concat(monthly_scenario_rates)

        df_inflation_rates_monthly['date_month'] = add_months_to_date(
            date_column=df_inflation_rates_monthly['valuation_date_month'], 
            months_column=df_inflation_rates_monthly['month']
        ) 

        # Output
        df_inflation_rates_monthly = df_inflation_rates_monthly[[
            'valuation_date',
            'scenario',   
            'scenario_id', 
            'shock',
            'rates',
            'shock_type',
            'instrument',
            'coupon_frequency',
            'convergence_years',
            'cra_bp',
            'ufr_bp',
            'shock_bp',
            'valuation_date_month',
            'date_month',
            'month',
            'discount_factor',        
            'forward_rate',
            'spot_inflation'
        ]]

        self.inflation_data['inflation_rates_monthly'] = df_inflation_rates_monthly

        return df_inflation_rates_monthly

    def get_hicp(
        self,
        valuation_date, 
        df_hicp,
        df_inflation_rates_monthly,
        input_rates='Inflation'
    ):

        ## Observed HICP
        df_hicp_observed = df_hicp.copy()[['date', 'date_month', 'hicp']]
        df_hicp_observed = df_hicp_observed[df_hicp_observed['date'] < valuation_date]
        df_hicp_observed = df_hicp_observed.set_index(['date_month']).sort_index(ascending=False).reset_index()
        df_hicp_observed['valuation_date'] = valuation_date
        df_hicp_observed["valuation_date_month"] = df_hicp_observed['valuation_date'].dt.to_period('M').dt.to_timestamp()
        df_hicp_observed['month'] = months_between_dates(date_start=df_hicp_observed['valuation_date_month'], date_end=df_hicp_observed['date_month']) 
        latest_hicp = df_hicp_observed.iloc[0].to_dict()

        df_inflation_rates_monthly = df_inflation_rates_monthly[df_inflation_rates_monthly['rates']==input_rates].copy().set_index(['scenario_id', 'shock'])

        hicp_output = []

        for scenario_id in df_inflation_rates_monthly.index.unique():

            ## Projected
            df_hicp_projected = df_inflation_rates_monthly.copy().loc[scenario_id].reset_index()
            df_hicp_projected['period'] = 'Projected'
            df_hicp_projected['forward_rate_factor'] = 1 + df_hicp_projected['forward_rate']
            df_hicp_projected['inflation_projection_factor'] = df_hicp_projected['forward_rate_factor'].cumprod()
            df_hicp_projected['hicp'] = latest_hicp['hicp'] * df_hicp_projected['inflation_projection_factor']

            df_hicp_projected['valuation_date'] = valuation_date
            df_hicp_projected["valuation_date_month"] = df_hicp_projected['valuation_date'].dt.to_period('M').dt.to_timestamp()
            df_hicp_projected['date_month'] = add_months_to_date(
                date_column=df_hicp_projected['valuation_date_month'], 
                months_column=df_hicp_projected['month']
            ) 

            ## Observed
            df_hicp_observed = df_hicp_observed.copy()
            df_hicp_observed['scenario_id'] = scenario_id[0]
            df_hicp_observed['scenario'] = df_hicp_projected['scenario'].iloc[0]
            df_hicp_observed['shock'] = scenario_id[1]
            df_hicp_observed['period'] = 'Observed'

            ## Combined
            df_scenario_hicp = pd.concat([df_hicp_observed, df_hicp_projected])
            hicp_output.append(df_scenario_hicp)

        df_hicp = pd.concat(hicp_output)

        df_hicp = df_hicp.set_index(['scenario_id', 'shock', 'month']).sort_index(ascending=True).reset_index()

        df_hicp = df_hicp[[
            'scenario',
            'scenario_id',
            'shock',
            'period',
            'valuation_date',
            'valuation_date_month',
            'date_month',
            'month',
            'discount_factor',
            'forward_rate',
            'spot_inflation',
            'forward_rate_factor',
            'inflation_projection_factor',
            'hicp'
        ]]

        self.inflation_data['hicp'] = df_hicp

        return df_hicp
    
    def get_all_inflation(
        self
    ):

        df_inflation_rates_annual = self.get_annual_rates(
            valuation_date=self.valuation_date,
            df_inflation_scenarios=self.df_inflation_scenarios,
            df_inflation_swap_rates=self.df_inflation_swap_rates
        )

        df_inflation_rates_monthly = self.get_monthly_inflation_curves(
            df_inflation_rates_annual=df_inflation_rates_annual
        )

        df_hicp = self.get_hicp(
            valuation_date=self.valuation_date,
            df_hicp=self.df_hicp,
            df_inflation_rates_monthly=df_inflation_rates_monthly,
            input_rates='Inflation'
        )

        return self.inflation_data
    