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
import config as cn

plot_width = 800
plot_height = 300


class App:
    """
    """

    def __init__(self, df_data, df_stations, df_parameters):

        self.df_parameters = df_parameters
        self.df_data = tools.add_time_columns(df_data)
        self.df_stations = df_stations
        self.df_stations.set_index("id", inplace=True)
        self.dic_stations = df_stations['name'].to_dict()
        self.station = {}
        self.lst_parameters = list(df_parameters.columns)
        self.start_jahr =  int(self.df_data['jahr'].min() + 1)
        self.end_jahr = int(self.df_data['jahr'].max())
        self.settings = {}
            
        self.plot_type_def =  {
            'linechart': {
                'legend': 'Liniendiagramm', 
                'lst_time_agg': {
                    'Jahr':{'col':'mitte_jahr', 'agg_interval': 'Jahr', 'title': 'Jahresmittelwerte', 'legend':"Jahresmittel",'settings':['parameters','date_from','date_to','show_band','mov_average_frame','show_guidelines'], 'defaults':{'date_from': datetime(self.start_jahr,1,1),'date_to':datetime.today(),'show_guidelines':True} },
                    'Monat':{'col':'mitte_monat', 'agg_interval': 'Monat', 'title': "Monats-Mittelwerte ({} bis {})", 'legend':"Monatsmittel",'settings':['parameters','date_from','date_to','show_band','mov_average_frame','show_guidelines'], 'defaults':{'date_from': datetime.today()-timedelta(365),'date_to':datetime.today(),'show_guidelines':True} },
                    'Woche':{'col':'mitte_woche', 'agg_interval': 'Woche', 'title': "Wochen-Mittelwerte ({} bis {})", 'legend':"Wochenmittel",'settings':['parameters','date_from','date_to','show_band','mov_average_frame','show_guidelines'], 'defaults':{'date_from': datetime(self.start_jahr,1,1),'date_to':datetime.today(),'show_guidelines':True} },
                    'Tag':{'col':'datum', 'agg_interval': 'Tag', 'title': 'Monatsmittelwerte nach Jahr', 'legend':f"Tagesmittel",'settings':['parameters','date_from','date_to','show_band','mov_average_frame','show_guidelines'], 'defaults':{'date_from': datetime(self.start_jahr,1,1),'date_to':datetime.today(),'show_guidelines':True} },
                    'Stunde':{'col':'zeit', 'agg_interval': 'Stunde', 'title': 'Wochenmittelwerte nach Jahr', 'legend':"Stundenmittel",'settings':['parameters','date_from','date_to','show_band','mov_average_frame','show_guidelines'], 'defaults':{'date_from': datetime(self.start_jahr,1,1),'date_to':datetime.today(),'show_guidelines':True} },
                },
            },
            'barchart': {
                'legend': 'Säulendiagramm', 
                'lst_time_agg': {
                    'Jahr':{'col':'jahr', 'agg_interval': 'Jahr', 'title': 'Jahresmittelwerte', 'legend':'Jahresmittel','settings':['parameters','years','show_guidelines'], 'defaults':{'parameters':'PM10','years':[self.start_jahr,self.end_jahr],'show_guidelines':False}, 'occurrence_expr': 'in'},
                    'Monat':{'col':'monat', 'agg_interval': 'Monat', 'title': "Monats-Mittelwerte ({} bis {})", 'legend':'Monatsmittel','settings':['parameters','years','show_guidelines'], 'defaults':{'parameters':'PM10','years':[self.start_jahr,self.end_jahr],'show_guidelines':False}, 'occurrence_expr': 'im'},
                    'Woche':{'col':'woche', 'agg_interval': 'Woche', 'title': "Wochen-Mittelwerte ({} bis {})", 'legend':'Wochenmittel','settings':['parameters','years','show_guidelines'], 'defaults':{'parameters':'PM10','years':[self.start_jahr,self.end_jahr],'show_guidelines':False}, 'occurrence_expr': 'in Woche'},
                    'Jahr-Monat':{'col':'mitte_monat', 'agg_interval': 'Jahr und Monat', 'title': 'Monatsmittelwerte nach Jahr', 'legend':'Monatsmittel','settings':['parameters','years','show_guidelines'], 'defaults':{'parameters':'PM10','years':[self.start_jahr,self.end_jahr],'show_guidelines':False}, 'occurrence_expr': 'im'},
                    'Jahr-Woche':{'col':'mitte_woche', 'agg_interval': 'Jahr und Woche', 'title': 'Wochenmittelwerte nach Jahr', 'legend':'Wochenmittel','settings':['parameters','years','show_guidelines'], 'defaults':{'parameters':'PM10','years':[self.start_jahr,self.end_jahr],'show_guidelines':False}, 'occurrence_expr': 'in Woche'},
                }
            },
            'boxplot': {
                'legend': 'Boxplot', 
                'lst_time_agg': {
                    'Jahr':{'col':'jahr', 'title': 'Jahresmittelwerte', 'legend':'Jahresmittel'},
                    'Monat':{'col':'monat', 'title': "Monats-Mittelwerte ({} bis {})", 'legend':'Monatsmittel'},
                    'Woche':{'col':'woche', 'title': "Wochen-Mittelwerte ({} bis {})", 'legend':'Wochenmittel'},
                    'Jahr-Monat':{'col':'mitte_monat', 'title': 'Monatsmittelwerte nach Jahr', 'legend':'Monatsmittel'},
                    'Jahr-Woche':{'col':'mitte_woche', 'title': 'Wochenmittelwerte nach Jahr', 'legend':'Wochenmittel'}
                },
            },
            'heatmap': {
                'legend': 'Heatmap', 
                'lst_time_agg': {
                    'Jahr':{'col':'jahr', 'title': 'Jahresmittelwerte', 'legend':'Jahresmittel'},
                    'Monat':{'col':'monat', 'title': "Monats-Mittelwerte ({} bis {})", 'legend':'Monatsmittel'},
                    'Woche':{'col':'woche', 'title': "Wochen-Mittelwerte ({} bis {})", 'legend':'Wochenmittel'},
                    'Jahr-Monat':{'col':'mitte_monat', 'title': 'Monatsmittelwerte nach Jahr', 'legend':'Monatsmittel'},
                    'Jahr-Woche':{'col':'mitte_woche', 'title': 'Wochenmittelwerte nach Jahr', 'legend':'Wochenmittel'}
                },
            }           
        }
        plot_legends = [x['legend'] for x in self.plot_type_def.values()]
        plot_keys = [x for x in self.plot_type_def.keys()]
        self.plot_type_options = dict(zip(plot_keys, plot_legends))
    
    def filter_data(self):
        df = self.df_data

        if 'date_from' in self.settings:
            start_series = self.df_data['datum'].min().to_pydatetime().date()
            end_series = self.df_data['datum'].max().to_pydatetime().date()
            if self.settings['date_from'] > start_series or self.settings['date_to'] < end_series:
                df = df[(df['zeit'].dt.date >= self.settings['date_from']) & (df['zeit'].dt.date <= self.settings['date_to'])]
        if 'years' in self.settings:
            if self.settings['years'][0] != self.start_jahr or self.settings['years'][1] != self.end_jahr:
                df = df[df['jahr'].isin(range(self.settings['years'][0], self.settings['years'][1]))]
        if self.settings['agg_time'] == 'Monat-Stunde':
            df = df[df['monat']==self.settings['monat']]
        return df
    

    def get_settings(self, required_options, defaults):
        """
        available options: ['agg_time','parameters','date_from','show_band','mov_average_frame','show_guidelines', 'years']
        """
        for x in required_options:
            if x == 'parameters':
                self.settings['parameters'] = st.sidebar.multiselect("Parameters", options = list(self.df_parameters.columns), default=list(self.df_parameters.columns))
            if x == 'years':
                self.settings['years'] = st.sidebar.slider('🔍Jahr', self.start_jahr, self.end_jahr, defaults['years'])
            if x == 'date_from':
                self.settings['date_from'] = st.sidebar.date_input('Von Datum', min_value=datetime(2003,1,1), max_value=datetime.now(), value=defaults['date_from'])
                self.settings['date_to'] = st.sidebar.date_input('Bis Datum', min_value=datetime(2003,1,1), max_value=datetime.now(), value=defaults['date_to'])
            if x == 'show_band':
                self.settings['show_band'] = st.sidebar.checkbox("Zeige 90% Fläche")
            if x == 'mov_average_frame':
                self.settings['mov_average_frame'] = st.sidebar.number_input("Zeige gleitendes Mittel (0 für nicht Anzeigen)", min_value=0, max_value=int(366/2))
            if x == 'show_guidelines':
                self.settings['show_guidelines'] = st.sidebar.checkbox('Zeige Grenzwerte', True)

    def show_boxplot(self):  
        def get_text(df, par):
            
            text = f"Diese Figur zeigt Zeitreihe von {par} von {self.settings['years'][0]} bis {self.settings['years'][1]}. "\
                f" die Werte sind nach {self.settings['agg_time']} aggregiert. Jede Box zeigt die Verteilung von 50% der Daten (25. - 75. Perzentil). Die Ausgezogenen Linien repräsentieren "\
                "1.5 * die Standardabweichung, was zirka 95% der Werte in der Verteilung entspricht. Alle Werte, die kleiner als 1.5 x die Standardabweichung oder grösser als 1.5 x die Standardabweichung sind, "\
                " u +- 1.5 Std entspricht in einer Normalveretilung rung 87% der Werte. Werte die ausserhalb dieses Intervall fallen, werden als Extremwerte bezeichnet und sind als individuelle Symbole (Kreise) geplottet."
            return text 
        
        
        def get_settings():
            self.settings['agg_time'] = st.sidebar.selectbox("Aggregiere Messungen nach",options=['Jahr','Monat','Woche','Tag'])
            self.settings['parameters'] = st.sidebar.multiselect("Parameters",options = list(self.df_parameters.columns), default=list(self.df_parameters.columns))
            self.settings['years'] = st.sidebar.slider('🔍Jahr', self.start_jahr, self.end_jahr, (self.start_jahr, self.end_jahr))
            if self.settings['agg_time'] == 'Monat-Stunde':
                self.settings['monat'] = st.sidebar.selectbox("Parameter",options=list(config.MONTHS_DICT.values()))
            self.settings['show_guidelines'] = st.sidebar.checkbox('Zeige Grenzwerte', True)

        
        def aggregate_data(df,par):   
            dict_agg_variable = {
                'Jahr': 'mitte_jahr',
                'Monat':'mitte_monat',
                'Woche':'mitte_woche',
                'Tag': 'datum',
                'Stunde': 'zeit'}
            
            par_title = par.replace('.','')  # remove dot, as it cannot be displayed in aggrid 
            t_agg =   dict_agg_variable[self.settings['agg_time']]       
            df = df[[par] + [t_agg]]
            df = df.rename(columns={par: par_title})
            self.settings['plot_title'] = f"{par} an Station {self.station['name']}: {dict_titles[self.settings['agg_time']]}"
            self.settings['tooltip'] = list(df.columns)
            self.settings['x'] = alt.X(f"{t_agg}:T", 
                axis=alt.Axis(title=''))
            self.settings['y'] = alt.Y(f"{par_title}:Q")
            return df

        def show_plot(df):
            chart = alt.Chart(df).mark_boxplot().encode(  
                        x=self.settings['x'],
                        y=self.settings['y'],
                        tooltip = self.settings['tooltip']
                    ).properties(width=plot_width, height=plot_height, title=self.settings['plot_title'])
            
            st.altair_chart(chart)
        
        get_settings()
        dict_titles = {'Jahr':'Jahresmittelwerte', 
            'Monat':f"Monats-Mittelwerte ({self.settings['years'][0]} bis {self.settings['years'][1]})",
            'Woche':f"Wochen-Mittelwerte ({self.settings['years'][0]} bis {self.settings['years'][1]})",
            'Tag': f"Tagesmittelwerte ({self.settings['years'][0]} bis {self.settings['years'][1]})",
            'Stunde': 'Stunden-Mittelwerte',
            'Jahr-Monat':'Monatsmittelwerte nach Jahr',
            'Jahr-Woche':'Wochenmittelwerte nach Jahr'
        }

        for par in self.settings['parameters']:
            df = self.filter_data()
            df = aggregate_data(df,par)
            show_plot(df)
            st.markdown(get_text(df, par))
            with st.beta_expander('Data'):
                AgGrid(df)
                st.markdown(tools.get_table_download_link(df), unsafe_allow_html=True)


    def show_linechart(self):  
        def get_text(df, par):
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

            text = f"Diese Figur zeigt Zeitreihe von {par} von {self.settings['date_from'].strftime('%d.%m.%Y')} bis {self.settings['date_to'].strftime('%d.%m.%Y')}. "\
                f"Die Messwerte wurden zu einem Wert pro {self.settings['agg_time']['agg_interval']} aggregiert. Diese Werte werden durch die durchgezogene Linie dargestellt.{band_expr()}{mov_avg()}"
            return text 
        

        def prepare_data(df, par):
            par_title = par.replace('.','')  # remove dot, as it cannot be displayed in aggrid 
            t_agg = self.settings['agg_time']
            df = df.melt(id_vars=[t_agg['col']], value_vars=par)
            df = df.groupby([t_agg['col'], 'variable'])['value'].agg(['mean', tools.percentile(5), tools.percentile(95)]).reset_index()
            df = df.rename(columns = {'variable': 'Legende', 'mean': 'Wert'})
            return df, par_title

        def prepare_plot(df, par, par_title):
            def get_lines():
                lines = []
                colors = []
                if self.settings['show_guidelines']:
                    guidelines = self.df_parameters[par]['guidelines']
                    # makre sure that e.g. a limit for the daily average is not shown with data averaged yearly as it might suggest
                    # that things are perfect
                    for gl in guidelines:
                        if tools.is_valid_timeagg(gl["time_agg_field"], self.settings['agg_time']['col']):
                            overlay = pd.DataFrame({'y': [gl['value']], 'Legende': [gl['legend']]})
                            line = alt.Chart(overlay).mark_rule(strokeWidth=2).encode(
                                    y="y", 
                                    color=alt.Color("Legende:N")
                            )
                            lines.append(line)
                            colors.append(gl['color'])
                    colors.append('steelblue')
                return lines, colors

            t_agg = self.settings['agg_time']
            self.settings['lines'], legend_colors = get_lines()
            self.settings['plot_title'] = f"{par} an Station {self.station['name']}: {t_agg['title']}"
            self.settings['tooltip'] = list(df.columns)
            self.settings['color'] = alt.Color('Legende:N', 
                scale=alt.Scale(range=legend_colors),
                # sort = alt.EncodingSortField( 'order', order = 'ascending' ),
            )

            if t_agg['col'] in ['jahr','monat','woche']:
                self.settings['x'] = alt.X(f"{t_agg['col']}:N", 
                    axis=alt.Axis(title=''))
            else:
                self.settings['x'] = alt.X(f"{t_agg['col']}:T", 
                    axis=alt.Axis(title='', format="%b %Y"))
            self.settings['y'] = alt.Y(f"Wert:Q", 
                axis=alt.Axis(title='Konzentration in µg/m3'))
            self.settings['color'] = alt.Color('Legende')
            self.settings['y_par'] = par

        def show_plot(df):
            chart = alt.Chart(df).mark_line().encode(  
                x=self.settings['x'],
                y=self.settings['y'],
                color=self.settings['color'],
                tooltip = self.settings['tooltip']
            ).properties(width=plot_width,height=plot_height,title=self.settings['plot_title'])
            
            if self.settings['show_band']:
                band = alt.Chart(df).mark_area(
                    opacity=0.3
                ).encode(
                    x=self.settings['x'],
                    y='percentile_5',
                    y2='percentile_95',
                    color=alt.Color('Legende')
                )
            if self.settings['mov_average_frame']>0:
                df['legend_mov_avg'] = 'Gleitendes Mittel'
                line_mov_avg = alt.Chart(df).mark_line(
                    strokeDash=[5,2],
                    size=2,
                    color="legend_mov_avg:N",
                ).transform_window(
                    rolling_mean=f"mean(Wert)",
                    frame=[-self.settings['mov_average_frame'], self.settings['mov_average_frame']]
                ).encode(
                    x=self.settings['x'],
                    y='rolling_mean:Q',
                )

            chart += band if self.settings['show_band'] else chart
            chart = chart + line_mov_avg if self.settings['mov_average_frame'] > 0 else chart
            if self.settings['show_guidelines']:
                for line in self.settings['lines']:
                    chart += line
            st.altair_chart(chart)
        

        self.get_settings(self.settings['agg_time']['settings'], self.settings['agg_time']['defaults'])
        
        for par in self.settings['parameters']:
            df = self.filter_data()
            df, par_title = prepare_data(df, par)
            prepare_plot(df, par, par_title)
            show_plot(df)
            st.markdown(get_text(df,par))
            with st.beta_expander('Data'):
                AgGrid(df)
                st.markdown(tools.get_table_download_link(df), unsafe_allow_html=True)


    def show_barchart(self):
        def get_text(df,par,par_title):
            def get_guidelines():
                result = ""
                if self.settings['show_guidelines']:
                    result = f" Die horizontalen Linien zeigen den Grenzwert für diesen Schadstoff."
                return result

            def min_max_comment():
                def get_occurrence_expression(t):
                    return f"{t_agg['occurrence_expr']} {t}"

                unit = self.df_parameters[par]['unit']
                min_val = df[par_title].min()
                rec = df[df[par_title]==min_val]
                t_agg = self.settings['agg_time']
                min_time = rec[t_agg['col']].iloc[0]

                max_val = df[par_title].max()
                rec = df[df[par_title]==max_val]
                max_time = rec[t_agg['col']].iloc[0]

                avg_val = df[par_title].mean() 

                text = (f" Der durchschnittliche Wert beträgt {avg_val: .1f}{unit}. Der tiefste Wert von {min_val: .1f}{unit} wurde {get_occurrence_expression(min_time)} erreicht,\n"
                    f" das Maximum von {max_val: .1f}{unit} trat {t_agg['occurrence_expr']} {max_time} auf.")
                return text
                
            
            min_max_comment()
            text = f"Diese Figur zeigt Zeitreihe von {par} von {self.settings['years'][0]} bis {self.settings['years'][1]} an Station {self.station['name']}. "\
                f"Die Messwerte wurden zu einem Wert pro {self.settings['agg_time']['agg_interval']} aggregiert (Mittelwert).{min_max_comment()}{get_guidelines()}"
            return text 

        def prepare_data(df, par):
            par_title = par.replace('.','')  # remove dot, as it cannot be displayed in aggrid 
            t_agg = self.settings['agg_time']
            df = df.groupby(t_agg['col'])[par].agg(['mean'])
            df = df.rename(columns = {'mean': par_title})
            df['Legende'] = t_agg['legend']
            df = df.reset_index()
            if t_agg['col']=='monat':
                df = df.replace({'monat': cn.MONTHS_DICT})
            
            return df, par_title

        def prepare_plot(df, par, par_title):
            def get_lines():
                lines = []
                colors = []
                if self.settings['show_guidelines']:
                    guidelines = self.df_parameters[par]['guidelines']
                    for gl in guidelines:
                        overlay = pd.DataFrame({'y': [gl['value']], 'Legende': [gl['legend']]})
                        line = alt.Chart(overlay).mark_rule(strokeWidth=2).encode(
                                y="y", 
                                color=alt.Color("Legende:N")
                        )
                        lines.append(line)
                        colors.append(gl['color'])
                colors.append('steelblue')
                return lines, colors

            t_agg = self.settings['agg_time']
            self.settings['lines'], legend_colors = get_lines()
            self.settings['plot_title'] = f"{par} an Station {self.station['name']}: {t_agg['title']}"
            self.settings['bar_width'] = plot_width / 2 / len(df) 
            self.settings['tooltip'] = list(df.columns)
            self.settings['color'] = alt.Color('Legende:N', 
                scale=alt.Scale(range=legend_colors),
                # sort = alt.EncodingSortField( 'order', order = 'ascending' ),
            )
            if t_agg['col'] == 'monat':
                self.settings['x'] = alt.X(f"{t_agg['col']}:N", 
                    axis=alt.Axis(title=''),
                    sort=list(cn.MONTHS_REV_DICT.keys()))
            elif t_agg['col'] in ['jahr','woche']:
                self.settings['x'] = alt.X(f"{t_agg['col']}:N", 
                    axis=alt.Axis(title=''))
            else:
                self.settings['x'] = alt.X(f"{t_agg['col']}:T", 
                    axis=alt.Axis(title='', format="%b %Y"))
            if t_agg['col'] == 'monat':
                self.settings['y'] = alt.Y(f"{par_title}:Q", 
                    axis=alt.Axis(title='Konzentration in µg/m3'),
                )
            else:
                self.settings['y'] = alt.Y(f"{par_title}:Q", 
                    axis=alt.Axis(title='Konzentration in µg/m3'))
            self.settings['y_par'] = par
            
                #self.settings['x_scale'] = (1,23)
            

        def show_plot(df):
            chart = alt.Chart(df).mark_bar(clip=True, width = self.settings['bar_width']).encode(
                x=self.settings['x'], 
                y=self.settings['y'], 
                color = self.settings['color'], 
                tooltip = self.settings['tooltip'],
            ).properties(width=plot_width,height=plot_height,title=self.settings['plot_title'])
            
            if self.settings['show_guidelines']:
                for line in self.settings['lines']:
                    chart += line
            st.altair_chart(chart)  #.resolve_scale(color='independent') 


        self.get_settings(self.settings['agg_time']['settings'],self.settings['agg_time']['defaults'])
        
        for par in self.settings['parameters']:
            df = self.filter_data()
            df, par_title = prepare_data(df, par)
            prepare_plot(df, par, par_title)
            show_plot(df)
            st.markdown(get_text(df,par, par_title))
            with st.beta_expander('Data'):
                AgGrid(df)
                st.markdown(tools.get_table_download_link(df), unsafe_allow_html=True)


    def show_heatmap(self):
        def get_settings():
            self.settings['agg_time'] = st.sidebar.selectbox("Aggregiere Messungen nach",options=['Monat','Tag','Stunde'])
            self.settings['parameters'] = st.sidebar.multiselect("Parameters",options = list(self.df_parameters.columns), default=list(self.df_parameters.columns))
            self.settings['years'] = st.sidebar.slider('🔍Jahr', self.start_jahr, self.end_jahr, (self.start_jahr, self.end_jahr))
            if self.settings['agg_time'] in ('Tag','Stunde'):
                self.settings['monat'] = st.sidebar.selectbox("Parameter",options=list(config.MONTHS_DICT.values()))

        def aggregate_data(df,par):   
            par_title = par.replace('.','')  # remove dot, as it cannot be displayed in aggrid 
            df['monat'] = df['monat'].replace(config.MONTHS_DICT)
            t_agg = dict_agg_variable[self.settings['agg_time']]
            df = df.groupby(t_agg['group_by'])[par].agg(['mean'])
            df = df.rename(columns={'mean': par_title}).reset_index()
            self.settings['plot_title'] = f"{par} an Station {self.station['name']}: {dict_titles[self.settings['agg_time']]}"
            self.settings['tooltip'] = list(df.columns)
            
            self.settings['x'] = alt.X(t_agg['x'], 
                sort=list(cn.MONTHS_REV_DICT.keys()),
                axis=alt.Axis(title=t_agg['x_title'])
            )
            self.settings['y'] = alt.Y(t_agg['y'], 
                sort=list(cn.MONTHS_REV_DICT.keys()),
                axis=alt.Axis(title=t_agg['y_title']))
            self.settings['color'] = alt.Color(f"{par_title}:Q")
            return df

        
        def show_plot():
            chart = alt.Chart(df).mark_rect().encode(  
            x=self.settings['x'],
            y=self.settings['y'],
            color=self.settings['color'],
            tooltip = self.settings['tooltip']
            ).properties(width=plot_width, height=plot_height*1.5, title=self.settings['plot_title'])
            st.altair_chart(chart)

        
        dict_agg_variable = {
            'Monat':{'x':'monat:N','y':'jahr:N','group_by':['monat','jahr'],'x_title':'Monat','y_title':'Jahr'},
            'Tag':{'x':'tag:O','y':'monat:O','group_by':['tag','monat'],'x_title':'Tag','y_title':'Monat'},
            'Stunde':{'x':'stunde:N','y':'tag:N','group_by':['stunde','tag'],'x_title':'Stunde','y_title':'Tag'},
        }
        st.write(self.settings['plot_type'])
        get_settings(['agg_time','parameters','years','show_guidelines'])
        dict_titles = {'Jahr':'Jahresmittelwerte', 
            'Monat':f"Monats-Mittelwerte ({self.settings['years'][0]} bis {self.settings['years'][1]})",
            'Woche':f"Wochen-Mittelwerte ({self.settings['years'][0]} bis {self.settings['years'][1]})",
            'Tag': f"Tagesmittelwerte ({self.settings['years'][0]} bis {self.settings['years'][1]})",
            'Stunde': 'Stunden-Mittelwerte',
            'Jahr-Monat':'Monatsmittelwerte nach Jahr',
            'Jahr-Woche':'Wochenmittelwerte nach Jahr'
        }

        for par in self.settings['parameters']:
            df = self.filter_data()
            df = aggregate_data(df, par)
            show_plot()
            with st.beta_expander('Data'):
                AgGrid(df)
                st.markdown(tools.get_table_download_link(df), unsafe_allow_html=True)


    def show_menu(self):
        _plot_type = st.sidebar.selectbox("Grafiktyp", options=list(self.plot_type_options.keys()),
            format_func=lambda x: self.plot_type_options[x])    
        self.settings['plot_type'] = self.plot_type_def[_plot_type]
        
        _station_id = st.sidebar.selectbox('Station', list(self.dic_stations.keys()),
                format_func=lambda x: self.dic_stations[x])    
        self.station = self.df_stations.loc[_station_id]
        
        time_agg_options = list(self.settings['plot_type']['lst_time_agg'].keys())
        _time_agg = st.sidebar.selectbox("Aggregiere Messungen nach", options=time_agg_options)
        self.settings['agg_time'] = self.settings['plot_type']['lst_time_agg'][_time_agg]

        if _plot_type == 'barchart':
            self.show_barchart()
        elif _plot_type == 'linechart':
            self.show_linechart()
        elif _plot_type == 'boxplot':
            self.show_boxplot()
        elif _plot_type == 'heatmap':
            self.show_heatmap()

        
    