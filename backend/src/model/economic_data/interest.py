import numpy as np
import pandas as pd

from utilities import text_to_months, left_join, add_months_to_date
from economic_data.extrapolation import SmithWilson, MonthlyConversion

class InterestRate:

    def __init__(
        self,
        valuation_date,
        df_interest_swap_rates,
        df_eiopa_shocks,
        df_interest_rate_scenarios
    ):
        
        # Valuation Date
        self.valuation_date = valuation_date
     
        # Refinitiv Interest Swap Rates
        self.df_interest_swap_rates = df_interest_swap_rates

        # EIOPA Shocks
        self.df_eiopa_shocks = df_eiopa_shocks

        # Interest Rates Scenarios              
        self.df_interest_rate_scenarios = df_interest_rate_scenarios

        # Liqud Tenors
        self.liquid_tenors = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 15, 20] 

        # Output
        self.eiopa_no_va = []
        self.interest_data = {}

    def get_eiopa_no_va_rates(
        self,
        df_interest_swap_rates,
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

        # Interest Swap Rates
        df_interest_swap_rates = df_interest_swap_rates.copy()[['tenor','swap_rate']].set_index("tenor")  

        # Shock swap rate
        df_interest_swap_rates['swap_rate'] = df_interest_swap_rates['swap_rate']  + (shock_bp / 10000.0)

        # Get liquid tenors
        df_liquid_rates = df_interest_swap_rates.loc[self.liquid_tenors]  
        df_liquid_rates['liquid_tenor_rate'] = df_liquid_rates['swap_rate']         
        df_liquid_rates = pd.DataFrame(df_liquid_rates['liquid_tenor_rate'])
         
        # Extrapolate using Smith Wilson
        sw = SmithWilson(
            inputLiquidRates=df_liquid_rates,
            instrument=instrument,
            CRA_bp=cra_bp,
            UFR_bp=ufr_bp,
            nCoup=coupon_frequency,
            Tconv=convergence_years
        )

        Q = sw.calcQ()
        sw.calcOptimalAlpha(Q, 1)
        sw.calcSW()

        # Output
        df_eiopa_no_va = sw.resultsAll['results']
        df_eiopa_no_va['year'] = df_eiopa_no_va.index
        df_eiopa_no_va = df_eiopa_no_va.rename(columns={
            'discount': 'discount_factor',
            'forwardac': 'forward_rate',
            'zeroac': 'spot_interest',
        })    

        # Add scenario parameters to output
        df_eiopa_no_va["scenario"] = scenario
        df_eiopa_no_va["shock"] = shock
        df_eiopa_no_va["rates"] = 'EIOPA_no_VA'

        # Parameters
        scenario_parameters = {
            'scenario': scenario,
            'scenario_id': scenario_id,
            'shock_type': shock_type,
            'instrument': instrument,
            'coupon_frequency': coupon_frequency,
            'convergence_years': convergence_years,
            'cra_bp': cra_bp,
            'ufr_bp': ufr_bp,
            'va_bp': 0.0,
            'shock_bp': shock_bp
        }

        df_eiopa_no_va = left_join(
            left_df=df_eiopa_no_va,
            right_df=pd.DataFrame(scenario_parameters, index=['scenario']),
            left_on=['scenario'],
            right_on=['scenario']
        )
   
        # Add liquid tenor rates used to output too
        df_eiopa_no_va = left_join(
            left_df=df_eiopa_no_va.reset_index(),
            right_df=df_liquid_rates.reset_index(),
            left_on=['year'],
            right_on=['tenor']
        )

        # Select relevant columns
        df_eiopa_no_va = df_eiopa_no_va[[
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
            'va_bp',
            'shock_bp',
            'year',
            'liquid_tenor_rate',
            'discount_factor',
            'forward_rate',
            'spot_interest'
        ]]

        self.eiopa_no_va.append(df_eiopa_no_va)

        return df_eiopa_no_va

    def get_eiopa_va_rates(
        self,
        df_interest_swap_rates,
        scenario,
        scenario_id,
        shock,
        shock_type,
        instrument,
        cra_bp,
        ufr_bp,
        va_bp,
        coupon_frequency,
        convergence_years,
        shock_bp
    ):
        # Interest Swap Rates
        df_interest_swap_rates = df_interest_swap_rates.reset_index().copy()

        # Get EIOPA no VA rate
        df_eiopa_no_va = self.get_eiopa_no_va_rates(
            df_interest_swap_rates=df_interest_swap_rates,
            scenario=scenario,
            scenario_id=scenario_id,
            shock=shock,
            shock_type=shock_type,
            instrument=instrument,
            cra_bp=cra_bp,
            ufr_bp=ufr_bp,
            coupon_frequency=coupon_frequency,
            convergence_years=convergence_years,
            shock_bp=shock_bp
        )
        
        # Get liquid tenors from EIOPA no VA rates
        df_eiopa_no_va = df_eiopa_no_va.copy()[['year','spot_interest']].set_index("year")
        liquid_tenors = range(1, int(max(self.liquid_tenors)) + 1)
        df_liquid_rates = df_eiopa_no_va.loc[liquid_tenors]

        # Shock interest rate and add VA
        df_liquid_rates['liquid_tenor_rate'] = (
            df_liquid_rates['spot_interest']  
            + (va_bp / 10000.0) 
        )

        df_liquid_rates = pd.DataFrame(df_liquid_rates['liquid_tenor_rate'])

        sw = SmithWilson(
            inputLiquidRates=df_liquid_rates,
            instrument="Zero",
            CRA_bp=0,
            UFR_bp=ufr_bp,
            nCoup=1,
            Tconv=convergence_years
        )

        Q = sw.calcQ()
        sw.calcOptimalAlpha(Q, 1)
        sw.calcSW()

        # Output
        df_eiopa_va = sw.resultsAll['results']
        df_eiopa_va['year'] = df_eiopa_va.index
        df_eiopa_va = df_eiopa_va.rename(columns={
            'discount': 'discount_factor',
            'forwardac': 'forward_rate',
            'zeroac': 'spot_interest',
        })  

        # Parameters
        scenario_parameters = {
            'scenario': scenario,
            'scenario_id': scenario_id,
            'shock_type': shock_type,
            'instrument': instrument,
            'coupon_frequency': coupon_frequency,
            'convergence_years': convergence_years,
            'cra_bp': cra_bp,
            'ufr_bp': ufr_bp,
            'va_bp': va_bp,
            'shock_bp': shock_bp
        }

        # Add scenario parameters to output
        df_eiopa_va["scenario"] = scenario
        df_eiopa_va["shock"] = shock
        df_eiopa_va["rates"] = 'EIOPA_incl_VA'   

        df_eiopa_va = left_join(
            left_df=df_eiopa_va,
            right_df=pd.DataFrame(scenario_parameters, index=['scenario']),
            left_on=['scenario'],
            right_on=['scenario']
        )

        # Add liquid tenor rates used to output too
        df_eiopa_va = left_join(
            left_df=df_eiopa_va.reset_index(),
            right_df=df_liquid_rates.reset_index(),
            left_on=['year'],
            right_on=['year']
        )

        # Select relevant columns
        df_eiopa_va = df_eiopa_va[[
            'scenario',
            'rates',
            'scenario_id',
            'shock',
            'shock_type',
            'instrument',
            'coupon_frequency',
            'convergence_years',
            'cra_bp',
            'ufr_bp',
            'va_bp',
            'shock_bp',
            'year',
            'liquid_tenor_rate',
            'discount_factor',
            'forward_rate',
            'spot_interest'
        ]]

        self.df_eiopa_va = df_eiopa_va

        return df_eiopa_va

    # def get_dnb_rates(
    #     self,
    #     df_interest_swap_rates,
    #     scenario,
    #     scenario_id,
    #     shock,
    #     shock_type,
    #     instrument,
    #     cra_bp,
    #     ufr_bp,
    #     va_bp,
    #     coupon_frequency,
    #     convergence_years,
    #     shock_bp
    # ):

    #     # Interest Swap Rates
    #     df_interest_swap_rates = df_interest_swap_rates.reset_index().copy()
        
    #     # Get EIOPA no VA rate
    #     df_eiopa_no_va = self.get_eiopa_no_va_rates(
    #         df_interest_swap_rates=df_interest_swap_rates,
    #         scenario=scenario,
    #         scenario_id=scenario_id,
    #         shock=shock,
    #         shock_type=shock_type,
    #         instrument=instrument,
    #         cra_bp=cra_bp,
    #         ufr_bp=ufr_bp,
    #         coupon_frequency=coupon_frequency,
    #         convergence_years=convergence_years,
    #         shock_bp=shock_bp
    #     )

    #     df_eiopa_no_va_swap = df_eiopa_no_va.copy()[['year', 'discount_factor', 'spot_interest']]
    #     df_eiopa_no_va_swap = df_eiopa_no_va_swap[df_eiopa_no_va_swap['year'] != 0]
    #     df_eiopa_no_va_swap["tenor"] = df_eiopa_no_va_swap["year"]
    #     df_eiopa_no_va_swap.set_index("tenor", inplace=True)
    #     df_eiopa_no_va_swap["swap_rate_cra"] = (1 - df_eiopa_no_va_swap["discount_factor"]) / df_eiopa_no_va_swap["discount_factor"].cumsum()
    #     df_eiopa_no_va_swap["swap_rate"] = df_eiopa_no_va_swap["swap_rate_cra"] + (cra_bp / 10000.0)

    #     # Get liqud tenor rates
    #     liquid_tenors = range(1, 21)
    #     df_interest_swap_rates1 = df_eiopa_no_va_swap.loc[liquid_tenors].copy()

    #     # Additional Liquid Tenors
    #     liqud_tenors_to_add = [25, 30, 40, 50]

    #     # Depends on the instrument specified
    #     if instrument.lower() == "swap":
    #         df_interest_swap_rates = df_interest_swap_rates.copy()[['tenor','swap_rate']].set_index("tenor") 
    #         df_interest_swap_rates['swap_rate'] = df_interest_swap_rates['swap_rate'] + (shock_bp / 10000.0) + (va_bp / 10000.0)
    #         df_interest_swap_rates2 = df_interest_swap_rates.loc[liqud_tenors_to_add] 
    #         df_interest_swap_rates2["swap_rate_cra"] = df_interest_swap_rates2["swap_rate"] - (cra_bp / 10000.0)
    #     elif instrument.lower() == "zero": 
    #         df_interest_swap_rates2 = df_eiopa_no_va_swap.loc[liqud_tenors_to_add]

    #     # Combined
    #     df_liquid_rates = pd.concat([df_interest_swap_rates1, df_interest_swap_rates2])
    #     df_liquid_rates['liquid_tenor_rate'] = df_liquid_rates['swap_rate_cra']          
    #     df_liquid_rates = pd.DataFrame(df_liquid_rates['liquid_tenor_rate'])
        
    #     # Extrapolate using Alternative Method
    #     alt_extrapolation = AlternativeExtrapolation(
    #         df_liquid_rates=df_liquid_rates
    #     )

    #     df_dnb_rates = alt_extrapolation.fromParToFwd(df_liquid_rates)

    #     # Output
    #     df_dnb_rates['year'] = df_dnb_rates.index
    #     df_dnb_rates = df_dnb_rates.rename(columns={
    #         'DF': 'discount_factor',
    #         'forwardsSpan': 'forward_rate',
    #         'tsAlt': 'spot_interest',
    #     })        

    #     # Parameters
    #     scenario_parameters = {
    #         'scenario': scenario,
    #         'scenario_id': scenario_id,
    #         'shock_type': shock_type,
    #         'instrument': instrument,
    #         'coupon_frequency': coupon_frequency,
    #         'convergence_years': convergence_years,
    #         'cra_bp': cra_bp,
    #         'ufr_bp': ufr_bp,
    #         'va_bp': 0.0,
    #         'shock_bp': shock_bp
    #     }

    #     # Add scenario parameters to output
    #     df_dnb_rates["scenario"] = scenario
    #     df_dnb_rates["shock"] = shock
    #     df_dnb_rates["rates"] = 'DNB'

    #     df_dnb_rates = left_join(
    #         left_df=df_dnb_rates,
    #         right_df=pd.DataFrame(scenario_parameters, index=['scenario']),
    #         left_on=['scenario'],
    #         right_on=['scenario']
    #     )

    #     # Add liquid tenor rates used to output too
    #     df_dnb_rates = left_join(
    #         left_df=df_dnb_rates.reset_index(),
    #         right_df=df_liquid_rates.reset_index(),
    #         left_on=['year'],
    #         right_on=['tenor']
    #     )

    #     # Select relevant columns
    #     df_dnb_rates = df_dnb_rates[[
    #         'scenario',
    #         'rates',
    #         'scenario_id',
    #         'shock',
    #         'shock_type',
    #         'instrument',
    #         'coupon_frequency',
    #         'convergence_years',
    #         'cra_bp',
    #         'ufr_bp',
    #         'va_bp',
    #         'shock_bp',
    #         'year',
    #         'liquid_tenor_rate',
    #         'discount_factor',
    #         'forward_rate',
    #         'spot_interest'
    #     ]]

    #     self.df_dnb_rates = df_dnb_rates
        
    #     return df_dnb_rates

    # def get_beleggingen_rates(
    #     self,
    #     df_interest_swap_rates,
    #     scenario,
    #     scenario_id,
    #     shock,
    #     shock_type,
    #     instrument,
    #     cra_bp,
    #     ufr_bp,
    #     va_bp,
    #     coupon_frequency,
    #     convergence_years,
    #     shock_bp
    # ):
    #     # Interest Swap Rates
    #     df_interest_swap_rates = df_interest_swap_rates.reset_index().copy()

    #     # Get EIOPA no VA rate
    #     df_dnb_rates = self.get_dnb_rates(
    #         df_interest_swap_rates=df_interest_swap_rates,
    #         scenario=scenario,
    #         scenario_id=scenario_id,
    #         shock=shock,
    #         shock_type=shock_type,
    #         instrument=instrument,
    #         cra_bp=cra_bp,
    #         ufr_bp=ufr_bp,
    #         va_bp=va_bp,
    #         coupon_frequency=coupon_frequency,
    #         convergence_years=convergence_years,
    #         shock_bp=shock_bp
    #     )  

    #     # Add back CRA to DNB rates
    #     df_beleggingen_rates = df_dnb_rates.copy()
    #     df_beleggingen_rates['spot_interest'] = df_beleggingen_rates['spot_interest'] + (cra_bp / 10000.0)

    #     # Add scenario parameters to output
    #     df_beleggingen_rates["scenario"] = scenario
    #     df_beleggingen_rates["rates"] = 'Beleggingen'

    #     # Parameters
    #     scenario_parameters = {
    #         'scenario': scenario,
    #         'scenario_id': scenario_id,
    #         'shock': shock,
    #         'shock_type': shock_type,
    #         'instrument': instrument,
    #         'coupon_frequency': coupon_frequency,
    #         'convergence_years': convergence_years,
    #         'cra_bp': cra_bp,
    #         'ufr_bp': ufr_bp,
    #         'va_bp': va_bp,
    #         'shock_bp': shock_bp
    #     }

    #     df_beleggingen_rates = left_join(
    #         left_df=df_beleggingen_rates,
    #         right_df=pd.DataFrame(scenario_parameters, index=['scenario']),
    #         left_on=['scenario'],
    #         right_on=['scenario']
    #     )

    #     return df_beleggingen_rates

    def get_scenario_interest_rates(
        self,
        scenario_parameters,
        df_interest_swap_rates
    ):
        rates = scenario_parameters['rates']
        scenario = scenario_parameters['scenario']
        scenario_id = scenario_parameters['scenario_id']
        shock_type = scenario_parameters['shock_type']    
        instrument = scenario_parameters['instrument']
        coupon_frequency = scenario_parameters['coupon_frequency']
        convergence_years = scenario_parameters['convergence_years']
        convergence_years = 60
        cra_bp = scenario_parameters['cra_bp']
        ufr_bp = scenario_parameters['ufr_bp']
        va_bp = scenario_parameters['va_bp']
        shock_bp = scenario_parameters['shock_bp']

        df_scenario_rates=None

        if rates == 'EIOPA_no_VA':
            df_scenario_rates = self.get_eiopa_no_va_rates(
                df_interest_swap_rates=df_interest_swap_rates,
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
            
            df_scenario_rates01 = self.get_eiopa_no_va_rates(
                df_interest_swap_rates=df_interest_swap_rates,
                scenario=scenario,
                scenario_id=scenario_id,
                shock='ir01',
                shock_type=shock_type,
                instrument=instrument,
                cra_bp=cra_bp,
                ufr_bp=ufr_bp,
                coupon_frequency=coupon_frequency,
                convergence_years=convergence_years,
                shock_bp = shock_bp + 1
            )

            df_scenario_rates = pd.concat([df_scenario_rates, df_scenario_rates01])
    
        elif rates == 'EIOPA_incl_VA':
            df_scenario_rates = self.get_eiopa_va_rates(
                df_interest_swap_rates=df_interest_swap_rates,
                scenario=scenario,
                scenario_id=scenario_id,
                shock='base',
                shock_type=shock_type,
                instrument=instrument,
                cra_bp=cra_bp,
                ufr_bp=ufr_bp,
                va_bp=va_bp,
                coupon_frequency=coupon_frequency,
                convergence_years=convergence_years,
                shock_bp=shock_bp
            )  

            df_scenario_rates01 = self.get_eiopa_va_rates(
                df_interest_swap_rates=df_interest_swap_rates,
                scenario=scenario,
                scenario_id=scenario_id,
                shock='ir01',
                shock_type=shock_type,
                instrument=instrument,
                cra_bp=cra_bp,
                ufr_bp=ufr_bp,
                va_bp=va_bp,
                coupon_frequency=coupon_frequency,
                convergence_years=convergence_years,
                shock_bp = shock_bp + 1
            )

            df_scenario_rates = pd.concat([df_scenario_rates, df_scenario_rates01])

        # elif rates == 'DNB':
        #     df_scenario_rates = self.get_dnb_rates(
        #         df_interest_swap_rates=df_interest_swap_rates,
        #         scenario=scenario,
        #         scenario_id=scenario_id,
        #         shock='base',
        #         shock_type=shock_type,
        #         instrument=instrument,
        #         cra_bp=cra_bp,
        #         ufr_bp=ufr_bp,
        #         va_bp=va_bp,
        #         coupon_frequency=coupon_frequency,
        #         convergence_years=convergence_years,
        #         shock_bp=shock_bp
        #     )  

        #     df_scenario_rates01 = self.get_dnb_rates(
        #         df_interest_swap_rates=df_interest_swap_rates,
        #         scenario=scenario,
        #         scenario_id=scenario_id,
        #         shock='ir01',
        #         shock_type=shock_type,
        #         instrument=instrument,
        #         cra_bp=cra_bp,
        #         ufr_bp=ufr_bp,
        #         va_bp=va_bp,
        #         coupon_frequency=coupon_frequency,
        #         convergence_years=convergence_years,
        #         shock_bp = shock_bp + 1
        #     )
  
        #     df_scenario_rates = pd.concat([df_scenario_rates, df_scenario_rates01])
       
        # elif rates == 'Beleggingen': 
        #     df_scenario_rates = self.get_beleggingen_rates(
        #         df_interest_swap_rates=df_interest_swap_rates,
        #         scenario=scenario,
        #         scenario_id=scenario_id,
        #         shock='base',
        #         shock_type=shock_type,
        #         instrument=instrument,
        #         cra_bp=cra_bp,
        #         ufr_bp=ufr_bp,
        #         va_bp=va_bp,
        #         coupon_frequency=coupon_frequency,
        #         convergence_years=convergence_years,
        #         shock_bp=shock_bp
        #     )  

        #     df_scenario_rates01 = self.get_beleggingen_rates(
        #         df_interest_swap_rates=df_interest_swap_rates,
        #         scenario=scenario,
        #         scenario_id=scenario_id,
        #         shock_type=shock_type,
        #         shock='ir01',
        #         instrument=instrument,
        #         cra_bp=cra_bp,
        #         ufr_bp=ufr_bp,
        #         va_bp=va_bp,
        #         coupon_frequency=coupon_frequency,
        #         convergence_years=convergence_years,
        #         shock_bp = shock_bp + 1
        #     )

            df_scenario_rates = pd.concat([df_scenario_rates, df_scenario_rates01])

        df_scenario_rates['scenario'] = scenario
        df_scenario_rates['scenario_id'] = scenario_id

        return df_scenario_rates
 
    def get_annual_rates(
        self,
        valuation_date,
        df_interest_swap_rates,
        df_interest_rate_scenarios
    ):
        df_exante_interest_scenarios = df_interest_rate_scenarios[df_interest_rate_scenarios['shock_type']=='exante']
        scenarios = df_exante_interest_scenarios['scenario_id'].unique() 
        
        ## Get annual rates
        results = []

        for scenario_id in scenarios:
            print(f'Calculating {scenario_id}...')

            scenario_parameters = (
                df_exante_interest_scenarios
                .copy()
                .set_index(['scenario_id'])
                .loc[[scenario_id]]
                .reset_index()
                .to_dict(orient='index')
            )[0]

            df_scenario_interest_rates = self.get_scenario_interest_rates(
                scenario_parameters=scenario_parameters,
                df_interest_swap_rates=df_interest_swap_rates
            )

            results.append(df_scenario_interest_rates)

        ## Combine
        df_interest_rates_annual = pd.concat(results)

        ## Add dates
        df_interest_rates_annual['valuation_date'] = valuation_date
        df_interest_rates_annual["valuation_date_month"] = df_interest_rates_annual['valuation_date'].dt.to_period('M').dt.to_timestamp()
        df_interest_rates_annual['date_month'] = add_months_to_date(
            date_column=df_interest_rates_annual['valuation_date_month'], 
            months_column=df_interest_rates_annual['year'] * 12
        ) 
        
        # Output
        # Select relevant columns
        df_interest_rates_annual = df_interest_rates_annual[[
            'valuation_date',
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
            'va_bp',
            'shock_bp',
            'valuation_date_month',
            'date_month',
            'year',
            'liquid_tenor_rate',
            'discount_factor',
            'forward_rate',
            'spot_interest'
        ]]

        self.df_interest_rates_annual = df_interest_rates_annual
        self.interest_data['interest_rates_annual'] = df_interest_rates_annual

        return df_interest_rates_annual
    
    def add_eiopa_shocks(
        self,
        df_interest_rates_annual,
        df_eiopa_shocks
    ):
        # Get Base EIOPA with no VA. These are created for every scenario 
        df_eiopa_no_va = pd.concat(self.eiopa_no_va)
        df_eiopa_no_va = df_eiopa_no_va[df_eiopa_no_va['shock'] == 'base'].copy()

        # EIOPA Shocks
        df_eiopa_no_va_shocks = left_join(
            left_df=df_eiopa_no_va,
            right_df=df_eiopa_shocks[['year', 'eiopa_shock_down', 'eiopa_shock_up']],
            left_on=['year'],
            right_on=['year']
        )

        df_eiopa_no_va_shocks["scr_interest_down_shock"] = np.minimum(0, -1 * df_eiopa_no_va_shocks["eiopa_shock_down"] * df_eiopa_no_va_shocks["spot_interest"])
        df_eiopa_no_va_shocks["scr_interest_up_shock"] = np.maximum(0.01, df_eiopa_no_va_shocks["eiopa_shock_up"] * np.abs(df_eiopa_no_va_shocks["spot_interest"]))

        df_eiopa_no_va_shocks = df_eiopa_no_va_shocks[[
            'rates',
            'scenario',
            'scenario_id',
            'shock',
            'shock_type',
            'instrument',
            'coupon_frequency',
            'convergence_years',
            'cra_bp',
            'ufr_bp',
            'va_bp',
            'shock_bp',
            'eiopa_shock_down',
            'eiopa_shock_up',
            'year',
            'liquid_tenor_rate',
            'discount_factor',
            'forward_rate',
            'spot_interest',
            'scr_interest_down_shock',
            'scr_interest_up_shock',
        ]]

        results = []

        for i, scenario_id in enumerate(df_interest_rates_annual['scenario_id'].unique()):

            df_scenario = df_interest_rates_annual[
                ((df_interest_rates_annual['scenario_id'] == scenario_id).copy())
                & (df_interest_rates_annual['shock'] == 'base')
            ]   

            df_scenario = left_join(
                left_df=df_scenario,
                right_df=df_eiopa_no_va_shocks,
                left_on=['year', 'scenario_id'],
                right_on=['year', 'scenario_id']
            )

            df_scenario_scr_interest_up = df_scenario.copy()
            df_scenario_scr_interest_up['shock'] = 'scr_interest_up'
            df_scenario_scr_interest_up["scr_shock"] =  df_scenario_scr_interest_up["scr_interest_up_shock"]
            df_scenario_scr_interest_up['interest_rate'] = df_scenario_scr_interest_up["spot_interest"] + df_scenario_scr_interest_up["scr_interest_up_shock"]

            df_scenario_scr_interest_down = df_scenario.copy()
            df_scenario_scr_interest_down['shock'] = 'scr_interest_down'
            df_scenario_scr_interest_down["scr_shock"] =  df_scenario_scr_interest_down["scr_interest_down_shock"]
            df_scenario_scr_interest_down['interest_rate'] = df_scenario_scr_interest_down["spot_interest"] + df_scenario_scr_interest_down['scr_interest_down_shock']
            
            df_scenario_rates = pd.concat([
                df_scenario_scr_interest_up,
                df_scenario_scr_interest_down
            ])

            results.append(df_scenario_rates)

        df_scr_interest_rates_annual = pd.concat(results)
        df_scr_interest_rates_annual['interest_rate'].fillna(0, inplace=True)
        df_scr_interest_rates_annual['forward_rate'].fillna(0, inplace=True)
        
        df_interest_rates_annual['interest_rate'] = df_interest_rates_annual['spot_interest']
        df_interest_rates_annual['interest_rate'].fillna(0, inplace=True)
        df_interest_rates_annual['forward_rate'].fillna(0, inplace=True)

        df_interest_rates_annual = pd.concat([df_interest_rates_annual, df_scr_interest_rates_annual])

        df_interest_rates_annual = df_interest_rates_annual[[
            'valuation_date',
            'rates',
            'scenario',
            'scenario_id',
            'shock',
            'shock_type',
            'instrument',
            'coupon_frequency',
            'convergence_years',
            'cra_bp',
            'ufr_bp',
            'va_bp',
            'shock_bp',
            'valuation_date_month',
            'date_month',
            'year',
            'liquid_tenor_rate',
            'discount_factor',
            'forward_rate',
            'interest_rate'
        ]]

        self.df_interest_rates_annual = df_interest_rates_annual
        self.interest_data['interest_rates_annual'] = df_interest_rates_annual        

        return df_interest_rates_annual

    def get_monthly_rates(
        self,
        df_interest_rates_annual
    ):
        df_interest_rates_annual = df_interest_rates_annual.copy().set_index(['scenario_id', 'shock'])

        monthly_scenario_rates = []

        for scenario_id in df_interest_rates_annual.index.unique():

            df_interest_rates_annual = df_interest_rates_annual.sort_index()
            df_scenario_annual_rates = df_interest_rates_annual.loc[scenario_id].copy().reset_index()

            mc = MonthlyConversion()

            df_monthly_scenario_rates = mc.convert_to_monthly(
                df_scenario_annual_rates=df_scenario_annual_rates,
                annual_rate_columns = ["interest_rate"]
            )

            # Discount Factor
            df_monthly_scenario_rates["discount_factor"] = (
                (1 + df_monthly_scenario_rates["interest_rate"]) 
                ** (-df_monthly_scenario_rates['month']/12)
            )

            df_monthly_scenario_rates = df_monthly_scenario_rates.set_index(['month']).sort_index()
            df_monthly_scenario_rates["discount_factor_lagged"] = df_monthly_scenario_rates["discount_factor"].shift(1)
            df_monthly_scenario_rates = df_monthly_scenario_rates.reset_index()

            # Forward Rate
            df_monthly_scenario_rates["forward_rate"] = np.where(
                df_monthly_scenario_rates['month'] == 0,
                df_monthly_scenario_rates['interest_rate'],
                (df_monthly_scenario_rates["discount_factor_lagged"] / df_monthly_scenario_rates["discount_factor"]) - 1
            )

            monthly_scenario_rates.append(df_monthly_scenario_rates)

        df_interest_rates_monthly = pd.concat(monthly_scenario_rates)

        df_interest_rates_monthly['date_month'] = add_months_to_date(
            date_column=df_interest_rates_monthly['valuation_date_month'], 
            months_column=df_interest_rates_monthly['month']
        ) 

        df_interest_rates_monthly = df_interest_rates_monthly[[
            'valuation_date',
            'scenario',
            'shock',
            'rates',
            'scenario_id',
            'shock_type',
            'instrument',
            'coupon_frequency',
            'convergence_years',
            'cra_bp',
            'ufr_bp',
            'va_bp',
            'shock_bp',
            'valuation_date_month',
            'date_month',
            'month',
            'discount_factor',        
            'forward_rate',
            'interest_rate'
        ]]

        self.interest_data['interest_rates_monthly'] = df_interest_rates_monthly

        return df_interest_rates_monthly

    def get_all_interest_rates(
        self
    ):
        df_interest_rates_annual = self.get_annual_rates(
            valuation_date=self.valuation_date,
            df_interest_swap_rates=self.df_interest_swap_rates,
            df_interest_rate_scenarios=self.df_interest_rate_scenarios
        )

        df_interest_rates_annual = self.add_eiopa_shocks(
            df_interest_rates_annual=df_interest_rates_annual,
            df_eiopa_shocks=self.df_eiopa_shocks
        )

        df_interest_rates_monthly = self.get_monthly_rates(
            df_interest_rates_annual=df_interest_rates_annual
        )
