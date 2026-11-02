import numpy as np
import pandas as pd
import requests
import json
from functools import reduce
from datetime import datetime

from utilities import left_join

class SmithWilson:
    """
    Core SW class. All inputs in BPs
    External depedencies: None
    User inputs: None
    """

    def __init__(
        self,
        instrument: str,
        inputLiquidRates: pd.Series,
        CRA_bp: float,
        UFR_bp: float,
        nCoup: int,
        Tconv: int,
    ):
        self.instrument = instrument
        self.inputRates = inputLiquidRates
        self.CRA = CRA_bp / 10000.0
        self.UFR = UFR_bp / 10000.0
        self.nCoup = int(nCoup)
        self.Tconv = Tconv       
       
        self.alphamin = 0.05  
        self.tau = 1.0 / 10000.0
        self.precision = 6
        self.stepSize = 0.1
        self.nIter = 20.0
        self.yrsOut = 120

    def calcQ(self) -> pd.DataFrame:
        """calculate Q matrix (input rates cashflow matrix)"""

        dataInput = self.inputRates
        nCoup = self.nCoup
        instrument = self.instrument
        UFR = self.UFR
        CRA = self.CRA

        lnUFR = np.log(1 + UFR)  # omega

        nRates = int(len(dataInput))
        umax = int(max(dataInput.index))

        u = dataInput.index.values  # liquid tenors
        r = dataInput.values - CRA

        # Cashflow matrix Q
        Q = np.zeros((nRates, umax * nCoup))

        if instrument in ["Swap", "Bond"]:
            for i in range(nRates):
                for j in range(u[i] * nCoup):
                    Q[i, j] = np.exp(-lnUFR * (j + 1) / nCoup) * (r[i] / nCoup)
                Q[i, j] = np.exp(-lnUFR * (j + 1) / nCoup) * (1 + r[i] / nCoup)

        elif instrument == "Zero":
            for i in range(nRates):
                Q[i, (u[i] - 1)] = np.exp(-lnUFR * u[i]) * ((1 + r[i]) ** u[i])

        Q = pd.DataFrame(Q)
        Q.index = u
        Q.columns = range(1, (umax * nCoup) + 1)

        return Q

    def hh(self, z: float) -> float:
        """negative exponential"""
        return (z + np.exp(-z)) / 2.0

    def Hmat(self, u: float, v: float) -> float:
        """heart of Wilson function"""
        return self.hh(u + v) - self.hh(np.abs(u - v))

    def calcGAlpha(self, alpha: float, Q: pd.DataFrame, nCoup: int) -> dict:
        """optimal alpha and g(alpha)"""

        nRates = len(Q)
        umax = Q.index.max()
        tau = self.tau
        Tconv = self.Tconv

        h = np.zeros((umax * nCoup, umax * nCoup))
        for i in range(h.shape[0]):
            for j in range(h.shape[1]):
                h[i, j] = self.Hmat(alpha * (i + 1) / nCoup, alpha * (j + 1) / nCoup)

        h = pd.DataFrame(h)
        h.index = range(1, umax * nCoup + 1)
        h.columns = range(1, umax * nCoup + 1)

        temp1 = 1 - Q.sum(axis=1)

        b = np.matmul(np.linalg.inv(np.matmul(np.matmul(Q, h), np.transpose(Q))), temp1)
        gamma = np.matmul(np.transpose(Q), b)

        temp2 = (gamma * ((gamma.index.values) / nCoup)).sum()
        temp3 = (gamma * np.sinh(alpha * (gamma.index.values) / nCoup)).sum()
        kappa = (1 + alpha * temp2) / temp3

        o1 = alpha / np.abs(1 - kappa * np.exp(Tconv * alpha)) - tau
        o2 = gamma
        galpha = {"o1": o1, "o2": o2}

        return galpha

    def alphaScan(
        self, lastAlpha: float, Q: pd.DataFrame, stepSize: float, nCoup: int
    ) -> dict:
        """alpha iterative optimization"""

        for alpha in np.arange(
            lastAlpha + stepSize / 10.0 - stepSize, lastAlpha, stepSize / 10.0
        ):
            # print('alpha from alphascan: ', alpha)
            galphaOutput = self.calcGAlpha(alpha, Q, nCoup)
            if galphaOutput["o1"] <= 0:
                break

        alphascanoutput = {"o1": alpha, "o2": galphaOutput["o2"]}
        return alphascanoutput

    def calcOptimalAlpha(self, Q: pd.DataFrame, nCoup: int) -> dict[float, pd.Series]:
        """optimal alpha and gamma function"""

        alphamin = self.alphamin
        galphaOutput = self.calcGAlpha(alphamin, Q, 1)

        if galphaOutput["o1"] <= 0:  # alpha is already optimal
            alpha = alphamin  
            gamma = galphaOutput["o2"]
        else:  
            stepSize = 0.1  
            for alpha in np.arange(alphamin + stepSize, self.nIter, self.stepSize):
                tmpGAlpha = self.calcGAlpha(alpha, Q, nCoup)
                if tmpGAlpha["o1"] <= 0:
                    break
            precision = 6
            for i in range(1, precision):
                alfascanoutput = self.alphaScan(alpha, Q, stepSize, nCoup)
                alpha = alfascanoutput["o1"]
                stepSize = stepSize / 10.0

            gamma = alfascanoutput["o2"]
        self.optAlphaGamma = {"alpha": alpha, "gamma": gamma}
        return self.optAlphaGamma

    def calcSW(self) -> dict[pd.DataFrame, pd.DataFrame, pd.DataFrame, float]:
        """Smith-Wilson extrapolation"""

        dataInput = self.inputRates
        optAlphaGamma = self.optAlphaGamma
        UFR = self.UFR
        CRA = self.CRA
        instrument = self.instrument
        nCoup = self.nCoup
        yrsOut = self.yrsOut
        umax = dataInput.index.max()

        lnUFR = np.log(1 + UFR)
        alpha = optAlphaGamma["alpha"]
        gamma = optAlphaGamma["gamma"]

        h = np.zeros((yrsOut + 1, umax * nCoup))
        g = np.zeros((yrsOut + 1, umax * nCoup))

        precision = self.precision  # 6
        alpha = np.round(alpha, precision)

        for i in range(h.shape[0]):
            for j in range(h.shape[1]):
                h[i, j] = self.Hmat(alpha * i, alpha * (j + 1) / nCoup)
                if (j + 1) / nCoup > i:
                    g[i, j] = alpha * (
                        1 - np.exp(-alpha * (j + 1) / nCoup) * np.cosh(alpha * i)
                    )
                else:
                    g[i, j] = (
                        alpha * np.exp(-alpha * i) * np.sinh(alpha * (j + 1) / nCoup)
                    )

        # results from here 
        results = {}
        results["tempdiscount"] = np.matmul(h, gamma)
        results["tempintensity"] = np.matmul(g, gamma)
        results = pd.DataFrame(results)

        temp = ((1 - np.exp(-alpha * (gamma.index.values) / nCoup)) * gamma).sum()

        results["discount"] = np.exp(-lnUFR * results.index) * (
            1 + results["tempdiscount"]
        )
        results["discount"][0] = 1

        results["yldintensity"] = lnUFR - np.log(1 + results["tempdiscount"]) / (
            results.index
        )
        results["yldintensity"].iloc[0] = lnUFR - alpha * temp

        results["fwintensity"] = lnUFR - results["tempintensity"] / (
            1 + results["tempdiscount"]
        )
        results["fwintensity"][0] = results["yldintensity"][0]

        results["zeroac"] = np.where(
            results.index > 0, (1 / results["discount"]) ** (1 / results.index) - 1, 0
        )
        results["forwardac"] = results["discount"].shift(1) / results["discount"] - 1

        results["forwardcc"] = np.log(1 + results["forwardac"])
        results["zerocc"] = np.log(1 + results["zeroac"])

        results = results[
            [
                "discount",
                "yldintensity",
                "zeroac",
                "fwintensity",
                "forwardcc",
                "forwardac",
            ]
        ]
        self.resultsAll = {
            "h": pd.DataFrame(h),
            "g": pd.DataFrame(g),
            "results": results,
            "optimalAlpha": alpha,
        }
        return self.resultsAll

    def calcSWall(self):
        Q = self.calcQ()
        optAlpha = self.calcOptimalAlpha(Q, 1)
        tmpRes = self.calcSW()
        return tmpRes

# class AlternativeExtrapolation:

#     def __init__(
#         self,
#         df_liquid_rates
#     ) -> None:
        
#         self.df_liquid_rates = df_liquid_rates

#     def discPar2Fwd(
#         self,
#         sumDF:float, 
#         lastDF:float, 
#         parRate:float, 
#         fwdRate:float, 
#         TminK: int
#     ) -> float:
        
#         ''' discount rate for forwards '''

#         D1=sumDF*parRate
#         D2=0

#         for i in range(1, (TminK+1)):
#             D1+= parRate*lastDF / ((1+fwdRate)**i)
#             D2+= -i*parRate*lastDF / ((1+fwdRate)**(i+1))
        
#         D1+=lastDF / ((1+fwdRate)**TminK) -1
#         D2+=-TminK*lastDF/((1+fwdRate)**(TminK+1))

#         return {'Disc1':D1, 'Disc2': D2}

#     def fromParToFwd(
#         self,
#         df_liquid_rates
#     ):
#         """spot-forward conversion to calculate alternative term structure"""

#         parRates = df_liquid_rates["liquid_tenor_rate"]
#         maturities = list(df_liquid_rates.index)

#         maturities.insert(0, 0) 

#         nForwards = len(parRates)  # o
#         fwds = np.zeros(nForwards)

#         span = 120  # yrs out
#         maxRuns = 20
#         maxError = 10**-10  # 0.0000000001

#         tmpDF = pd.DataFrame(
#             index=range(0, span + 1), 
#             columns=["DF", "sumDF", "forwardsSpan"]
#         )

#         tmpDF["DF"].loc[0] = 1  # discount factor
#         tmpDF["sumDF"].loc[0] = 0  # cumulative discount factor

#         for j in range(1, nForwards + 1):
#             fwd = 0
#             dVal = self.discPar2Fwd(
#                 sumDF=tmpDF["sumDF"].loc[maturities[j - 1]],
#                 lastDF=tmpDF["DF"].loc[maturities[j - 1]],
#                 parRate=parRates.iloc[j - 1],
#                 fwdRate=fwd,
#                 TminK=maturities[j] - maturities[j - 1],
#             )

#             k = 0
#             while (not (np.abs(dVal["Disc1"]) < maxError)) and (k <= maxRuns):
#                 fwd += -dVal["Disc1"] / dVal["Disc2"]
#                 dVal = self.discPar2Fwd(
#                     sumDF=tmpDF["sumDF"].loc[maturities[j - 1]],
#                     lastDF=tmpDF["DF"].loc[maturities[j - 1]],
#                     parRate=parRates.iloc[j - 1],
#                     fwdRate=fwd,
#                     TminK=maturities[j] - maturities[j - 1],
#                 )

#                 k += 1

#             fwds[j - 1] = fwd

#             for i in range(maturities[j - 1] + 1, maturities[j] + 1):
#                 tmpDF["forwardsSpan"].loc[i] = fwd
#                 tmpDF["DF"].loc[i] = tmpDF["DF"].loc[i - 1] / (
#                     1 + tmpDF["forwardsSpan"].loc[i]
#                 )
#                 tmpDF["sumDF"].loc[i] = tmpDF["sumDF"].loc[i - 1] + tmpDF["DF"].loc[i]

#         for i in range(maturities[nForwards] + 1, span + 1):
#             tmpDF["forwardsSpan"].loc[i] = tmpDF["forwardsSpan"].loc[i - 1]
#             tmpDF["DF"].loc[i] = tmpDF["DF"].loc[i - 1] / (
#                 1 + tmpDF["forwardsSpan"].loc[i]
#             )
#             tmpDF["sumDF"].loc[i] = tmpDF["sumDF"].loc[i - 1] + tmpDF["DF"].loc[i]

#         tmpDF["tsAlt"] = np.nan
#         # tmpDF["tsAlt"].loc[1] = tmpDF["forwardsSpan"].loc[1]
        
#         # for i in range(2, len(tmpDF)):
#         #     tmpDF["tsAlt"].loc[i] = (
#         #         ((1 + float(tmpDF["tsAlt"].loc[i - 1])) ** (i - 1))
#         #         * (1 + float(tmpDF["forwardsSpan"].loc[i]))
#         #     ) ** (1 / i) - 1
#         tmpDF.loc[1, "tsAlt"] = tmpDF.loc[1, "forwardsSpan"]
#         for i in range(2, len(tmpDF)):
#             tmpDF.loc[i, "tsAlt"] = (
#                 ((1 + float(tmpDF.loc[i - 1, "tsAlt"])) ** (i - 1))
#                 * (1 + float(tmpDF.loc[i, "forwardsSpan"]))
#             ) ** (1 / i) - 1

#         return tmpDF   
    
class MonthlyConversion:

    def __init__(self) -> None:
        
        pass

    def convert_to_monthly(
        self,
        df_scenario_annual_rates: pd.DataFrame,
        scaling_exponent=-0.04,
        annual_rate_columns = ["spot_interest", "spot_interest01", "scr_interest_down", "scr_interest_up"]
    ):
        
        ## Get Scenario Parameters
        scenario_parameters = df_scenario_annual_rates.iloc[0].to_dict()
        scenario = scenario_parameters['scenario']

        lst = [
            'scenario',
            'rates',
            'shock',
            'shock_type',
            'input_rates',
            'instrument',
            'coupon_frequency',
            'convergence_years',
            'cra_bp',
            'ufr_bp',
            'va_bp',
            'shock_bp'
        ]

        # scenario_parameters = {k:scenario_parameters[k] if k in scenario_parameters.keys() else None for k in lst}

        ## Convert columns to monthly
        res = []
        for annual_rate_column in annual_rate_columns:

            df_annual_rates = df_scenario_annual_rates.copy()
            df_annual_rates = df_annual_rates.set_index(['year']).sort_index()
            df_annual_rates['rate'] = df_annual_rates[annual_rate_column] 
            df_annual_rates['lagged_rate'] = df_annual_rates['rate'].shift(-1)
            df_monthly_rates = df_annual_rates.loc[df_annual_rates.index.repeat(12)]
            df_monthly_rates['year'] = df_monthly_rates.index
            df_monthly_rates['month'] = range(1, len(df_monthly_rates)+1)
            df_monthly_rates['month2'] = (df_monthly_rates['month'] % 12).replace(0, 12)
            df_monthly_rates['ratio']=(
                (np.exp(scaling_exponent*df_monthly_rates['month2']/12)-np.exp(scaling_exponent))
                / (1-np.exp(scaling_exponent))
            )

            df_monthly_rates.index=range(len(df_monthly_rates))
            df_monthly_rates['rate'] = df_monthly_rates[annual_rate_column] 
            df_monthly_rates['discount_factor']=(1+df_monthly_rates['rate'])**(-df_monthly_rates['year'])
            df_monthly_rates['lagged_discount_factor']=(1+df_monthly_rates['lagged_rate'])**(-(df_monthly_rates['year']+1))

            df_monthly_rates['ma_discount_factor'] = (
                df_monthly_rates['ratio'] * df_monthly_rates['discount_factor']
                + (1 - df_monthly_rates['ratio']) * df_monthly_rates['lagged_discount_factor']
            )
            df_monthly_rates['lagged_ma_discount_factor']=df_monthly_rates['ma_discount_factor'].shift(1)
            df_monthly_rates['lagged_ma_discount_factor'] = np.where(
                df_monthly_rates.index == 0,
                1,
                df_monthly_rates['lagged_ma_discount_factor']
            )
            df_monthly_rates.dropna(subset='lagged_ma_discount_factor', inplace=True)
            df_monthly_rates[annual_rate_column]=df_monthly_rates['lagged_ma_discount_factor']**(-1/(df_monthly_rates.index/12))-1

            res.append(df_monthly_rates[annual_rate_column])   

        df_scenario_monthly_rates = reduce(lambda left, right: pd.merge(left, right, left_index=True, right_index=True), res)
        df_scenario_monthly_rates = pd.DataFrame(df_scenario_monthly_rates)
        df_scenario_monthly_rates['month'] = df_scenario_monthly_rates.index
        df_scenario_monthly_rates['scenario'] = scenario

        ## Add scenario meta data
        df_scenario_monthly_rates = left_join(
            left_df=df_scenario_monthly_rates,
            right_df=pd.DataFrame(scenario_parameters, index=['scenario']),
            left_on=['scenario'],
            right_on=['scenario']
        )

        return df_scenario_monthly_rates