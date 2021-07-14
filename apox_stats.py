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
        self.df_data = df_data
        self.df_stations = df_stations
        self.df_stations.set_index("id", inplace=True)
        self.dic_stations = df_stations['name'].to_dict()
        self.station = {}
        self.df_parameters = df_parameters


        self.start_jahr =  int(self.df_data['jahr'].min() + 1)
        self.end_jahr = int(self.df_data['jahr'].max())
    
    
    def get_cols(self):
            cols = []
            if self.stat_type == 'nach Jahr':
                cols.append({'name': 'jahr', 'type':["numericColumn","numberColumnFilter","customNumericFormat"], 'precision':0})
            elif self.stat_type == 'nach Monat':
                cols.append({'name': 'jahr', 'type':["numericColumn","numberColumnFilter","customNumericFormat"], 'precision':0})
                cols.append({'name': 'monat', 'type':["numericColumn","numberColumnFilter","customNumericFormat"], 'precision':0})
            else:
                cols.append({'name': 'Datum', 'type':["dateColumn","dateColumnFilter","customDateFormat"], 'precision':0})

            cols.append({'name':'min', 'type':["numericColumn","numberColumnFilter","customNumericFormat"], 'precision':1})
            cols.append({'name':'max', 'type':["numericColumn","numberColumnFilter","customNumericFormat"], 'precision':1})
            cols.append({'name':'mean', 'type':["numericColumn","numberColumnFilter","customNumericFormat"], 'precision':1})
            cols.append({'name':'std', 'type':["numericColumn","numberColumnFilter","customNumericFormat"], 'precision':1})
            cols.append({'name':'percentile_5', 'type':["numericColumn","numberColumnFilter","customNumericFormat"], 'precision':1})
            cols.append({'name':'percentile_25', 'type':["numericColumn","numberColumnFilter","customNumericFormat"], 'precision':1})
            cols.append({'name':'percentile_50', 'type':["numericColumn","numberColumnFilter","customNumericFormat"], 'precision':1})
            cols.append({'name':'percentile_75', 'type':["numericColumn","numberColumnFilter","customNumericFormat"], 'precision':1})
            cols.append({'name':'percentile_90', 'type':["numericColumn","numberColumnFilter","customNumericFormat"], 'precision':1})
            cols.append({'name':'percentile_95', 'type':["numericColumn","numberColumnFilter","customNumericFormat"], 'precision':1})
            cols.append({'name':'percentile_99', 'type':["numericColumn","numberColumnFilter","customNumericFormat"], 'precision':1})
            cols.append({'name':'count', 'type':["numericColumn","numberColumnFilter","customNumericFormat"], 'precision':0})
            return cols

    def show_daily_stats(self):
        def percentile(n):
            def percentile_(x):
                return np.percentile(x, n)
            percentile_.__name__ = 'percentile_%s' % n
            return percentile_
            
        jahr = st.sidebar.selectbox('Jahr', options = range(self.start_jahr, self.end_jahr+1))
        monat = st.sidebar.selectbox('Monat', options = range(1, 13))
        text = f"### Tages-Statistik der Luftschadstoffe {', '.join(self.parameters)} für Station {self.station['name']} im {config.MONTHS_DICT[monat]} {jahr}."
        st.markdown(text)
        _df = self.df_data[(self.df_data['jahr']==jahr) & (self.df_data['monat'] == monat)]
        for par in self.parameters:
            st.markdown(f'**{par}**')
            _stats = _df.groupby(['datum'])[par].agg(['min','max','mean', 'std', 'count', percentile(5), percentile(25), percentile(50), percentile(75), percentile(90), percentile(95), percentile(99)]).reset_index()
            tools.show_table(_stats, self.get_cols(), tools.get_table_settings(_stats))
            st.markdown(tools.get_table_download_link(_stats),unsafe_allow_html=True)


    def show_monthly_stats(self):
        jahr = st.sidebar.selectbox('Jahr', options = range(self.start_jahr, self.end_jahr + 1))

        text = f"### Monats-Statistik der Luftschadstoffe {', '.join(self.parameters)} für Station {self.station['name']} im Jahr {jahr}."
        st.markdown(text)

        _df = self.df_data[self.df_data['jahr']==jahr]
        for par in self.parameters:
            st.markdown(f'**{par}**')
            _stats = _df.groupby(['jahr', 'monat'])[par].agg(['min','max','mean', 'std', 'count', tools.percentile(5), tools.percentile(25), tools.percentile(50), tools.percentile(75), tools.percentile(90), tools.percentile(95), tools.percentile(99)]).reset_index()
            tools.show_table(_stats, self.get_cols(), tools.get_table_settings(_stats))
            st.markdown(tools.get_table_download_link(_stats),unsafe_allow_html=True)

    def show_yearly_stats(self):
        jahre = st.sidebar.slider('Jahr', self.start_jahr, self.end_jahr, (self.start_jahr, self.end_jahr))
        text = f"### Jahres-Statistik der Luftschadstoffe {','.join(self.parameters)} für Station {self.station['name']} für die Jahre {self.start_jahr} bis {self.end_jahr}."
        st.markdown(text)
        _df = self.df_data[self.df_data['jahr'].isin(range(jahre[0], jahre[1]) )]
        for par in self.parameters:
            st.markdown(f'**{par}**')
            _stats = _df.groupby(['jahr'])[par].agg(['min','max','mean', 'std', 'count', tools.percentile(5), tools.percentile(25), tools.percentile(50), tools.percentile(75), tools.percentile(90), tools.percentile(95), tools.percentile(99)]).reset_index()
            tools.show_table(_stats, self.get_cols(), tools.get_table_settings(_stats))
            st.markdown(tools.get_table_download_link(_stats),unsafe_allow_html=True)

    def show_menu(self):
        _station_id = st.sidebar.selectbox('Station', list(self.dic_stations.keys()),
            format_func=lambda x: self.dic_stations[x])    
        self.station = self.df_stations.loc[_station_id]
        type_options = ['nach Jahr', 'nach Monat', 'nach Tag']
        self.stat_type = st.sidebar.selectbox("Statistik", options=type_options)
        self.parameters = st.sidebar.multiselect("Parameters",options = list(self.df_parameters.columns), default=list(self.df_parameters.columns))
        
        if self.stat_type == 'nach Jahr':
            self.show_yearly_stats()
        elif self.stat_type == 'nach Monat':
            self.show_monthly_stats()
        elif self.stat_type == 'nach Tag':
            self.show_daily_stats()
        elif self.stat_type == 'Grenzwert Überschreitungen':
            self.show_exceedances()

        
    