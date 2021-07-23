import streamlit as st
import pandas as pd
import altair as alt
from datetime import datetime, timedelta

import config as cn

LST_MENU = ('Einleitung', '1. August', 'Neujahr')

class App:
    """
    """

    def __init__(self, df_data, df_stations, df_parameters):
        self.df_data = df_data
        self.df_stations = df_stations
        self.dic_stations = df_stations['name'].to_dict()
        self.df_parameters = df_parameters
        self.start_jahr =  int(self.df_data['jahr'].min() + 1)
        self.end_jahr = int(self.df_data['jahr'].max())
        self.settings = {}

    def prepare_data(self):
        def prepare_hourly_data(diff_tage):
            result = pd.DataFrame()
            
            for year in self.settings['years']:
                start_frame = datetime(year,self.settings['ref_month'], self.settings['ref_day']) - timedelta(diff_tage)
                end_frame = datetime(year,self.settings['ref_month'], self.settings['ref_day']) + timedelta(diff_tage)
                time_diff = datetime(year,self.settings['ref_month'], self.settings['ref_day']) - datetime(2000,self.settings['ref_month'], self.settings['ref_day'])
                df = self.df_data[ (self.df_data['datum'] >= start_frame) & (self.df_data['datum'] <= end_frame) ]
                df['norm_time'] = df['zeit'] - time_diff
                df['jahr'] = year # make sure that newyear works as well
                if len(result)==0:
                    result = df
                else:
                    result = pd.concat([result,df], axis=0)
            #result['norm_time'] = pd.to_datetime([f"2000-{m}-{d} {h}:00" for m,d,h in zip(result.monat, result.tag, result.stunde)])
            
            return result
        
        def prepare_daily_data(diff_tage):
            result = pd.DataFrame()
            
            for year in self.settings['years']:
                start_frame = datetime(year,self.settings['ref_month'], self.settings['ref_day']) - timedelta(diff_tage)
                end_frame = datetime(year,self.settings['ref_month'], self.settings['ref_day']) + timedelta(diff_tage)
                time_diff = datetime(year,self.settings['ref_month'], self.settings['ref_day']) - datetime(2000,self.settings['ref_month'], self.settings['ref_day'])
                df = self.df_data[ (self.df_data['datum'] >= start_frame) & (self.df_data['datum'] <= end_frame) ]
                df = df.groupby(['datum'])['PM10'].agg(['mean']).reset_index()
                df['norm_time'] = df['datum'] - time_diff
                df['jahr'] = year # make sure that newyear works as well
                df.rename(columns={'mean':'PM10'}, inplace = True)
                if len(result)==0:
                    result = df
                else:
                    result = pd.concat([result,df], axis=0)
            #result['norm_time'] = pd.to_datetime([f"2000-{m}-{d} {h}:00" for m,d,h in zip(result.monat, result.tag, result.stunde)])
            
            return result
        
        diff = (self.settings['interval']-1)/2
        if diff <=0:
            diff = 1
        if self.settings['t_agg'] == 'Stundenwerte':
            return prepare_hourly_data(diff)
        else:
            return prepare_daily_data(diff)

    
    def prepare_plot(self):
        dic_title = {'1. August': 'Feinstaub Konzentrationen am 1. August', 'Neujahr': 'Feinstaub Konzentrationen am Neujahr'}
        self.settings['x'] = alt.X()
        self.settings['x'] = alt.X(f"norm_time:T", 
                axis=alt.Axis(title='', format='%d.%m :%H'))
        self.settings['y'] = alt.Y('PM10:Q', axis=alt.Axis(title='PM10 (µg/m³)'))
        self.settings['color'] = 'jahr:N'
        self.settings['color'] = 'jahr:N'
        self.settings['plot_title'] = dic_title[self.settings['menu']]
        self.settings['tooltip'] = [alt.Tooltip('norm_time:T', format='%d.%m %H'), alt.Tooltip('PM10:Q', format='.1f')]
    
    def show_plot(self, df):
        line = alt.Chart(pd.DataFrame({'y': [50]})).mark_rule(strokeWidth=2, color = "red").encode(y=alt.Y('y:Q', axis=alt.Axis(title='')))
                    
        chart = alt.Chart(df).mark_line().encode(  
            x=self.settings['x'],
            y=self.settings['y'],
            color=self.settings['color'],
            tooltip=self.settings['tooltip'],
        ).properties(width=cn.default_plot_width,height=cn.default_plot_height,title=self.settings['plot_title'])
        
        st.altair_chart(chart + line)

    def show_effects(self):
       pass

    def get_settings(self):
        _station_id = st.sidebar.selectbox('Station', list(self.dic_stations.keys()),
        format_func=lambda x: self.dic_stations[x])    
        self.station = self.df_stations.loc[_station_id]
        self.settings['t_agg'] = st.sidebar.selectbox('zeitliche Auflösung', ['Stundenwerte', 'Tagesmittel'])
        self.settings['years'] = st.sidebar.multiselect('Jahre',options= range(self.start_jahr, self.end_jahr), default = range(self.start_jahr, self.end_jahr) )
        self.settings['interval'] = st.sidebar.number_input('Zeitfenster in Tagen', self.settings['interval'])
        

    def show_firework_effects(self):
        st.image('./images/feuerwerk.jpg', caption=None, width=None, use_column_width='auto', clamp=False, channels='RGB', output_format='auto')
        st.markdown('[Quelle Abbildung](https://www.bs.ch/bilddatenbank#tree=7195)')

        text = """Feuerwerke erzeugen Rauch und damit Feinstaub. Die resultierende Zunahme der PM10 und PM2.5 Konzentrationen lassen sich in der basler Luft in den meisten Jahren gut 
am Silvester und am 1. August beobachten. Zwar sind die extrem hohen Werte in der Regel von kurzer Dauer, doch können sie, bei bereits 
erhöhter Basiskonzentration der Schadstoffe, zur Überschreitung des Tagesmittels von 50µg/m³ für PM10 führen. Dies war zum Beispiel in 2008 und 2010 mit Werten über 400µg/m³.
der Fall. Gut unterscheiden lassen sich am Nationalfeiertag auch das Feuerwerk der Stadt Basel, welches am 30. Juli gezündet wird und die privaten Feuerwerke, die am Abend des 1. August stattfinden und eine zwar tiefere, aber länger 
andauernde Feinstaub-Spitze verursachen.

In verschiedenen Jahren treten keine prominente Spitzenwerte auf, da wegen der herrschenden Windrichtung die Schadstoffwolke nicht in Richtung Messtation geblasen wurde, oder wenn das 
Feuerwerk abgesagt wurde, zum Beispiel in 2018 (Trockenheit-bedingt) oder im 2020 (Covid-19 bedingt). 

Wichtiger als die Spitze selbst ist die Fläche unter der Spitze, d.h. wie lange die Rauchwolke über der Stadt gehangen ist: Kurze hohe Spitzen können den Tagesmittelwert weniger stark beeinflussen 
als weniger hohe dafür aber lang andauernde Spitzen. So waren die Spitzenwerte von PM10 am 2.8.2011 nur knapp über 85, dafür klangen die Werte erst nach ca. 5 Stunden ab 
und der Tagesmittelwert von 54µg/m³ überschritt den Grenzwert von PM10.

Auf dieser Seite können die Effekte der Feuerwerke über mehrere Jahre hinweg vergleichen. Die Stundewerte geben die Spitzen in der höchsten Auflösung wieder. 
Die Aggregation nach Tag (Mittelwert) beantwortet hingegen die Fragestellung, ob das Feuerwerk zu einer Überschreitung des Tages-Grenzwerts geführt hat. 

Weitere Informationen:
- [Feuerwerke und Umweltbelastung](https://www.bafu.admin.ch/bafu/de/home/themen/luft/dossiers/feuerwerke-und-umweltbelastung.html)
- [Artikel von www.scienceinschool.org](https://www.scienceinschool.org/de/2011/issue21/fireworks)
"""
        st.markdown(text)


    def show_menu(self):
        self.settings['menu'] = st.sidebar.selectbox('Auswahl', options = LST_MENU)

        if self.settings['menu'] == 'Einleitung':
            self.show_firework_effects()
        elif self.settings['menu'] == '1. August':    
            self.settings['interval'] = 3
            self.get_settings()
            self.settings['ref_month'] = 8
            self.settings['ref_day'] = 1
            df = self.prepare_data()
            self.prepare_plot()
            self.show_plot(df)
        else:
            self.settings['interval'] = 21
            self.get_settings()
            self.settings['ref_month'] = 1
            self.settings['ref_day'] = 1
            df = self.prepare_data()
            self.prepare_plot()
            self.show_plot(df)

        
    