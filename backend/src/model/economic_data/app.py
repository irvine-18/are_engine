
import json
import os
import pandas as pd
import numpy as np

# from settings import Settings
from economic_data.interest import InterestRate
from economic_data.inflation import Inflation
from utilities import export_dict_to_xlsx, add_months_to_date, left_join, months_between_dates

class EconomicDataExtraction:

    def __init__(
        self,
        valuation_date,
        files,
        # settings
    ):
        # Files
        self.path_refinitiv_swap_rates = files["refinitiv_swap_rates"]
        self.path_inflation_swap_rates = files["inflation_swap_rates"]
        # self.path_bloomberg_swap_rates = files["bloomberg_swap_rates"]
        self.path_hicp = files["hicp"]
        self.path_eiopa_rfr = files["eiopa_rfr"]
        self.path_eiopa_equity_adjustment = files["eiopa_equity_adjustment"]

        # Valuation Date
        self.valuation_date = valuation_date   

        # # Data Specifications
        # self.data_specs = settings.data_specs

        # # Scenario Parameters
        # self.df_interest_scenarios = settings.parameters['interest_scenarios']
        # self.df_inflation_scenarios = settings.parameters['inflation_scenarios']

        # Data
        self.dict_raw_data = {}

    # def get_refinitiv_swap_rates(
    #     self, 
    #     valuation_date, 
    #     file_paths,
    #     data_specs
    # ):
       
    #     print("=" * 85)
    #     print("Refinitiv Swap Rates")
    #     print("=" * 85)

    #     from data.files import Refinitiv_Swap_Rates

    #     file_path = file_paths[0] if isinstance(file_paths, list) else file_paths

    #     rsw = Refinitiv_Swap_Rates(
    #         valuation_date=valuation_date,
    #         file_path=file_path,
    #         data_specs=data_specs
    #     )

    #     rsw.get_refinitiv_swap_rates()
        
    #     ## Append results
    #     self.dict_raw_data['interest_swap_rates'] = rsw.df_interest_swap_rates
        
    #     return self.dict_raw_data

    # def get_eiopa_rfr(
    #     self, 
    #     valuation_date, 
    #     file_paths,
    #     data_specs
    # ): 

    #     print("=" * 85)
    #     print("EIOPA RFR")
    #     print("=" * 85)

    #     from data.files import EIOPA_RFR

    #     file_path = file_paths[0] if isinstance(file_paths, list) else file_paths

    #     rfr = EIOPA_RFR(
    #         valuation_date=self.valuation_date,
    #         file_path=file_path,
    #         data_specs=self.data_specs
    #     )

    #     rfr.get_eiopa_parameters()
    #     dict_eiopa_rfr = rfr.dict_eiopa_rfr

    #     df_eiopa_parameters = dict_eiopa_rfr['df_eiopa_parameters']
    #     df_eiopa_shocks = dict_eiopa_rfr['df_eiopa_shocks']

    #     self.dict_raw_data['eiopa_parameters'] = dict_eiopa_rfr['df_eiopa_parameters']
    #     self.dict_raw_data['eiopa_shocks'] = dict_eiopa_rfr['df_eiopa_shocks']

    #     self.df_eiopa_parameters = df_eiopa_parameters
    #     self.df_eiopa_shocks = df_eiopa_shocks

    #     return self.dict_raw_data

    # def get_inflation_swap_rates(
    #     self, 
    #     valuation_date, 
    #     file_paths,
    #     data_specs
    # ):

    #     print("=" * 85)
    #     print("Inflation Swap Rates")
    #     print("=" * 85)

    #     from data.files import Inflation_Swap_Rates

    #     file_path = file_paths[0] if isinstance(file_paths, list) else file_paths

    #     isr = Inflation_Swap_Rates(
    #         valuation_date=valuation_date,
    #         file_path=file_path,
    #         data_specs=data_specs
    #     )

    #     isr.get_inflation_swap_rates()
        
    #     ## Append Results
    #     self.dict_raw_data['inflation_swap_rates'] = isr.df_inflation_swap_rates

    #     return self.dict_raw_data
    
    # def get_hicp(
    #     self, 
    #     valuation_date, 
    #     file_paths,
    #     data_specs
    # ):

    #     print("=" * 85)
    #     print("HICP")
    #     print("=" * 85)

    #     from data.files import HICP

    #     file_path = file_paths[0] if isinstance(file_paths, list) else file_paths

    #     hcp = HICP(
    #         valuation_date=self.valuation_date,
    #         file_path=file_path,
    #         data_specs=self.data_specs,
    #     )

    #     hcp.get_hicp()

    #     self.dict_raw_data['hicp'] = hcp.df_hicp

    #     return self.dict_raw_data

    # def get_eiopa_equity_adjustment(
    #     self, 
    #     valuation_date, 
    #     file_paths,
    #     data_specs
    # ):

    #     print("=" * 85)
    #     print("Equity Symmetric Adjustment")
    #     print("=" * 85)

    #     from data.files import EquitySymmetricAdjustment

    #     file_path = file_paths[0] if isinstance(file_paths, list) else file_paths

    #     esa = EquitySymmetricAdjustment(
    #         valuation_date=valuation_date,
    #         file_path=file_path,
    #         data_specs=data_specs
    #     )

    #     esa.get_eiopa_equity_adjustment()

    #     ## Append results
    #     self.dict_raw_data['eiopa_equity_adjustment'] = esa.df_eiopa_equity_adjustment

    #     return self.dict_raw_data

    def create_rates_scenarios(
        self,
        df_eiopa_parameters,
        df_interest_scenarios
    ): 

        eiopa_parameters = df_eiopa_parameters.to_dict(orient='records')[0]
        interest_scenarios = df_interest_scenarios.to_dict(orient='records')
        exante_interest_scenarios = df_interest_scenarios[df_interest_scenarios['shock_type']=='exante'].to_dict(orient='records')

        results = []

        for scenario_parameters in exante_interest_scenarios:

            scenario = {
                "rates": scenario_parameters['rates'],
                "scenario": scenario_parameters['scenario'],
                "scenario_id": scenario_parameters['scenario_id'],
                "shock_type": scenario_parameters['shock_type'], 
                "shock_bp": scenario_parameters['shock_bp'],              
                "instrument": scenario_parameters['instrument'],
                "coupon_frequency": eiopa_parameters[scenario_parameters['coupon_frequency']],
                "convergence_years": eiopa_parameters[scenario_parameters['convergence_years']],
                "cra_bp": eiopa_parameters[scenario_parameters['cra_bp']],
                "ufr_bp": eiopa_parameters[scenario_parameters['ufr_bp']],
                "va_bp": eiopa_parameters[scenario_parameters['va_bp']] 
            }
            
            results.append(scenario)

        df_interest_rate_scenarios = pd.DataFrame(results)

        # Parallel Shocks
        df_parallel_interest_scenarios = df_interest_scenarios[df_interest_scenarios['shock_type']=='parallel']
        df_interest_rate_scenarios = pd.concat([df_interest_rate_scenarios, df_parallel_interest_scenarios])
        self.df_interest_rate_scenarios = df_interest_rate_scenarios
        
        # df_interest_rate_scenarios = pd.DataFrame(results)

        self.dict_raw_data['interest_rate_scenarios'] = df_interest_rate_scenarios
        self.dict_raw_data['inflation_scenarios'] = self.df_inflation_scenarios

        return df_interest_rate_scenarios
    
    def get_all_data(
        self
    ):

        # if self.path_refinitiv_swap_rates is not None:       
        #     self.get_refinitiv_swap_rates(
        #         valuation_date=self.valuation_date,
        #         file_paths=self.path_refinitiv_swap_rates,
        #         data_specs=self.data_specs
        #     )

        # if self.path_eiopa_rfr is not None:          
        #     self.get_eiopa_rfr(
        #         valuation_date=self.valuation_date,
        #         file_paths=self.path_eiopa_rfr,
        #         data_specs=self.data_specs
        #     )

        # if self.path_hicp is not None:    
        #     self.get_hicp(
        #         valuation_date=self.valuation_date,
        #         file_paths=self.path_hicp,
        #         data_specs=self.data_specs
        #     )

        # if self.path_inflation_swap_rates is not None:
        #     self.get_inflation_swap_rates(
        #         valuation_date=self.valuation_date,
        #         file_paths=self.path_inflation_swap_rates,
        #         data_specs=self.data_specs
        #     )

        # if self.path_eiopa_equity_adjustment is not None:        
        #     self.get_eiopa_equity_adjustment(
        #         valuation_date=self.valuation_date,
        #         file_paths=self.path_eiopa_equity_adjustment,
        #         data_specs=self.data_specs
        #     )

        if self.df_eiopa_parameters is not None:
            self.create_rates_scenarios(
                df_eiopa_parameters=self.df_eiopa_parameters,
                df_interest_scenarios=self.df_interest_scenarios
            )
        
    def export_to_local(
        self, 
        file_path=None, 
        dict_raw_data=None
    ):
        dict_raw_data = self.dict_raw_data if dict_raw_data is None else dict_raw_data
        file_path = f"Economic File Data - {self.valuation_date.strftime('%Y-%m-%d')}.xlsx" if file_path is None else file_path
            
        export_dict_to_xlsx(
            data_dict=dict_raw_data,
            file_path=file_path 
        )

class EconomicDataEngine:

    def __init__(
        self,
        valuation_date=None,
        dict_raw_data=None,
        settings=None,
    ) -> None:

        # Valuation Date
        self.valuation_date = valuation_date

        # Settings
        self.settings = settings

        # Raw Data
        self.df_interest_swap_rates = dict_raw_data['interest_swap_rates']
        self.df_eiopa_shocks = dict_raw_data['eiopa_shocks']
        self.df_inflation_swap_rates = dict_raw_data['inflation_swap_rates']
        self.df_hicp = dict_raw_data['hicp']
        self.df_eiopa_equity_adjustment = dict_raw_data['eiopa_equity_adjustment']
        self.df_interest_rate_scenarios = dict_raw_data['interest_rate_scenarios']
        self.df_inflation_scenarios = dict_raw_data['inflation_scenarios']

        # Output
        self.economic_data = {}

    def get_interest_rates_data(
        self,
        valuation_date,
        df_interest_swap_rates,
        df_eiopa_shocks,
        df_interest_rate_scenarios
    ):

        interest = InterestRate(
            valuation_date=valuation_date,
            df_interest_swap_rates=df_interest_swap_rates,
            df_interest_rate_scenarios=df_interest_rate_scenarios,
            df_eiopa_shocks=df_eiopa_shocks
        )

        interest.get_all_interest_rates()
        interest_data = interest.interest_data
        self.interest_data = interest_data

        return interest_data

    def get_inflation_data(
        self,
        valuation_date,
        df_inflation_swap_rates,
        df_hicp,
        df_inflation_scenarios
    ):

        inflation = Inflation(
            valuation_date=valuation_date,
            df_inflation_scenarios=df_inflation_scenarios,
            df_inflation_swap_rates=df_inflation_swap_rates,
            df_hicp=df_hicp
        )

        inflation.get_all_inflation()
        
        inflation_data = inflation.inflation_data
        self.inflation_data = inflation_data

        return inflation_data
        
    def get_eiopa_equity_adjustments_data(
        self,
        valuation_date,
        df_eiopa_equity_adjustment
    ):

        df_eiopa_equity_adjustment['valuation_date'] = valuation_date
        df_eiopa_equity_adjustment["valuation_date_month"] = df_eiopa_equity_adjustment["valuation_date"].dt.to_period("M").dt.to_timestamp() 

        eiopa_equity_adjustment = df_eiopa_equity_adjustment[df_eiopa_equity_adjustment["valuation_date"]==df_eiopa_equity_adjustment["date"]]

        if len(eiopa_equity_adjustment) == 0:
            df_eiopa_equity_adjustment = df_eiopa_equity_adjustment.set_index(['date']).head(1).reset_index()
        else: 
            df_eiopa_equity_adjustment = eiopa_equity_adjustment

        df_eiopa_equity_adjustment = df_eiopa_equity_adjustment[[
            'date',
            'valuation_date',
            'eiopa_equity_adjustment'
        ]]

        self.eiopa_equity_adjustment = df_eiopa_equity_adjustment

        return df_eiopa_equity_adjustment

    def get_assets_rates(
        self,
        df_interest_rates_monthly,
        df_inflation_rates_monthly,
        df_hicp_monthly
    ):

        df_beleggingen_rates = df_interest_rates_monthly[df_interest_rates_monthly['rates']=='Beleggingen'].reset_index(drop=True)
        df_base_beleggingen_rates = df_beleggingen_rates[df_beleggingen_rates['scenario']=='Base']
        df_base_beleggingen_rates = df_base_beleggingen_rates[[
            'month', 
            'interest_rate'
        ]]

        df_cost_inflation_rates = df_inflation_rates_monthly[df_inflation_rates_monthly['rates']=='Cost Inflation'].reset_index(drop=True)
        df_base_cost_inflation_rates = df_inflation_rates_monthly[df_inflation_rates_monthly['scenario']=='Base'].reset_index(drop=True)
        df_base_cost_inflation_rates = df_base_cost_inflation_rates[[
            'month', 
            'spot_inflation'
        ]]

        df_hicp_monthly = df_hicp_monthly[['scenario', 'shock', 'month', 'hicp']].copy()
        df_base_hicp = df_hicp_monthly[df_hicp_monthly['scenario']=='Base'].reset_index(drop=True)
        df_base_hicp = df_base_hicp[[
            'month', 
            'hicp'
        ]]

        ## Interest Rate Sensitivities (using base inflation and HICP)
        df_interest_sensitivities = left_join(
            left_df=df_beleggingen_rates,
            right_df=df_base_cost_inflation_rates,
            left_on=['month', 'shock'],
            right_on=['month', 'shock']
        )

        df_interest_sensitivities = left_join(
            left_df=df_interest_sensitivities,
            right_df=df_base_hicp,
            left_on=['month', 'shock'],
            right_on=['month', 'shock']
        )

        ## Inflation Sensitivities (using base interest rates)
        df_inflation_sensitivities = left_join(
            left_df=df_cost_inflation_rates,
            right_df=df_base_beleggingen_rates,
            left_on=['month', 'shock'],
            right_on=['month', 'shock']
        )

        df_inflation_sensitivities=df_inflation_sensitivities[df_inflation_sensitivities['scenario'] != "Base"]

        df_inflation_sensitivities = left_join(
            left_df=df_inflation_sensitivities,
            right_df=df_hicp_monthly,
            left_on=['shock', 'month'],
            right_on=['shock', 'month']
        )

        # Combine
        df_rates = pd.concat([
            df_interest_sensitivities, 
            df_inflation_sensitivities
        ])

        df_rates = df_rates[[
            'scenario', 
            'shock_bp', 
            'valuation_date', 
            'valuation_date_month',
            'date_month', 
            'month', 
            'interest_rate', 
            'spot_inflation', 
            'hicp'
        ]]

        return df_rates

    def get_liabilities_rates(
        self,
        df_interest_rates_monthly,
        scenario_ids = [
            "EIOPA_incl_VA (IR50_Down)",
            "EIOPA_incl_VA (IR50_Up)",
            "EIOPA_incl_VA (Base)",
            "DNB (Base)",
            "EIOPA_no_VA (Base)",
        ]
    ):

        df_liabilities_rates = df_interest_rates_monthly[
            [
                "rates",
                "scenario_id",
                "scenario",
                "shock",
                "valuation_date",
                "valuation_date_month",
                "date_month",
                "month",
                "interest_rate",
            ]
        ].copy()

        df_liabilities_rates = df_liabilities_rates[df_liabilities_rates['scenario_id'].isin(scenario_ids)]

        # df_liabilities_rates = df_liabilities_rates.rename(columns={'interest_rate': 'spot_interest'})

        self.df_liabilities_rates = df_liabilities_rates

        return df_liabilities_rates

    def get_all_economic_data(
        self
    ):

        ## Get Interest Rate Data
        interest_data = self.get_interest_rates_data(
            valuation_date=self.valuation_date,
            df_interest_swap_rates=self.df_interest_swap_rates,
            df_eiopa_shocks=self.df_eiopa_shocks,
            df_interest_rate_scenarios=self.df_interest_rate_scenarios
        )

        ## Get Inflation and HICP Data
        inflation_data = self.get_inflation_data(
            valuation_date=self.valuation_date,
            df_inflation_swap_rates=self.df_inflation_swap_rates,
            df_hicp=self.df_hicp,
            df_inflation_scenarios=self.df_inflation_scenarios
        )

        ## Get EIOPA Equity Adjustment
        eiopa_equity_adjustment = self.get_eiopa_equity_adjustments_data(
            valuation_date=self.valuation_date,
            df_eiopa_equity_adjustment=self.df_eiopa_equity_adjustment
        )

        ## Get Asset Risk Engine Economic Data
        df_interest_rates_monthly = interest_data['interest_rates_monthly']
        df_inflation_rates_monthly = inflation_data['inflation_rates_monthly']
        df_hicp = inflation_data['hicp']

        df_rates = self.get_reporting_rates(
            df_beleggingen_rates=df_interest_rates_monthly[df_interest_rates_monthly['rates']=='Beleggingen'].reset_index(drop=True),
            df_cost_inflation_rates=df_inflation_rates_monthly[df_inflation_rates_monthly['rates']=='Cost Inflation'].reset_index(drop=True),
            df_hicp=df_hicp
        )

        ## Output   
        self.economic_data.update(inflation_data)    
        self.economic_data.update(interest_data)
        self.economic_data['eiopa_equity_adjustment'] = eiopa_equity_adjustment
        self.economic_data['rates'] = df_rates

        return self.economic_data

    def export_to_local(
        self,
        file_path=None
    ):

        file_path = file_path or f"./Economic Data - {self.valuation_date.strftime('%Y-%m-%d')}.xlsx"  

        export_dict_to_xlsx(
            data_dict=self.economic_data,
            file_path=file_path
        )

