import os
import pandas as pd
import numpy as np
from typing import Optional, Dict, Any
from datetime import datetime
from scipy.optimize import minimize

from settings import Settings
from asset_risk.asset_methods import AssetMethods

from utilities import (
    expand_grid, 
    months_between_dates, 
    add_months_to_date, 
    left_join
)

class Asset():

    """
    Asset class for modeling various types of financial assets or positions in assets, including government bonds,
    corporate debt funds, money market funds, swaps, and private equity.

    Attributes:
    ---------------
    # settings
    settings (Class): class containing settings for the model.
        df_modelling_properties (pd.DataFrame): DataFrame containing modelling properties.
        df_spread_risk_coefficients (pd.DataFrame): DataFrame containing spread risk parameters.
        df_cqs_rating_mapping: DataFrame containing mapping for to convert asset rating to a cqs value (used only for SCR Spread Risk)

    # Rates and parameters
    df_rates (pd.DataFrame): DataFrame containing interest and inflation data.

    # Assets
    asset_properties (dict): Dictionary containing asset-specific properties and attributes. All asset properties are also available as attributes

    # kwags
    For any other property specified

    """

    def __init__(
        self,
        valuation_date: datetime,
        asset_properties: dict,
        df_rates: pd.DataFrame,
        df_eiopa_equity_adjustment: pd.DataFrame = None,
        df_modelling_properties: pd.DataFrame = None,
        df_cqs_rating_mapping: pd.DataFrame = None,
        df_spread_risk_coefficients: pd.DataFrame = None,
        **kwargs: Any
    ):
        # Settings
        self.df_modelling_properties = df_modelling_properties
        self.df_cqs_rating_mapping = df_cqs_rating_mapping
        self.df_spread_risk_coefficients = df_spread_risk_coefficients

        # Economic Data
        self.df_rates = df_rates
        self.eiopa_equity_adjustment = df_eiopa_equity_adjustment.to_dict(orient='records')[0]['eiopa_equity_adjustment']

        # Asset Properties
        self.assign_properties(asset_properties=asset_properties, valuation_date=valuation_date)

        # Cashflow Modelling  
        self.z_spread = 0    
        self.df_asset_cashflows = None
        self.df_market_values = None
        self.df_bucket_summary = None

        # Risk      
        self.df_scr_interest_risk = None
        self.df_scr_spread_risk = None
        self.df_scr_equity_risk = None
        self.df_scr_currency_risk = None
        self.df_scr_concentration_risk = None
        self.df_scr_risk = None
    
    def assign_properties(
        self,
        valuation_date: datetime,
        asset_properties: Dict,
        modelling_properties = None
    ) -> None:
        """
        Assigns asset properties, modelling properties and a cashflow function to the Asset class

        Parameters
        -------------
        valuation_date : datetime 
            Date of valuation        
        asset_properties : dict
            Dictionary containing asset properties.
        modelling_properties : dict
            Dictionary containing modelling properties.    
        """

        # Parameters
        df_modelling_properties = modelling_properties or self.df_modelling_properties

        modelling_properties = self.df_modelling_properties.set_index('modelling_class').to_dict(orient='index')

        # Add valuation date
        asset_properties["valuation_date"] = valuation_date
            
        # Assign asset properties as class properties
        self.asset_properties = asset_properties

        for key, value in asset_properties.items():
            setattr(self, key, value)

        # Add modelling properties to class properties
        modelling_class = asset_properties["modelling_class"]
        asset_modelling_properties = modelling_properties[modelling_class]

        for key, value in asset_modelling_properties.items():
            setattr(self, key, value)
        
        # Get cash_flow function
        cashflow_function_name = asset_modelling_properties["cashflow_function_name"]

        if cashflow_function_name.lower() == "none":
            self.cashflow_function = None 
        else:
            self.cashflow_function = getattr(AssetMethods(), cashflow_function_name, None)

        return asset_properties

    def get_scenario_rates(
        self, 
        scenario: str,
        df_rates: pd.DataFrame = None
    ) -> pd.DataFrame:
        """
        Get rates for a particular scenario from the rates DataFrame.

        Parameters
        -------------
        scenario : str
            Scenario being modelled
        df_rates : pd.DataFrame
            DataFrame containing rates data.

        Returns
        -------------
        df_scenario_rates : pd.DataFrame
            DataFrame containing scenario rates.
        """

        # Paramters
        df_rates = df_rates if df_rates else self.df_rates

        # Get scenario rates
        df_scenario_rates = (
            df_rates.copy()
            .set_index("scenario")
            .loc[scenario]
            .reset_index()
        )

        return df_scenario_rates
    
    def create_asset_cashflow_matrix(
        self,
        df_scenario_rates: pd.DataFrame,
        asset_properties: dict,
        projection_years: int = 120
    ) -> pd.DataFrame:
        """
        Create an asset cashflow matrix based on the provided asset properties and scenario rates.

        Parameters
        -------------
        asset_properties : dict
            Dictionary containing asset properties.
        df_scenario_rates : pd.DataFrame
            DataFrame containing scenario rates.      
        projection_years : int
            Number of years for cashflow projection.

        Returns
        -------------
        df_cashflow_matrix : pd.DataFrame
            DataFrame containing the asset's cashflow matrix.
        """

        df_asset_properties = pd.DataFrame([asset_properties])
        position_id = asset_properties["position_id"]
        valuation_date = asset_properties["valuation_date"]
        maturity_date = asset_properties["maturity_date"] if "maturity_date" in asset_properties else None
        first_call_date = asset_properties["first_call_date"] if "first_call_date" in asset_properties else None
        next_coupon_date = asset_properties["next_coupon_date"] if "next_coupon_date" in asset_properties else None
        coupon_frequency = asset_properties["coupon_frequency"] if "coupon_frequency" in asset_properties else None

        if (maturity_date is not None) & (first_call_date is not None) &  (first_call_date != "00:00:00"):
            if first_call_date < maturity_date:
                maturity_date = first_call_date  

        # Create matrix
        df_cashflow_matrix = expand_grid(
            data_dict={
                "position_id": [position_id],
                "month": range(projection_years * 12 + 1),
            }
        )

        # Assumes all cashflows happen and the end of the month
        df_cashflow_matrix["valuation_date"] = valuation_date
        df_cashflow_matrix["valuation_date_month"] = df_cashflow_matrix["valuation_date"].dt.to_period("M").dt.to_timestamp() 
        df_cashflow_matrix["date_month"] = add_months_to_date(
            date_column=df_cashflow_matrix["valuation_date_month"],
            months_column=df_cashflow_matrix["month"],
        )       
        
        # Indicators
        if maturity_date:
            df_cashflow_matrix["maturity_date"] = maturity_date
            df_cashflow_matrix["months_to_maturity"] = months_between_dates(
                date_start=df_cashflow_matrix["date_month"],
                date_end=df_cashflow_matrix["maturity_date"],
            )              
            df_cashflow_matrix["indicator_maturity_payment"] = (df_cashflow_matrix["months_to_maturity"] == 0).astype("int32")          

        if next_coupon_date and maturity_date:
            df_cashflow_matrix["next_coupon_date"] = next_coupon_date
            df_cashflow_matrix["coupon_frequency"] = coupon_frequency

            df_cashflow_matrix["months_between_coupons"] = np.where(
                df_cashflow_matrix["coupon_frequency"] == 0,
                0,
                12 / df_cashflow_matrix["coupon_frequency"],
            )

            df_cashflow_matrix["months_after_next_coupon"] = months_between_dates(
                date_start=df_cashflow_matrix["next_coupon_date"],
                date_end=df_cashflow_matrix["date_month"],
            )

            df_cashflow_matrix["indicator_coupon_payment"] = (
                (df_cashflow_matrix["months_after_next_coupon"] >= 0)
                & (df_cashflow_matrix["months_to_maturity"] >= 0)
                & (df_cashflow_matrix["months_after_next_coupon"]  % df_cashflow_matrix["months_between_coupons"] == 0)
            )
        
            df_cashflow_matrix["indicator_coupon_payment"] = df_cashflow_matrix["indicator_coupon_payment"].astype("int32")

        # Append rates
        df_cashflow_matrix = left_join(
            left_df=df_cashflow_matrix,
            right_df=df_scenario_rates,
            left_on=["month"],
            right_on=["month"],
        )
        
        # Add asset properties
        df_cashflow_matrix = left_join(
            left_df=df_cashflow_matrix,
            right_df=df_asset_properties,
            left_on=["position_id"],
            right_on=["position_id"],
        )

        return df_cashflow_matrix

    def calc_cashflow_payments(
        self,
        asset_properties: dict,
        df_cashflow_matrix: pd.DataFrame,
        spot_interest: str = "spot_interest",
        spot_inflation: str = "spot_inflation",
        inflation_index: str = "hicp",
        **kwargs: Any,
    ) -> pd.DataFrame:
        
        """
        Calculate asset cashflows based on the provided asset properties and asset valuation method.

        Parameters
        -------------
            df_cashflow_matrix : pd.DataFrame
                DataFrame containing calculated asset cashflows.
            asset_properties : dict
                Name of the interest rate column in the cashflows DataFrame.
            required_asset_properties : str
                Name of the interest rate column in the cashflows DataFrame.
            spot_interest : str
                Name of the interest rate column in the cashflows DataFrame.
            spot_inflation : str
                Name of the inflation rate column in the cashflows DataFrame.
            inflation_index : str
                Name of the inflation index column in the cashflows DataFrame.

        Returns
        -------------
            df_scenario_cashflows : pd.DataFrame
                DataFrame containing calculated asset cashflows.
        """
            
        df_scenario_cashflows = self.cashflow_function(
            df_cashflow_matrix=df_cashflow_matrix,
            spot_interest=spot_interest,
            spot_inflation=spot_inflation,
            projected_inflation_index=inflation_index,
            **asset_properties
        )

        return df_scenario_cashflows

    def calc_z_spread(
        self, 
        df_scenario_cashflows: pd.DataFrame
    ) -> float:
        """
        Calculate the Z-spread for the asset based on the provided cashflows.

        Parameters
        -------------
        df_scenario_cashflows : pd.DataFrame
            DataFrame containing asset cashflows data.

        Returns
        -------------
        z_spread : pd.DataFrame
            DataFrame containing cashflows with Z-spread calculated.
        """

        def objective_function(x, self, df_scenario_cashflows):
            """
            Objective function to minimize for Z-spread calculation.

            Parameters
            -------------
            x : float
                Z-spread value.
            df_scenario_cashflows : pd.DataFrame
                DataFrame containing cashflows.

            Returns
            -------------
            float: Objective function value.
            """
            df_scenario_cashflows = df_scenario_cashflows.copy()
            df_scenario_cashflows["spot_spread"] = df_scenario_cashflows["spot_interest"] + x
            df_scenario_cashflows["discount_factor"] = (1 + df_scenario_cashflows["spot_spread"]) ** (-df_scenario_cashflows["month"] / 12)
            df_scenario_cashflows["discounted_cashflow"] = df_scenario_cashflows["cashflow"] * df_scenario_cashflows["discount_factor"]

            market_value = df_scenario_cashflows["market_value"].unique()[0]
            proxy_market_value = df_scenario_cashflows["discounted_cashflow"].sum()

            delta = np.abs(market_value - proxy_market_value)

            return float(delta)

        z_spread = 0

        res = minimize(
            fun=objective_function,
            x0=0,
            args=(self, df_scenario_cashflows),
            method="nelder-mead"
        )   

        z_spread = float(res["x"][0] * 10000)

        return z_spread

    def calc_discounted_cashflows(
        self,
        df_scenario_cashflows: pd.DataFrame,
        z_spread: Optional[float] = 0,
        spot_interest: str = "spot_interest",
    ) -> pd.DataFrame:
        """
        Discount the asset cashflows based on the provided Z-spread and interest rate.

        Parameters
        -------------
        df_scenario_cashflows : pd.DataFrame
            DataFrame containing asset cashflows data.
        z_spread : float
            Z-spread value.
        spot_interest : str 
            Name of the interest rate column in the cashflows DataFrame.
        
        Returns
        -------------
        df_scenario_cashflows: pd.DataFrame
            DataFrame containing discounted cashflows.

        """
    
        df_scenario_cashflows = df_scenario_cashflows.copy()        
        
        if z_spread is None:
            z_spread = self.z_spread

        df_scenario_cashflows["z_spread"] = z_spread

        # Discount factor including z-Spread
        df_scenario_cashflows["discount_factor"] = (
            1
            + df_scenario_cashflows[spot_interest]
            + df_scenario_cashflows["z_spread"] / 10000
        ) ** (-df_scenario_cashflows["month"] / 12)

        # Discounted Payments
        df_scenario_cashflows["discounted_coupon_payment"] = (
            df_scenario_cashflows["coupon_payment"] 
            * df_scenario_cashflows["discount_factor"]
        )

        df_scenario_cashflows["discounted_maturity_payment"] = (
            df_scenario_cashflows["maturity_payment"]
            * df_scenario_cashflows["discount_factor"]
        )

        df_scenario_cashflows["discounted_cashflow"] = (
            df_scenario_cashflows["cashflow"]
            * df_scenario_cashflows["discount_factor"]
        )

        return df_scenario_cashflows

    def calc_cashflows(
        self,
        asset_properties,
        scenario: str = "Base",
        calculate_z_spread: bool = True
    ) -> pd.DataFrame:
        """
        Run a single scenario for the asset based on asset properties and the scenario rates.

        Parameters
        -------------
        scenario : str
            Name of the scenario.
        calculate_z_spread : pd.DataFrame
            DataFrame containing scenario-specific interest rates.

        Returns
        -------------
        df_scenario_cashflows : pd.DataFrame
            DataFrame containing the discounted cashflows of the scenario.
        """

        df_scenario_rates = self.get_scenario_rates(scenario=scenario)
        df_cashflow_matrix = self.create_asset_cashflow_matrix(df_scenario_rates=df_scenario_rates, asset_properties=asset_properties)
        inflation_index = self.inflation_index if 'inflation_index' in self.asset_properties else None

        # Run the scenario vs shock combination
        scenario_results = []

        shocks = {
            "spot_interest": {
                "spot_interest": "spot_interest",
                "spot_inflation": "spot_inflation",
                "inflation_index": inflation_index,
            },
            "scr_interest_down": {
                "spot_interest": "scr_interest_down",
                "spot_inflation": "spot_inflation",
                "inflation_index": inflation_index,
            },
            "scr_interest_up": {
                "spot_interest": "scr_interest_up",
                "spot_inflation": "spot_inflation",
                "inflation_index": inflation_index,
            },
            "ir01": {
                "spot_interest": "spot_interest01",
                "spot_inflation": "spot_inflation",
                "inflation_index": inflation_index,
            },
            "inf01": {
                "spot_interest": "spot_interest",
                "spot_inflation": "spot_inflation01",
                "inflation_index": f"{inflation_index}01",
            },
        }

        for shock in shocks:
            spot_interest = shocks[shock]["spot_interest"]
            spot_inflation = shocks[shock]["spot_inflation"]
            inflation_index = shocks[shock]["inflation_index"]

            df_scenario_cashflows = self.calc_cashflow_payments(
                asset_properties=asset_properties,
                df_cashflow_matrix=df_cashflow_matrix,
                spot_interest=spot_interest,
                spot_inflation=spot_inflation,
                inflation_index=inflation_index
            )

            if calculate_z_spread:
                z_spread = self.calc_z_spread(df_scenario_cashflows=df_scenario_cashflows)
            else:
                z_spread = self.z_spread

            discounted_cashflows = self.calc_discounted_cashflows(
                df_scenario_cashflows=df_scenario_cashflows,
                z_spread=z_spread, 
                spot_interest=spot_interest
            )

            discounted_cashflows["shock"] = shock

            scenario_results.append(discounted_cashflows)

        # Combine scenario results
        df_scenario_cashflows = pd.concat(scenario_results)

        # Remove working columns
        cashflow_columns = [
            'position_id',
            'portfolio',
            'asset_id',
            'storage_class',
            'internal_class',
            'modelling_class',
            'fixed_or_floating',
            'counterparty',
            'country_of_issuer',
            'valuation_date',
            'nominal',
            'market_value',

            'scenario',
            'shock',            
            'month',
            'date_month',  
            'z_spread',
            'coupon_payment',
            'maturity_payment',
            'cashflow',
            'discount_factor',
            'discounted_coupon_payment',
            'discounted_maturity_payment',
            'discounted_cashflow'
        ]

        df_scenario_cashflows = df_scenario_cashflows[cashflow_columns]

        # Remove zero columns
        df_scenario_cashflows = df_scenario_cashflows[df_scenario_cashflows["cashflow"] != 0]

        # Append scenario cashflows to asset cashflows
        if self.df_asset_cashflows is None:
            df_asset_cashflows = df_scenario_cashflows
        else:
            df_asset_cashflows = pd.concat([self.df_asset_cashflows, df_scenario_cashflows])

        self.df_asset_cashflows = df_asset_cashflows

        return df_scenario_cashflows

    def calc_market_values(
        self, 
        df_scenario_cashflows: pd.DataFrame
    ) -> pd.DataFrame:

        """
        Calculate market values (sum of discounted cashflows) for the asset based on asset cashflows.

        Parameters
        -------------
        df_scenario_cashflows : pd.DataFrame
            DataFrame containing asset cashflows data.

        Returns
        -------------
        df_scenario_market_values: pd.DataFrame
            DataFrame containing market values and related information.
        """

        df_scenario_cashflows = df_scenario_cashflows.copy()
        
        # Add bucket
        # Define the bins and labels in a dictionary
        bucket1_bin_dict = {
            0: '0.25Y',
            4: '01Y',
            12: '02Y',
            24: '03Y',
            36: '05Y',
            60: '07Y',
            84: '10Y',
            120: '15Y',
            180: '20Y',
            240: '25Y',
            300: '30Y',
            360: '40Y',
            480: '50Y',
            600: '51Y+'
        }

        bucket2_bin_dict = {
            0: '1 upto 5 years',
            60: '6 upto 10 years',
            120: '11 upto 15 years',
            180: '16 upto 20 years',
            240: '21 upto 25 years',
            300: '26 upto 30 years',
            360: '31 upto 35 years',
            420: '36 upto 40 years',
            480: '41 upto 45 years',
            540: '46 upto 50 years',
            600: '51 years+'
        }

        # Use pd.cut to create the 'group' column with ordered=False
        df_scenario_cashflows['bucket1'] = pd.cut(
            df_scenario_cashflows['month'], 
            bins=sorted(bucket1_bin_dict.keys()) + [float('inf')], 
            labels=[bucket1_bin_dict[key] for key in sorted(bucket1_bin_dict.keys())], 
            right=False, 
            ordered=False
        ).astype('str')

        df_scenario_cashflows['bucket2'] = pd.cut(
            df_scenario_cashflows['month'], 
            bins=sorted(bucket2_bin_dict.keys()) + [float('inf')], 
            labels=[bucket2_bin_dict[key] for key in sorted(bucket2_bin_dict.keys())], 
            right=False, 
            ordered=False
        ).astype('str')

        df_scenario_cashflows['bucket'] = (df_scenario_cashflows['month'] / 60).apply(lambda x: int(x) + 1)

        # Aggregate cashflows by portfolio, asset, scenario, bucket
        aggregation_columns = [
            "portfolio",
            "position_id",
            "asset_id",            
            "scenario",
            "bucket",           
            "bucket1",           
            "bucket2",
            "counterparty",
            "storage_class",
            "modelling_class",
            "internal_class",
            "country_of_issuer",
            "valuation_date"
        ]

        aggregation_functions = {
            "discounted_cashflow": "sum"
        }

        df_scenario_cashflows.fillna(0, inplace=True)

        df_scenario_market_values = df_scenario_cashflows.pivot_table(
            index=aggregation_columns,
            columns="shock",
            values="discounted_cashflow",
            aggfunc=aggregation_functions,
        ).reset_index()

    	# Rename market value columns
        df_scenario_market_values.rename(
            columns={
                'spot_interest': 'shocked_mv_base',
                'scr_interest_down': 'shocked_mv_scr_interest_down',
                'scr_interest_up': 'shocked_mv_scr_interest_up',
                'ir01': 'shocked_mv_ir01',
                'inf01': 'shocked_mv_inf01',
            },
            inplace=True
        )

        # Differences
        df_scenario_market_values['scr_interest_down_risk'] = df_scenario_market_values['shocked_mv_scr_interest_down'] - df_scenario_market_values['shocked_mv_base']
        df_scenario_market_values['scr_interest_up_risk'] = df_scenario_market_values['shocked_mv_scr_interest_up'] - df_scenario_market_values['shocked_mv_base'] 
        df_scenario_market_values['ir01'] = df_scenario_market_values['shocked_mv_ir01'] - df_scenario_market_values['shocked_mv_base'] 
        df_scenario_market_values['inf01'] = df_scenario_market_values['shocked_mv_inf01'] - df_scenario_market_values['shocked_mv_base'] 

        # Select specific columns in order
        df_scenario_market_values = df_scenario_market_values[
            [
                'valuation_date',
                'portfolio',
                'position_id',
                'asset_id',
                'scenario',
                "bucket",           
                "bucket1",           
                "bucket2",
                'counterparty',
                'storage_class',
                'modelling_class',
                'internal_class',
                'country_of_issuer',
                'shocked_mv_base',
                'shocked_mv_scr_interest_down',
                'shocked_mv_scr_interest_up',
                'shocked_mv_ir01',
                'shocked_mv_inf01',
                'scr_interest_down_risk',
                'scr_interest_up_risk',
                'ir01',
                'inf01'
            ]
        ]

        # Append scenario market values to market values 
        if self.df_market_values is None:
            df_market_values = df_scenario_market_values
        else:
            df_market_values = pd.concat([self.df_market_values, df_scenario_market_values])

        self.df_market_values = df_market_values

        return df_scenario_market_values

    def calc_scr_interest_risk(
        self,
        df_scenario_market_values: pd.DataFrame, 
        scenario: str = "Base"
    ) -> pd.DataFrame:
        
        """
        Calculate solvency capital requirement (SCR) related to interest rate risk.

        Parameters
        -------------
        scenario : str
            Name of the scenario.
        df_scenario_market_values : pd.DataFrame
            DataFrame containing market values and related information.
        asset_properties : dict
            Dictionary containing asset properties.

        Returns:
        -------------
        df_scenario_scr_interest_risk : pd.DataFrame
            DataFrame containing SCR interest risk calculations.

        """
        asset_properties = self.asset_properties
        model_scr_interest_risk = self.model_scr_interest_risk

        if model_scr_interest_risk == True:

            # Aggregate cashflows by portfolio, asset, scenario, bucket
            aggregation_columns = [
                "valuation_date",
                "portfolio",
                "position_id",
                "asset_id",            
                "scenario",
                "counterparty",
                "storage_class",
                "modelling_class",
                "internal_class",
                "country_of_issuer"
            ]
                        
            aggregation_functions = {
                "shocked_mv_base": "sum",
                "scr_interest_down_risk": "sum",
                "scr_interest_up_risk": "sum",
                "ir01": "sum",
                "inf01": "sum"
            }

            df_scenario_market_values.fillna(0, inplace=True)

            df_scenario_scr_interest_risk = df_scenario_market_values.pivot_table(
                index=aggregation_columns,
                aggfunc=aggregation_functions,
            ).reset_index()

        else:

            df_scenario_scr_interest_risk = pd.DataFrame(
                data = {
                    "position_id": self.position_id,
                    "scenario": scenario,
                    'z_spread': 0,
                    "spot_interest": 0,
                    "scr_interest_down_risk": 0,
                    "scr_interest_up_risk": 0,
                    "ir01": 0,
                    "inf01": 0
                },
                index=['scenario']
            )

        # Append output
        if self.df_scr_interest_risk is None:
            df_scr_interest_risk = df_scenario_scr_interest_risk
        else:
            df_scr_interest_risk = pd.concat([self.df_scr_interest_risk, df_scenario_scr_interest_risk])

        self.df_scr_interest_risk = df_scr_interest_risk
    
        return df_scenario_scr_interest_risk

    def calc_scr_spread_risk(
        self, 
        scenario: str = "Base"
    ) -> pd.DataFrame:
        
        """
        Calculate solvency capital requirement (SCR) related to spread risk.

        Parameters
        -------------
        scenario : str
            Name of the scenario.
        model_scr_spread_risk : bool
            To indicate weather SCR Spread risk calculation applies to asset
        position_id : str
            Position ID
        rating : str
            Credit ating of instrument
        duration : float
            Duration of instrument
        market_value : float
            Reported market value of instrument
        df_cqs_rating_mapping : pd.DataFrame
            DataFrame containing mapping to get CQS from credit rating
        df_spread_risk_coefficients : pd.DataFrame
            DataFrame containing spread risk parameters.
            
        Returns
        -------------
        df_scenario_scr_spread_risk : pd.DataFrame
            The calculated SCR for spread risk.

        """
        position_id = self.position_id
        model_scr_spread_risk = self.model_scr_spread_risk
        df_cqs_rating_mapping = self.df_cqs_rating_mapping
        df_spread_risk_coefficients = self.df_spread_risk_coefficients
        
        # Calculate scr_spread if model_scr_spread_risk indicator is True
        if model_scr_spread_risk == True:

            rating = self.rating
            modified_duration = self.modified_duration
            market_value = self.market_value
            
            # Get asset CQS from rating and mapping
            cqs = df_cqs_rating_mapping.set_index('rating').loc[rating][0]

            # Calculate the truncated duration
            duration = max(1, modified_duration) # TO CHECK - Why?
            truncated_duration = min((5 * np.floor(duration / 5)), 20)

            # Get coefficients using cqs and trunced duration
            df_spread_risk_coefficients = df_spread_risk_coefficients.set_index(["cqs", "truncated_duration"])
            parameters = df_spread_risk_coefficients.loc[(cqs, truncated_duration)].to_dict()
            ai = parameters['ai']
            bi = parameters['bi']

            # Calculate Spread Risk
            scr_spread_coefficient = ai + bi * (duration - truncated_duration)
            scr_spread = market_value * scr_spread_coefficient
        
        else:

            scr_spread = 0

        scr_spread = {
            "position_id": position_id,
            "scenario": scenario,
            'scr_spread_risk': scr_spread
        }
        
        df_scenario_scr_spread_risk = pd.DataFrame(scr_spread, index=['scenario'])

        # Append to output   
        if self.df_scr_spread_risk is None:
            df_scr_spread_risk = df_scenario_scr_spread_risk
        else:
            df_scr_spread_risk = pd.concat([self.df_scr_interest_risk, df_scenario_scr_spread_risk])

        self.df_scr_spread_risk = df_scr_spread_risk
    
        return df_scenario_scr_spread_risk

    def calc_scr_equity_risk(
        self, 
        scenario: str = "Base"
    )-> pd.DataFrame: 
        
        """
        Calculate solvency capital requirement (SCR) related to equity risk.

        Parameters
        -------------
        scenario : str
            Name of the scenario.
        model_scr_equity_risk : bool
           To indicate weather SCR Equity risk calculation applies to asset        
        position_id : str
            Position ID
        equity_type : int
            SCR Equity type 
        eiopa_equity_adjustment : float
            EIOPA equity symmetric adjustment
        market_value : float
            Reported market value of instrument
         
        Returns
        -------------
        df_scenario_scr_equity_risk : pd.DataFrame 
            The calculated SCR for equity risk.
        """
        
        position_id = self.position_id
        model_scr_equity_risk = self.model_scr_equity_risk

        if model_scr_equity_risk == True:

            equity_type = self.equity_type
            eiopa_equity_adjustment = self.eiopa_equity_adjustment
            market_value = self.market_value

            if int(equity_type) == 1:
                scr_equity = market_value * (eiopa_equity_adjustment + 0.39)
                shocked_mv_base = market_value
            elif int(equity_type) == 2:
                scr_equity = market_value * (eiopa_equity_adjustment + 0.49)

                shocked_mv_base = market_value
        else:
            scr_equity = 0
            shocked_mv_base = 0

        scr_equity_risk = {
            "position_id": position_id,
            "scenario": scenario,
            "shocked_mv_base": shocked_mv_base,
            "scr_equity_risk": scr_equity
        }

        df_scenario_scr_equity_risk =  pd.DataFrame(scr_equity_risk, index=['scenario'])
        
        # Append to output
        if self.df_scr_equity_risk is None:
            df_scr_equity_risk = df_scenario_scr_equity_risk
        else:
            df_scr_equity_risk = pd.concat([self.df_scr_equity_risk, df_scenario_scr_equity_risk])

        self.df_scr_equity_risk = df_scr_equity_risk
    
        return df_scenario_scr_equity_risk

    def calc_scr_currency_risk(
        self, 
        scenario: str = "Base",
        exchange_rate: float = 1.0,
        market_value: float = None,
        scr_currency_shock: float = 0.25
    )-> pd.DataFrame: 
        
        """
        Calculate solvency capital requirement (SCR) related to cuurency risk.

        Parameters
        -------------
        scenario : str
            Name of the scenario
        exchange_rate : int
            Exchange rate
        market_value : float
            Market value in local currency
         
        Returns
        -------------
        df_scr_currency_risk : pd.DataFrame 
            The calculated SCR Currency Risk.
        """
        
        position_id = self.position_id
        market_value = self.market_value
        model_scr_currency_risk = self.model_scr_currency_risk

        if model_scr_currency_risk == True:
            
            scr_currency_risk = None
            shocked_mv_base = market_value
        else:
            scr_currency_risk = 0
            shocked_mv_base = 0

        scr_default_risk = {
            "position_id": position_id,
            "scenario": scenario,
            "shocked_mv_base": shocked_mv_base,
            "fx01": scr_currency_risk,
            "scr_currency_risk_down": scr_currency_risk,
            "scr_currency_risk_up": scr_currency_risk
        }

        df_scr_currency_risk = pd.DataFrame(scr_currency_risk, index=['scenario'])
        
        # Append to output
        if self.df_scr_currency_risk is None:
            df_scr_currency_risk = df_scr_currency_risk
        else:
            df_scr_currency_risk = pd.concat([self.df_scr_currency_risk, df_scr_currency_risk])

        self.df_scr_currency_risk = df_scr_currency_risk
    
        return df_scr_currency_risk
    
    def calc_scenario_scr_risk(
        self,
        scenario: str = "Base",
        calculate_z_spread: bool = True
    ) -> pd.DataFrame:
        """
        Calculate the Solvency Capital Requirement (SCR) for various risk components.

        Returns:
            pd.DataFrame: DataFrame containing SCR calculations for different risk components.
        """
        asset_properties = self.asset_properties
        model_scr_interest_risk = self.model_scr_interest_risk

        # Calculate cashflows if model_scr_interest_risk is True. Some assets like Equity do not need this
        if model_scr_interest_risk:
            df_scenario_cashflows = self.calc_cashflows(
                asset_properties=asset_properties,
                scenario=scenario,
                calculate_z_spread=calculate_z_spread
            ) 
            df_scenario_market_values = self.calc_market_values(df_scenario_cashflows=df_scenario_cashflows)
        else:
            df_scenario_cashflows = None
            df_scenario_market_values = None

        # Calculate SCR Interest Risk for all assets. It creates a placholder zero output for assets without Interest Risk
        df_scenario_scr_interest_risk = self.calc_scr_interest_risk(
            scenario=scenario,
            df_scenario_market_values=df_scenario_market_values
        )

        # Calculate SCR Spread Risk
        df_scenario_scr_spread_risk = self.calc_scr_spread_risk(scenario=scenario)

        # Calculate SCR Equity Risk
        df_scenario_scr_equity_risk = self.calc_scr_equity_risk(scenario=scenario)

        # Output
        df_asset_info = pd.DataFrame([asset_properties])

        df_scenario_scr_risk = left_join(
            left_df=df_asset_info, 
            right_df=df_scenario_scr_interest_risk, 
            left_on=["position_id"], 
            right_on=["position_id"]
        )
        df_scenario_scr_risk = left_join(
            left_df=df_scenario_scr_risk, 
            right_df=df_scenario_scr_spread_risk, 
            left_on=["position_id"], 
            right_on=["position_id"]
        )
        df_scenario_scr_risk = left_join(
            left_df=df_scenario_scr_risk,
            right_df=df_scenario_scr_equity_risk,
            left_on=["position_id"],
            right_on=["position_id"]
        )

        columns = [
            'position_id',
            'portfolio',
            'asset_id',
            'storage_class',
            'internal_class',
            'modelling_class',
            'fixed_or_floating',
            'counterparty',
            'country_of_issuer',
            'management_style',
            'quotation_currency',
            'exchange_rate',
            'valuation_date',
            'nominal',
            'market_value',

            'scenario',
            'z_spread',
            'shocked_mv_base',
            'ir01',
            'inf01',
            'scr_interest_down_risk',
            'scr_interest_up_risk',
            'scr_spread_risk',
            'scr_equity_risk',
        ]
        
        df_scenario_scr_risk = df_scenario_scr_risk[columns]

        # Append to output
        if self.df_scr_risk is None:
            df_scr_risk = df_scenario_scr_risk
        else:
            df_scr_risk = pd.concat([self.df_scr_risk, df_scenario_scr_risk])

        self.df_scr_risk = df_scr_risk
    
        return df_scenario_scr_risk

    def calc_sensitivities_scr_risk(
        self,
        scenarios=None
    ) -> pd.DataFrame:
        
        """
        Calculate the shocked cashflows for each scenario provided in the rates. 

        Args:
            asset_properties (dict): Dictionary containing asset properties.
            df_rates (pd.DataFrame): DataFrame containing market interest rates for each scenario.

        Returns:
            pd.DataFrame: DataFrame containing cashflows for each shock vs scenario combination.
        """
        df_rates = self.df_rates
        model_scr_interest_risk = self.model_scr_interest_risk
        asset_properties = self.asset_properties
        inflation_index = self.asset_properties["inflation_index"] if "inflation_index" in self.asset_properties else None

        # Calculate the z-Spread for the Base scenario using the Spot Rates i.e. unshocked
        if model_scr_interest_risk:
            df_base_rates = self.get_scenario_rates(scenario="Base")
            df_cashflow_matrix = self.create_asset_cashflow_matrix(asset_properties=self.asset_properties, df_scenario_rates=df_base_rates)

            df_scenario_cashflows = self.calc_cashflow_payments(
                asset_properties=asset_properties,
                df_cashflow_matrix=df_cashflow_matrix,
                spot_interest="spot_interest",
                spot_inflation="spot_inflation",
                inflation_index=inflation_index
            )

            z_spread = self.calc_z_spread(df_scenario_cashflows=df_scenario_cashflows)

            self.z_spread = z_spread
            self.asset_properties["z_spread"] = z_spread

        # Run rate scenarios (sensitivities) Using the z-Spread calculated above
        # Run all scenarios if not specified
        if scenarios is None:
            scenarios = df_rates["scenario"].unique()
        
        for scenario in scenarios:
            
            self.calc_scenario_scr_risk(
                scenario=scenario,
                calculate_z_spread=False
            )

        return self
