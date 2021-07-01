import streamlit as st
from st_aggrid import AgGrid
import pandas as pd
import numpy as np
import altair as alt
import calendar

from queries import qry
import config
from st_aggrid import AgGrid


class App:
    """
    """

    def __init__(self, df_data, df_stations, df_parameters):
        def add_time_columns(df):
            self.df_data = df_data
            self.df_data['datum'] = pd.to_datetime(self.df_data['zeit']).dt.date
            self.df_data['datum'] = pd.to_datetime(self.df_data['datum'])
            self.df_data['woche'] = df_data['zeit'].dt.isocalendar().week
            self.df_data['jahr'] = df_data['zeit'].dt.year    
            self.df_data['monat'] = df_data['zeit'].dt.month 
            self.df_data['monat'] = self.df_data['monat'].replace(config.MONTHS_DICT)
            self.df_data['mitte_woche'] = pd.to_datetime(df_data['datum']) - pd.to_timedelta(df_data['zeit'].dt.dayofweek % 7 - 2, unit='D')
            #self.df_data['mitte_woche'] = df_data['mitte_woche_datum'].dt.date 
            self.df_data['mitte_monat'] = pd.to_datetime(df_data['datum']) - pd.to_timedelta(df_data['zeit'].dt.day + 14, unit='D')
            self.df_data['mitte_jahr'] = pd.to_datetime(df_data['datum']) - pd.to_timedelta(df_data['zeit'].dt.dayofyear + (365/2), unit='D')
            self.df_data['stunde'] = pd.to_datetime(self.df_data['zeit']).dt.hour
            #st.write(df.head())
            return df

        self.df_data = add_time_columns(df_data)
        self.df_stations = df_stations
        self.df_stations.set_index("id", inplace=True)
        self.dic_stations = df_stations['name'].to_dict()
        self.station = {}
        self.df_parameters = df_parameters
        self.lst_parameters = list(df_parameters['name'])
        self.start_jahr =  int(self.df_data['jahr'].min() + 1)
        self.end_jahr = int(self.df_data['jahr'].max())
        self.settings = {}
    
   
    def show_linechart(self):
        pass

    def show_barchart(self):
        def get_settings():
            self.settings['agg_time'] = st.sidebar.selectbox("Aggregiere Messungen nach",options=['Jahr','Monat','Jahr-Monat','Jahr-Woche','Jahr-Tag','Monat-Stunde'])
            self.settings['par'] = st.sidebar.selectbox("Parameter",options=self.lst_parameters)
            self.settings['years'] = st.sidebar.slider('🔍Jahr', self.start_jahr, self.end_jahr, (self.start_jahr, self.end_jahr))
            if self.settings['agg_time'] == 'Monat-Stunde':
                self.settings['monat'] = st.sidebar.selectbox("Parameter",options=list(config.MONTHS_DICT.values()))

        def filter_data():
            df = self.df_data
            if self.settings['years'][0] != self.start_jahr or self.settings['years'][1] != self.end_jahr:
                df = df[df['jahr'].isin(range(self.settings['years'][0], self.settings['years'][1]))]
            if self.settings['agg_time'] == 'Monat-Stunde':
                df = df[df['monat']==self.settings['monat']]
            return df

        def aggregate_data(df):
            self.settings['y_par'] = self.settings['par'].replace('.','')
            self.settings['bar_width'] = 20
            self.settings['x_axis_format'] = "%Y"
            if self.settings['agg_time'] == 'Jahr':
                df = df.groupby(['mitte_jahr', 'jahr'])[self.settings['par']].agg(['mean'])
                df = df.rename(columns = {'mean': self.settings['y_par']})
                self.settings['x_par'] = 'mitte_jahr'
                self.settings['tooltip'] = ['jahr', self.settings['y_par']]
            if self.settings['agg_time'] == 'Monat':
                df = df.groupby(['monat'])[self.settings['par']].agg(['mean'])
                df = df.rename(columns = {'mean': self.settings['y_par']})
                self.settings['x_par'] = 'monat'
                self.settings['tooltip'] = ['monat', self.settings['y_par']]
                self.settings['x_axis_format'] = ""
            if self.settings['agg_time'] == 'Jahr-Monat':
                df = df.groupby(['mitte_monat', 'jahr','monat'])[self.settings['par']].agg(['mean'])
                df = df.rename(columns = {'mean': self.settings['y_par']})
                self.settings['x_par'] = 'mitte_monat'
                self.settings['tooltip'] = ['jahr','monat', self.settings['y_par']]
                self.settings['x_axis_format'] = "%b %Y"
                self.settings['bar_width'] = 4
            if self.settings['agg_time'] == 'Jahr-Woche':
                df = df.groupby(['mitte_woche', 'jahr','monat'])[self.settings['par']].agg(['mean'])
                df = df.rename(columns = {'mean': self.settings['y_par']})
                self.settings['x_par'] = 'mitte_woche'
                self.settings['tooltip'] = ['jahr','monat', self.settings['y_par']]
                self.settings['bar_width'] = 2
            if self.settings['agg_time'] == 'Jahr-Tag':
                df = df.groupby(['datum'])[self.settings['par']].agg(['mean'])
                df = df.rename(columns = {'mean': self.settings['y_par']})
                self.settings['x_par'] = 'datum'
                self.settings['tooltip'] = ['datum', self.settings['y_par']]
                self.settings['x_axis_format'] = "%Y-%m-%d"
                self.settings['bar_width'] = 2
            if self.settings['agg_time'] == 'Monat-Stunde':
                df = df.groupby(['stunde'])[self.settings['par']].agg(['mean'])
                df = df.rename(columns = {'mean': self.settings['y_par']})
                self.settings['x_par'] = 'stunde'
                self.settings['tooltip'] = ['zeit', self.settings['y_par']]
                self.settings['x_axis_format'] = ""
                self.settings['x_scale'] = (1,23)
            
            
            df = df.reset_index()
            #st.write(df)
            return df

        get_settings()
        df = filter_data()
        df = aggregate_data(df)
        
        if 'x_scale' in self.settings:
            x_scale = alt.Scale(domain=self.settings['x_scale'])
        else:
            x_scale = alt.Scale()
        if 'y_scale' in self.settings:
            y_scale = alt.Scale(domain=self.settings['y_scale'])
        else:
            y_scale = alt.Scale()
        df_guideline = pd.DataFrame({'Grenzwert Jahresmittel': [10]})
        df_guideline2 = pd.DataFrame({'Grenzwert Tagesmittel': [25]})

        line1_color = alt.Color('Grenzwert Jahresmittel', scale=alt.Scale(scheme='bluepurple'))
        line1 = alt.Chart(df_guideline).mark_rule(color='red').encode(y='Grenzwert Jahresmittel', tooltip='Grenzwert Jahresmittel')
        line2 = alt.Chart(df_guideline2).mark_rule(color='darkorange').encode(y='Grenzwert Tagesmittel', tooltip='Grenzwert Tagesmittel')
        
        chart = alt.Chart(df).mark_bar(clip=True, width = self.settings['bar_width']).encode(  # width = 800/len(df)
            x=alt.X(self.settings['x_par'], 
                scale=x_scale, 
                axis=alt.Axis(title='', format=self.settings['x_axis_format']), 
                sort = list(config.MONTHS_REV_DICT)),
            y=alt.Y(self.settings['y_par'], 
                scale=y_scale, 
                axis=alt.Axis(title=self.settings['par'] + '(µg/m3)')),
            tooltip = self.settings['tooltip']
        ).properties(width=800,height=300)
        guidelines = line1 if line2 == None else line1 + line2
        st.altair_chart(chart + guidelines )
        with st.beta_expander('Data'):
            AgGrid(df)


    def show_menu(self):
        plot_types = ['Säulendiagramm', 'Liniendiagramm', 'Boxplot', 'Heatmap']
        plot_type = st.sidebar.selectbox("Grafiktyp", options=plot_types)
        
        _station_id = st.sidebar.selectbox('Station', list(self.dic_stations.keys()),
                format_func=lambda x: self.dic_stations[x])    
        self.station = self.df_stations.loc[_station_id]
        
        if plot_type == 'Säulendiagramm':
            self.show_barchart()
        elif plot_type == 'Liniendiagramm':
            self.show_linechart()
        elif plot_type == 'Boxplot':
            self.show_linechart()
        elif plot_type == 'Heatmap':
            self.show_heatmap()

        
    