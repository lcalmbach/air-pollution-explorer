import streamlit as st
from st_aggrid import AgGrid
import pandas as pd
import numpy as np
from st_aggrid import AgGrid

from queries import qry
#import tools
import config
import tools


class App:
    """
    """

    def __init__(self, df_data, df_stations, df_parameters):
        def add_time_columns(df):
            self.df_data = df_data
            self.df_data['datum'] = pd.to_datetime(self.df_data['zeit']).dt.date
            self.df_data['woche'] = df_data['zeit'].dt.isocalendar().week
            self.df_data['mitte_woche_datum'] = pd.to_datetime(df_data['zeit']) - pd.to_timedelta(df_data['zeit'].dt.dayofweek % 7 - 2, unit='D')
            self.df_data['mitte_woche_datum'] = df_data['mitte_woche_datum'].dt.date 
            self.df_data['jahr'] = df_data['zeit'].dt.year    
            self.df_data['monat'] = df_data['zeit'].dt.month  
            return df

        self.df_data = add_time_columns(df_data)
        self.df_stations = df_stations
        self.df_stations.set_index("id", inplace=True)
        self.dic_stations = df_stations['name'].to_dict()
        self.station = {}
        self.df_parameters = df_parameters


        self.start_jahr =  int(self.df_data['jahr'].min() + 1)
        self.end_jahr = int(self.df_data['jahr'].max())
    
    
    def show_daily_stats(self):
        def percentile(n):
            def percentile_(x):
                return np.percentile(x, n)
            percentile_.__name__ = 'percentile_%s' % n
            return percentile_

        jahr = st.sidebar.selectbox('Jahr', options = range(self.start_jahr, self.end_jahr+1))
        monat = st.sidebar.selectbox('Monat', options = range(1, 13))
        text = f"### Statistik der Luftschadstoffe {', '.join(self.parameters)} für Station {self.station['name']} im {config.MONTHS_DICT[monat]} {jahr}."
        st.markdown(text)
        _df = self.df_data[(self.df_data['jahr']==jahr) & (self.df_data['monat'] == monat)]
        for par in self.parameters:
            st.markdown(f'**{par}**')
            _stats = _df.groupby(['datum'])[par].agg(['min','max','mean', 'std', percentile(5), percentile(25), percentile(50), percentile(75), percentile(90), percentile(99), 'count'])
            AgGrid(_stats.reset_index())


    def show_monthly_stats(self):
        jahr = st.sidebar.selectbox('Jahr', options = range(self.start_jahr, self.end_jahr + 1))

        text = f"### Statistik der Luftschadstoffe {', '.join(self.parameters)} für Station {self.station['name']} im Jahr {jahr}."
        st.markdown(text)

        _df = self.df_data[self.df_data['jahr']==jahr]
        for par in self.parameters:
            st.markdown(f'**{par}**')
            _stats = _df.groupby(['jahr', 'monat'])[par].agg(['min','max','mean', 'std', tools.percentile(5), tools.percentile(25), tools.percentile(50), tools.percentile(75), tools.percentile(90), tools.percentile(99), 'count'])
            AgGrid(_stats.reset_index())

    def show_yearly_stats(self):
        def percentile(n):
            def percentile_(x):
                return np.percentile(x, n)
            percentile_.__name__ = 'percentile_%s' % n
            return percentile_

        
        jahre = st.sidebar.slider('Jahr', self.start_jahr, self.end_jahr, (self.start_jahr, self.end_jahr))
        text = f"### Statistik der Luftschadstoffe {','.join(self.parameters)} für Station {self.station['name']} für die Jahre {self.start_jahr} bis {self.end_jahr}."
        st.markdown(text)
        _df = self.df_data[self.df_data['jahr'].isin(range(jahre[0], jahre[1]) )]
        for par in self.parameters:
            st.markdown(f'**{par}**')
            _stats = _df.groupby(['jahr'])[par].agg(['min','max','mean', 'std', percentile(5), percentile(25), percentile(50), percentile(75), percentile(90), percentile(99), 'count'])
            AgGrid(_stats.reset_index())

    def show_exceedances(self):
        jahre = st.sidebar.slider('Jahr', self.start_jahr, self.end_jahr, (self.start_jahr, self.end_jahr))
        _df = self.df_data[self.df_data['jahr'].isin(range(jahre[0], jahre[1]) )]
        text = f"Für {self.station['name']} wurden Messungen von {self.start_jahr} bis {self.end_jahr} durchgeführt."
        st.markdown(text)
        for par in self.parameters:
            st.markdown(f'**{par}**')
            _stats = pd.DataFrame()
            AgGrid(_stats.reset_index())

    def show_menu(self):
        _station_id = st.sidebar.selectbox('Station', list(self.dic_stations.keys()),
            format_func=lambda x: self.dic_stations[x])    
        self.station = self.df_stations.loc[_station_id]
        type_options = ['nach Jahr', 'nach Monat', 'nach Tag']
        stat_type = st.sidebar.selectbox("Statistik", options=type_options)
        self.parameters = st.sidebar.multiselect("Parameters",options = list(self.df_parameters.columns), default=list(self.df_parameters.columns))
        
        if stat_type == 'nach Jahr':
            self.show_yearly_stats()
        elif stat_type == 'nach Monat':
            self.show_monthly_stats()
        elif stat_type == 'nach Tag':
            self.show_daily_stats()
        elif stat_type == 'Grenzwert Überschreitungen':
            self.show_exceedances()

        
    