import streamlit as st
import pandas as pd
import json
from streamlit.report_thread import get_report_ctx

#from queries import qry
from st_aggrid import AgGrid

class App:
    """
    """

    def __init__(self, df_data, df_stations, df_parameters):
        self.df_data = df_data
        self.df_stations = df_stations
        self.df_parameters = df_parameters
    
    def show_info(self):
        with open('./intro.md', encoding='UTF8') as f:
            info = f.read()
            st.markdown(info)
            st.markdown(f"#### {self.df_stations.iloc[0]['name']}")
            st.markdown(self.df_stations.iloc[0]['beschreibung'])
        

    def show_menu(self):
        #station = st.sidebar()
        self.show_info()

        
    