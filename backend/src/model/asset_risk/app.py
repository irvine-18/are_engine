# import os
# import re
# import time
# import tempfile
# import multiprocessing
# import pandas as pd
# import numpy as np
# from pprint import pprint
# from datetime import datetime

# from asset_risk.asset_model import Asset
# from utilities import export_dict_to_xlsx, left_join

# from settings import Settings

# class AssetRiskData:

#     def __init__(
#         self,
#         valuation_date,
#         file_asset_data,
#         file_economic_data,
#         settings
#     ):
#         # Files
#         self.file_asset_data = file_asset_data
#         self.file_economic_data = file_economic_data

#         # Valuation Date
#         self.valuation_date = valuation_date

#         # Settings
#         self.settings = settings

#         # Asset Risk Data
#         self.dict_asset_data = None
#         self.dict_economic_data = None

#     def get_asset_data(
#         self,
#         valuation_date,
#         file_asset_data
#     ):

#         dict_asset_data = pd.read_excel(
#             file_asset_data,
#             sheet_name=None
#         )

#         self.dict_asset_data = dict_asset_data

#         return dict_asset_data

#     def get_economic_data(
#         self, 
#         valuation_date, 
#         file_economic_data
#     ): 

#         dict_economic_data = pd.read_excel(
#             file_economic_data, 
#             sheet_name=None, 
#             parse_dates=True
#         )

#         self.dict_economic_data = dict_economic_data
        
#         return dict_economic_data

#     def get_all_data(
#         self
#     ):
        
#         if self.file_asset_data is not None:
#             self.get_asset_data(
#                 valuation_date=self.valuation_date,
#                 file_asset_data=self.file_asset_data
#             )

#         if self.file_economic_data is not None:
#             self.get_economic_data(
#                 valuation_date=self.valuation_date,
#                 file_economic_data=self.file_economic_data
#             )

# class AssetRiskEngine:

#     def __init__(
#         self,
#         valuation_date,
#         dict_asset_data,
#         dict_economic_data,
#         settings,
#         azure_storage_service=None
#     ):

#         self.valuation_date = valuation_date

#         # Settings
#         self.df_modelling_properties=settings.parameters["modelling_properties"]
#         self.df_cqs_rating_mapping=settings.parameters["cqs_rating_mapping"]
#         self.df_spread_risk_coefficients=settings.parameters["spread_risk_coefficients"]

#         # Asset Data
#         self.dict_asset_data = dict_asset_data

#          # Economic Data
#         self.df_rates= dict_economic_data["rates"]
#         self.df_eiopa_equity_adjustment = dict_economic_data["eiopa_equity_adjustment"]

#         # Azure Storage
#         self.azure_storage_service = azure_storage_service

#     def run_asset_sensitivities(
#         self,
#         asset_properties,
#         scenarios=None
#     ):

#         """
#         Calculate SCR risk for a single asset or position.

#         Args:
#             asset_properties (dict): dictionary containing asset properties.
#             scenarios (list): List of scenarios to run

#         Returns:
#             Asset: An Asset class with all with the calculated properties and fields.
#         """

#         print(f"Running {asset_properties['portfolio']} - {asset_properties['modelling_class']}: {asset_properties['position_id']}....")

#         asset = Asset(
#             asset_properties=asset_properties,
#             valuation_date=self.valuation_date,
#             df_rates=self.df_rates,
#             df_eiopa_equity_adjustment=self.df_eiopa_equity_adjustment,
#             df_modelling_properties=self.df_modelling_properties,
#             df_cqs_rating_mapping=self.df_cqs_rating_mapping,
#             df_spread_risk_coefficients=self.df_spread_risk_coefficients
#         )

#         asset.calc_sensitivities_scr_risk(scenarios=scenarios)

#         return asset

#     def run_modelling_class_sensitivities(
#         self,
#         df_modelling_class,
#         scenarios=None
#     ):

#         """
#         Calculate SCR risk for a modelling_class of assets.

#         Args:
#             df_modelling_class (pd.DataFrame): DataFrame containing asset properties of a particular modelling class.
#             scenarios (list): List of scenarios to run

#         Returns:
#             dict: A dictionary containing modelling_class cashflows and SCR risk data.
#         """
#         cashflows = []
#         market_values = []
#         scr_risk = []

#         dict_asset_data = df_modelling_class.to_dict(orient="records")

#         for i, asset_properties in enumerate(dict_asset_data):
            
#             # Calculate asset risk sensitivities for each asset
#             asset = self.run_asset_sensitivities(
#                 asset_properties=asset_properties, 
#                 scenarios=scenarios
#             )

#             # Append cashflow data
#             if asset.df_asset_cashflows is not None:
#                 cashflows.append(asset.df_asset_cashflows) 

#             # Append cashflow data
#             if asset.df_market_values is not None:
#                 market_values.append(asset.df_market_values) 

#             # Append scr risk to result list
#             scr_risk.append(asset.df_scr_risk)

#         # Join into one df
#         df_modelling_class_cashflows = pd.concat(cashflows) if len(cashflows) > 0 else None
#         df_modelling_market_values= pd.concat(market_values) if len(market_values) > 0 else None
#         df_modelling_class_scr_risk = pd.concat(scr_risk) if len(scr_risk) > 0 else None
        
#         modelling_class_data = {    
#             'cashflows': df_modelling_class_cashflows,
#             'market_values': df_modelling_market_values,
#             'scr_risk': df_modelling_class_scr_risk
#         }

#         return modelling_class_data

#     def run_all_assets_sensitivities(
#         self,
#         scenarios=None
#     ):
#         """
#         Calculate SCR risk for all assets in a linear manner.

#         Args:
#             scenarios (list): List of scenarios to run

#         Returns:
#             dict: A dictionary containing modelling_class cashflows and SCR risk data for all assets.
#         """
        
#         dict_asset_data = self.dict_asset_data.copy()

#         start_time = time.time()
#         modelling_class_cashflows = []
#         modelling_class_market_values = []
#         modelling_class_scr_risk = []

#         for i, modelling_class in enumerate(dict_asset_data):
#             print("-" * 80)
#             print(f"Processing Asset: {modelling_class}")
#             print("-" * 80)

#             df_modelling_class = dict_asset_data[modelling_class]
            
#             modelling_class_results = self.run_modelling_class_sensitivities(
#                 df_modelling_class=df_modelling_class, 
#                 scenarios=scenarios
#             )

#             cashflows = modelling_class_results['cashflows']
#             market_values = modelling_class_results['market_values']
#             scr_risk = modelling_class_results['scr_risk']

#             if cashflows is not None:
#                 modelling_class_cashflows.append(cashflows)
#             if market_values is not None:
#                 modelling_class_market_values.append(market_values)
#             if scr_risk is not None:
#                 modelling_class_scr_risk.append(scr_risk)
           

#         df_cashflows = pd.concat(modelling_class_cashflows) if len(modelling_class_cashflows) > 0 else None
#         df_market_values = pd.concat(modelling_class_market_values) if len(modelling_class_market_values) > 0 else None
#         df_scr_risk = pd.concat(modelling_class_scr_risk) if len(modelling_class_scr_risk) > 0 else None

#         all_results = {    
#             'cashflows': df_cashflows,
#             'market_values': df_market_values,
#             'scr_risk': df_scr_risk
#         }

#         print(f"Scenario calculation completed in: {(time.time() - start_time) / 60:.2f} minutes")

#         self.asset_risk_results = all_results

#         return all_results

#     def export_to_local(
#         self,
#         file_path=None
#     ):

#         file_path = file_path or f"./Asset Risk Data - {self.valuation_date.strftime('%Y-%m-%d')}.xlsx"  

#         export_dict_to_xlsx(
#             data_dict=self.asset_risk_results,
#             file_path=file_path
#         )

#     def export_to_azure(
#         self,
#         file_name=None,
#         blob_folder=None,
#         container = "ace"
#     ):
#         file_name = file_name or f"./Asset Risk Data - {self.valuation_date.strftime('%Y-%m-%d')}.xlsx"  
#         blob_folder = blob_folder or self.valuation_date.strftime("%Y-%m-%d") + "/asset_risk_engine/output"

#         with tempfile.TemporaryDirectory() as tmpdirname:

#             file_path = os.path.join(tmpdirname, file_name)

#             export_dict_to_xlsx(
#                 data_dict=self.asset_risk_results,
#                 file_path=file_path
#             )

#             response = self.azure_storage_service.upload_blob(
#                 container=container,
#                 file_path=file_path,
#                 blob=file_name,
#                 blob_folder=blob_folder,
#                 overwrite=True
#             )

# class ReportingOutput:

#     def __init__(
#         self,
#         valuation_date,
#         df_cashflows,
#         df_market_values,
#         df_scr_risk,
#         azure_storage_service=None
#     ):
#         # Valuation Date
#         self.valuation_date=valuation_date

#         # Market Risk Output
#         self.df_cashflows=df_cashflows
#         self.df_scr_risk=df_scr_risk
#         self.df_market_values=df_market_values

#         # Azure Storage
#         self.azure_storage_service = azure_storage_service

#         self.finance_results = None

#     def get_key_asset_info(
#         self,
#         df_scr_risk
#     ):
#         # Aggregate cashflows by portfolio, asset, scenario, bucket
#         aggregation_columns = [
#             "valuation_date",
#             "scenario",
#             "portfolio",
#             "position_id",
#             "asset_id", 
#             "internal_class",
#             "storage_class",
#             "fixed_or_floating",
#             "modelling_class",           
#             "counterparty",
#             "country_of_issuer"
#         ]

#         aggregation_functions = {
#             "z_spread": "sum",
#             "nominal": "sum",
#             "market_value": "sum",
#             "scr_interest_down_risk": "sum",
#             "scr_interest_up_risk": "sum",
#             "scr_spread_risk": "sum",
#             "scr_equity_risk": "sum",
#             # "scr_default_risk": "sum"
#         }

#         df_scr_risk = df_scr_risk.copy().fillna(0)

#         df_key_asset_info = df_scr_risk.pivot_table(
#             index=aggregation_columns,
#             aggfunc=aggregation_functions,
#         ).reset_index()

#         columns={
#             'position_id': 'Portfolio ID',
#             'asset_id': 'ID/ISIN',
#             'internal_class': 'Internal Class',
#             'modelling_class': 'Modelling Class',
#             'storage_class': 'Storage Class',
#             'fixed_or_floating': 'Fixed or Floating',
#             'counterparty': 'Counterparty',
#             'country_of_issuer': 'Country',
#             'z_spread': 'Z-Spread',
#             'nominal': 'Nominal',
#             'market_value': 'Base Market Value',
#             'scr_interest_down_risk': 'SCR Interest - Down',
#             'scr_interest_up_risk': 'SCR Interest - Up',
#             'scr_spread_risk': 'SCR Spread',
#             'scr_equity_risk': 'SCR Equity',
#             # 'scr_default_risk': 'SCR Default'
#         }

#         df_key_asset_info = df_key_asset_info.rename(
#             columns=columns
#         )

#         df_key_asset_info = df_key_asset_info[['portfolio', 'scenario'] + [columns[v] for v in columns.keys()]]

#         return df_key_asset_info

#     def get_monthly_cashflows(
#         self,
#         df_cashflows
#     ):
#         # Aggregate cashflows by portfolio, asset, scenario, bucket
#         aggregation_columns = [
#             "portfolio",
#             "scenario",
#             "shock",
#             "month",
#             "date_month", 
#         ]

#         aggregation_functions = {
#             "discounted_cashflow": "sum"
#         }

#         df_cashflows = df_cashflows.copy()[df_cashflows['shock'] == 'spot_interest'].fillna(0)

#         df_cashflows = df_cashflows.pivot_table(
#             index=aggregation_columns,
#             columns=["asset_id"],
#             aggfunc=aggregation_functions,
#             values=['discounted_cashflow'],
#             fill_value=0,
#             margins=True,
#             margins_name='Total'
#         )['discounted_cashflow'].reset_index()

#         columns={
#             'month': 'Month',
#             'date_month': 'Date',
#             'total': 'Total'
#         }

#         df_cashflows = df_cashflows.rename(
#             columns=columns
#         )

#         return df_cashflows
    
#     def get_bucket_summary(
#         self,
#         df_market_values,
#         type
#     ):
#         # Aggregate cashflows by portfolio, asset, scenario, bucket
#         aggregation_columns = [
#             "portfolio",
#             "scenario",
#             "bucket2",
#         ]

#         aggregation_functions = {
#             type: "sum"
#         }

#         df_bucket_summary = df_market_values.copy().fillna(0)

#         df_bucket_summary = df_bucket_summary.pivot_table(
#             index=aggregation_columns,
#             columns=['storage_class'],
#             aggfunc=aggregation_functions,
#             values=[type],
#             margins=True,
#             fill_value=0,
#             margins_name="All Assets"
#         )[type].reset_index()

#         columns={
#             'bucket2': 'Bucket'
#         }

#         df_bucket_summary = df_bucket_summary.rename(
#             columns=columns
#         )

#         return df_bucket_summary
    
#     def get_bucket_analysis(
#         self,
#         df_market_values,
#         type
#     ):
#         # Aggregate cashflows by portfolio, asset, scenario, bucket
#         aggregation_columns = [
#             "portfolio",
#             "asset_id",
#             "scenario"
#         ]

#         aggregation_functions = {
#             type: "sum"
#         }

#         df_bucket_analysis = df_market_values.copy().fillna(0)

#         df_bucket_analysis = df_bucket_analysis.pivot_table(
#             index=aggregation_columns,
#             columns=['bucket1'],
#             aggfunc=aggregation_functions,
#             values=[type],
#             margins=True,
#             fill_value=0,
#             margins_name="Total"
#         )[type].reset_index()

#         columns={
#             'asset_id': 'Asset ID'
#         }

#         df_bucket_analysis = df_bucket_analysis.rename(
#             columns=columns
#         )

#         df_bucket_analysis = df_bucket_analysis[df_bucket_analysis['Total'] != 0]

#         return df_bucket_analysis
    
#     def get_finance_output(
#         self
#     ):
        
#         df_key_asset_info= self.get_key_asset_info(df_scr_risk=self.df_scr_risk)
#         df_monthly_cashflows= self.get_monthly_cashflows(df_cashflows=self.df_cashflows)
#         df_bucket_summary_ir01= self.get_bucket_summary(df_market_values=self.df_market_values, type='ir01')
#         df_bucket_summary_inf01= self.get_bucket_summary(df_market_values=self.df_market_values, type='inf01')
#         df_bucket_analysis_ir01= self.get_bucket_analysis(df_market_values=self.df_market_values, type='ir01')
#         df_bucket_analysis_inf01= self.get_bucket_analysis(df_market_values=self.df_market_values, type='inf01')

#         finance_results = {}

#         for portfolio in ['LTV', 'LTU']:

#             for scenario in df_key_asset_info['scenario'].unique():

#                 df_key_asset_info_ = df_key_asset_info.copy()[
#                     (df_key_asset_info['portfolio']==portfolio)
#                     & (df_key_asset_info['scenario']==scenario)
#                 ].drop(columns=['portfolio', 'scenario'])

#                 df_monthly_cashflows_ = df_monthly_cashflows.copy()[
#                     (df_monthly_cashflows['portfolio']==portfolio)
#                     & (df_monthly_cashflows['scenario']==scenario)
#                 ].drop(columns=['portfolio', 'scenario', 'shock'])


#                 df_bucket_summary_ir01_ = df_bucket_summary_ir01.copy()[
#                     (df_bucket_summary_ir01['portfolio']==portfolio)
#                     & (df_bucket_summary_ir01['scenario']==scenario)
#                 ].drop(columns=['portfolio', 'scenario'])

#                 df_bucket_summary_inf01_ = df_bucket_summary_inf01.copy()[
#                     (df_bucket_summary_inf01['portfolio']==portfolio)
#                     & (df_bucket_summary_inf01['scenario']==scenario)
#                 ].drop(columns=['portfolio', 'scenario'])

#                 df_bucket_analysis_ir01_ = df_bucket_analysis_ir01.copy()[
#                     (df_bucket_analysis_ir01['portfolio']==portfolio)
#                     & (df_bucket_analysis_ir01['scenario']==scenario)
#                 ].drop(columns=['portfolio', 'scenario'])

#                 df_bucket_analysis_inf01_ = df_bucket_analysis_inf01.copy()[
#                     (df_bucket_analysis_inf01['portfolio']==portfolio)
#                     & (df_bucket_analysis_inf01['scenario']==scenario)
#                 ].drop(columns=['portfolio', 'scenario'])

#                 work_book = {}

#                 work_book['Valuation Date'] = pd.DataFrame({'Valuation Date': self.valuation_date}, index=['valuation_date'])
#                 work_book['Run Date'] = pd.DataFrame({'Valuation Date': datetime.today()}, index=['run_date'])
#                 work_book['Key Asset Information'] = df_key_asset_info_
#                 work_book['Cashflows (M)'] = df_monthly_cashflows_
#                 work_book['Bucket Summary (IR01)'] = df_bucket_summary_ir01_
#                 work_book['Bucket Analysis (IR01)'] = df_bucket_analysis_ir01_
#                 work_book['Bucket Summary (INF01)'] = df_bucket_summary_inf01_
#                 work_book['Bucket Analysis (INF01)'] = df_bucket_analysis_inf01_

#                 finance_results[f"{portfolio} ({scenario}) - {self.valuation_date.strftime('%Y-%m-%d')}.xlsx"] = work_book

#         self.finance_results = finance_results

#         return finance_results

#     def export_results_to_local(
#         self,
#         folder='./',
#         finance_results=None
#     ):
        
#         finance_results = self.finance_results if finance_results is None else finance_results

#         for work_book in finance_results.keys():
            
#             export_dict_to_xlsx(
#                 data_dict = finance_results[work_book],
#                 file_path = os.path.join(folder, work_book)
#             )  

#         print("Done Exporting")

# class AssetDataChecks:

#     def __init__(
#         self,
#         file_assets_current,
#         file_assets_previous,
#         file_assets_raw_data
#     ):
#         self.file_assets_current=file_assets_current
#         self.file_assets_previous=file_assets_previous
#         self.file_assets_raw_data=file_assets_raw_data

#         self.df_assets_current=None
#         self.df_assets_previous=None
#         self.df_position_list=None

#         self.dict_differences_with_prev = None

#     def load_data(
#         self
#     ):

#         assets_current = pd.read_excel(self.file_assets_current, sheet_name=None)
#         df_assets_current = pd.concat(assets_current).reset_index(drop=True)
#         self.df_assets_current = df_assets_current

#         assets_previous = pd.read_excel(self.file_assets_previous, sheet_name=None)
#         df_assets_previous = pd.concat(assets_previous).reset_index(drop=True)
#         self.df_assets_previous = df_assets_previous

#         assets_raw_data = pd.read_excel(self.file_assets_raw_data, sheet_name=None)
#         df_position_list = assets_raw_data['position_list']
#         self.df_position_list = df_position_list
        
#     def get_field_differences(
#         self,
#         df_comparison,
#         field,
#         delta_method,
#         modelling_classes
#     ):
#         df = df_comparison[df_comparison['field']==field]

#         if modelling_classes is not None:
#             df = df_comparison[df_comparison['field'].isin(modelling_classes)]

#         df_pivot = pd.pivot_table(
#             df, 
#             values=['value'], 
#             index=['position_id', 'portfolio', 'asset_id'],
#             columns=['valuation_date'],
#             aggfunc="max"
#         )['value'].reset_index()

#         valuation_dates = df_comparison['valuation_date'].unique()
#         valuation_dates.sort()
#         current_valuation_date = valuation_dates[1]
#         previous_valuation_date = valuation_dates[0]

#         if delta_method == 'numeric':
#             df_pivot['delta'] = df_pivot[current_valuation_date] - df_pivot[previous_valuation_date]
#             df_pivot['delta_perc']  = df_pivot['delta'] / df_pivot[previous_valuation_date].replace(0, np.nan) 
#         elif delta_method == 'date':
#             df_pivot['delta'] = df_pivot[current_valuation_date] - df_pivot[previous_valuation_date]
#         elif delta_method == 'integer':
#             df_pivot['delta'] = df_pivot[current_valuation_date] - df_pivot[previous_valuation_date]
#         elif delta_method == 'bool':
#             df_pivot['delta'] = df_pivot[current_valuation_date] == df_pivot[previous_valuation_date]

#         df_pivot['abs_delta'] = df_pivot['delta'].abs()

#         df_pivot = df_pivot.sort_values(by=['abs_delta'], ascending=False)

#         return df_pivot

#     def get_differences_with_prev(
#         self,
#         df_assets_current,
#         df_assets_previous
#     ):
        
#         df_assets = pd.concat([df_assets_current, df_assets_previous])
            
#         value_vars = {
#             'nominal': {
#                 'delta_method': 'numeric',
#                 'modelling_classes': None,
#             },
#             'market_value': {
#                 'delta_method': 'numeric',
#                 'modelling_classes': None,
#             },
#             'maturity_date': {
#                 'delta_method': 'date',
#                 'modelling_classes': None,
#             },
#             'next_coupon_date': {
#                 'delta_method': 'date',
#                 'modelling_classes': None,
#             },
#             'coupon_frequency': {
#                 'delta_method': 'integer',
#                 'modelling_classes': None,
#             },
#             'annual_fixed_coupon_rate': {
#                 'delta_method': 'numeric',
#                 'modelling_classes': None,
#             },
#             'annual_nominal_coupon_rate': {
#                 'delta_method': 'numeric',
#                 'modelling_classes': None,
#             },
#             'annual_floating_coupon_rate': {
#                 'delta_method': 'numeric',
#                 'modelling_classes': None,
#             },
#             'annual_coupon_spread': {
#                 'delta_method': 'numeric',
#                 'modelling_classes': None
#             },
#             'annual_floating_interest_rate': {
#                 'delta_method': 'numeric',
#                 'modelling_classes': None,
#             },
#             'annual_interest_rate': {
#                 'delta_method': 'numeric',
#                 'modelling_classes': None,
#             },
#             'current_indexation_coefficient': {
#                 'delta_method': 'numeric',
#                 'modelling_classes': None,
#             },
#             'first_call_date': {
#                 'delta_method': 'date',
#                 'modelling_classes': None,
#             },
#             'modified_duration': {
#                 'delta_method': 'integer',
#                 'modelling_classes': None,
#             },
#             'storage_class': {
#                 'delta_method': 'bool',
#                 'modelling_classes': None,
#             },
#             'internal_class': {
#                 'delta_method': 'bool',
#                 'modelling_classes': None,
#             },
#             'modelling_class': {
#                 'delta_method': 'bool',
#                 'modelling_classes': None,
#             },
#             'fixed_or_floating': {
#                 'delta_method': 'bool',
#                 'modelling_classes': None,
#             },
#             'counterparty': {
#                 'delta_method': 'bool',
#                 'modelling_classes': None,
#             },
#             'country_of_issuer': {
#                 'delta_method': 'bool',
#                 'modelling_classes': None,
#             },
#             'management_style': {
#                 'delta_method': 'bool',
#                 'modelling_classes': None,
#             },
#             'rating': {
#                 'delta_method': 'bool',
#                 'modelling_classes': None,
#             },
#             'quotation_currency': {
#                 'delta_method': 'bool',
#                 'modelling_classes': None,
#             },
#             'exchange_rate': {
#                 'delta_method': 'bool',
#                 'modelling_classes': None,
#             },
#             'receiver_leg': {
#                 'delta_method': 'bool',
#                 'modelling_classes': None,
#             },
#             'trade_effective_date': {
#                 'delta_method': 'bool',
#                 'modelling_classes': None,
#             },
#             'swap_term': {
#                 'delta_method': 'bool',
#                 'modelling_classes': None,
#             },
#             'annual_fixed_interest_rate': {
#                 'delta_method': 'bool',
#                 'modelling_classes': None,
#             },
#             'inflation_index': {
#                 'delta_method': 'bool',
#                 'modelling_classes': None,
#             },
#             'inflation_index_start': {
#                 'delta_method': 'numeric',
#                 'modelling_classes': None,
#             },
#             'inflation_index_lag': {
#                 'delta_method': 'numeric',
#                 'modelling_classes': None,
#             },
#             'domestic_or_foreign': {
#                 'delta_method': 'bool',
#                 'modelling_classes': None,
#             },
#             'exchange_rate_start': {
#                 'delta_method': 'numeric',
#                 'modelling_classes': None,
#             },
#             'nominal_quotation_currency': {
#                 'delta_method': 'numeric',
#                 'modelling_classes': None,
#             },
#             'nominal_portfolio_currency': {
#                 'delta_method': 'numeric',
#                 'modelling_classes': None,
#             },
#             'equity_type': {
#                 'delta_method': 'bool',
#                 'modelling_classes': None,
#             },
#             'cash': {
#                 'delta_method': 'numeric',
#                 'modelling_classes': None,
#             },
#             'construction_deposits': {
#                 'delta_method': 'numeric',
#                 'modelling_classes': None,
#             },
#         }

#         df_comparison = pd.melt(
#             frame=df_assets,
#             id_vars=['position_id', 'portfolio', 'asset_id', 'valuation_date'],
#             value_vars=value_vars,
#             var_name='field',
#             value_name='value'
#         )

#         df_comparison['valuation_date'] = df_comparison['valuation_date'].dt.strftime(date_format='%Y-%m-%d')

#         results = {}

#         for field in value_vars.keys():
#             delta_method = value_vars[field]['delta_method']
#             modelling_classes = value_vars[field]['modelling_classes']

#             df = self.get_field_differences(
#                 df_comparison=df_comparison,
#                 field=field,
#                 delta_method=delta_method,
#                 modelling_classes=modelling_classes
#             )

#             results[field] = df

#         self.dict_differences_with_prev = results

#         return results

#     def get_differences_with_position_list(
#         df_assets_current, 
#         df_position_list
#     ): 
#         pass

#     def get_transctions_recon(
#         df_assets_current, 
#         df_assets_previous, 
#         df_position_list
#     ): 
#         pass

#     def asset_data_checks(
#         self
#     ):
        
#         self.load_data()

#         dict_differences_with_prev = self.get_differences_with_prev(
#             df_assets_current=self.df_assets_current, 
#             df_assets_previous=self.df_assets_previous
#         )

# class AssetRiskEngineValidation:

#     def __init__(
#         self,
#         file_ace_results,
#         files_r1_output,
#         file_shadow_model_results,
#         file_assigned_asset_classes
#     ):
#         self.file_ace_results = file_ace_results
#         self.files_r1_output = files_r1_output
#         self.file_shadow_model_results = file_shadow_model_results
#         self.file_assigned_asset_classes = file_assigned_asset_classes

#         self.df_ace_key_assets = None
#         self.df_r1_key_assets = None
#         self.df_shadow_model_key_assets = None

#         self.df_comparison = None

#     def get_ace_sensitivities(
#         self,
#         file_ace_results
#     ):

#         df_ace_key_assets = pd.read_excel(
#             file_ace_results, 
#             sheet_name="scr_risk"
#         )

#         df_ace_key_assets['ace_'] = ">>>"

#         columns = {
#             'position_id': 'position_id',
#             'portfolio': 'portfolio',
#             'asset_id': 'asset_id',
#             'storage_class': 'storage_class',
#             'internal_class': 'internal_class',
#             'modelling_class': 'modelling_class',
#             'fixed_or_floating': 'fixed_or_floating',

#             'scenario': 'scenario',
#             'ace_': 'ace_',
#             'z_spread': 'py_z_spread',
#             'nominal': 'py_nominal',
#             'shocked_mv_base': 'py_market_value',
#             'scr_interest_down_risk': 'py_scr_interest_down',
#             'scr_interest_up_risk': 'py_scr_interest_up',
#             'scr_spread_risk': 'py_scr_spread',
#             'scr_equity_risk': 'py_scr_equity'
#         }

#         df_ace_key_assets = df_ace_key_assets[columns.keys()]

#         df_ace_key_assets.rename(
#             columns=columns,
#             inplace=True
#         )

#         self.df_ace_key_assets = df_ace_key_assets

#         return df_ace_key_assets

#     def get_race1_sensitivities(
#         self,
#         files_r1_output,
#         file_assigned_asset_classes
#     ):
        
#         df_assigned_asset_classes = pd.read_excel(file_assigned_asset_classes)

#         result_list = []

#         for file_path in files_r1_output:

#             beleggingen_match = re.search(r'(Beleggingen LUV|Beleggingen LV)', file_path)

#             if beleggingen_match:
#                 beleggingen_file = beleggingen_match.group(0)

#                 if beleggingen_file == "Beleggingen LUV":
#                     portfolio = "LTU"
#                 else:
#                     portfolio = "LTV"

#                 df_key_asset = pd.read_excel(os.path.join('', file_path), sheet_name="Key Asset Information")
#                 df_key_asset['scenario'] = "Base"
#                 df_key_asset['portfolio'] = portfolio

#                 result_list.append(df_key_asset)

#         df_r1_key_assets = pd.concat(result_list)

#         df_r1_key_assets = left_join(
#             left_df=df_r1_key_assets,
#             right_df=df_assigned_asset_classes,
#             left_on=['id'],
#             right_on=['id']
#         )

#         df_r1_key_assets['position_id'] = np.where(
#             df_r1_key_assets['storageClass'] == 'Derivatives',
#             df_r1_key_assets['portfolio'] + "_" + df_r1_key_assets['id'] + "_" + df_r1_key_assets['fixedOrFloating'],
#             df_r1_key_assets['portfolio'] + "_" + df_r1_key_assets['id'] 
#         )

#         df_r1_key_assets['position_id'] = np.where(
#             df_r1_key_assets['modellingClass'] == 'Derivatives - FX Forward',
#             np.where(
#                 df_r1_key_assets['fixedOrFloating'] == 'fixed',
#                 df_r1_key_assets['portfolio'] + "_" + df_r1_key_assets['id'] + "_domestic",
#                 df_r1_key_assets['portfolio'] + "_" + df_r1_key_assets['id'] + "_foreign"
#             ),
#             df_r1_key_assets['position_id']
#         )

#         df_r1_key_assets['r1_scr_equity'] = 0
#         df_r1_key_assets['r1_inf01'] = 0
#         df_r1_key_assets['r1_dv01'] = 0
#         df_r1_key_assets['r1_'] = ">>>"

#         columns = {
#             'position_id': 'position_id',
#             'portfolio': 'portfolio',
#             'scenario': 'scenario',

#             'r1_': 'r1_',
#             'spread': 'r1_z_spread',
#             'nominal': 'r1_nominal',
#             'marketValue': 'r1_market_value',
#             'SCR Interest Down': 'r1_scr_interest_down',
#             'SCR Interest Up': 'r1_scr_interest_up',
#             'SCR Spread': 'r1_scr_spread' 
#         }

#         df_r1_key_assets = df_r1_key_assets[columns.keys()]

#         df_r1_key_assets.rename(
#             columns=columns,
#             inplace=True
#         )

#         self.df_r1_key_assets = df_r1_key_assets

#         return df_r1_key_assets

#     def get_shadow_model_sensitivities(
#         self,
#         file_shadow_model_results
#     ):

#         df_shadow_model_key_assets = pd.read_excel(
#             file_shadow_model_results, 
#             sheet_name="Key Asset Information"
#         )

#         df_shadow_model_key_assets['shadow_model_'] = ">>>"

#         columns = {
#             'position_id': 'position_id',
#             'portfolio': 'portfolio',

#             'scenario': 'scenario',
#             'shadow_model_': 'shadow_model_',
#             'z_spread': 'sm_z_spread',
#             'nominal': 'sm_nominal',
#             'scenario_base_market_value': 'sm_market_value',
#             'scr_interest_down': 'sm_scr_interest_down',
#             'scr_interest_up': 'sm_scr_interest_up',
#             'scr_spread': 'sm_scr_spread',
#             'scr_equity': 'sm_scr_equity'
#         }

#         df_shadow_model_key_assets = df_shadow_model_key_assets[columns.keys()]

#         df_shadow_model_key_assets.rename(
#             columns=columns,
#             inplace=True
#         )

#         self.df_shadow_model_key_assets = df_shadow_model_key_assets

#         return df_shadow_model_key_assets

#     def get_comparison(
#         self
#     ):

#         df_ace_key_assets = self.get_ace_sensitivities(
#             file_ace_results=self.file_ace_results
#         )

#         df_r1_key_assets = self.get_race1_sensitivities(
#             files_r1_output=self.files_r1_output,
#             file_assigned_asset_classes=self.file_assigned_asset_classes
#         )

#         df_shadow_model_key_assets = self.get_shadow_model_sensitivities(
#             file_shadow_model_results=self.file_shadow_model_results
#         )

#         df_comparison = pd.merge(
#             left = df_ace_key_assets,
#             right = df_r1_key_assets,
#             how='left',
#             left_on = ['scenario', 'portfolio', 'position_id'],
#             right_on = ['scenario', 'portfolio', 'position_id']
#         )

#         df_comparison = pd.merge(
#             left = df_comparison,
#             right = df_shadow_model_key_assets,
#             how='left',
#             left_on = ['scenario', 'portfolio', 'position_id'],
#             right_on = ['scenario', 'portfolio', 'position_id']
#         )

#         # ACE 2.0 vs RACE 1.0
#         df_comparison['py_vs_r1_z_spread'] = df_comparison['py_z_spread'] - df_comparison['r1_z_spread']
#         df_comparison['py_vs_r1_nominal'] = df_comparison['py_nominal'] - df_comparison['r1_nominal']
#         df_comparison['py_vs_r1_market_value '] = df_comparison['py_market_value'] - df_comparison['r1_market_value']
#         df_comparison['py_vs_r1_scr_interest_down'] = df_comparison['py_scr_interest_down'] - df_comparison['r1_scr_interest_down']
#         df_comparison['py_vs_r1_scr_interest_up'] = df_comparison['py_scr_interest_up'] - df_comparison['r1_scr_interest_up']
#         df_comparison['py_vs_r1_scr_spread'] = df_comparison['py_scr_spread'] - df_comparison['r1_scr_spread']

#         # ACE 2.0 vs Shadow Model
#         df_comparison['py_vs_sm_z_spread'] = df_comparison['py_z_spread'] - df_comparison['sm_z_spread']
#         df_comparison['py_vs_sm_nominal'] = df_comparison['py_nominal'] - df_comparison['sm_nominal']
#         df_comparison['py_vs_sm_market_value '] = df_comparison['py_market_value'] - df_comparison['sm_market_value']
#         df_comparison['py_vs_sm_scr_interest_down'] = df_comparison['py_scr_interest_down'] - df_comparison['sm_scr_interest_down']
#         df_comparison['py_vs_sm_scr_interest_up'] = df_comparison['py_scr_interest_up'] - df_comparison['sm_scr_interest_up']
#         df_comparison['py_vs_sm_scr_spread'] = df_comparison['py_scr_spread'] - df_comparison['sm_scr_spread']
#         df_comparison['py_vs_sm_scr_equity'] = df_comparison['py_scr_equity'] - df_comparison['sm_scr_equity']

#         # RACE 1.0 vs Shadow Model
#         df_comparison['r1_vs_sm_z_spread'] = df_comparison['r1_z_spread'] - df_comparison['sm_z_spread']
#         df_comparison['r1_vs_sm_nominal'] = df_comparison['r1_nominal'] - df_comparison['sm_nominal']
#         df_comparison['r1_vs_sm_market_value '] = df_comparison['r1_market_value'] - df_comparison['sm_market_value']
#         df_comparison['r1_vs_sm_scr_interest_down'] = df_comparison['r1_scr_interest_down'] - df_comparison['sm_scr_interest_down']
#         df_comparison['r1_vs_sm_scr_interest_up'] = df_comparison['r1_scr_interest_up'] - df_comparison['sm_scr_interest_up']
#         df_comparison['r1_vs_sm_scr_spread'] = df_comparison['r1_scr_spread'] - df_comparison['sm_scr_spread']


#         self.validation_data = {'Comparison': df_comparison}

#         return df_comparison

#     def export_to_local(
#         self,
#         file_path=None
#     ):

#         file_path = file_path or f"./Market Risk Valiadation - {self.valuation_date.strftime('%Y-%m-%d')}.xlsx"  

#         export_dict_to_xlsx(
#             data_dict=self.validation_data,
#             file_path=file_path
#         )
