"""
    Collection of useful functions.
"""

__author__ = "lcalmbach@gmail.com"

import config as cn
import streamlit as st
import pandas as pd
import numpy as np
import base64
from datetime import datetime

from st_aggrid import GridOptionsBuilder, AgGrid, GridUpdateMode, DataReturnMode, JsCode


def get_cs_item_list(lst, separator=',', quote_string=""):
    result = ''
    for item in lst:
        result += quote_string + str(item) + quote_string + separator
    result = result[:-1]
    return result


def color_gradient(row: int, value_col: str, min_val: float, max_val: float, rgb: str) -> int:
    """
    Projects a value on a color gradient scale given the min and max value.
    the color gradient type is defined in the config, e.g. blue-green, red, blue etc.
    returns a string with rgb values
    """

    result = {'r': 0, 'g': 0, 'b': 0}
    if max_val - min_val != 0:
        x = int((row[value_col] - min_val) / (max_val - min_val) * 255)
    else:
        x = 0

    if cn.GRADIENT == 'blue-green':
        if row[value_col] > max_val:
            result['r'] = 255
        else:
            result['g'] = x
            result['b'] = abs(255 - x)
    return result[rgb]


def get_pivot_data(df, group_by):
    """
    Returns a pivot table from the raw data table. df must include the station name, the data column and the
    group by column. Example
    input:
    ¦Station¦date       ¦parameter  ¦value  ¦
    -----------------------------------------
    ¦MW1    ¦1/1/2001   ¦calcium    ¦10     ¦
    ¦MW1    ¦1/1/2001   ¦chloride   ¦21     ¦

    output:
    ¦Station¦date       ¦calcium    ¦chloride   ¦
    ---------------------------------------------
    ¦MW1    ¦1/1/2001   ¦10         ¦21         ¦

    :param df:          dataframe holding the data to be pivoted
    :param group_by:
    :return:
    """

    result = pd.pivot_table(df, values=cn.VALUES_VALUE_COLUMN, index=[cn.SAMPLE_DATE_COLUMN, cn.STATION_NAME_COLUMN,
                                                                      group_by], columns=[cn.PAR_NAME_COLUMN],
                            aggfunc=np.average)
    return result


def remove_nan_columns(df: pd.DataFrame):
    """
    Removes all empty columns from a data frame. This is used to reduce unnecessary columns when displaying tables.
    Since there is only one station table but different data collection may have different data fields, often not all
    fields are used in many cases. when displaying station or parameter information, empy columns can be excluded in
    order to make the table easier to read.

    :param df: dataframe from which empty dolumns should be removed
    :return:
    """

    lis = df.loc[:, df.isna().all()]
    for col in lis:
        del df[col]
    return df


def remove_columns(df: pd.DataFrame, lis: list) -> pd.DataFrame:
    """
    Removes columns specified in a list from a data frame. This is used to reduce unnecessary columns when
    displaying tables.

    :param lis: list of columns to remove from the dataframe
    :param df: dataframe with columns to be deleted
    :return: dataframe with deleted columns
    """

    for col in lis:
        del df[col]
    return df


def get_table_download_link(df: pd.DataFrame) -> str:
    """
    Generates a link allowing the data in a given panda dataframe to be downloaded

    :param df:  table with data
    :return:    link string including the data
    """

    csv = df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()  # some strings <-> bytes conversions necessary here
    href = f'<a href="data:file/csv;base64,{b64}">Download csv file</a>'

    return href


def transpose_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Transposes a dataframe that has exactly 1 row and n columns to a table that has 2 columns and n rows. column names
    become row headers.

    Parameters:
    -----------
    :param df:
    :return:

    :param df:  dataframe to be transposed
    :return:    transposed data frame having 2 columns and n rows
    """

    result = pd.DataFrame({"Field": [], "Value": []})
    for key, value in df.iteritems():
        df2 = pd.DataFrame({"Field": [key], "Value": [df.iloc[-1][key]]})
        result = result.append(df2)
    result = result.set_index('Field')
    return result

def dic2html_table(dic: dict, key_col_width_pct: int)-> str:
    """
    Converts a key value dictionary into a html table
    """
    html_table = '<table>'
    for x in dic:
        html_table += f'<tr><td style="width: {key_col_width_pct}%;">{x}</td><td>{dic[x]}</td>'
    html_table += '</table>'
    return html_table

def show_grid(df:pd.DataFrame, title, col_cfg:dict={}):
    #Infer basic colDefs from dataframe types
    gb = GridOptionsBuilder.from_dataframe(df)

    #customize gridOptions
    
    gb.configure_default_column(groupable=False, value=True, enableRowGroup=False, editable=True)

    if col_cfg != None:
        for col in col_cfg:
            gb.configure_column(col['name'], type=col['type'], custom_format_string=col['custom_format_string'])
            col['type']=["dateColumnFilter","customDateTimeFormat"]
            col['precision']=2
            col['custom_format_string'] = 'yyyy-MM-dd HH:mm zzz'
    #gb.configure_column("apple", type=["numericColumn","numberColumnFilter","customNumericFormat"], precision=2, aggFunc='sum')
    #gb.configure_column("banana", type=["numericColumn", "numberColumnFilter", "customNumericFormat"], precision=1, aggFunc='avg')
    #gb.configure_column("chocolate", type=["numericColumn", "numberColumnFilter", "customCurrencyFormat"], custom_currency_symbol="CHF ", aggFunc='max')

    #configures last row to use custom styles based on cell's value, injecting JsCode on components front end
    
    if grd_cfg['enable_sidebar']:
        gb.configure_side_bar()

    if grd_cfg['enable_selection']:
        gb.configure_selection(grd_cfg['selection_mode'])
        if grd_cfg['use_checkbox']:
            gb.configure_selection(grd_cfg['selection_mode'], use_checkbox=True, groupSelectsChildren=grd_cfg['groupSelectsChildren'], groupSelectsFiltered=grd_cfg['groupSelectsFiltered'])
        if ((grd_cfg['selection_mode'] == 'multiple') & (not grd_cfg['use_checkbox'])):
            gb.configure_selection(grd_cfg['selection_mode'], use_checkbox=False, rowMultiSelectWithClick=grd_cfg['rowMultiSelectWithClic'], suppressRowDeselection=grd_cfg['suppressRowDeselection'])

    if grd_cfg['enable_pagination']:
        if grd_cfg['paginationAutoSize']:
            gb.configure_pagination(paginationAutoPageSize=True)
        else:
            gb.configure_pagination(paginationAutoPageSize=False, paginationPageSize=grd_cfg['paginationPageSize'])

    gb.configure_grid_options(domLayout='normal')
    gridOptions = gb.build()

    #Display the grid
    with st.spinner("Loading Grid..."):
        st.header(title)
        grid_response = AgGrid(
            df, 
            gridOptions=gridOptions,
            height=grd_cfg['grid_height'], 
            width='100%',
            data_return_mode=grd_cfg['return_mode_value'], 
            update_mode=grd_cfg['update_mode_value'],
            fit_columns_on_grid_load=grd_cfg['fit_columns_on_grid_load'],
            allow_unsafe_jscode=True, #Set it to True to allow jsfunction to be injected
            enable_enterprise_modules=grd_cfg['enable_enterprise_modules'],
            )
    
    df_result = grid_response['data']
    selected = grid_response['selected_rows']
    
    sel_id = selected[0]['id'] if len(selected)>0 else -999
    return df_result, sel_id

def left(s, amount):
    return s[:amount]

def right(s, amount):
    return s[-amount:]

def mid(s, offset, amount):
    return s[offset:offset+amount]

def percentile(n):
        def percentile_(x):
            return np.percentile(x, n)
        percentile_.__name__ = 'percentile_%s' % n
        return percentile_