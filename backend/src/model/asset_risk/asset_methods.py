import pandas as pd
import numpy as np
from typing import Optional, Dict, Any

class AssetMethods:

    def calc_bond_fixed_coupon(
        self,
        df_cashflow_matrix: pd.DataFrame,
        coupon_frequency: int,
        annual_fixed_coupon_rate: float,
        nominal: float,
        **kwargs: Any
    ) -> pd.DataFrame:

        """Calculate cashflows for a bond with a fixed coupon rate.

        Parameters
        ----------
        df_cashflow_matrix : DataFrame
            DataFrame containing a matrix including columns for indicator flags 
            for coupon and maturity payments, nominal values, and spot interest rates.
        coupon_frequency : int 
            Number of coupons per year.
        annual_fixed_coupon_rate : float
            Fixed annual coupon rate of the bond.
        nominal : float
            Bond principal value.

        Returns
        -------
        df_asset_cashflows : DataFrame
            DataFrame with calculated cashflows.

        """

        df_asset_cashflows = df_cashflow_matrix.copy()

        # Calculate effective coupon rate
        df_asset_cashflows["effective_coupon_rate"] = (
            0 if coupon_frequency == 0 else annual_fixed_coupon_rate / coupon_frequency
        )

        # Calculate cashflows
        df_asset_cashflows["coupon_payment"] = (
            df_asset_cashflows["indicator_coupon_payment"]
            * df_asset_cashflows["effective_coupon_rate"]
            * nominal
        )

        df_asset_cashflows["maturity_payment"] = (
            df_asset_cashflows["indicator_maturity_payment"] * nominal
        )

        df_asset_cashflows["cashflow"] = (
            df_asset_cashflows["coupon_payment"]
            + df_asset_cashflows["maturity_payment"]
        )

        return df_asset_cashflows

    def calc_bond_inflation_linked(
        self,
        df_cashflow_matrix: pd.DataFrame,
        annual_nominal_coupon_rate: float,
        coupon_frequency: int,
        current_indexation_coefficient: float,
        spot_inflation: str,
        **kwargs: Any
    ) -> pd.DataFrame:

        """Calculate cashflows for an bond with coupons that depend on inflation.

        Parameters
        ----------
        df_cashflow_matrix : DataFrame
            A DataFrame containing a matrix which includes columns for indicator flags for coupon
            and maturity payments, nominal values, and spot interest rates.
        annual_nominal_coupon_rate : float
            The annual nominal coupon rate for the bond, expressed as a decimal (e.g., 0.05 for 5%).
        coupon_frequency : int
            The number of coupon payments per year.
        current_indexation_coefficient : float
            The current indexation coefficient, representing the inflation adjustment factor applied
            to the bond's principal value.
        spot_inflation : str
            The column name in `df_cashflow_matrix` containing the assumed monthly annualised projected inflation rates.

        Returns
        -------
        DataFrame
            An updated DataFrame that includes the calculated cashflows for the bond, taking into
            account the inflation adjustments.

        """

        df_asset_cashflows = df_cashflow_matrix.copy()

        # Calculate effective coupon rate
        df_asset_cashflows["effective_nominal_coupon_rate"] = (
            0
            if coupon_frequency == 0
            else annual_nominal_coupon_rate / coupon_frequency
        )

        # Calculate inflation adjusted nominal
        df_asset_cashflows["projected_indexation_coefficient"] = (
            current_indexation_coefficient
            * (1 + df_asset_cashflows[spot_inflation])
            ** (df_asset_cashflows["month"] / 12)
        )

        df_asset_cashflows["inflation_adjusted_nominal"] = (
            df_asset_cashflows["nominal"]
            * df_asset_cashflows["projected_indexation_coefficient"]
        )

        # Calculate coupons
        df_asset_cashflows["coupon_payment"] = (
            df_asset_cashflows["indicator_coupon_payment"]
            * df_asset_cashflows["effective_nominal_coupon_rate"]
            * df_asset_cashflows["inflation_adjusted_nominal"]
        )

        # Calculate maturity payment
        df_asset_cashflows["maturity_payment"] = (
            df_asset_cashflows["indicator_maturity_payment"]
            * df_asset_cashflows["inflation_adjusted_nominal"]
        )

        # Calculate cash flows
        df_asset_cashflows["cashflow"] = (
            df_asset_cashflows["coupon_payment"]
            + df_asset_cashflows["maturity_payment"]
        )

        return df_asset_cashflows

    def calc_bond_floating_interest(
        self,
        df_cashflow_matrix: pd.DataFrame,
        coupon_frequency: float,
        annual_floating_coupon_rate: float,
        annual_coupon_spread: float,
        spot_interest: str,
        **kwargs: Any
    ) -> pd.DataFrame:
        
        """Calculates the cashflows for floating interest rate bonds. 
        
        Parameters
        ----------
            df_cashflow_matrix : pd.DataFrame
                DataFrame containing a matrix including columns for indicator flags for coupon and maturity payments, nominal values, and spot interest rates.
            coupon_frequency : float
                Number of coupons per year.
            annual_floating_coupon_rate : float
                The current yield of the bond.
            annual_coupon_spread : float
                The spread added to the reference rate to deswap_termine the coupon rate.
            spot_interest : str
                The name of the column in `df_cashflow_matrix` that contains the spot 
                interest rate data to be used for calculating the coupons.

        Returns
        ----------
            DataFrame: Updated DataFrame with calculated cashflows.

        """
        df_asset_cashflows = df_cashflow_matrix.copy()
        coupon_frequency = 0 if coupon_frequency == 0 else coupon_frequency
        months_between_coupons = 0 if coupon_frequency == 0 else 12 / coupon_frequency

        # Current coupon rate
        effective_current_coupon_rate = (
            0
            if coupon_frequency == 0
            else (annual_floating_coupon_rate - annual_coupon_spread) / coupon_frequency
        )

        # Future coupon rates
        # Spot interest rate, now and at next coupon
        df_asset_cashflows["spot_interest_now"] = (
            df_asset_cashflows["indicator_coupon_payment"]
            * df_asset_cashflows[spot_interest]
        )

        df_asset_cashflows["spot_interest_next_coupon"] = (
            df_asset_cashflows["indicator_coupon_payment"]
            * df_asset_cashflows[spot_interest].shift(-int(months_between_coupons))
        )

        # Time (in years), now and at next coupon
        df_asset_cashflows["t_now"] = df_asset_cashflows["month"] / 12
        df_asset_cashflows["t_next_coupon"] = (df_asset_cashflows["month"] + months_between_coupons) / 12

        # Calculate forward rate between coupons
        df_asset_cashflows["forw_rate_between_coupons"] = (
            (1 + df_asset_cashflows["spot_interest_next_coupon"]) ** df_asset_cashflows["t_next_coupon"] / 
            (1 + df_asset_cashflows["spot_interest_now"]) ** df_asset_cashflows["t_now"] 
            - 1
        )
        
        # Get the lagged forward rate
        df_asset_cashflows["lagged_forw_rate_between_coupons"] = df_asset_cashflows["forw_rate_between_coupons"].shift(1)
        
        # Coupon rate
        df_asset_cashflows["floating_coupon_rate"] = df_asset_cashflows["lagged_forw_rate_between_coupons"].replace(to_replace=0, method='ffill')

        df_asset_cashflows["floating_coupon_rate"] = np.where(
            df_asset_cashflows["months_after_next_coupon"] <= 0,
            effective_current_coupon_rate,
            df_asset_cashflows["floating_coupon_rate"],
        )

        # Adjust for Coupon Spread
        df_asset_cashflows["effective_coupon_rate"] = np.where(
            df_asset_cashflows["month"] == 0,
            0,
            ((1 + df_asset_cashflows["floating_coupon_rate"]) ** coupon_frequency + annual_coupon_spread) ** (1 / df_asset_cashflows["coupon_frequency"]) - 1
        )
 
        # Calculate cashflows
        df_asset_cashflows["coupon_payment"] = (
            df_asset_cashflows["indicator_coupon_payment"]
            * df_asset_cashflows["nominal"]
            * df_asset_cashflows["effective_coupon_rate"]
        )
        df_asset_cashflows["maturity_payment"] = (
            df_asset_cashflows["indicator_maturity_payment"]
            * df_asset_cashflows["nominal"]
        )
        df_asset_cashflows["cashflow"] = (
            df_asset_cashflows["coupon_payment"]
            + df_asset_cashflows["maturity_payment"]
        )

        df_asset_cashflows = df_asset_cashflows[df_asset_cashflows["months_to_maturity"] >= 0]

        return df_asset_cashflows

    def calc_ils_fixed(
        self, 
        df_cashflow_matrix: pd.DataFrame, 
        swap_term: int,
        annual_fixed_interest_rate: float,
        nominal: float,
        **kwargs: Any
    ) -> pd.DataFrame:
        """
        Calculate cashflows for a inflation linked swap fixed leg which is settled only at maturity i.e. no inswap_termediate coupon payments

        Parameters
        --------------
        df_cashflow_matrix : DataFrame
            A DataFrame containing a matrix which includes columns for indicator flags for coupon
            and maturity payments, nominal values, and spot interest rates.
        swap_term : int
            The term of the swap in years.
        annual_fixed_interest_rate : float
            The fixed interest rate agreed upon for the swap
        nominal : float
            The nominal or principal amount of the swap.

        Returns
        ----------
            DataFrame: Updated DataFrame with calculated cashflows.

        """

        df_asset_cashflows = df_cashflow_matrix.copy()

        # Calculate cashflows
        df_asset_cashflows["coupon_payment"] = 0
        
        maturity_payment = nominal * (1 + annual_fixed_interest_rate) ** swap_term
        df_asset_cashflows["maturity_payment"] = (
            df_asset_cashflows["indicator_maturity_payment"] * maturity_payment
        )

        df_asset_cashflows["cashflow"] = df_asset_cashflows["maturity_payment"]

        # Remove irrelevant rows
        df_asset_cashflows = df_asset_cashflows[df_asset_cashflows["months_to_maturity"] >= 0]

        return df_asset_cashflows

    def calc_ils_floating(
        self,
        df_cashflow_matrix: pd.DataFrame,
        projected_inflation_index: str,
        inflation_index_start: float,
        inflation_index_lag: int,
        **kwargs: Any
    ) -> pd.DataFrame:
        """
        Calculate cashflows for the floating leg of an inflation-linked swap

        Parameters
        --------------
        df_cashflow_matrix : DataFrame
            A DataFrame containing a matrix which includes columns for indicator flags for coupon
            and maturity payments, nominal values, and spot interest rates.
        inflation_index : str
            The name of the column in 'df_cashflow_matrix' that represents the inflation index to be used for 
            adjusting the cashflows.
        inflation_index_start : float
            The base value of the inflation index at the start of the swap's life, used to calculate the 
            indexation coefficient for adjusting the cashflows.
        inflation_index_lag : int
            The number of months by which the inflation data is lagged in the calculation, reflecting the 
            delay between the actual inflation period and the availability of the data.

        Returns
        ----------
            DataFrame: Updated DataFrame with calculated cashflows.
            
        """

        # Calculates the inflation index for asset cashflows by shifting the inflation index column based on the specified lag
        df_asset_cashflows = df_cashflow_matrix.copy()
        df_asset_cashflows["projected_inflation_index"] = df_asset_cashflows[projected_inflation_index]
        df_asset_cashflows["date_month"] = df_asset_cashflows["date_month"].dt.to_period("M").dt.to_timestamp()
        df_asset_cashflows.set_index("date_month", inplace=True)
        df_asset_cashflows["lagged_inflation_index"] = df_asset_cashflows["projected_inflation_index"].shift(int(inflation_index_lag)+1).fillna(method='backfill')

        # Calculate index coefficient
        df_asset_cashflows["inflation_index_start"] = inflation_index_start
        df_asset_cashflows["indexation_coefficient"] = df_asset_cashflows["lagged_inflation_index"] / df_asset_cashflows["inflation_index_start"]

        # Calculate cashflows
        df_asset_cashflows["coupon_payment"] = 0
        df_asset_cashflows["maturity_payment"] = (
            df_asset_cashflows["indicator_maturity_payment"]
            * df_asset_cashflows["nominal"]
            * df_asset_cashflows["indexation_coefficient"]
        )
        df_asset_cashflows["cashflow"] = df_asset_cashflows["maturity_payment"]

        df_asset_cashflows = df_asset_cashflows[df_asset_cashflows["months_to_maturity"] >= 0].reset_index()

        return df_asset_cashflows

    def calc_irs_fixed(
        self,
        df_cashflow_matrix: pd.DataFrame,
        coupon_frequency: int,
        annual_fixed_interest_rate: float,
        nominal: float,
        **kwargs: Any
    ) -> pd.DataFrame:

        """Calculate cashflows for a interest rate fixed leg 
        This is currently modelled exactly like a fixed interest rate bond

        Parameters
        ----------
        df_cashflow_matrix : DataFrame
            DataFrame containing a matrix including columns for indicator flags 
            for coupon and maturity payments, nominal values, and spot interest rates.
        coupon_frequency : int 
            Number of coupons per year.
        annual_fixed_interest_rate : float
            Fixed annual interest rate agreed.
        nominal : float
            Bond principal value.

        Returns
        -------
        df_asset_cashflows : DataFrame
            Updated DataFrame with calculated cashflows.

        """

        df_asset_cashflows = df_cashflow_matrix.copy()

        # Calculate effective coupon rate
        df_asset_cashflows["effective_coupon_rate"] = (
            0 if coupon_frequency == 0 else annual_fixed_interest_rate / coupon_frequency
        )

        # Calculate cashflows
        df_asset_cashflows["coupon_payment"] = (
            df_asset_cashflows["indicator_coupon_payment"]
            * df_asset_cashflows["effective_coupon_rate"]
            * nominal
        )

        df_asset_cashflows["maturity_payment"] = (
            df_asset_cashflows["indicator_maturity_payment"] * nominal
        )

        df_asset_cashflows["cashflow"] = (
            df_asset_cashflows["coupon_payment"]
            + df_asset_cashflows["maturity_payment"]
        )

        return df_asset_cashflows

    def calc_irs_floating(
        self,
        df_cashflow_matrix: pd.DataFrame,
        coupon_frequency: float,
        annual_floating_interest_rate: float,
        annual_coupon_spread: float,
        spot_interest: str,
        **kwargs: Any
    ) -> pd.DataFrame:
        
        """Calculate cashflows for a interest rate swap floating leg 
        This is currently modelled exactly like a floating rates bond
        
        Parameters
        ----------
            df_cashflow_matrix : pd.DataFrame
                DataFrame containing a matrix including columns for indicator flags for coupon and maturity payments, nominal values, and spot interest rates.
            coupon_frequency : float
                Number of coupons per year.
            annual_floating_interest_rate : float
                The current yield of the bond.
            annual_coupon_spread : float
                The spread added to the reference rate to deswap_termine the coupon rate.
            spot_interest : str
                The name of the column in `df_cashflow_matrix` that contains the spot 
                interest rate data to be used for calculating the coupons.

        Returns
        ----------
            DataFrame: Updated DataFrame with calculated cashflows.

        """
        df_asset_cashflows = df_cashflow_matrix.copy()
        months_between_coupons = 0 if coupon_frequency == 0 else 12 / coupon_frequency

        # Spot interest rate, now and at next coupon
        df_asset_cashflows["spot_interest_now"] = (
            df_asset_cashflows["indicator_coupon_payment"]
            * df_asset_cashflows[spot_interest]
        )

        df_asset_cashflows["spot_interest_next_coupon"] = (
            df_asset_cashflows["indicator_coupon_payment"]
            * df_asset_cashflows[spot_interest].shift(-int(months_between_coupons))
        )

        # Time (in years), now and at next coupon
        df_asset_cashflows["t_now"] = df_asset_cashflows["month"] / 12
        df_asset_cashflows["t_next_coupon"] = (df_asset_cashflows["month"] + months_between_coupons) / 12

        # Calculate forward rate between coupons
        df_asset_cashflows["forw_rate_between_coupons"] = (
            (1 + df_asset_cashflows["spot_interest_next_coupon"]) ** df_asset_cashflows["t_next_coupon"] / 
            (1 + df_asset_cashflows["spot_interest_now"]) ** df_asset_cashflows["t_now"] 
            - 1
        )

        # Get the lagged forward rate
        df_asset_cashflows["lagged_forw_rate_between_coupons"] = df_asset_cashflows["forw_rate_between_coupons"].shift(1)
        df_asset_cashflows["floating_coupon_rate"] = df_asset_cashflows["lagged_forw_rate_between_coupons"].replace(to_replace=0, method='ffill')

        # Adjust for Coupon Spread 
        df_asset_cashflows["effective_coupon_spread"] = 0 if coupon_frequency == 0 else annual_coupon_spread / coupon_frequency
        df_asset_cashflows["floating_coupon_rate_adjusted"] = df_asset_cashflows["floating_coupon_rate"] + df_asset_cashflows["effective_coupon_spread"]

        # Using adjusted current coupon rate between now and the next coupon date. 
        # From there use the floating_coupon_rate_adjusted
        effective_current_coupon_rate = (
            0
            if coupon_frequency == 0
            else (annual_floating_interest_rate + annual_coupon_spread) / coupon_frequency
        )
        
        df_asset_cashflows["effective_coupon_rate"] = np.where(
            df_asset_cashflows["month"] == 0,
            0,
            np.where(
                df_asset_cashflows["months_after_next_coupon"] <= 0,
                effective_current_coupon_rate,
                df_asset_cashflows["floating_coupon_rate_adjusted"],
            ),
        )

        # Calculate cashflows
        df_asset_cashflows["coupon_payment"] = (
            df_asset_cashflows["indicator_coupon_payment"]
            * df_asset_cashflows["nominal"]
            * df_asset_cashflows["effective_coupon_rate"]
        )
        df_asset_cashflows["maturity_payment"] = (
            df_asset_cashflows["indicator_maturity_payment"]
            * df_asset_cashflows["nominal"]
        )
        df_asset_cashflows["cashflow"] = (
            df_asset_cashflows["coupon_payment"]
            + df_asset_cashflows["maturity_payment"]
        )

        df_asset_cashflows = df_asset_cashflows[df_asset_cashflows["months_to_maturity"] >= 0]

        return df_asset_cashflows

    def calc_fx_forwards(
        self, 
        df_cashflow_matrix: pd.DataFrame, 
        exchange_rate: int,
        nominal_portfolio_currency: float,
        nominal_quotation_currency: float,
        market_value: float,
        annual_interest_rate: float,
        **kwargs: Any
    ) -> pd.DataFrame:
        """
        Calculate cashflows for a inflation linked swap fixed leg which is settled only at maturity i.e. no inswap_termediate coupon payments

        Parameters
        --------------
        df_cashflow_matrix : DataFrame
            A DataFrame containing a matrix which includes columns for indicator flags for coupon
            and maturity payments, nominal values, and spot interest rates.
        exchange_rate : int
            The term of the swap in years.
        nominal_quotation_currency : float
            The fixed interest rate agreed upon for the swap
        market_value : float
            The nominal or principal amount of the swap.

        Returns
        ----------
            DataFrame: Updated DataFrame with calculated cashflows.

        """

        df_asset_cashflows = df_cashflow_matrix.copy()

        # Calculate cashflows
        df_asset_cashflows["coupon_payment"] = (
            df_asset_cashflows["indicator_maturity_payment"]
            * df_asset_cashflows["nominal_portfolio_currency"]
            * ((1 + annual_interest_rate)**(df_asset_cashflows["month"]/12) - 1)
        )
        df_asset_cashflows["coupon_payment"] = 0
        
        maturity_payment = nominal_quotation_currency/exchange_rate
        df_asset_cashflows["maturity_payment"] = df_asset_cashflows["indicator_maturity_payment"] * maturity_payment
        df_asset_cashflows["cashflow"] = df_asset_cashflows["maturity_payment"] + df_asset_cashflows["coupon_payment"]
        df_asset_cashflows["nominal"] = df_asset_cashflows["nominal_portfolio_currency"]

        # Remove irrelevant rows
        df_asset_cashflows = df_asset_cashflows[df_asset_cashflows["months_to_maturity"] >= 0]

        return df_asset_cashflows