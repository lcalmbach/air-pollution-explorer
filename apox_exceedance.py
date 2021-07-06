import streamlit as st
from st_aggrid import AgGrid
import pandas as pd
import numpy as np
from st_aggrid import AgGrid

from queries import qry
#import tools
import config
import tools

min_number_months_measured = 8

class App:
    """
    """

    def __init__(self, df_data, df_stations, df_parameters):
        self.df_data = tools.add_time_columns(df_data)
        self.df_stations = df_stations
        self.df_stations.set_index("id", inplace=True)
        self.dic_stations = df_stations['name'].to_dict()
        self.station = {}
        self.df_parameters = df_parameters

        self.start_jahr =  int(self.df_data['jahr'].min() + 1)
        self.end_jahr = int(self.df_data['jahr'].max())
    

    def get_jahre_mit_monatlichen_daten(self,df,par):
        min_number_months_measured = 8

        df = df.groupby(['jahr','monat'])[par].agg(['count'])
        df = df[df['count']>0].reset_index()
        df = df.groupby(['jahr'])['count'].agg(['count']).reset_index()
        df = df[df['count']>min_number_months_measured].reset_index()
        return (df['jahr'].unique().tolist())

    def analyse_excceedances(self, gl, par):
        def analyse_year():
            df = self.df_data.groupby([gl['time_agg_field']])[par['name_short']].agg(['mean', 'count']).reset_index()
            df = df[df[gl['time_agg_field']].isin(self.get_jahre_mit_monatlichen_daten(self.df_data, par['name_short']))]
            df['exceedance'] = df['mean'] - gl['value']
            df = df.rename(columns={'jahr':'Jahr', 'mean': 'Mittelwert', 'count': 'Anzahl Messungen', 'exceedance': 'Abweichung vom Grenzwert'} )
            return df

        def analyse_day():
            df = self.df_data.groupby(['jahr',gl['time_agg_field']])[par['name_short']].agg(['mean', 'count']).reset_index()
            df['exceedance'] = df['mean'] - gl['value']
            df['is_exceedance'] = df['exceedance'].apply(lambda val: 1 if val > 0 else 0)
            df['no_exceedance'] = abs(df['is_exceedance'] - 1)
            
            df = df.groupby(['jahr'])['exceedance','no_exceedance','is_exceedance',].agg(['sum']).reset_index()
            df['pct_exceedances'] = df['is_exceedance'] / (df['no_exceedance'] + df['is_exceedance']) * 100
            df.columns = df.columns.map('_'.join)
            df = df.rename(columns={'jahr_':'Jahr', 'no_exceedance_sum': f"Anz<{gl['value']}", 'is_exceedance_sum': f"Anz>={gl['value']}", 'pct_exceedances_':'pct_exceedances'} )
            df = df[['Jahr', f"Anz<{gl['value']}", f"Anz>={gl['value']}",'pct_exceedances']]
            return df

        def analyse_hour():
            df = self.df_data[['jahr', par['name_short']]]
            df['exceedance'] = df[par['name_short']] - gl['value']
            df['is_exceedance'] = df['exceedance'].apply(lambda val: 1 if val > 0 else 0)
            df['no_exceedance'] = abs(df['is_exceedance'] - 1)
            
            df = df.groupby(['jahr'])['exceedance','no_exceedance','is_exceedance',].agg(['sum']).reset_index()
            df['pct_exceedances'] = df['is_exceedance'] / (df['no_exceedance'] + df['is_exceedance']) * 100
            df.columns = df.columns.map('_'.join)
            df = df.rename(columns={'jahr_':'Jahr', 'no_exceedance_sum': f"Anz<{gl['value']}", 'is_exceedance_sum': f"Anz>={gl['value']}", 'pct_exceedances_':'pct_exceedances'} )
            df = df[['Jahr', f"Anz<{gl['value']}", f"Anz>={gl['value']}",'pct_exceedances']]
            return df

        st.markdown(f"### Grenzwert: {gl['legend']} für {par['name_long']}: {gl['value']}")
        st.markdown(gl['comment'])
        st.markdown('Grenzwert-Überschreitungen')

        if gl['time_agg_field'] == 'jahr':
            df = analyse_year()
        elif gl['time_agg_field'] == 'datum':
            df = analyse_day()
        elif gl['time_agg_field'] == 'stunde':
            df = analyse_hour()
        AgGrid(df)
        st.markdown(f"Überschreitungen des Jahresgrenzwerts werden nur in Jahren ausgewiesen, in welchen während mindestestens {min_number_months_measured} Monaten gemessen wurde")
        

    def show_exceedance(self):
        for par in self.parameters:
            rec = self.df_parameters[par]
            for gl in rec['guidelines']:
                self.analyse_excceedances(gl, rec)


    def show_menu(self):
        _station_id = st.sidebar.selectbox('Station', list(self.dic_stations.keys()),
            format_func=lambda x: self.dic_stations[x])    
        self.station = self.df_stations.loc[_station_id]
        self.parameters = st.sidebar.multiselect("Parameters",options = list(self.df_parameters.columns), default=list(self.df_parameters.columns))
        
        self.show_exceedance()

        
    