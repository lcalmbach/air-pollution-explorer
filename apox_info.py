import streamlit as st
import pandas as pd
from datetime import datetime

import config

LST_MENU = ('Über LQX-BS', 'Parameter', 'Stationen')

class App:
    """
    """

    def __init__(self, df_data, df_stations, df_parameters):
        self.df_data = df_data
        self.df_stations = df_stations
        self.df_parameters = df_parameters
    
    def show_about(self):
        stations = len(self.df_stations)
        year_from = self.df_data['zeit'].min().strftime('%Y')
        year_to = self.df_data['zeit'].max().strftime('%Y')
        most_current_record = self.df_data['zeit'].max().strftime('%d.%m.%Y %H:%M')
        now_as_CET = datetime.now(tz=config.tz_GMT).strftime('%d.%m.%Y %H:%M')
        with open('./intro.md', encoding='UTF8') as f:
            st.markdown(f.read().format(stations, year_from, year_to, most_current_record, now_as_CET))   
        
    def show_stations(self):
        text = ""
        for index, row in self.df_stations.iterrows():
            text = (f"### {row['name']}\n") 
            text += row['beschreibung']
        st.markdown(text)   


    def show_parameters(self):
        with open('./parameter.md', encoding='UTF8') as f:
            st.markdown(f.read())   


    def show_menu(self):
        menu = st.sidebar.selectbox('Auswahl', options = LST_MENU)
        if menu =='Über LQX-BS':
            self.show_about()
        elif menu =='Parameter':
            self.show_parameters()
        elif menu =='Stationen':
            self.show_stations()

        
    