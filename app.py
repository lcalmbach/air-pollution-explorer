"""
The Environmental data explorer app allows to explorer environmental datasets. 
"""

import streamlit as st
import logging
import pandas as pd

import apox_stats
import apox_info
import apox_plots
import config as cn

__version__ = '0.0.1' 
__author__ = 'Lukas Calmbach'
__author_email__ = 'lcalmbach@gmail.com'
VERSION_DATE = '2021-06-12'
my_name = 'Air Pollution Explorer'
my_kuerzel = "apox-I"
GIT_REPO = 'https://github.com/lcalmbach/air-pol-ex'
config = {} # dictionary mit allen Konfigurationseinträgen
APP_INFO = f"""<div style="background-color:powderblue; padding: 10px;border-radius: 15px;">
    <small>App created by <a href="mailto:{__author_email__}">{__author__}</a><br>
    version: {__version__} ({VERSION_DATE})<br>
    <a href="{GIT_REPO}">git-repo</a>
    """
MENU_DIC = {apox_info: 'Info', apox_stats: 'Statistiken', apox_plots: ' Grafiken'}
LOGGING_LEVEL = logging.ERROR
logging.basicConfig(format='%(levelname) %(asctime)s %(message)s', level=LOGGING_LEVEL)


def get_data():
    df_data = pd.read_parquet('./data/apox_data.pq')
    df_stations = pd.read_json('./data/stations.json')
    df_parameters = pd.read_json('./data/parameters.json')
    return df_data, df_stations, df_parameters


def main():
    app = st.sidebar.selectbox("Menu", options=list(MENU_DIC.keys()),
        format_func=lambda x: MENU_DIC[x])
    #app.show_menu()
    df_data, df_stations, df_parameters = get_data()
    app = app.App(df_data, df_stations, df_parameters)
    app.show_menu()


if __name__ == "__main__":
    main()
    



