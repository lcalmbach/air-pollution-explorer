import streamlit as st
from st_aggrid import AgGrid
import pandas as pd
import numpy as np
import altair as alt
import calendar
from pandas._libs.tslibs.timestamps import Timestamp

from queries import qry
import config
from st_aggrid import AgGrid
from datetime import datetime, timedelta
import tools

plot_width = 800
plot_height = 300


class App:
    """
    """

    def __init__(self, df_data, df_stations, df_parameters):
        def add_time_columns(df):
            self.df_parameters = df_parameters
            self.df_data = df_data
            self.df_data['datum'] = pd.to_datetime(self.df_data['zeit']).dt.date
            self.df_data['datum'] = pd.to_datetime(self.df_data['datum'])
            self.df_data['woche'] = df_data['zeit'].dt.isocalendar().week
            self.df_data['jahr'] = df_data['zeit'].dt.year    
            self.df_data['monat'] = df_data['zeit'].dt.month 
            self.df_data['mitte_woche'] = pd.to_datetime(df_data['datum']) - pd.to_timedelta(df_data['zeit'].dt.dayofweek % 7 - 2, unit='D')
            #self.df_data['mitte_woche'] = df_data['mitte_woche_datum'].dt.date 
            self.df_data['mitte_monat'] = pd.to_datetime(df_data['datum']) - pd.to_timedelta(df_data['zeit'].dt.day + 14, unit='D')
            self.df_data['mitte_jahr'] = pd.to_datetime(df_data['datum']) - pd.to_timedelta(df_data['zeit'].dt.dayofyear + (365/2), unit='D')
            self.df_data['stunde'] = pd.to_datetime(self.df_data['zeit']).dt.hour
            self.df_data['tag'] = pd.to_datetime(self.df_data['zeit']).dt.day
            return df

        self.df_data = add_time_columns(df_data)
        self.df_stations = df_stations
        self.df_stations.set_index("id", inplace=True)
        self.dic_stations = df_stations['name'].to_dict()
        self.station = {}
        self.df_parameters = df_parameters
        self.lst_parameters = list(df_parameters.columns)
        self.start_jahr =  int(self.df_data['jahr'].min() + 1)
        self.end_jahr = int(self.df_data['jahr'].max())
        self.settings = {}
    

    def filter_data(self):
        df = self.df_data
        if 'date_from' in self.settings:
            start_series = self.df_data['datum'].min().to_pydatetime().date()
            end_series = self.df_data['datum'].max().to_pydatetime().date()
            if self.settings['date_from'] > start_series and self.settings['date_to'] < end_series:
                df = df[(df['zeit'].dt.date >= self.settings['date_from']) & (df['zeit'].dt.date <= self.settings['date_to'])]
        if 'years' in self.settings:
            if self.settings['years'][0] != self.start_jahr or self.settings['years'][1] != self.end_jahr:
                df = df[df['jahr'].isin(range(self.settings['years'][0], self.settings['years'][1]))]
        if self.settings['agg_time'] == 'Monat-Stunde':
            df = df[df['monat']==self.settings['monat']]
        return df
    

    def show_boxplot(self):  
        def get_text(df):
            
            text = f"Diese Figur zeigt Zeitreihe von {self.settings['par']} von {self.settings['date_from'].strftime('%d.%m.%Y')} bis {self.settings['date_to'].strftime('%d.%m.%Y')}. "\
                f" die Werte sind nach {self.settings['agg_time']} aggregiert. Jede Box zeigt die Verteilung von 50% der Daten (25. - 75. Perzentil). Die Ausgezogenen Linien repräsentieren "\
                "1.5 * die Standardabweichung, was zirka 95% der Werte in der Verteilung entspricht. Alle Werte, die kleiner als 1.5 x die Standardabweichung oder grösser als 1.5 x die Standardabweichung sind, "\
                " u +- 1.5 Std entspricht in eienr Normalveretilung rung 87% der Werte. Werte die ausserhalb dieses Intervall fallen, werden als Extremwerte bezeichnet und sind als individuelle Symbole (Kreise) geplottet."

            return text 
        
        
        def get_settings():
            self.settings['agg_time'] = st.sidebar.selectbox("Aggregiere Messungen nach",options=['Jahr','Monat','Woche','Tag'])
            self.settings['par'] = st.sidebar.selectbox("Parameter", options=self.lst_parameters)
            self.settings['date_from'] = st.sidebar.date_input('Von Datum',datetime(2003,1,1), datetime.now(),datetime(2003,1,1))
            self.settings['date_to'] = st.sidebar.date_input('Bis Datum',datetime(2003,1,1), datetime.now(), datetime.now())

        
        def aggregate_data(df,):   
            dict_agg_variable = {
                'Jahr': 'mitte_jahr',
                'Monat':'mitte_monat',
                'Woche':'mitte_woche',
                'Tag': 'datum',
                'Stunde': 'zeit'}
            t_agg =   dict_agg_variable[self.settings['agg_time']]       
            df = df[[self.settings['par']] + [t_agg]]
            df = df.rename(columns={self.settings['par']: self.settings['par'].replace('.','')})
            self.settings['tooltip'] = list(df.columns)
            self.settings['x'] = alt.X(f"{t_agg}:T", 
                axis=alt.Axis(title=''))
            self.settings['y'] = alt.Y(f"{self.settings['par'].replace('.','')}:Q", 
                axis=alt.Axis(title='Konzentration in ug/m3'))
            
            return df

        def show_plot(df):
            chart = alt.Chart(df).mark_boxplot().encode(  
            x=self.settings['x'],
            y=self.settings['y'],
            tooltip = self.settings['tooltip']
            ).properties(width=plot_width, height=plot_height)
            
            st.altair_chart(chart)
        
        get_settings()
        df = self.filter_data()
        df = aggregate_data(df)
        show_plot(df)
        st.markdown(get_text(df))
        with st.beta_expander('Data'):
            AgGrid(df)


    def show_linechart(self):  
        def get_text(df):
            def get_parameters():
                if len(self.settings['par'])==1:
                    result = self.settings['par'][0]
                elif len(self.settings['par'])==2:
                    result = f"{self.settings['par'][0] } und {self.settings['par'][0] }"
                elif len(self.settings['par'])>2:
                    result = ", ".join(self.settings['par'][:-1]) + ' und ' + self.settings['par'][-1]
                return result

            def band_expr():
                if self.settings['show_band']:
                    return ' Die leicht durchsichtige Fläche zeigt die Fläche, welche 90% der Werte beinhaltet (von 5% zu 95% Perzentil).'
                else:
                    return ''

            def mov_avg():
                if self.settings['mov_average_frame']:
                    return f" Die gestrichelte Linie zeigt den gleitenden Mittelwert: jeder Punkt dieser Linie ist ein Mittelwert aller Werte, die {self.settings['mov_average_frame']} Tage vor "\
                        f" und {self.settings['mov_average_frame']} Tage nach diesem Zeitpunkt liegen. Je grösser das Zeitfenster, desto mehr wird die Kurve geglättet."
                else:
                    return ''

            text = f"Diese Figur zeigt Zeitreihe von {get_parameters()} von {self.settings['date_from'].strftime('%d.%m.%Y')} bis {self.settings['date_to'].strftime('%d.%m.%Y')}. "\
                f"Die Messwerte wurden zu einem Wert pro {self.settings['agg_time']} aggregiert. Diese Werte werden durch die durchgezogene Linie dargestellt.{band_expr()}{mov_avg()}"
            return text 
        
        
        def get_settings():
            self.settings['agg_time'] = st.sidebar.selectbox("Aggregiere Messungen nach",options=['Monat','Woche','Tag','Stunde'])
            self.settings['par'] = st.sidebar.multiselect("Parameter", options=self.lst_parameters,default=['PM2.5'])
            self.settings['date_from'] = st.sidebar.date_input('Von Datum',min_value=datetime(2003,1,1), max_value=datetime.now(), value = datetime(2003,1,1))
            self.settings['date_to'] = st.sidebar.date_input('Bis Datum',min_value=datetime(2003,1,1), max_value=datetime.now(), value = datetime.now())
            #if self.settings['agg_time'] in ('Tag','Stunde'):
            #    self.settings['monat'] = st.sidebar.selectbox("Monat",options=list(config.MONTHS_DICT.values()))
            self.settings['show_band'] = st.sidebar.checkbox("Zeige 90% Fläche")
            self.settings['mov_average_frame'] = st.sidebar.number_input("Zeige gleitendes Mittel (0 für nicht Anzeigen)", min_value=0, max_value=int(366/2))
        

        def aggregate_data(df,):   
            t_agg =   dict_agg_variable[self.settings['agg_time']]       
            df = df[self.settings['par'] + [t_agg]]
            df = df.melt(id_vars=[t_agg], value_vars=self.settings['par'])
            df = df.groupby([t_agg, 'variable'])['value'].agg(['mean', tools.percentile(5), tools.percentile(95)]).reset_index()
    
            self.settings['tooltip'] = list(df.columns)
            self.settings['x'] = alt.X(f"{t_agg}:T", 
                axis=alt.Axis(title=''))
            self.settings['y'] = alt.Y("mean:Q", 
                axis=alt.Axis(title='Konzentration in ug/m3'))
            self.settings['y_par'] = "mean"
            self.settings['color'] = alt.Color("variable:N")
            
            return df

        def show_plot(df):
            chart = alt.Chart(df).mark_line().encode(  
            x=self.settings['x'],
            y=self.settings['y'],
            color=self.settings['color'],
            tooltip = self.settings['tooltip']
            ).properties(width=plot_width, height=plot_height)
            
            if self.settings['show_band']:
                band = alt.Chart(df).mark_area(
                    opacity=0.3
                ).encode(
                    x=self.settings['x'],
                    y='percentile_5',
                    y2='percentile_95',
                    color = 'variable'
                )
            if self.settings['mov_average_frame']>0:
                line_mov_avg = alt.Chart(df).mark_line(
                    strokeDash=[5,2],
                    size=2
                ).transform_window(
                    rolling_mean=f"mean({self.settings['y_par']})",
                    frame=[-self.settings['mov_average_frame'], self.settings['mov_average_frame']]
                ).encode(
                    x=self.settings['x'],
                    y='rolling_mean:Q',
                    color = alt.Color('variable')
                )

            combi = chart
            combi += band if self.settings['show_band'] else combi
            combi = combi + line_mov_avg if self.settings['mov_average_frame'] > 0 else combi
            st.altair_chart(combi)
        
        dict_agg_variable = {'Jahr':'mitte_jahr', 
            'Monat':'mitte_monat',
            'Woche':'mitte_woche',
            'Tag': 'datum',
            'Stunde': 'zeit'}
        get_settings()
        df = self.filter_data()
        df = aggregate_data(df)
        show_plot(df)
        st.markdown(get_text(df))
        with st.beta_expander('Data'):
            AgGrid(df)


    def show_barchart(self):
        def get_text(df):
            def get_guidelines():
                result = ""
                if self.settings['show_guidelines']:
                    result = f"Die horizontalen Linien zeigen den Grenzwert."
                return result
            text = f"Diese Figur zeigt Zeitreihe von {self.settings['par']} von {self.settings['date_from']} bis {self.settings['date_to']} an Station `{self.station['name']}`. "\
                f"Die Messwerte wurden zu einem Wert pro {self.settings['agg_time']} aggregiert (Mittelwert). {get_guidelines()}"
            return text 

        def get_settings():
            self.settings['agg_time'] = st.sidebar.selectbox("Aggregiere Messungen nach",options=list(dict_agg_variable.keys()))
            self.settings['par'] = st.sidebar.selectbox("Parameter",options=self.lst_parameters)
            self.settings['years'] = st.sidebar.slider('🔍Jahr', self.start_jahr, self.end_jahr, (self.start_jahr, self.end_jahr))
            if self.settings['agg_time'] == 'Monat-Stunde':
                self.settings['monat'] = st.sidebar.selectbox("Parameter",options=list(config.MONTHS_DICT.values()))
            self.settings['show_guidelines'] = st.sidebar.checkbox('Zeige Grenzwerte', True)

        def aggregate_data(df):
            par = self.settings['par'].replace('.','')
            t_agg = dict_agg_variable[self.settings['agg_time']]
            df = df.groupby([t_agg])[self.settings['par']].agg(['mean'])
            df = df.rename(columns = {'mean': self.settings['par'].replace('.','')})
            df = df.reset_index()
            self.settings['plot_title'] = f"{self.settings['par']} an Station {self.station['name']}: {dict_titles[self.settings['agg_time']]}"
            self.settings['bar_width'] = plot_width / 2 / len(df) 
            self.settings['tooltip'] =list(df.columns)
            if t_agg in ['jahr','monat','woche']:
                self.settings['x'] = alt.X(f"{t_agg}:N", 
                    axis=alt.Axis(title=''))
            else:
                self.settings['x'] = alt.X(f"{t_agg}:T", 
                    axis=alt.Axis(title='', format="%b %Y"))
            self.settings['y'] = alt.Y(f"{par}:Q", 
                axis=alt.Axis(title='Konzentration in µg/m3'))
            self.settings['y_par'] = par
                #self.settings['x_scale'] = (1,23)
            
            return df

        def show_plot(df):
            if self.settings['show_guidelines']:
                lines = []
                guidelines = self.df_parameters[self.settings['par']]['guidelines']
                for gl in guidelines:
                    df[gl['legend']] = gl['value']
                    line = alt.Chart(df).mark_rule(color=gl['color']).encode(y=gl['legend'], tooltip=gl['legend'])
                    lines.append(line)

            chart = alt.Chart(df).mark_bar(clip=True, width = self.settings['bar_width']).encode(
                x=self.settings['x'], 
                y=self.settings['y'], 
                tooltip = self.settings['tooltip']
            ).properties(width=plot_width,height=plot_height,title=self.settings['plot_title'])
            if self.settings['show_guidelines']:
                for line in lines:
                    chart += line
                
            st.altair_chart(chart )

        dict_agg_variable = {'Jahr':'jahr', 
            'Monat':'monat',
            'Woche':'woche',
            'Jahr-Monat':'mitte_monat',
            'Jahr-Woche':'mitte_woche'
        }
        get_settings()
        dict_titles = {'Jahr':'Jahresmittelwerte', 
            'Monat':f"Monats-Mittelwerte ({self.settings['years'][0]} bis {self.settings['years'][1]})",
            'Woche':f"Wochen-Mittelwerte ({self.settings['years'][0]} bis {self.settings['years'][1]})",
            'Tag': f"Tagesmittelwerte ({self.settings['years'][0]} bis {self.settings['years'][1]})",
            'Stunde': 'Stunden-Mittelwerte',
            'Jahr-Monat':'Monatsmittelwerte nach Jahr',
            'Jahr-Woche':'Wochenmittelwerte nach Jahr'
        }

        df = self.filter_data()
        df = aggregate_data(df)
        show_plot(df)
        # st.markdown(get_text(df))
        with st.beta_expander('Data'):
            AgGrid(df)


    def show_heatmap(self):
        def get_settings():
            self.settings['agg_time'] = st.sidebar.selectbox("Aggregiere Messungen nach",options=['Monat','Tag','Stunde'])
            self.settings['par'] = st.sidebar.selectbox("Parameter",options=self.lst_parameters)
            self.settings['years'] = st.sidebar.slider('🔍Jahr', self.start_jahr, self.end_jahr, (self.start_jahr, self.end_jahr))
            if self.settings['agg_time'] in ('Tag','Stunde'):
                self.settings['monat'] = st.sidebar.selectbox("Parameter",options=list(config.MONTHS_DICT.values()))

        def aggregate_data(df,):   
            df['monat'] = df['monat'].replace(config.MONTHS_DICT)
            t_agg = dict_agg_variable[self.settings['agg_time']]
            # df = df[[self.settings['par'], 'jahr', 'monat'] + [t_agg]]
            df = df.groupby(t_agg['group_by'])[self.settings['par']].agg(['mean'])
            df = df.rename(columns={'mean': self.settings['par'].replace('.','')}).reset_index()
            self.settings['tooltip'] = list(df.columns)
            self.settings['x'] = alt.X(t_agg['x'], 
                axis=alt.Axis(title=t_agg['x_title']))
            self.settings['y'] = alt.Y(t_agg['y'], 
                axis=alt.Axis(title=t_agg['y_title']))
            #self.settings['y_par'] = self.settings['par'].replace('.','')
            self.settings['color'] = alt.Color(f"{self.settings['par'].replace('.','')}:Q")
            return df

        
        def show_plot():
            chart = alt.Chart(df).mark_rect().encode(  
            x=self.settings['x'],
            y=self.settings['y'],
            color=self.settings['color'],
            tooltip = self.settings['tooltip']
            ).properties(width=plot_width, height=plot_height)
            
            st.altair_chart(chart)

        
        dict_agg_variable = {
            'Monat':{'x':'monat:N','y':'jahr:N','group_by':['monat','jahr'],'x_title':'Monat','y_title':'Jahr'},
            'Tag':{'x':'tag:O','y':'monat:O','group_by':['tag','monat'],'x_title':'Tag','y_title':'Monat'},
            'Stunde':{'x':'stunde:N','y':'tag:N','group_by':['stunde','tag'],'x_title':'Stunde','y_title':'Monat'},
        }
        get_settings()
        dict_titles = {'Jahr':'Jahresmittelwerte', 
            'Monat':f"Monats-Mittelwerte ({self.settings['years'][0]} bis {self.settings['years'][1]})",
            'Woche':f"Wochen-Mittelwerte ({self.settings['years'][0]} bis {self.settings['years'][1]})",
            'Tag': f"Tagesmittelwerte ({self.settings['years'][0]} bis {self.settings['years'][1]})",
            'Stunde': 'Stunden-Mittelwerte',
            'Jahr-Monat':'Monatsmittelwerte nach Jahr',
            'Jahr-Woche':'Wochenmittelwerte nach Jahr'
        }
        df = self.filter_data()
        df = aggregate_data(df)
        show_plot()
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
            self.show_boxplot()
        elif plot_type == 'Heatmap':
            self.show_heatmap()

        
    