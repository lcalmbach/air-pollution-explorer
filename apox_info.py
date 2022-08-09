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
        def get_current_values_list():
            text = ''
            rec = self.df_data.sort_values(by='zeit',ascending=False).head(1)
            rec.rename(columns={rec.columns[0]:'value'})
            for par in self.df_parameters:
                text += f"- **{self.df_parameters[par]['name_short']}**: {rec.iloc[0][par] :.1f}{self.df_parameters[par]['unit']} \n"
            return text

        stations = len(self.df_stations)
        year_from = self.df_data['jahr'].min()
        year_to = self.df_data['jahr'].max()
        most_current_record = self.df_data['zeit'].max().strftime('%d.%m.%Y %H:%M')
        now_as_CET = datetime.now(tz=config.tz_GMT).strftime('%d.%m.%Y %H:%M')
        current_values = get_current_values_list()
        with open('./intro.md', encoding='UTF8') as f:
            st.markdown(f.read().format(stations, year_from, year_to, most_current_record, now_as_CET, current_values))   
        
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
        st.image('./images/Roche mit Baustelle im Abendlicht, März 2020.jpg', caption=None, width=None, use_column_width='auto', clamp=False, channels='RGB', output_format='auto')
        st.markdown('[Quelle Abbildung](https://www.bs.ch/bilddatenbank#tree=6376&details=38519)')
        menu = st.sidebar.selectbox('Auswahl', options = LST_MENU)
        if menu =='Über LQX-BS':
            self.show_about()
        elif menu =='Parameter':
            self.show_parameters()
        elif menu =='Stationen':
            self.show_stations()